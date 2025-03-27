"""Project Manager agent for handling project management tasks."""

import os
from typing import Dict, Any, List
import yaml
from loguru import logger
from rich.console import Console
from rich.table import Table
from datetime import datetime
import json

from core.agent_base import BaseAgent, Task
from core.agent_orchestrator import TaskDependency
from core.feedback_system import FeedbackSystem, TaskCompletion, MilestoneStatus

class ProjectManagerAgent(BaseAgent):
    """Agent responsible for project management and task coordination."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.console = Console()
        self.project_config = self._load_project_config()
        self.feedback_system = FeedbackSystem(self.llm_interface, self.slack_bot)
        
    async def initialize(self):
        """Initialize the agent."""
        await super().initialize()
        await self.feedback_system.initialize()
        
    def _load_project_config(self) -> Dict[str, Any]:
        """Load project configuration from YAML file."""
        try:
            with open("config/project_config.yaml", 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load project config: {e}")
            return {}
    
    def _log_task_assignment(self, agent_name: str, task_description: str):
        """Log task assignment with rich formatting."""
        table = Table(title="Task Assignment")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Agent", agent_name)
        table.add_row("Task", task_description)
        self.console.print(table)
        self.logger.info(f"Assigned task to {agent_name}: {task_description}")

    def _generate_tasks_from_project(self, path: str, project_name: str) -> List[Dict[str, Any]]:
        """Analyze source directory and generate build tasks."""
        task_list = []
        task_id_prefix = project_name.lower().replace(" ", "_")

        # First pass: Create all tasks
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)

                if file.endswith(".tsx"):
                    name = os.path.splitext(file)[0]
                    task_list.append({
                        "task_id": f"{task_id_prefix}_rebuild_{name.lower()}",
                        "task_type": "frontend.component_creation",
                        "description": f"Recreate React component: {name}",
                        "metadata": {
                            "source_file": file_path,
                            "component_name": name,
                            "framework": "react"
                        },
                        "depends_on": []  # Initialize empty dependencies
                    })

                elif file.endswith(".py") and "route" in file:
                    route = os.path.splitext(file)[0]
                    task_list.append({
                        "task_id": f"{task_id_prefix}_validate_{route.lower()}",
                        "task_type": "qa.backend_validation",
                        "description": f"Validate backend route file: {route}",
                        "metadata": {
                            "file_path": file_path,
                            "test_type": "integration"
                        },
                        "depends_on": []  # Initialize empty dependencies
                    })

        # Second pass: Add dependencies based on file relationships
        for i, task in enumerate(task_list):
            if task["task_type"] == "qa.backend_validation":
                # Find corresponding build task
                build_task_id = task["task_id"].replace("_validate_", "_build_")
                for other_task in task_list:
                    if other_task["task_id"] == build_task_id:
                        task["depends_on"].append(build_task_id)
                        break
            elif task["task_type"] == "qa.frontend_validation":
                # Find corresponding component task
                component_task_id = task["task_id"].replace("_validate_", "_rebuild_")
                for other_task in task_list:
                    if other_task["task_id"] == component_task_id:
                        task["depends_on"].append(component_task_id)
                        break

        # Convert task dictionaries to TaskDependency objects
        task_dependencies = []
        for task_dict in task_list:
            # Map task types to agent IDs
            agent_id_map = {
                "frontend": "frontend_agent",
                "qa": "qa_agent",
                "backend": "backend_agent"
            }
            task_type_prefix = task_dict["task_type"].split(".")[0]
            agent_id = agent_id_map.get(task_type_prefix, task_type_prefix)

            task_dep = TaskDependency(
                task_id=task_dict["task_id"],
                depends_on=task_dict["depends_on"],
                agent_id=agent_id,
                task_type=task_dict["task_type"],
                description=task_dict["description"],
                metadata=task_dict["metadata"]
            )
            task_dependencies.append(task_dep)

        return task_dependencies

    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute project management tasks."""
        self.log_task_start(task)
        start_time = datetime.now()

        try:
            # Case 1: Benchmark project analysis
            if task.metadata.get("generate_tasks") and task.metadata.get("source_path"):
                project_path = task.metadata["source_path"]
                project_name = task.metadata.get("project_name", task.task_id)
                new_tasks = self._generate_tasks_from_project(project_path, project_name)

                # Convert TaskDependency objects to dictionaries for the result
                results = []
                for new_task in new_tasks:
                    self._log_task_assignment(new_task.agent_id, new_task.description)
                    results.append({
                        "task_id": new_task.task_id,
                        "task_type": new_task.task_type,
                        "description": new_task.description,
                        "agent_id": new_task.agent_id,
                        "depends_on": new_task.depends_on,
                        "metadata": new_task.metadata
                    })

                # Record task completion
                completion = TaskCompletion(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    estimated_duration=task.metadata.get("estimated_duration", 0),
                    actual_duration=(datetime.now() - start_time).total_seconds(),
                    start_time=start_time,
                    end_time=datetime.now(),
                    complexity=task.metadata.get("complexity", 5),
                    dependencies=task.metadata.get("dependencies", []),
                    success=True,
                    notes=f"Generated {len(results)} subtasks from benchmark project"
                )
                
                await self.feedback_system.record_task_completion(completion)

                self.log_task_end(task, {"generated_tasks": len(results)})
                return {
                    "status": "success",
                    "message": f"Generated {len(results)} subtasks from benchmark project",
                    "details": {"tasks": results}
                }

            # Case 2: Normal PM assignments
            task_assignments = task.metadata.get("task_assignments", [])
            results = []
            for assignment in task_assignments:
                agent_name = assignment.get("agent")
                task_description = assignment.get("task_description")

                if not agent_name or not task_description:
                    self.logger.warning(f"Invalid task assignment: {assignment}")
                    continue

                new_task = Task(
                    task_id=f"pm-{len(results)}",
                    task_type=agent_name,
                    description=task_description,
                    priority=task.priority,
                    metadata=assignment.get("metadata", {})
                )

                self._log_task_assignment(agent_name, task_description)
                results.append({
                    "agent": agent_name,
                    "task": task_description,
                    "status": "assigned"
                })

            # Record task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.metadata.get("dependencies", []),
                success=True,
                notes=f"Processed {len(results)} task assignments"
            )
            
            await self.feedback_system.record_task_completion(completion)

            self.log_task_end(task, {"processed_assignments": len(results)})
            return {"results": results}

        except Exception as e:
            # Record failed task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.metadata.get("dependencies", []),
                success=False,
                notes=f"Failed: {str(e)}"
            )
            
            await self.feedback_system.record_task_completion(completion)
            await self.handle_error(task, e)

    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare project management tasks."""
        if "task_assignments" in task.metadata:
            for assignment in task.metadata["task_assignments"]:
                if not isinstance(assignment, dict):
                    raise ValueError("Each task assignment must be a dictionary")
                if "agent" not in assignment or "task_description" not in assignment:
                    raise ValueError("Each assignment must contain 'agent' and 'task_description'")
        return task

    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing PM task: {task.task_id}")
        return {}

    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the project management task."""
        logger.info(f"Executing PM task: {task.task_id}")
        return {
            "status": "success",
            "message": f"PM task {task.task_id} completed",
            "details": {
                "task_type": task.task_type,
                "task_id": task.task_id,
                "description": task.description
            }
        }

    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing PM task: {task.task_id}")
        return result

    async def update_milestone_status(self, milestone_id: str, status: str, progress: float):
        """Update milestone status and notify relevant parties."""
        try:
            milestone_file = self.feedback_system.data_dir / "milestones.json"
            if not milestone_file.exists():
                return
                
            with open(milestone_file, 'r') as f:
                milestones = json.load(f)
                
            # Find and update milestone
            for milestone in milestones:
                if milestone["milestone_id"] == milestone_id:
                    milestone["status"] = status
                    milestone["progress"] = progress
                    if status == "completed":
                        milestone["actual_completion"] = datetime.now().isoformat()
                        
                    # Save updated milestone data
                    with open(milestone_file, 'w') as f:
                        json.dump(milestones, f, indent=2)
                        
                    # Send milestone update to Slack
                    await self.feedback_system._send_milestone_update(milestone)
                    break
                    
        except Exception as e:
            logger.error(f"Failed to update milestone status: {e}")
            raise

    async def get_agent_performance_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific agent."""
        try:
            metrics_file = self.feedback_system.data_dir / f"agent_metrics_{agent_id}.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load agent metrics: {e}")
            return {}

    async def get_project_metrics(self) -> Dict[str, Any]:
        """Get overall project metrics."""
        try:
            metrics = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "average_accuracy": 0,
                "milestone_progress": {},
                "agent_performance": {}
            }
            
            # Get milestone progress
            milestone_file = self.feedback_system.data_dir / "milestones.json"
            if milestone_file.exists():
                with open(milestone_file, 'r') as f:
                    milestones = json.load(f)
                    for milestone in milestones:
                        metrics["milestone_progress"][milestone["name"]] = {
                            "progress": milestone["progress"],
                            "status": milestone["status"]
                        }
            
            # Get agent performance
            for agent_id in self.project_config.get("agents", []):
                metrics["agent_performance"][agent_id] = await self.get_agent_performance_metrics(agent_id)
                
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get project metrics: {e}")
            return {}
