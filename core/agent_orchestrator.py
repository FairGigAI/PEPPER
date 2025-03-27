"""Agent orchestrator for coordinating agent interactions and task management."""

import os
import yaml
import asyncio
import time
import uuid
import json
from typing import Dict, Any, List, Type, Optional, Set, TYPE_CHECKING
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import ConfigLoader, BaseAgentConfig, AGENT_CONFIG_TYPES
    from .agent_base import Task, BaseAgent
    from .task_router import TaskRouter
    from .agent_metrics import record_metric
    from .exceptions import TransientError, FatalError, PEPPERError, AgentError
    from .feedback_system import FeedbackSystem, TaskCompletion, MilestoneStatus

# Runtime imports
from .exceptions import TransientError, FatalError, PEPPERError, AgentError
from .agent_metrics import record_metric

class TaskDependency:
    """Represents a task dependency with metadata."""
    
    def __init__(self, task_id: str, agent_id: str, description: str, 
                 depends_on: List[str] = None, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.agent_id = agent_id
        self.description = description
        self.depends_on = depends_on or []
        self.metadata = metadata or {}
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.result = None

class RetryStrategy:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 32.0,
        strategy: str = "exponential"
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'RetryStrategy':
        """Create a RetryStrategy from configuration."""
        return cls(
            max_retries=config.get("retries", 3),
            base_delay=config.get("delay", 1.0),
            max_delay=config.get("max_delay", 32.0),
            strategy=config.get("backoff_strategy", "exponential")
        )
        
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on strategy."""
        if self.strategy == "exponential":
            delay = min(
                self.base_delay * (2 ** (attempt - 1)),
                self.max_delay
            )
        elif self.strategy == "linear":
            delay = min(
                self.base_delay * attempt,
                self.max_delay
            )
        elif self.strategy == "fixed":
            delay = self.base_delay
        else:
            logger.warning(f"Unknown backoff strategy: {self.strategy}, using exponential")
            delay = min(
                self.base_delay * (2 ** (attempt - 1)),
                self.max_delay
            )
        return delay

class AgentOrchestrator:
    """Coordinates agent interactions and manages task execution."""
    
    def __init__(self, config_path: str = "config/project_config.yaml"):
        """Initialize the orchestrator.
        
        Args:
            config_path: Path to the project configuration file
        """
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_dir=os.path.dirname(config_path))
        self.config = self._load_config()
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.router = TaskRouter()
        self.tasks: Dict[str, TaskDependency] = {}
        self.completed_tasks: Dict[str, TaskDependency] = {}
        self.console = Console()
        self.feedback_system = FeedbackSystem(None, None)  # Will be initialized later
        self.milestones: Dict[str, 'MilestoneStatus'] = {}
        
        # Task dependency tracking
        self.task_dependencies: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        
        # Default retry configuration
        self.default_retry_strategy = RetryStrategy()
        self.transient_errors: Dict[Type[Exception], int] = {
            TransientError: 3,
            ConnectionError: 3,
            TimeoutError: 3,
            FileNotFoundError: 1,
            PermissionError: 1
        }
        
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logger.remove()  # Remove default handler
        
        # File handler (without colors)
        logger.add(
            "logs/orchestrator.log",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            rotation="500 MB",
            retention="10 days",
            colorize=True
        )
        
        # Console handler with colors
        logger.add(
            lambda msg: self.console.print(msg, markup=True),
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True,
            enqueue=True
        )
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration using the new ConfigLoader."""
        try:
            # Load system config
            system_config = self.config_loader.load_system_config()
            
            # Load agent configs
            agent_configs = self.config_loader.load_agent_configs()
            
            # Combine configs
            config = {
                "system": system_config,
                "agents": agent_configs,
                "tasks": self.config_loader.load_tasks()
            }
            
            # Convert task configs to TaskDependency objects
            if "tasks" in config:
                config["tasks"] = [
                    TaskDependency(
                        task_id=task.get("id"),
                        agent_id=task.get("agent"),
                        description=task.get("task", ""),
                        metadata={
                            **task.get("metadata", {}),
                            "priority": task.get("priority", "MEDIUM")
                        }
                    )
                    for task in config["tasks"]
                ]
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise FatalError(f"Configuration loading failed: {e}")
            
    async def initialize(self):
        """Initialize the orchestrator and its components."""
        logger.info("Initializing agent orchestrator...")
        
        # Initialize feedback system
        await self.feedback_system.initialize()
        
        # Load existing milestones
        milestone_file = self.feedback_system.data_dir / "milestones.json"
        if milestone_file.exists():
            with open(milestone_file, 'r') as f:
                milestone_data = json.load(f)
                for milestone in milestone_data:
                    self.milestones[milestone["milestone_id"]] = MilestoneStatus(**milestone)
                    
        # Load agent configurations
        agent_configs = self.config.get("agents", {})
        for agent_id, config in agent_configs.items():
            agent_type = config.get("type")
            if agent_type in AGENT_CONFIG_TYPES:
                agent_class = AGENT_CONFIG_TYPES[agent_type]
                self.agents[agent_id] = agent_class(agent_id, config)
            else:
                logger.warning(f"Unknown agent type: {agent_type}")
                
        # Load tasks from config
        self.tasks = {task.task_id: task for task in self.config.get("tasks", [])}
        logger.info(f"Loaded {len(self.tasks)} tasks from config")
        
        # Display available agents
        self._display_agents()
        
    def _display_agents(self):
        """Display available agents and their capabilities."""
        table = Table(title="Available Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        
        for agent_id, agent in self.agents.items():
            table.add_row(
                agent_id,
                agent.__class__.__name__,
                "Ready"
            )
            
        self.console.print(table)
        
    async def add_task(
        self,
        task_id: str,
        agent_id: str,
        task_type: str,
        description: str,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Add a task to the queue with dependencies."""
        # Create task dependency
        task = TaskDependency(
            task_id=task_id,
            agent_id=agent_id,
            description=description,
            depends_on=dependencies or [],
            metadata=metadata
        )
        
        # Add to task queue
        self.tasks[task_id] = task
        
        # Update dependency tracking
        self.task_dependencies[task_id] = set(dependencies or [])
        for dep in dependencies:
            if dep not in self.reverse_dependencies:
                self.reverse_dependencies[dep] = set()
            self.reverse_dependencies[dep].add(task_id)
            
        logger.info(f"Added task to queue: {task_id}")
        
        # Display task details
        table = Table(title=f"Task Details: {task_id}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Type", task_type)
        table.add_row("Description", description)
        table.add_row("Agent", agent_id)
        table.add_row("Dependencies", ", ".join(dependencies) if dependencies else "None")
        
        self.console.print(table)
        
    async def request_agent_task(
        self,
        requesting_agent_id: str,
        target_agent_id: str,
        task_type: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle inter-agent task requests."""
        if target_agent_id not in self.agents:
            raise AgentError(f"Unknown target agent: {target_agent_id}")
            
        # Create task ID
        task_id = f"inter-{requesting_agent_id}-{target_agent_id}-{len(self.tasks)}"
        
        # Add task with dependency on requesting agent's current task
        await self.add_task(
            task_id=task_id,
            agent_id=target_agent_id,
            task_type=task_type,
            description=description,
            metadata=metadata
        )
        
        logger.info(
            f"Agent {requesting_agent_id} requested task from {target_agent_id}: "
            f"{task_id}"
        )
        
        return {
            "status": "requested",
            "task_id": task_id,
            "target_agent": target_agent_id
        }
        
    def _get_ready_tasks(self) -> List[TaskDependency]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready_tasks = []
        for task in self.tasks.values():
            if task.status == "pending" and all(
                dep in self.completed_tasks
                for dep in task.depends_on
            ):
                ready_tasks.append(task)
        return ready_tasks
        
    async def process_tasks(self):
        """Process all tasks in the queue with dependency management."""
        logger.info("Starting task processing...")
        
        while self.tasks:
            # Get tasks ready to execute
            ready_tasks = self._get_ready_tasks()
            
            if not ready_tasks:
                # No tasks ready, wait for dependencies
                await asyncio.sleep(1)
                continue
                
            # Process ready tasks
            for task in ready_tasks:
                if task.agent_id not in self.agents:
                    logger.error(f"Unknown agent: {task.agent_id}")
                    continue
                    
                # Create task object
                task_obj = Task(
                    task_id=task.task_id,
                    task_type=task.agent_id,
                    description=task.description,
                    metadata=task.metadata
                )
                
                try:
                    # Execute task with retry logic
                    result = await self._execute_task_with_retry(task.agent_id, task_obj)
                    
                    # Ensure result is a dictionary
                    if not isinstance(result, dict):
                        result = {"status": "success", "result": result}
                    if "status" not in result:
                        result["status"] = "success"
                    
                    # Update task status
                    task.status = "completed" if result["status"] == "success" else "failed"
                    task.result = result
                    
                    # Handle PM agent task results that contain new tasks
                    if task.agent_id == "pm_agent":
                        await self._handle_pm_task_results(task, result)
                    
                    # Move to completed tasks
                    self.tasks.pop(task.task_id)
                    self.completed_tasks[task.task_id] = task
                    
                    # Display result
                    self._display_result(task_obj, result)
                    
                    # Update milestone if applicable
                    if task.metadata and task.metadata.get("milestone_id"):
                        await self._update_milestone_progress(task.metadata["milestone_id"])
                    
                except Exception as e:
                    logger.error(f"Failed to process task {task.task_id}: {str(e)}")
                    task.status = "failed"
                    task.result = {
                        "status": "error",
                        "error": str(e),
                        "error_type": "processing_error"
                    }
                    self.tasks.pop(task.task_id)
                    self.completed_tasks[task.task_id] = task
                    
                    # Record failed task completion
                    completion = TaskCompletion(
                        task_id=task.task_id,
                        agent_id=task.agent_id,
                        estimated_duration=task.metadata.get("estimated_duration", 0),
                        actual_duration=(datetime.now() - task.start_time).total_seconds() if task.start_time else 0,
                        start_time=task.start_time,
                        end_time=datetime.now(),
                        complexity=task.metadata.get("complexity", 5),
                        dependencies=task.depends_on,
                        success=False,
                        notes=f"Failed: {str(e)}"
                    )
                    await self.feedback_system.record_task_completion(completion)
                
    async def _handle_pm_task_results(self, task: TaskDependency, result: Dict[str, Any]):
        """Handle PM agent task results that contain new tasks."""
        details = result.get("details", {})
        if not isinstance(details, dict):
            return
            
        tasks_list = details.get("tasks", [])
        if not isinstance(tasks_list, list):
            return
            
        for new_task_dict in tasks_list:
            if not isinstance(new_task_dict, dict):
                continue
                
            # Create new task dependency
            new_task = TaskDependency(
                task_id=new_task_dict.get("task_id", str(uuid.uuid4())),
                agent_id=new_task_dict.get("agent_id", ""),
                description=new_task_dict.get("description", ""),
                depends_on=new_task_dict.get("depends_on", []),
                metadata=new_task_dict.get("metadata", {})
            )
            
            # Add to task queue and update dependency tracking
            self.tasks[new_task.task_id] = new_task
            self.task_dependencies[new_task.task_id] = set(new_task.depends_on)
            for dep in new_task.depends_on:
                if dep not in self.reverse_dependencies:
                    self.reverse_dependencies[dep] = set()
                self.reverse_dependencies[dep].add(new_task.task_id)
            
            logger.info(f"Added new task to queue: {new_task.task_id}")
            
    async def _execute_task_with_retry(
        self,
        agent_id: str,
        task: Task,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """Execute a task with smart retry logic."""
        strategy = self._get_retry_strategy(agent_id)
        start_time = time.time()
        
        try:
            logger.info(
                f"Executing task {task.task_id} with {agent_id} "
                f"(attempt {attempt})"
            )
            result = await self.agents[agent_id].run_task(task)
            
            # Record successful execution
            duration_ms = (time.time() - start_time) * 1000
            record_metric(
                agent_name=agent_id,
                task_type=task.task_type,
                task_description=task.description,
                status="PASS",
                duration_ms=duration_ms,
                retries_attempted=attempt - 1,
                retry_success=True if attempt > 1 else None,
                retry_strategy_used=strategy.strategy if attempt > 1 else None
            )
            
            # Record task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=duration_ms / 1000,
                start_time=datetime.fromtimestamp(start_time),
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.metadata.get("dependencies", []),
                success=True,
                notes="Task completed successfully"
            )
            await self.feedback_system.record_task_completion(completion)
            
            return result
            
        except Exception as e:
            retry_count = self._get_retry_count(e, agent_id)
            duration_ms = (time.time() - start_time) * 1000
            
            if retry_count == 0:
                # Fatal error or no retries allowed
                logger.error(
                    f"Task {task.task_id} failed with fatal error: {str(e)}"
                )
                record_metric(
                    agent_name=agent_id,
                    task_type=task.task_type,
                    task_description=task.description,
                    status="FAIL",
                    duration_ms=duration_ms,
                    retries_attempted=attempt - 1,
                    retry_success=False if attempt > 1 else None,
                    retry_strategy_used=strategy.strategy if attempt > 1 else None
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": "fatal",
                    "attempts": attempt,
                    "retry_strategy": strategy.strategy
                }
                
            if attempt <= retry_count:
                delay = strategy.calculate_delay(attempt)
                logger.warning(
                    f"Task {task.task_id} failed on attempt {attempt}: {str(e)}. "
                    f"Retrying in {delay:.1f} seconds... "
                    f"(Error type: {e.__class__.__name__}, "
                    f"Strategy: {strategy.strategy})"
                )
                await asyncio.sleep(delay)
                return await self._execute_task_with_retry(
                    agent_id=agent_id,
                    task=task,
                    attempt=attempt + 1
                )
            else:
                logger.error(
                    f"Task {task.task_id} failed after {retry_count} attempts. "
                    f"Final error: {str(e)}"
                )
                record_metric(
                    agent_name=agent_id,
                    task_type=task.task_type,
                    task_description=task.description,
                    status="FAIL",
                    duration_ms=duration_ms,
                    retries_attempted=attempt - 1,
                    retry_success=False,
                    retry_strategy_used=strategy.strategy
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": "max_retries_exceeded",
                    "attempts": attempt,
                    "retry_strategy": strategy.strategy
                }
        
    def _display_result(self, task: Task, result: Dict[str, Any]):
        """Display task execution result."""
        table = Table(title=f"Task Result: {task.task_id}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Description", task.description)
        table.add_row("Status", result.get("status", "unknown"))
        
        if "error" in result:
            table.add_row("Error", result["error"])
            table.add_row("Error Type", result.get("error_type", "unknown"))
            table.add_row("Attempts", str(result.get("attempts", 1)))
        else:
            for key, value in result.get("details", {}).items():
                table.add_row(key, str(value))
                
        self.console.print(table)
        
    async def run(self):
        """Run the orchestrator."""
        try:
            await self.initialize()
            await self.process_tasks()
            logger.info("Task processing completed")
            
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            raise 

    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")
        
    async def create_task(self, task_id: str, agent_id: str, description: str,
                         depends_on: List[str] = None, metadata: Dict[str, Any] = None) -> TaskDependency:
        """Create a new task and register it with the orchestrator."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")
            
        task = TaskDependency(task_id, agent_id, description, depends_on, metadata)
        self.tasks[task_id] = task
        
        # Check if this task is part of a milestone
        if metadata and metadata.get("milestone_id"):
            milestone_id = metadata["milestone_id"]
            if milestone_id in self.milestones:
                self.milestones[milestone_id].tasks.append({
                    "task_id": task_id,
                    "description": description,
                    "completed": False
                })
                await self._update_milestone_progress(milestone_id)
                
        return task
        
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task and its dependencies."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        task = self.tasks[task_id]
        
        # Check dependencies
        for dep_id in task.depends_on:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency {dep_id} not found")
            dep_task = self.tasks[dep_id]
            if dep_task.status != "completed":
                raise ValueError(f"Dependency {dep_id} not completed")
                
        # Execute task
        agent = self.agents[task.agent_id]
        task.start_time = datetime.now()
        task.status = "running"
        
        try:
            result = await agent.run_task(Task(
                task_id=task_id,
                task_type=task.agent_id,
                description=task.description,
                metadata=task.metadata
            ))
            
            task.status = "completed"
            task.end_time = datetime.now()
            task.result = result
            
            # Record task completion
            completion = TaskCompletion(
                task_id=task_id,
                agent_id=task.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(task.end_time - task.start_time).total_seconds(),
                start_time=task.start_time,
                end_time=task.end_time,
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.depends_on,
                success=True,
                notes=f"Task completed successfully"
            )
            
            await self.feedback_system.record_task_completion(completion)
            
            # Update milestone if applicable
            if task.metadata and task.metadata.get("milestone_id"):
                await self._update_milestone_progress(task.metadata["milestone_id"])
                
            return result
            
        except Exception as e:
            task.status = "failed"
            task.end_time = datetime.now()
            
            # Record failed task completion
            completion = TaskCompletion(
                task_id=task_id,
                agent_id=task.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(task.end_time - task.start_time).total_seconds(),
                start_time=task.start_time,
                end_time=task.end_time,
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.depends_on,
                success=False,
                notes=f"Failed: {str(e)}"
            )
            
            await self.feedback_system.record_task_completion(completion)
            raise
            
    async def _update_milestone_progress(self, milestone_id: str) -> None:
        """Update milestone progress and send notifications if needed.
        
        Args:
            milestone_id: ID of the milestone to update
        """
        if milestone_id not in self.milestones:
            logger.warning(f"Milestone {milestone_id} not found")
            return
            
        milestone = self.milestones[milestone_id]
        total_tasks = len(milestone.tasks)
        completed_tasks = sum(1 for task in milestone.tasks if task["completed"])
        
        # Calculate progress
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Check for delays
        estimated_completion = datetime.fromisoformat(milestone.estimated_completion)
        if progress < 50 and estimated_completion < datetime.now():
            delay_reason = "Tasks taking longer than estimated"
            await self._handle_milestone_delay(milestone, delay_reason)
            
        # Update milestone status
        if progress == 100:
            milestone.status = "completed"
            milestone.actual_completion = datetime.now().isoformat()
        elif progress > 0:
            milestone.status = "in_progress"
        else:
            milestone.status = "pending"
            
        milestone.progress = progress
        
        try:
            # Save updated milestone data
            milestone_file = self.feedback_system.data_dir / "milestones.json"
            with open(milestone_file, 'w') as f:
                json.dump([m.dict() for m in self.milestones.values()], f, indent=2)
                
            # Send milestone update notification
            await self._send_milestone_notification(milestone)
            
            logger.info(
                f"Updated milestone {milestone_id}: "
                f"progress={progress:.1f}%, status={milestone.status}"
            )
        except Exception as e:
            logger.error(f"Failed to update milestone {milestone_id}: {e}")
            raise FatalError(f"Milestone update failed: {e}")
        
    async def _handle_milestone_delay(self, milestone: 'MilestoneStatus', delay_reason: str) -> None:
        """Handle milestone delay by sending notifications and updating status.
        
        Args:
            milestone: The milestone that is delayed
            delay_reason: Reason for the delay
        """
        milestone.status = "delayed"
        
        try:
            # Send delay notification
            await self._send_delay_notification(milestone, delay_reason)
            
            # Update milestone data
            milestone_file = self.feedback_system.data_dir / "milestones.json"
            with open(milestone_file, 'w') as f:
                json.dump([m.dict() for m in self.milestones.values()], f, indent=2)
                
            logger.warning(
                f"Milestone {milestone.milestone_id} delayed: {delay_reason}"
            )
        except Exception as e:
            logger.error(f"Failed to handle milestone delay: {e}")
            raise FatalError(f"Milestone delay handling failed: {e}")
            
    async def _send_milestone_notification(self, milestone: 'MilestoneStatus') -> None:
        """Send milestone update notification via Slack bot.
        
        Args:
            milestone: The milestone to notify about
        """
        if "slack_bot" not in self.agents:
            logger.warning("Slack bot not available for milestone notification")
            return
            
        try:
            slack_bot = self.agents["slack_bot"]
            await slack_bot.run_task(Task(
                task_id=f"milestone-notification-{milestone.milestone_id}",
                task_type="slack_bot",
                description="Send milestone update notification",
                metadata={
                    "type": "milestone_notification",
                    "milestone": milestone.dict()
                }
            ))
            logger.info(f"Sent milestone notification for {milestone.milestone_id}")
        except Exception as e:
            logger.error(f"Failed to send milestone notification: {e}")
            # Don't raise here as this is a non-critical operation
        
    async def _send_delay_notification(self, milestone: 'MilestoneStatus', delay_reason: str) -> None:
        """Send milestone delay notification via Slack bot.
        
        Args:
            milestone: The delayed milestone
            delay_reason: Reason for the delay
        """
        if "slack_bot" not in self.agents:
            logger.warning("Slack bot not available for delay notification")
            return
            
        try:
            slack_bot = self.agents["slack_bot"]
            await slack_bot.run_task(Task(
                task_id=f"delay-notification-{milestone.milestone_id}",
                task_type="slack_bot",
                description="Send milestone delay notification",
                metadata={
                    "type": "delay_notification",
                    "milestone": milestone.dict(),
                    "delay_reason": delay_reason
                }
            ))
            logger.info(f"Sent delay notification for {milestone.milestone_id}")
        except Exception as e:
            logger.error(f"Failed to send delay notification: {e}")
            # Don't raise here as this is a non-critical operation
        
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a task.
        
        Args:
            task_id: ID of the task to get status for
            
        Returns:
            Dictionary containing task status information
            
        Raises:
            ValueError: If task is not found
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        task = self.tasks[task_id]
        return {
            "task_id": task_id,
            "agent_id": task.agent_id,
            "description": task.description,
            "status": task.status,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "result": task.result,
            "dependencies": task.depends_on,
            "metadata": task.metadata
        }
        
    def get_milestone_status(self, milestone_id: str) -> Dict[str, Any]:
        """Get the current status of a milestone.
        
        Args:
            milestone_id: ID of the milestone to get status for
            
        Returns:
            Dictionary containing milestone status information
            
        Raises:
            ValueError: If milestone is not found
        """
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone {milestone_id} not found")
            
        milestone = self.milestones[milestone_id]
        return milestone.dict()
        
    async def get_project_metrics(self) -> Dict[str, Any]:
        """Get overall project metrics.
        
        Returns:
            Dictionary containing project metrics including:
            - Task statistics
            - Milestone statistics
            - Agent-specific metrics
            - Progress tracking
        """
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "tasks": {
                    "total": len(self.tasks),
                    "completed": sum(1 for task in self.tasks.values() if task.status == "completed"),
                    "failed": sum(1 for task in self.tasks.values() if task.status == "failed"),
                    "in_progress": sum(1 for task in self.tasks.values() if task.status == "running"),
                    "pending": sum(1 for task in self.tasks.values() if task.status == "pending")
                },
                "milestones": {
                    "total": len(self.milestones),
                    "completed": sum(1 for milestone in self.milestones.values() if milestone.status == "completed"),
                    "delayed": sum(1 for milestone in self.milestones.values() if milestone.status == "delayed"),
                    "in_progress": sum(1 for milestone in self.milestones.values() if milestone.status == "in_progress"),
                    "pending": sum(1 for milestone in self.milestones.values() if milestone.status == "pending"),
                    "progress": {
                        milestone_id: milestone.progress
                        for milestone_id, milestone in self.milestones.items()
                    }
                },
                "agents": {}
            }
            
            # Add agent-specific metrics
            for agent_id, agent in self.agents.items():
                agent_tasks = [task for task in self.tasks.values() if task.agent_id == agent_id]
                metrics["agents"][agent_id] = {
                    "total_tasks": len(agent_tasks),
                    "completed_tasks": sum(1 for task in agent_tasks if task.status == "completed"),
                    "failed_tasks": sum(1 for task in agent_tasks if task.status == "failed"),
                    "in_progress_tasks": sum(1 for task in agent_tasks if task.status == "running"),
                    "pending_tasks": sum(1 for task in agent_tasks if task.status == "pending"),
                    "success_rate": (
                        sum(1 for task in agent_tasks if task.status == "completed") / len(agent_tasks) * 100
                        if agent_tasks else 0
                    )
                }
                
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect project metrics: {e}")
            raise FatalError(f"Metrics collection failed: {e}") 