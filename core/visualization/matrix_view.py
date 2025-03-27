"""Matrix View for PEPPER - Real-time terminal visualization of agent activities."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.style import Style
from loguru import logger

class MatrixView:
    """Matrix-style terminal view for PEPPER agents."""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.agent_panels: Dict[str, List[str]] = {}
        self.max_log_lines = 20
        self.is_running = False
        
    def setup_layout(self):
        """Set up the terminal layout with header, main content, and footer."""
        # Create main layout
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main area into agent panels
        self.layout["main"].split_row(
            Layout(name="frontend"),
            Layout(name="backend"),
            Layout(name="qa"),
            Layout(name="pm")
        )
        
        # Initialize agent panels
        self.agent_panels = {
            "frontend": [],
            "backend": [],
            "qa": [],
            "pm": []
        }
        
    def create_header(self) -> Panel:
        """Create the header panel with PEPPER status."""
        header_text = Text("PEPPER Matrix View", style="bold magenta")
        header_text.append("\n")
        header_text.append(f"Time: {datetime.now().strftime('%H:%M:%S')}", style="cyan")
        
        return Panel(
            header_text,
            style="bold white",
            title="PEPPER",
            border_style="magenta"
        )
        
    def create_agent_panel(self, agent_id: str) -> Panel:
        """Create a panel for a specific agent."""
        logs = self.agent_panels.get(agent_id, [])
        # Keep only the last max_log_lines
        logs = logs[-self.max_log_lines:]
        
        # Create panel content
        content = Text()
        for log in logs:
            content.append(f"{log}\n")
            
        return Panel(
            content,
            title=f"Agent: {agent_id}",
            border_style="blue",
            height=20
        )
        
    def create_footer(self) -> Panel:
        """Create the footer panel with controls."""
        footer_text = Text()
        footer_text.append("Controls: ", style="bold")
        footer_text.append("q: Quit | r: Refresh | c: Clear | h: Help", style="cyan")
        
        return Panel(
            footer_text,
            style="bold white",
            border_style="magenta"
        )
        
    def update_agent_log(self, agent_id: str, message: str):
        """Update the log for a specific agent."""
        if agent_id in self.agent_panels:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.agent_panels[agent_id].append(log_entry)
            
    def clear_agent_logs(self):
        """Clear all agent logs."""
        for agent_id in self.agent_panels:
            self.agent_panels[agent_id] = []
            
    async def handle_keyboard(self):
        """Handle keyboard input for controls."""
        while self.is_running:
            if await asyncio.get_event_loop().run_in_executor(None, lambda: self.console.input()):
                key = await asyncio.get_event_loop().run_in_executor(None, lambda: self.console.input())
                if key.lower() == 'q':
                    self.is_running = False
                elif key.lower() == 'c':
                    self.clear_agent_logs()
                elif key.lower() == 'r':
                    self.console.clear()
                elif key.lower() == 'h':
                    self.show_help()
                    
    def show_help(self):
        """Show help information."""
        help_text = """
        PEPPER Matrix View Help:
        ------------------------
        q: Quit the matrix view
        r: Refresh the display
        c: Clear all logs
        h: Show this help message
        
        Agent Panels:
        ------------
        Each panel shows real-time logs from different PEPPER agents:
        - Frontend: Frontend development agent
        - Backend: Backend development agent
        - QA: Quality assurance agent
        - PM: Project management agent
        """
        self.console.print(Panel(help_text, title="Help", border_style="green"))
        
    async def run(self):
        """Run the matrix view."""
        self.setup_layout()
        self.is_running = True
        
        try:
            with Live(self.layout, refresh_per_second=4) as live:
                while self.is_running:
                    # Update layout
                    self.layout["header"].update(self.create_header())
                    self.layout["frontend"].update(self.create_agent_panel("frontend"))
                    self.layout["backend"].update(self.create_agent_panel("backend"))
                    self.layout["qa"].update(self.create_agent_panel("qa"))
                    self.layout["pm"].update(self.create_agent_panel("pm"))
                    self.layout["footer"].update(self.create_footer())
                    
                    # Handle keyboard input
                    await self.handle_keyboard()
                    
                    # Small delay to prevent CPU overuse
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error in matrix view: {e}")
            self.is_running = False
        finally:
            self.console.clear()
            
    def stop(self):
        """Stop the matrix view."""
        self.is_running = False 