"""Script to generate and send daily summary of agent activities."""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
from core.slack_bot import SlackBot
from core.emailer import Emailer

class DailySummary:
    """Generates and sends daily summary of agent activities."""
    
    def __init__(self, log_dir: str = "logs", channel: str = "#agent-updates"):
        self.log_dir = Path(log_dir)
        self.channel = channel
        self.slack_bot = SlackBot()
        self.emailer = Emailer()
        
    def _load_agent_stats(self) -> Dict[str, Any]:
        """Load agent statistics from log files."""
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retries": 0,
            "agents": {}
        }
        
        # Load metrics from the last 24 hours
        cutoff_time = datetime.now() - timedelta(days=1)
        
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        
                        if timestamp < cutoff_time:
                            continue
                            
                        agent_id = log_entry.get('agent_id', 'unknown')
                        if agent_id not in stats['agents']:
                            stats['agents'][agent_id] = {
                                'tasks': 0,
                                'completed': 0,
                                'failed': 0,
                                'retries': 0
                            }
                            
                        agent_stats = stats['agents'][agent_id]
                        agent_stats['tasks'] += 1
                        stats['total_tasks'] += 1
                        
                        if log_entry.get('status') == 'completed':
                            agent_stats['completed'] += 1
                            stats['completed_tasks'] += 1
                        elif log_entry.get('status') == 'failed':
                            agent_stats['failed'] += 1
                            stats['failed_tasks'] += 1
                            
                        if log_entry.get('retry_count', 0) > 0:
                            agent_stats['retries'] += 1
                            stats['retries'] += 1
                            
                    except json.JSONDecodeError:
                        continue
                        
        return stats
        
    def _format_agent_stats(self, stats: Dict[str, Any], format: str = 'slack') -> str:
        """
        Format agent statistics for display.
        
        Args:
            stats: The statistics to format
            format: The output format ('slack' or 'email')
        """
        output = []
        
        # Overall stats
        if format == 'slack':
            output.append(f"*Overall Statistics*")
        else:
            output.append("<h2>Overall Statistics</h2>")
            
        output.append(f"Total Tasks: {stats['total_tasks']}")
        output.append(f"Completed: {stats['completed_tasks']}")
        output.append(f"Failed: {stats['failed_tasks']}")
        output.append(f"Total Retries: {stats['retries']}")
        output.append("")
        
        # Per-agent stats
        if format == 'slack':
            output.append("*Agent Statistics*")
        else:
            output.append("<h2>Agent Statistics</h2>")
            
        for agent_id, agent_stats in stats['agents'].items():
            if format == 'slack':
                output.append(f"\n*{agent_id}*")
            else:
                output.append(f"<h3>{agent_id}</h3>")
                
            output.append(f"Tasks: {agent_stats['tasks']}")
            output.append(f"Completed: {agent_stats['completed']}")
            output.append(f"Failed: {agent_stats['failed']}")
            output.append(f"Retries: {agent_stats['retries']}")
            
        return "\n".join(output)
        
    def _format_errors(self, stats: Dict[str, Any], format: str = 'slack') -> str:
        """
        Format error statistics for display.
        
        Args:
            stats: The statistics to format
            format: The output format ('slack' or 'email')
        """
        if stats['failed_tasks'] == 0:
            return "No errors reported in the last 24 hours."
            
        output = []
        if format == 'slack':
            output.append("*Error Summary*")
        else:
            output.append("<h2>Error Summary</h2>")
            
        for agent_id, agent_stats in stats['agents'].items():
            if agent_stats['failed'] > 0:
                if format == 'slack':
                    output.append(f"\n*{agent_id}*: {agent_stats['failed']} failed tasks")
                else:
                    output.append(f"<p><strong>{agent_id}</strong>: {agent_stats['failed']} failed tasks</p>")
                    
        return "\n".join(output)
        
    def _generate_html_email(self, stats: Dict[str, Any]) -> str:
        """Generate HTML version of the email."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h2 {{ color: #2c3e50; }}
                h3 {{ color: #34495e; }}
                .stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .error {{ color: #dc3545; }}
                .success {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <h1>Daily Agent Summary</h1>
            <div class="stats">
                {self._format_agent_stats(stats, 'email')}
            </div>
            <div class="error">
                {self._format_errors(stats, 'email')}
            </div>
        </body>
        </html>
        """
        
    def send_summary(self) -> bool:
        """Generate and send daily summary to Slack and email."""
        try:
            # Load and format statistics
            stats = self._load_agent_stats()
            
            # Send to Slack
            slack_stats = self._format_agent_stats(stats, 'slack')
            slack_errors = self._format_errors(stats, 'slack')
            slack_summary = self.slack_bot.format_message(
                "Daily Agent Summary",
                f"{slack_stats}\n\n{slack_errors}"
            )
            slack_summary += "\n\n_TODO: Support Slack threads for task discussions_"
            slack_sent = self.slack_bot.send_message(self.channel, slack_summary)
            
            # Send email if enabled
            email_sent = True
            if os.getenv('ENABLE_EMAIL_SUMMARY', 'true').lower() == 'true':
                email_subject = f"Daily Agent Summary - {datetime.now().strftime('%Y-%m-%d')}"
                email_body = f"Daily Agent Summary\n\n{self._format_agent_stats(stats, 'email')}\n\n{self._format_errors(stats, 'email')}"
                email_html = self._generate_html_email(stats)
                
                email_sent = self.emailer.send_email(
                    to=self.emailer.to_email,
                    subject=email_subject,
                    body=email_body,
                    html_body=email_html
                )
                
            return slack_sent and email_sent
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            error_msg = self.slack_bot.format_error(f"Failed to generate daily summary: {e}")
            self.slack_bot.send_message(self.channel, error_msg)
            return False
            
def main():
    """Main entry point for the daily summary script."""
    summary = DailySummary()
    if summary.send_summary():
        logger.info("Daily summary sent successfully")
    else:
        logger.error("Failed to send daily summary")
        
if __name__ == "__main__":
    main() 