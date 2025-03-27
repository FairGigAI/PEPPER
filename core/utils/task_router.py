"""Task router for directing tasks to appropriate agents."""

from typing import Dict, List, Optional, Type, Any
from loguru import logger

from .agent_base import BaseAgent, Task

class TaskRouter:
    """Routes tasks to appropriate agents based on task type."""
    
    def __init__(self):
        """Initialize the task router with available agents."""
        self.agent_types: Dict[str, str] = {
            "frontend.component_creation": "FrontendAgent",
            "frontend.styling": "FrontendAgent",
            "frontend.state_management": "FrontendAgent",
            "backend.api_development": "BackendAgent",
            "backend.database": "BackendAgent",
            "backend.microservices": "BackendAgent",
            "qa.testing": "QAAgent",
            "qa.automation": "QAAgent",
            "pm.planning": "ProjectManagerAgent",
            "pm.resource_allocation": "ProjectManagerAgent"
        }
        
    def get_agent(self, task_type: str) -> Optional[Type[BaseAgent]]:
        """Get the appropriate agent for a task type."""
        agent_name = self.agent_types.get(task_type)
        if not agent_name:
            logger.error(f"Unknown agent type: {task_type}")
            return None
            
        # Lazy import of agent classes
        try:
            if agent_name == "FrontendAgent":
                from agents.specialized.frontend.frontend_agent import FrontendAgent
                return FrontendAgent
            elif agent_name == "BackendAgent":
                from agents.specialized.backend.backend_agent import BackendAgent
                return BackendAgent
            elif agent_name == "QAAgent":
                from agents.qa_agent import QAAgent
                return QAAgent
            elif agent_name == "ProjectManagerAgent":
                from agents.pm_agent import ProjectManagerAgent
                return ProjectManagerAgent
            else:
                logger.error(f"Unknown agent name: {agent_name}")
                return None
        except ImportError as e:
            logger.error(f"Failed to import agent {agent_name}: {e}")
            return None
        
    async def route_task(self, task: Task) -> Dict[str, Any]:
        """Route a task to the appropriate agent and execute it."""
        agent_class = self.get_agent(task.task_type)
        if not agent_class:
            raise ValueError(f"No agent found for task type: {task.task_type}")
            
        agent = agent_class(task.task_id, {})  # Empty config for now
        return await agent.execute(task)

    def get_available_agents(self) -> List[str]:
        """Get list of registered agent types."""
        return list(self.agent_types.keys()) 