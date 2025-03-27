#!/usr/bin/env python3
"""P.E.P.P.E.R. - Project Execution and Planning Platform for Engineering Resources."""

import os
import sys
import asyncio
import argparse
from typing import Optional
from loguru import logger
from core.config import ConfigLoader
from core.visualization.matrix_view import MatrixView
from core.agent_base import BaseAgent
from core.monitoring import record_metric
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()

def setup_logging(verbose: bool, debug: bool) -> None:
    """Configure logging based on verbosity level."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

def display_banner() -> None:
    """Display PEPPER banner."""
    banner = r"""
    [bold magenta]
                                                              /|  
                                                            .-((--.
    ██████╗ ███████╗██████╗ ██████╗ ███████╗██████╗        ( '`^'; )
    ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗       `;#    |
    ██████╔╝█████╗  ██████╔╝██████╔╝█████╗  ██████╔╝        \#    |
    ██╔═══╝ ██╔══╝  ██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗         \#   \ 
    ██║     ███████╗██║     ██║     ███████╗██║  ██║          '-.  ) 
    ╚═╝     ╚══════╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝             \(    
                                                                  `     
    [/bold magenta]
    [italic]Project Execution and Planning Platform for Enhanced Resource Management
    ...or spicy assistant to an eccentric billionaire...[/italic]

    Pepper is the AI-powered project execution and planning platform for enhanced resource management. 

    - It automates tasks, manages resources, and ensures projects are completed on time and within budget. 
    - It is designed to be a multi-agent system that can be used to manage projects of any size and complexity. 
    - It is built on top of the latest LLM and AI technologies to provide a powerful and flexible platform 
    for project management. 
    - It is designed to be used by anyone, anywhere, and anytime.

    Pepper is the coding and near-autonomous agent assistant that will build your next big idea. 
    [bold red]
    BUT!!! it is a tool and it is not a replacement for your brain. 
    You are still the one who needs to do the thinking, and you are responsible
    for the output of the code and the decisions made. 
    [/bold red]
    [bold green] Code responsibly, and have fun! [/bold green]
    """
    console.print(Panel(banner, border_style="blue"))

def display_help_table() -> None:
    """Display help information in a formatted table."""
    table = Table(title="PEPPER Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Options", style="yellow")

    commands = [
        ("init", "Initialize a new PEPPER project", "--name, --template"),
        ("start", "Start the PEPPER system", "--config, --env"),
        ("stop", "Stop the PEPPER system", "--force"),
        ("status", "Display system status", "--json, --detailed"),
        ("config", "Manage configurations", "show, edit, validate"),
        ("agent", "Manage agents", "list, start, stop, status"),
        ("task", "Manage tasks", "create, list, assign, complete"),
        ("report", "Generate reports", "--type, --format, --period"),
        ("monitor", "Monitor system metrics", "--interval, --metrics"),
        ("backup", "Backup system state", "--type, --destination"),
        ("restore", "Restore system state", "--source, --force"),
        ("update", "Update system components", "--component, --version"),
        ("clean", "Clean system resources", "--type, --force"),
        ("help", "Show this help message", "--verbose"),
    ]

    for cmd, desc, opts in commands:
        table.add_row(cmd, desc, opts)

    console.print(table)

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all commands and options."""
    parser = argparse.ArgumentParser(
        description="PEPPER - Project Execution and Planning Platform for Enhanced Resource Management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--env",
        type=str,
        help="Environment to use (dev, staging, prod)"
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Enable matrix view for agent visualization"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new PEPPER project")
    init_parser.add_argument("--name", required=True, help="Project name")
    init_parser.add_argument("--template", help="Project template to use")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the PEPPER system")
    start_parser.add_argument("--force", action="store_true", help="Force start")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the PEPPER system")
    stop_parser.add_argument("--force", action="store_true", help="Force stop")

    # Status command
    status_parser = subparsers.add_parser("status", help="Display system status")
    status_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    status_parser.add_argument("--detailed", action="store_true", help="Show detailed status")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configurations")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("edit", help="Edit configuration")
    config_subparsers.add_parser("validate", help="Validate configuration")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Manage agents")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command")
    agent_subparsers.add_parser("list", help="List all agents")
    agent_subparsers.add_parser("start", help="Start an agent")
    agent_subparsers.add_parser("stop", help="Stop an agent")
    agent_subparsers.add_parser("status", help="Show agent status")

    # Task command
    task_parser = subparsers.add_parser("task", help="Manage tasks")
    task_subparsers = task_parser.add_subparsers(dest="task_command")
    task_subparsers.add_parser("create", help="Create a new task")
    task_subparsers.add_parser("list", help="List all tasks")
    task_subparsers.add_parser("assign", help="Assign a task")
    task_subparsers.add_parser("complete", help="Mark a task as complete")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("--type", choices=["daily", "weekly", "monthly"], help="Report type")
    report_parser.add_argument("--format", choices=["text", "json", "html"], help="Report format")
    report_parser.add_argument("--period", help="Report period")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor system metrics")
    monitor_parser.add_argument("--interval", type=int, help="Update interval in seconds")
    monitor_parser.add_argument("--metrics", nargs="+", help="Metrics to monitor")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup system state")
    backup_parser.add_argument("--type", choices=["full", "config", "data"], help="Backup type")
    backup_parser.add_argument("--destination", help="Backup destination path")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore system state")
    restore_parser.add_argument("--source", required=True, help="Backup source path")
    restore_parser.add_argument("--force", action="store_true", help="Force restore")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update system components")
    update_parser.add_argument("--component", help="Component to update")
    update_parser.add_argument("--version", help="Target version")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean system resources")
    clean_parser.add_argument("--type", choices=["logs", "cache", "temp"], help="Resource type")
    clean_parser.add_argument("--force", action="store_true", help="Force clean")

    return parser

async def main() -> Optional[int]:
    """Main entry point for PEPPER."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose, args.debug)

    # Display banner
    display_banner()

    # Handle help command
    if args.command == "help" or not args.command:
        display_help_table()
        return 0

    # Initialize matrix view if requested
    matrix_view = None
    if args.matrix:
        matrix_view = MatrixView()

    # Handle other commands
    try:
        if args.command == "init":
            # Initialize project
            pass
        elif args.command == "start":
            # Start system with matrix view if requested
            if matrix_view:
                await matrix_view.run()
            else:
                # Regular start
                pass
        elif args.command == "stop":
            # Stop system
            if matrix_view:
                matrix_view.stop()
            pass
        elif args.command == "status":
            # Show status
            pass
        elif args.command == "config":
            # Handle config commands
            pass
        elif args.command == "agent":
            # Handle agent commands
            pass
        elif args.command == "task":
            # Handle task commands
            pass
        elif args.command == "report":
            # Generate reports
            pass
        elif args.command == "monitor":
            # Monitor system
            pass
        elif args.command == "backup":
            # Backup system
            pass
        elif args.command == "restore":
            # Restore system
            pass
        elif args.command == "update":
            # Update system
            pass
        elif args.command == "clean":
            # Clean system
            pass

        return 0
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 