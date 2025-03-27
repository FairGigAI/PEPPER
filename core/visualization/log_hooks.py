"""Log hooks for connecting agent logs to visualization components."""

from typing import Optional, Callable
from loguru import logger
from .matrix_view import MatrixView

class LogHook:
    """Hook system for connecting logs to visualization components."""
    
    def __init__(self):
        self.matrix_view: Optional[MatrixView] = None
        self.log_handlers: Dict[str, Callable] = {}
        
    def set_matrix_view(self, matrix_view: MatrixView):
        """Set the matrix view for log visualization."""
        self.matrix_view = matrix_view
        
    def register_agent(self, agent_id: str):
        """Register an agent for log handling."""
        self.log_handlers[agent_id] = self._create_agent_handler(agent_id)
        
    def _create_agent_handler(self, agent_id: str) -> Callable:
        """Create a log handler for a specific agent."""
        def handle_log(message: str):
            """Handle log message for the agent."""
            if self.matrix_view:
                self.matrix_view.update_agent_log(agent_id, message)
            logger.info(f"[{agent_id}] {message}")
        return handle_log
        
    def get_handler(self, agent_id: str) -> Optional[Callable]:
        """Get the log handler for a specific agent."""
        return self.log_handlers.get(agent_id)
        
    def remove_agent(self, agent_id: str):
        """Remove an agent's log handler."""
        if agent_id in self.log_handlers:
            del self.log_handlers[agent_id]
            
    def clear(self):
        """Clear all log handlers."""
        self.log_handlers.clear()
        self.matrix_view = None

# Global log hook instance
log_hook = LogHook() 