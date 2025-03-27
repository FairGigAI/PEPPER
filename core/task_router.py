"""Task routing module for P.E.P.P.E.R."""

from typing import Dict, Any, Optional, List
from loguru import logger
from .agent_base import BaseAgent, Task
from .exceptions import TaskError

class TaskRouter:
    """Routes tasks to appropriate agents."""
    
    def __init__(self):
        """Initialize the task router."""
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Task] = []
        self.routing_rules: Dict[str, str] = {}
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the router.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")
        
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the router.
        
        Args:
            agent_id: ID of agent to unregister
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            
    def add_routing_rule(self, task_type: str, agent_id: str) -> None:
        """Add a routing rule for task types.
        
        Args:
            task_type: Type of task to route
            agent_id: ID of agent to route to
        """
        self.routing_rules[task_type] = agent_id
        logger.info(f"Added routing rule: {task_type} -> {agent_id}")
        
    def route_task(self, task: Task) -> Optional[BaseAgent]:
        """Route a task to the appropriate agent.
        
        Args:
            task: Task to route
            
        Returns:
            Agent to handle the task, or None if no agent found
        """
        try:
            # Check routing rules first
            if task.task_type in self.routing_rules:
                agent_id = self.routing_rules[task.task_type]
                if agent_id in self.agents:
                    return self.agents[agent_id]
                    
            # Fall back to agent capabilities
            for agent in self.agents.values():
                if agent.can_handle_task(task):
                    return agent
                    
            logger.warning(f"No agent found for task type: {task.task_type}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to route task: {e}")
            raise TaskError(f"Task routing failed: {e}")
            
    def queue_task(self, task: Task) -> None:
        """Add a task to the queue.
        
        Args:
            task: Task to queue
        """
        self.task_queue.append(task)
        logger.info(f"Queued task: {task.task_id}")
        
    def process_queue(self) -> None:
        """Process all tasks in the queue."""
        while self.task_queue:
            task = self.task_queue.pop(0)
            agent = self.route_task(task)
            if agent:
                try:
                    agent.handle_task(task)
                except Exception as e:
                    logger.error(f"Failed to process task {task.task_id}: {e}")
                    # Requeue failed tasks
                    self.queue_task(task)
            else:
                logger.error(f"No agent available for task: {task.task_id}")
                
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of an agent.
        
        Args:
            agent_id: ID of agent to check
            
        Returns:
            Agent status information
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return {
                "id": agent.agent_id,
                "type": agent.agent_type,
                "status": agent.status,
                "current_task": agent.current_task.task_id if agent.current_task else None
            }
        return {}
        
    def get_queue_status(self) -> Dict[str, Any]:
        """Get status of the task queue.
        
        Returns:
            Queue status information
        """
        return {
            "queue_length": len(self.task_queue),
            "tasks": [task.task_id for task in self.task_queue],
            "agents": {
                agent_id: self.get_agent_status(agent_id)
                for agent_id in self.agents
            }
        } 