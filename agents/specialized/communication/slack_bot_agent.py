"""Slack Bot agent for handling Slack communications."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table

from core.agent_base import BaseAgent, Task
from core.config_models import SlackBotAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency
from core.feedback_system import FeedbackSystem, MilestoneStatus

class SlackBotAgent(BaseAgent):
    """Agent responsible for Slack communications and notifications."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, SlackBotAgentConfig):
            raise FatalError(f"Invalid configuration for SlackBotAgent {agent_id}")
            
        self.console = Console()
        self.output_dir = self.config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.feedback_system = FeedbackSystem(self.llm_interface, self.slack_bot)
        self.notification_channels = config.get("notification_channels", {})
        
    async def initialize(self):
        """Initialize the agent."""
        await super().initialize()
        await self.feedback_system.initialize()
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing Slack bot task: {task.task_id}")
        
        # Validate message type
        message_type = task.metadata.get("message_type", "notification")
        if message_type not in self.config.supported_message_types:
            raise FatalError(f"Unsupported message type: {message_type}")
            
        return {
            "message_type": message_type,
            "channel": task.metadata.get("channel", "general"),
            "priority": task.metadata.get("priority", "normal")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the Slack bot task."""
        logger.info(f"Executing Slack bot task: {task.task_id}")
        
        # Get message content
        content = task.metadata.get("content", {})
        
        # Generate Slack message
        message = self._generate_slack_message(content, task.metadata)
        
        # Send message to Slack
        try:
            # Simulate sending message to Slack
            logger.info(f"Sending message to Slack channel: {task.metadata.get('channel')}")
            
            # Save message documentation
            output_file = f"slack_message_{task.task_id.lower()}.md"
            output_path = os.path.join(self.output_dir, output_file)
            
            self._save_message_docs(message, task.metadata, output_path)
            logger.info(f"Generated message documentation: {output_path}")
            
            return {
                "status": "success",
                "message": "Message sent to Slack",
                "details": {
                    "output_file": output_file,
                    "message_type": task.metadata.get("message_type"),
                    "channel": task.metadata.get("channel"),
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise
            
    def _generate_slack_message(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Slack message based on content and metadata."""
        message_type = metadata.get("message_type", "notification")
        channel = metadata.get("channel", "general")
        priority = metadata.get("priority", "normal")
        
        # Define message components
        components = []
        
        if message_type == "notification":
            components = self._generate_notification_components(content)
        elif message_type == "alert":
            components = self._generate_alert_components(content)
        elif message_type == "report":
            components = self._generate_report_components(content)
            
        # Generate message blocks
        blocks = self._generate_message_blocks(components, priority)
        
        return {
            "type": message_type,
            "channel": channel,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "blocks": blocks
        }
        
    def _generate_notification_components(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate components for notification message."""
        components = []
        
        # Extract notification details
        title = content.get("title", "Notification")
        description = content.get("description", "")
        actions = content.get("actions", [])
        
        components.append({
            "type": "header",
            "text": title
        })
        
        if description:
            components.append({
                "type": "section",
                "text": description
            })
            
        if actions:
            components.append({
                "type": "actions",
                "elements": actions
            })
            
        return components
        
    def _generate_alert_components(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate components for alert message."""
        components = []
        
        # Extract alert details
        severity = content.get("severity", "warning")
        title = content.get("title", "Alert")
        description = content.get("description", "")
        details = content.get("details", {})
        
        components.append({
            "type": "header",
            "text": f"🚨 {title}",
            "style": self._get_severity_style(severity)
        })
        
        if description:
            components.append({
                "type": "section",
                "text": description
            })
            
        if details:
            components.append({
                "type": "section",
                "fields": self._format_details_fields(details)
            })
            
        return components
        
    def _generate_report_components(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate components for report message."""
        components = []
        
        # Extract report details
        title = content.get("title", "Report")
        summary = content.get("summary", "")
        sections = content.get("sections", [])
        
        components.append({
            "type": "header",
            "text": title
        })
        
        if summary:
            components.append({
                "type": "section",
                "text": summary
            })
            
        for section in sections:
            components.append({
                "type": "section",
                "text": f"*{section['title']}*\n{section['content']}"
            })
            
        return components
        
    def _get_severity_style(self, severity: str) -> str:
        """Get style based on severity level."""
        if severity == "critical":
            return "danger"
        elif severity == "high":
            return "warning"
        else:
            return "primary"
            
    def _format_details_fields(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format details into Slack fields."""
        fields = []
        
        for key, value in details.items():
            fields.append({
                "type": "mrkdwn",
                "text": f"*{key}*\n{value}"
            })
            
        return fields
        
    def _generate_message_blocks(self, components: List[Dict[str, Any]], priority: str) -> List[Dict[str, Any]]:
        """Generate Slack message blocks."""
        blocks = []
        
        # Add priority indicator
        if priority == "high":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *High Priority Message*"
                }
            })
            
        # Add components
        blocks.extend(components)
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        return blocks
        
    def _save_message_docs(self, message: Dict[str, Any], metadata: Dict[str, Any], output_path: str):
        """Save message documentation to markdown file."""
        with open(output_path, 'w') as f:
            f.write(f"""# Slack Message

## Overview
This document outlines the Slack message content and metadata.

## Message Information
- **Type:** {message['type']}
- **Channel:** {message['channel']}
- **Priority:** {message['priority']}
- **Timestamp:** {message['timestamp']}

## Components

""")
            
            for component in message["components"]:
                f.write(f"""### {component['type']}
**Content:**
{component.get('text', 'N/A')}

""")
                
            f.write("""## Message Blocks

""")
            for block in message["blocks"]:
                f.write(f"""### {block['type']}
**Content:**
{block.get('text', 'N/A')}

""")
                
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing Slack bot task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "message_type": task.metadata.get("message_type"),
            "channel": task.metadata.get("channel"),
            "priority": task.metadata.get("priority")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare Slack bot tasks."""
        if "content" not in task.metadata:
            raise ValueError("Message content must be specified in task metadata")
        return task 

    def _log_notification(self, channel: str, message: str):
        """Log notification with rich formatting."""
        table = Table(title="Slack Notification")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Channel", channel)
        table.add_row("Message", message)
        self.console.print(table)
        self.logger.info(f"Sent notification to {channel}: {message}")

    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute Slack communication tasks."""
        self.log_task_start(task)
        start_time = datetime.now()

        try:
            # Case 1: Send milestone notification
            if task.metadata.get("type") == "milestone_notification":
                milestone = task.metadata.get("milestone")
                if not milestone:
                    raise ValueError("No milestone data provided")
                    
                channel = self.notification_channels.get("milestones", "general")
                message = self._format_milestone_message(milestone)
                
                # Send to Slack
                await self.slack_bot.send_message(channel, message)
                self._log_notification(channel, message)
                
                # Record task completion
                completion = TaskCompletion(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    estimated_duration=task.metadata.get("estimated_duration", 0),
                    actual_duration=(datetime.now() - start_time).total_seconds(),
                    start_time=start_time,
                    end_time=datetime.now(),
                    complexity=task.metadata.get("complexity", 1),
                    dependencies=task.metadata.get("dependencies", []),
                    success=True,
                    notes=f"Sent milestone notification for {milestone['name']}"
                )
                
                await self.feedback_system.record_task_completion(completion)
                
                return {"status": "success", "message": "Milestone notification sent"}

            # Case 2: Send delay notification
            if task.metadata.get("type") == "delay_notification":
                milestone = task.metadata.get("milestone")
                delay_reason = task.metadata.get("delay_reason")
                if not milestone or not delay_reason:
                    raise ValueError("Missing milestone or delay reason")
                    
                channel = self.notification_channels.get("alerts", "general")
                message = self._format_delay_message(milestone, delay_reason)
                
                # Send to Slack
                await self.slack_bot.send_message(channel, message)
                self._log_notification(channel, message)
                
                # Record task completion
                completion = TaskCompletion(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    estimated_duration=task.metadata.get("estimated_duration", 0),
                    actual_duration=(datetime.now() - start_time).total_seconds(),
                    start_time=start_time,
                    end_time=datetime.now(),
                    complexity=task.metadata.get("complexity", 1),
                    dependencies=task.metadata.get("dependencies", []),
                    success=True,
                    notes=f"Sent delay notification for {milestone['name']}"
                )
                
                await self.feedback_system.record_task_completion(completion)
                
                return {"status": "success", "message": "Delay notification sent"}

            # Case 3: Send general notification
            message = task.metadata.get("message")
            channel = task.metadata.get("channel", "general")
            
            if not message:
                raise ValueError("No message provided")
                
            # Send to Slack
            await self.slack_bot.send_message(channel, message)
            self._log_notification(channel, message)
            
            # Record task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 1),
                dependencies=task.metadata.get("dependencies", []),
                success=True,
                notes=f"Sent general notification to {channel}"
            )
            
            await self.feedback_system.record_task_completion(completion)
            
            return {"status": "success", "message": "Notification sent"}

        except Exception as e:
            # Record failed task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 1),
                dependencies=task.metadata.get("dependencies", []),
                success=False,
                notes=f"Failed: {str(e)}"
            )
            
            await self.feedback_system.record_task_completion(completion)
            await self.handle_error(task, e)

    def _format_milestone_message(self, milestone: Dict[str, Any]) -> str:
        """Format milestone message for Slack."""
        status_emoji = {
            "completed": "✅",
            "in_progress": "🔄",
            "delayed": "⚠️",
            "blocked": "🚫"
        }.get(milestone["status"], "📌")
        
        message = f"{status_emoji} *Milestone Update: {milestone['name']}*\n"
        message += f"Status: {milestone['status'].title()}\n"
        message += f"Progress: {milestone['progress']}%\n"
        
        if milestone.get("actual_completion"):
            completion_time = datetime.fromisoformat(milestone["actual_completion"])
            message += f"Completed: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            message += f"Estimated completion: {milestone['estimated_completion']}\n"
            
        if milestone.get("tasks"):
            message += "\n*Tasks:*\n"
            for task in milestone["tasks"]:
                task_status = "✅" if task.get("completed") else "🔄"
                message += f"{task_status} {task['description']}\n"
                
        return message

    def _format_delay_message(self, milestone: Dict[str, Any], delay_reason: str) -> str:
        """Format delay notification message for Slack."""
        message = f"⚠️ *Milestone Delay Alert: {milestone['name']}*\n"
        message += f"Current progress: {milestone['progress']}%\n"
        message += f"Delay reason: {delay_reason}\n"
        message += f"Original estimated completion: {milestone['estimated_completion']}\n"
        
        if milestone.get("tasks"):
            message += "\n*Blocked Tasks:*\n"
            for task in milestone["tasks"]:
                if not task.get("completed"):
                    message += f"🔄 {task['description']}\n"
                    
        return message 