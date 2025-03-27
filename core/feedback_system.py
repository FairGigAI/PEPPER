"""Feedback system for improving estimates and milestone tracking."""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from pydantic import BaseModel
from core.agent_base import BaseAgent
from core.communication import SecureCommunication
from core.exceptions import FatalError
import asyncio
from pathlib import Path

class TaskCompletion(BaseModel):
    """Model for task completion data."""
    task_id: str
    agent_id: str
    estimated_duration: float
    actual_duration: float
    start_time: datetime
    end_time: datetime
    complexity: float
    dependencies: List[str]
    success: bool
    notes: Optional[str] = None

class MilestoneStatus(BaseModel):
    """Model for milestone status."""
    milestone_id: str
    name: str
    estimated_completion: datetime
    actual_completion: Optional[datetime]
    status: str  # pending, in_progress, completed, delayed
    tasks: List[str]
    progress: float
    delay_reason: Optional[str] = None

class FeedbackSystem:
    """Manages feedback loop for improving estimates and milestone tracking."""
    
    def __init__(self, llm_interface, slack_bot_agent):
        """Initialize the feedback system."""
        self.llm = llm_interface
        self.slack_bot = slack_bot_agent
        self.communication = SecureCommunication("feedback_system")
        self.data_dir = Path("data/feedback")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize the feedback system."""
        # Load historical data
        self.historical_data = await self._load_historical_data()
        
    async def record_task_completion(self, completion: TaskCompletion):
        """Record task completion data for analysis."""
        try:
            # Save completion data
            await self._save_completion_data(completion)
            
            # Analyze completion data
            analysis = await self._analyze_completion(completion)
            
            # Update agent performance metrics
            await self._update_agent_metrics(completion.agent_id, analysis)
            
            # Check for milestone updates
            await self._check_milestone_status(completion)
            
            return {
                "status": "success",
                "message": "Task completion recorded and analyzed",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to record task completion: {e}")
            raise
            
    async def _analyze_completion(self, completion: TaskCompletion) -> Dict[str, Any]:
        """Analyze task completion data."""
        # Calculate accuracy metrics
        time_difference = completion.actual_duration - completion.estimated_duration
        accuracy_percentage = 1 - (abs(time_difference) / completion.estimated_duration)
        
        # Analyze patterns
        patterns = await self._analyze_patterns(completion)
        
        return {
            "time_difference": time_difference,
            "accuracy_percentage": accuracy_percentage,
            "patterns": patterns,
            "recommendations": await self._generate_recommendations(completion, patterns)
        }
        
    async def _analyze_patterns(self, completion: TaskCompletion) -> Dict[str, Any]:
        """Analyze patterns in task completion data."""
        prompt = f"""Analyze the following task completion data for patterns:
        Task ID: {completion.task_id}
        Agent: {completion.agent_id}
        Estimated Duration: {completion.estimated_duration}
        Actual Duration: {completion.actual_duration}
        Complexity: {completion.complexity}
        
        Consider:
        1. Estimation accuracy by complexity level
        2. Common delay factors
        3. Agent-specific patterns
        4. Dependency impact"""
        
        analysis = await self.llm.analyze_text(prompt, "Extract patterns and insights")
        return analysis
        
    async def _generate_recommendations(self, completion: TaskCompletion, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving estimates."""
        prompt = f"""Based on the following data and patterns, generate recommendations for improving estimates:
        
        Task Data:
        - ID: {completion.task_id}
        - Agent: {completion.agent_id}
        - Complexity: {completion.complexity}
        - Time Difference: {completion.actual_duration - completion.estimated_duration}
        
        Patterns:
        {json.dumps(patterns, indent=2)}
        
        Generate specific, actionable recommendations for:
        1. Improving estimation accuracy
        2. Reducing delays
        3. Optimizing agent performance"""
        
        recommendations = await self.llm.generate_text(prompt)
        return recommendations.split("\n")
        
    async def _update_agent_metrics(self, agent_id: str, analysis: Dict[str, Any]):
        """Update agent performance metrics."""
        metrics_file = self.data_dir / f"agent_metrics_{agent_id}.json"
        
        try:
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = {
                    "total_tasks": 0,
                    "average_accuracy": 0,
                    "completion_times": [],
                    "patterns": {}
                }
                
            # Update metrics
            metrics["total_tasks"] += 1
            metrics["average_accuracy"] = (
                (metrics["average_accuracy"] * (metrics["total_tasks"] - 1) + 
                 analysis["accuracy_percentage"]) / metrics["total_tasks"]
            )
            metrics["completion_times"].append({
                "timestamp": datetime.now().isoformat(),
                "accuracy": analysis["accuracy_percentage"]
            })
            
            # Update patterns
            for pattern, value in analysis["patterns"].items():
                if pattern not in metrics["patterns"]:
                    metrics["patterns"][pattern] = []
                metrics["patterns"][pattern].append(value)
                
            # Save updated metrics
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update agent metrics: {e}")
            raise
            
    async def _check_milestone_status(self, completion: TaskCompletion):
        """Check and update milestone status."""
        # Get milestone data
        milestone_file = self.data_dir / "milestones.json"
        if not milestone_file.exists():
            return
            
        try:
            with open(milestone_file, 'r') as f:
                milestones = json.load(f)
                
            # Find relevant milestone
            for milestone in milestones:
                if completion.task_id in milestone["tasks"]:
                    # Update milestone progress
                    completed_tasks = sum(1 for task in milestone["tasks"] 
                                       if task in self._get_completed_tasks())
                    progress = completed_tasks / len(milestone["tasks"])
                    
                    # Check for delays
                    if progress < self._calculate_expected_progress(milestone):
                        await self._handle_milestone_delay(milestone, completion)
                        
                    # Update milestone status
                    milestone["progress"] = progress
                    if progress >= 1.0:
                        milestone["status"] = "completed"
                        milestone["actual_completion"] = datetime.now().isoformat()
                        
                    # Save updated milestone data
                    with open(milestone_file, 'w') as f:
                        json.dump(milestones, f, indent=2)
                        
                    # Send milestone update to Slack
                    await self._send_milestone_update(milestone)
                    
                    break
                    
        except Exception as e:
            logger.error(f"Failed to check milestone status: {e}")
            raise
            
    async def _handle_milestone_delay(self, milestone: Dict[str, Any], completion: TaskCompletion):
        """Handle milestone delays."""
        delay_reason = await self._analyze_delay_reason(milestone, completion)
        
        # Update milestone with delay information
        milestone["status"] = "delayed"
        milestone["delay_reason"] = delay_reason
        
        # Send delay notification to Slack
        await self._send_delay_notification(milestone, delay_reason)
        
    async def _analyze_delay_reason(self, milestone: Dict[str, Any], completion: TaskCompletion) -> str:
        """Analyze reason for milestone delay."""
        prompt = f"""Analyze the following milestone delay and determine the root cause:
        
        Milestone:
        - Name: {milestone['name']}
        - Expected Progress: {self._calculate_expected_progress(milestone)}
        - Current Progress: {milestone['progress']}
        
        Latest Task:
        - ID: {completion.task_id}
        - Agent: {completion.agent_id}
        - Time Difference: {completion.actual_duration - completion.estimated_duration}
        
        Provide a concise explanation of the delay reason."""
        
        return await self.llm.generate_text(prompt)
        
    async def _send_milestone_update(self, milestone: Dict[str, Any]):
        """Send milestone update to Slack."""
        message = f"""Milestone Update: {milestone['name']}
        
        Status: {milestone['status'].title()}
        Progress: {milestone['progress']*100:.1f}%
        Tasks Completed: {sum(1 for task in milestone['tasks'] if task in self._get_completed_tasks())}/{len(milestone['tasks'])}
        
        {'⚠️ Delay Reason: ' + milestone['delay_reason'] if milestone.get('delay_reason') else ''}"""
        
        await self.slack_bot.send_message(message)
        
    async def _send_delay_notification(self, milestone: Dict[str, Any], delay_reason: str):
        """Send delay notification to Slack."""
        message = f"""⚠️ Milestone Delay Alert: {milestone['name']}
        
        Current Progress: {milestone['progress']*100:.1f}%
        Expected Progress: {self._calculate_expected_progress(milestone)*100:.1f}%
        
        Delay Reason: {delay_reason}
        
        Recommended Actions:
        {await self._generate_delay_actions(milestone, delay_reason)}"""
        
        await self.slack_bot.send_message(message)
        
    async def _generate_delay_actions(self, milestone: Dict[str, Any], delay_reason: str) -> str:
        """Generate recommended actions for handling delay."""
        prompt = f"""Based on the following milestone delay, generate specific actions to address it:
        
        Milestone: {milestone['name']}
        Delay Reason: {delay_reason}
        Current Progress: {milestone['progress']*100:.1f}%
        
        Generate 3-5 specific, actionable recommendations."""
        
        return await self.llm.generate_text(prompt)
        
    def _calculate_expected_progress(self, milestone: Dict[str, Any]) -> float:
        """Calculate expected progress based on time elapsed."""
        start_time = datetime.fromisoformat(milestone["start_time"])
        expected_end = datetime.fromisoformat(milestone["estimated_completion"])
        current_time = datetime.now()
        
        total_duration = (expected_end - start_time).total_seconds()
        elapsed_duration = (current_time - start_time).total_seconds()
        
        return min(1.0, max(0.0, elapsed_duration / total_duration))
        
    def _get_completed_tasks(self) -> List[str]:
        """Get list of completed task IDs."""
        completed_tasks = []
        for file in self.data_dir.glob("completion_*.json"):
            try:
                with open(file, 'r') as f:
                    completion = json.load(f)
                    if completion.get("success"):
                        completed_tasks.append(completion["task_id"])
            except Exception as e:
                logger.error(f"Failed to read completion file {file}: {e}")
        return completed_tasks
        
    async def _save_completion_data(self, completion: TaskCompletion):
        """Save task completion data."""
        file_path = self.data_dir / f"completion_{completion.task_id}.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(completion.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save completion data: {e}")
            raise
            
    async def _load_historical_data(self) -> Dict[str, Any]:
        """Load historical completion data."""
        historical_data = {
            "completions": [],
            "patterns": {},
            "metrics": {}
        }
        
        try:
            # Load completion data
            for file in self.data_dir.glob("completion_*.json"):
                with open(file, 'r') as f:
                    historical_data["completions"].append(json.load(f))
                    
            # Load agent metrics
            for file in self.data_dir.glob("agent_metrics_*.json"):
                agent_id = file.stem.replace("agent_metrics_", "")
                with open(file, 'r') as f:
                    historical_data["metrics"][agent_id] = json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            
        return historical_data 