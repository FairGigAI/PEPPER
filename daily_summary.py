"""Generate daily summary reports from P.E.P.P.E.R. metrics."""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Constants
METRICS_FILE = "logs/metrics.csv"
REPORT_DIR = "reports"
MAX_TASK_TYPES = 5

class DailySummary:
    """Generate and display daily summaries of agent performance."""
    
    def __init__(self):
        self.console = Console()
        self.metrics_df = None
        self.report_date = datetime.now().date()
        
    def load_metrics(self) -> bool:
        """Load metrics from CSV file."""
        if not os.path.exists(METRICS_FILE):
            self.console.print("[red]Error: Metrics file not found[/red]")
            return False
            
        try:
            self.metrics_df = pd.read_csv(METRICS_FILE)
            # Convert timestamp to datetime
            self.metrics_df["timestamp"] = pd.to_datetime(self.metrics_df["timestamp"])
            # Filter for today's data
            self.metrics_df = self.metrics_df[
                self.metrics_df["timestamp"].dt.date == self.report_date
            ]
            return True
        except Exception as e:
            self.console.print(f"[red]Error loading metrics: {e}[/red]")
            return False
            
    def calculate_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Calculate statistics for a specific agent."""
        agent_df = self.metrics_df[self.metrics_df["agent_name"] == agent_name]
        
        if agent_df.empty:
            return {
                "total_tasks": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "task_types": [],
                "retry_rate": 0
            }
            
        # Basic stats
        total_tasks = len(agent_df)
        success_rate = (agent_df["status"] == "PASS").mean() * 100
        avg_duration = agent_df["duration_ms"].mean()
        
        # Task type distribution
        task_types = agent_df["task_type"].value_counts().head(MAX_TASK_TYPES)
        task_type_list = [
            f"{task_type} ({count})"
            for task_type, count in task_types.items()
        ]
        
        # Retry rate
        retry_rate = (
            agent_df["retries_attempted"].notna() & 
            (agent_df["retries_attempted"] > 0)
        ).mean() * 100
        
        return {
            "total_tasks": total_tasks,
            "success_rate": round(success_rate, 2),
            "avg_duration": round(avg_duration, 2),
            "task_types": task_type_list,
            "retry_rate": round(retry_rate, 2)
        }
        
    def generate_markdown_report(self) -> str:
        """Generate markdown report content."""
        report = [
            f"# Daily Summary Report - {self.report_date}",
            "",
            "## Overview",
            f"- Total Tasks: {len(self.metrics_df)}",
            f"- Success Rate: {(self.metrics_df['status'] == 'PASS').mean() * 100:.2f}%",
            f"- Average Duration: {self.metrics_df['duration_ms'].mean():.2f}ms",
            "",
            "## Agent Performance",
        ]
        
        # Add agent sections
        for agent_name in self.metrics_df["agent_name"].unique():
            stats = self.calculate_agent_stats(agent_name)
            
            report.extend([
                f"### {agent_name}",
                f"- Tasks Completed: {stats['total_tasks']}",
                f"- Success Rate: {stats['success_rate']}%",
                f"- Average Duration: {stats['avg_duration']}ms",
                f"- Retry Rate: {stats['retry_rate']}%",
                "",
                "#### Common Task Types",
                *[f"- {task_type}" for task_type in stats["task_types"]],
                ""
            ])
            
        # Add TODO section
        report.extend([
            "## TODO",
            "- [ ] Slack integration for automated reporting",
            "- [ ] Email distribution of reports",
            "- [ ] Custom report templates",
            "- [ ] Performance trend analysis",
            "- [ ] Agent-specific recommendations"
        ])
        
        return "\n".join(report)
        
    def display_console_summary(self):
        """Display summary in the console using rich formatting."""
        # Overview panel
        total_tasks = len(self.metrics_df)
        success_rate = (self.metrics_df["status"] == "PASS").mean() * 100
        avg_duration = self.metrics_df["duration_ms"].mean()
        
        overview = Panel(
            f"Total Tasks: {total_tasks}\n"
            f"Success Rate: {success_rate:.2f}%\n"
            f"Average Duration: {avg_duration:.2f}ms",
            title="Daily Overview",
            border_style="blue"
        )
        self.console.print(overview)
        
        # Agent performance table
        table = Table(title="Agent Performance")
        table.add_column("Agent", style="cyan")
        table.add_column("Tasks", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Avg Duration", justify="right")
        table.add_column("Retry Rate", justify="right")
        
        for agent_name in self.metrics_df["agent_name"].unique():
            stats = self.calculate_agent_stats(agent_name)
            table.add_row(
                agent_name,
                str(stats["total_tasks"]),
                f"{stats['success_rate']}%",
                f"{stats['avg_duration']}ms",
                f"{stats['retry_rate']}%"
            )
            
        self.console.print(table)
        
        # Task type breakdown
        task_types = self.metrics_df["task_type"].value_counts()
        type_table = Table(title="Task Type Distribution")
        type_table.add_column("Task Type", style="cyan")
        type_table.add_column("Count", justify="right")
        
        for task_type, count in task_types.head(MAX_TASK_TYPES).items():
            type_table.add_row(task_type, str(count))
            
        self.console.print(type_table)
        
    def save_report(self, content: str):
        """Save the report to a markdown file."""
        # Create reports directory if it doesn't exist
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        # Generate filename with date
        filename = f"daily_report_{self.report_date}.md"
        filepath = os.path.join(REPORT_DIR, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            self.console.print(f"[green]Report saved to {filepath}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving report: {e}[/red]")
            
    def run(self):
        """Generate and display the daily summary."""
        if not self.load_metrics():
            return
            
        # Generate markdown report
        report_content = self.generate_markdown_report()
        
        # Display console summary
        self.display_console_summary()
        
        # Save report
        self.save_report(report_content)
        
        # Display TODO section
        self.console.print("\n[bold]TODO:[/bold]")
        self.console.print(Markdown("""
        - [ ] Slack integration for automated reporting
        - [ ] Email distribution of reports
        - [ ] Custom report templates
        - [ ] Performance trend analysis
        - [ ] Agent-specific recommendations
        """))

if __name__ == "__main__":
    summary = DailySummary()
    summary.run() 