"""Timeline Estimator agent for analyzing task queues and generating timeline estimates."""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from rich.console import Console
from rich.table import Table
import json
import asyncio
from collections import defaultdict

from core.agent_base import BaseAgent, Task
from core.config_models import TimelineEstimatorAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency
from core.feedback_system import FeedbackSystem, TaskCompletion

class TimelineEstimatorAgent(BaseAgent):
    """Agent responsible for analyzing task queues and generating timeline estimates."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, TimelineEstimatorAgentConfig):
            raise FatalError(f"Invalid configuration for TimelineEstimatorAgent {agent_id}")
            
        self.console = Console()
        self.output_dir = self.config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.feedback_system = FeedbackSystem(self.llm_interface, self.slack_bot)
        
        # Agent throughput tracking
        self.agent_throughput = defaultdict(lambda: {
            "tasks_per_minute": 0,
            "average_duration": 0,
            "total_tasks": 0,
            "last_update": None
        })
        
    async def initialize(self):
        """Initialize the agent."""
        await super().initialize()
        await self.feedback_system.initialize()
        await self._load_historical_throughput()
        
    async def _load_historical_throughput(self):
        """Load historical throughput data from feedback system."""
        try:
            for agent_id in self.config.agent_ids:
                metrics_file = self.feedback_system.data_dir / f"agent_metrics_{agent_id}.json"
                if metrics_file.exists():
                    with open(metrics_file, 'r') as f:
                        metrics = json.load(f)
                        if "completion_times" in metrics:
                            # Calculate average duration and throughput
                            durations = [t["duration"] for t in metrics["completion_times"]]
                            if durations:
                                self.agent_throughput[agent_id]["average_duration"] = sum(durations) / len(durations)
                                self.agent_throughput[agent_id]["tasks_per_minute"] = 60 / self.agent_throughput[agent_id]["average_duration"]
                                self.agent_throughput[agent_id]["total_tasks"] = len(durations)
                                self.agent_throughput[agent_id]["last_update"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Failed to load historical throughput: {e}")
            
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing timeline estimation task: {task.task_id}")
        
        # Validate task queue
        task_queue = task.metadata.get("task_queue", [])
        if not task_queue:
            raise FatalError("No task queue provided")
            
        return {
            "task_queue": task_queue,
            "simulation_mode": task.metadata.get("simulation_mode", "optimistic"),
            "update_throughput": task.metadata.get("update_throughput", True)
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the timeline estimation task."""
        logger.info(f"Executing timeline estimation task: {task.task_id}")
        
        start_time = datetime.now()
        
        try:
            # Get task queue and simulation parameters
            task_queue = task.metadata.get("task_queue", [])
            simulation_mode = task.metadata.get("simulation_mode", "optimistic")
            update_throughput = task.metadata.get("update_throughput", True)
            
            # Analyze task queue
            analysis = await self._analyze_task_queue(task_queue)
            
            # Simulate execution
            simulation = await self._simulate_execution(
                task_queue,
                analysis,
                simulation_mode
            )
            
            # Generate timeline estimate
            timeline = await self._generate_timeline_estimate(simulation)
            
            # Update agent throughput if requested
            if update_throughput:
                await self._update_agent_throughput(simulation)
            
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
                notes=f"Generated timeline estimate for {len(task_queue)} tasks"
            )
            
            await self.feedback_system.record_task_completion(completion)
            
            return {
                "status": "success",
                "message": "Timeline estimate generated",
                "details": {
                    "analysis": analysis,
                    "simulation": simulation,
                    "timeline": timeline
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate timeline estimate: {e}")
            
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
            raise
            
    async def _analyze_task_queue(self, task_queue: List[TaskDependency]) -> Dict[str, Any]:
        """Analyze task queue for dependencies and resource requirements."""
        analysis = {
            "total_tasks": len(task_queue),
            "task_types": defaultdict(int),
            "agent_workload": defaultdict(int),
            "dependency_chains": [],
            "critical_path": [],
            "resource_requirements": defaultdict(int)
        }
        
        # Analyze task types and agent workload
        for task in task_queue:
            analysis["task_types"][task.task_type] += 1
            analysis["agent_workload"][task.agent_id] += 1
            
            # Analyze resource requirements
            if "resource_requirements" in task.metadata:
                for resource, amount in task.metadata["resource_requirements"].items():
                    analysis["resource_requirements"][resource] += amount
                    
        # Find dependency chains
        analysis["dependency_chains"] = self._find_dependency_chains(task_queue)
        
        # Find critical path
        analysis["critical_path"] = self._find_critical_path(task_queue)
        
        return analysis
        
    def _find_dependency_chains(self, task_queue: List[TaskDependency]) -> List[List[str]]:
        """Find all dependency chains in the task queue."""
        chains = []
        visited = set()
        
        def dfs(task_id: str, current_chain: List[str]):
            if task_id in visited:
                return
                
            visited.add(task_id)
            current_chain.append(task_id)
            
            task = next((t for t in task_queue if t.task_id == task_id), None)
            if task:
                for dep_id in task.depends_on:
                    dfs(dep_id, current_chain)
                    
            if len(current_chain) > 1:
                chains.append(current_chain.copy())
                
        for task in task_queue:
            if task.task_id not in visited:
                dfs(task.task_id, [])
                
        return chains
        
    def _find_critical_path(self, task_queue: List[TaskDependency]) -> List[str]:
        """Find the critical path in the task queue."""
        # Create dependency graph
        graph = defaultdict(list)
        for task in task_queue:
            for dep_id in task.depends_on:
                graph[dep_id].append(task.task_id)
                
        # Calculate earliest completion time for each task
        earliest_completion = {}
        for task in task_queue:
            if not task.depends_on:
                earliest_completion[task.task_id] = self._estimate_task_duration(task)
            else:
                max_dep_completion = max(
                    earliest_completion.get(dep_id, 0)
                    for dep_id in task.depends_on
                )
                earliest_completion[task.task_id] = (
                    max_dep_completion + self._estimate_task_duration(task)
                )
                
        # Find tasks on critical path
        critical_path = []
        max_completion = max(earliest_completion.values())
        
        for task in task_queue:
            if earliest_completion[task.task_id] == max_completion:
                critical_path.append(task.task_id)
                
        return critical_path
        
    def _estimate_task_duration(self, task: TaskDependency) -> float:
        """Estimate task duration based on agent throughput."""
        agent_id = task.agent_id
        throughput = self.agent_throughput[agent_id]
        
        if throughput["tasks_per_minute"] > 0:
            # Use historical throughput
            base_duration = 60 / throughput["tasks_per_minute"]
        else:
            # Use default duration
            base_duration = 5.0  # 5 minutes per task
            
        # Adjust based on complexity
        complexity = task.metadata.get("complexity", 5)
        return base_duration * (complexity / 5)
        
    async def _simulate_execution(
        self,
        task_queue: List[TaskDependency],
        analysis: Dict[str, Any],
        simulation_mode: str
    ) -> Dict[str, Any]:
        """Simulate task execution with concurrent agent collaboration."""
        simulation = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": 0,
            "agent_utilization": defaultdict(float),
            "task_completion_times": {},
            "resource_usage": defaultdict(list)
        }
        
        # Initialize agent states
        agent_states = defaultdict(lambda: {
            "current_task": None,
            "start_time": None,
            "completed_tasks": []
        })
        
        # Sort tasks by priority and dependencies
        ready_tasks = self._get_ready_tasks(task_queue)
        completed_tasks = set()
        
        current_time = datetime.now()
        simulation_time = 0
        
        while ready_tasks or any(state["current_task"] for state in agent_states.values()):
            # Update agent states
            for agent_id, state in agent_states.items():
                if state["current_task"]:
                    task = state["current_task"]
                    duration = self._estimate_task_duration(task)
                    
                    if simulation_time >= state["start_time"] + duration:
                        # Task completed
                        state["completed_tasks"].append({
                            "task_id": task.task_id,
                            "start_time": state["start_time"],
                            "end_time": simulation_time,
                            "duration": duration
                        })
                        simulation["task_completion_times"][task.task_id] = {
                            "start": state["start_time"],
                            "end": simulation_time,
                            "duration": duration
                        }
                        completed_tasks.add(task.task_id)
                        state["current_task"] = None
                        state["start_time"] = None
                        
            # Assign new tasks to idle agents
            for agent_id, state in agent_states.items():
                if not state["current_task"] and ready_tasks:
                    # Find suitable task for agent
                    task = self._find_suitable_task(ready_tasks, agent_id)
                    if task:
                        state["current_task"] = task
                        state["start_time"] = simulation_time
                        ready_tasks.remove(task)
                        
            # Update ready tasks
            new_ready_tasks = self._get_ready_tasks(task_queue)
            ready_tasks.extend(new_ready_tasks)
            
            # Advance simulation time
            simulation_time += 1
            
        # Calculate final metrics
        simulation["end_time"] = (datetime.now() + timedelta(minutes=simulation_time)).isoformat()
        simulation["total_duration"] = simulation_time
        
        # Calculate agent utilization
        for agent_id, state in agent_states.items():
            total_working_time = sum(
                task["duration"]
                for task in state["completed_tasks"]
            )
            simulation["agent_utilization"][agent_id] = (
                total_working_time / simulation_time
                if simulation_time > 0 else 0
            )
            
        return simulation
        
    def _get_ready_tasks(self, task_queue: List[TaskDependency]) -> List[TaskDependency]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready_tasks = []
        for task in task_queue:
            if all(dep_id in self.completed_tasks for dep_id in task.depends_on):
                ready_tasks.append(task)
        return ready_tasks
        
    def _find_suitable_task(
        self,
        ready_tasks: List[TaskDependency],
        agent_id: str
    ) -> Optional[TaskDependency]:
        """Find a suitable task for an agent based on task type and priority."""
        suitable_tasks = [
            task for task in ready_tasks
            if task.agent_id == agent_id
        ]
        
        if not suitable_tasks:
            return None
            
        # Sort by priority and complexity
        return max(
            suitable_tasks,
            key=lambda t: (
                t.metadata.get("priority", "MEDIUM"),
                t.metadata.get("complexity", 5)
            )
        )
        
    async def _generate_timeline_estimate(self, simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed timeline estimate from simulation results."""
        timeline = {
            "start_time": simulation["start_time"],
            "end_time": simulation["end_time"],
            "total_duration": simulation["total_duration"],
            "milestones": [],
            "agent_schedules": defaultdict(list),
            "resource_allocations": defaultdict(list),
            "risk_factors": []
        }
        
        # Generate milestones
        timeline["milestones"] = self._generate_milestones(simulation)
        
        # Generate agent schedules
        for task_id, completion in simulation["task_completion_times"].items():
            task = next(
                (t for t in self.current_task_queue if t.task_id == task_id),
                None
            )
            if task:
                timeline["agent_schedules"][task.agent_id].append({
                    "task_id": task_id,
                    "start_time": completion["start"],
                    "end_time": completion["end"],
                    "duration": completion["duration"]
                })
                
        # Identify risk factors
        timeline["risk_factors"] = self._identify_risk_factors(simulation)
        
        return timeline
        
    def _generate_milestones(self, simulation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate milestones based on task completion times."""
        milestones = []
        current_milestone = {
            "name": "Project Start",
            "time": simulation["start_time"],
            "tasks_completed": 0,
            "total_tasks": len(self.current_task_queue)
        }
        milestones.append(current_milestone)
        
        # Add milestones at 25%, 50%, and 75% completion
        total_tasks = len(self.current_task_queue)
        milestone_percentages = [25, 50, 75]
        
        for percentage in milestone_percentages:
            target_tasks = int(total_tasks * percentage / 100)
            completion_time = None
            
            for task_id, completion in simulation["task_completion_times"].items():
                if len(milestones[-1]["tasks_completed"]) >= target_tasks:
                    completion_time = completion["end"]
                    break
                    
            if completion_time:
                milestones.append({
                    "name": f"{percentage}% Complete",
                    "time": completion_time,
                    "tasks_completed": target_tasks,
                    "total_tasks": total_tasks
                })
                
        # Add final milestone
        milestones.append({
            "name": "Project Completion",
            "time": simulation["end_time"],
            "tasks_completed": total_tasks,
            "total_tasks": total_tasks
        })
        
        return milestones
        
    def _identify_risk_factors(self, simulation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential risk factors in the timeline."""
        risks = []
        
        # Check agent utilization
        for agent_id, utilization in simulation["agent_utilization"].items():
            if utilization > 0.9:
                risks.append({
                    "type": "high_utilization",
                    "agent": agent_id,
                    "severity": "high",
                    "description": f"Agent {agent_id} has high utilization ({utilization:.1%})"
                })
                
        # Check task dependencies
        for task in self.current_task_queue:
            if len(task.depends_on) > 3:
                risks.append({
                    "type": "complex_dependencies",
                    "task_id": task.task_id,
                    "severity": "medium",
                    "description": f"Task {task.task_id} has many dependencies ({len(task.depends_on)})"
                })
                
        # Check resource requirements
        for resource, usage in simulation["resource_usage"].items():
            if max(usage) > 0.8:
                risks.append({
                    "type": "resource_constraint",
                    "resource": resource,
                    "severity": "high",
                    "description": f"Resource {resource} has high peak usage ({max(usage):.1%})"
                })
                
        return risks
        
    async def _update_agent_throughput(self, simulation: Dict[str, Any]):
        """Update agent throughput metrics based on simulation results."""
        for agent_id, completion_times in simulation["task_completion_times"].items():
            if agent_id in self.agent_throughput:
                throughput = self.agent_throughput[agent_id]
                throughput["total_tasks"] += 1
                throughput["average_duration"] = (
                    (throughput["average_duration"] * (throughput["total_tasks"] - 1) +
                     completion_times["duration"]) / throughput["total_tasks"]
                )
                throughput["tasks_per_minute"] = 60 / throughput["average_duration"]
                throughput["last_update"] = datetime.now().isoformat()
                
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing timeline estimation task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "simulation_mode": task.metadata.get("simulation_mode"),
            "update_throughput": task.metadata.get("update_throughput")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare timeline estimation tasks."""
        if "task_queue" not in task.metadata:
            raise ValueError("Task queue must be specified in task metadata")
        return task 