"""Base agent implementation for P.E.P.P.E.R."""

import os
import json
from typing import Dict, Any, Optional, List, Union, Type, TypeVar, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
from loguru import logger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import BaseAgentConfig, ConfigLoader
    from .agent_llm import LLMInterface
    from .agent_container import ContainerManager
    from .agent_communication import SecureCommunication
    from .agent_metrics import record_metric

class Task(BaseModel):
    """Task model for agent processing."""
    
    task_id: str
    task_type: str
    priority: int
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    payload: Dict[str, Any]
    
class BaseAgent:
    """Base class for all P.E.P.P.E.R. agents."""
    
    def __init__(
        self,
        agent_id: str,
        config: Optional['BaseAgentConfig'] = None,
        llm_interface: Optional['LLMInterface'] = None,
        container_manager: Optional['ContainerManager'] = None,
        communication: Optional['SecureCommunication'] = None
    ):
        """Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Agent configuration
            llm_interface: LLM interface for agent operations
            container_manager: Container manager for agent operations
            communication: Communication interface for agent operations
        """
        self.agent_id = agent_id
        self.config = config
        self.llm_interface = llm_interface
        self.container_manager = container_manager
        self.communication = communication
        
        self._setup_logging()
        self._setup_api()
        
    def _setup_logging(self) -> None:
        """Set up logging for the agent."""
        log_dir = Path("logs") / self.agent_id
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_dir / f"{datetime.now().strftime('%Y%m%d')}.log",
            rotation="1 day",
            retention="7 days",
            level="INFO"
        )
        
    def _setup_api(self) -> None:
        """Set up FastAPI application for the agent."""
        self.app = FastAPI(title=f"P.E.P.P.E.R. {self.agent_id} Agent")
        
        @self.app.get("/status")
        async def get_status():
            """Get agent status."""
            return {
                "agent_id": self.agent_id,
                "status": "running",
                "config": self.config.dict() if self.config else None
            }
            
        @self.app.post("/task")
        async def assign_task(task: Task):
            """Assign a task to the agent.
            
            Args:
                task: Task to assign
                
            Returns:
                Task assignment result
                
            Raises:
                HTTPException: If task assignment fails
            """
            try:
                if not self.can_handle_task(task.task_type):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent cannot handle task type: {task.task_type}"
                    )
                    
                result = await self.handle_task(task)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Task assignment failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Task assignment failed: {str(e)}"
                )
                
    async def handle_task(self, task: Task) -> Dict[str, Any]:
        """Handle an assigned task.
        
        Args:
            task: Task to handle
            
        Returns:
            Task handling result
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement handle_task")
        
    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle a task type.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True if agent can handle the task type, False otherwise
        """
        if not self.config:
            return False
        return task_type in self.config.supported_tasks
        
    async def start(self) -> None:
        """Start the agent."""
        logger.info(f"Starting agent: {self.agent_id}")
        if self.container_manager:
            await self.container_manager.start_container(self.agent_id)
            
    async def stop(self) -> None:
        """Stop the agent."""
        logger.info(f"Stopping agent: {self.agent_id}")
        if self.container_manager:
            await self.container_manager.stop_container(self.agent_id)
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics.
        
        Returns:
            Dictionary of agent metrics
        """
        return {
            "agent_id": self.agent_id,
            "status": "running",
            "tasks_processed": 0,
            "errors": 0,
            "last_active": datetime.now().isoformat()
        }
        
    def update_metrics(self, metric_name: str, value: Any) -> None:
        """Update agent metrics.
        
        Args:
            metric_name: Name of the metric to update
            value: Value to set for the metric
        """
        if TYPE_CHECKING:
            record_metric(f"{self.agent_id}.{metric_name}", value)

    def log_task_start(self, task: Task):
        """Log task start."""
        self.logger.info(
            f"Starting task {task.task_id} with {self.agent_id}: "
            f"{task.description}"
        )
        task.start_time = datetime.now()
        task.status = "running"
        
    def log_task_end(self, task: Task, result: Dict[str, Any]):
        """Log task completion."""
        status = result.get("status", "unknown")
        self.logger.info(
            f"Completed task {task.task_id} with {self.agent_id}: {status}"
        )
        task.end_time = datetime.now()
        task.status = "completed" if status == "success" else "failed"
        task.result = result
        
    async def handle_error(self, task: Task, error: Exception):
        """Handle task execution errors."""
        self.logger.error(
            f"Error in task {task.task_id} with {self.agent_id}: {str(error)}"
        )
        task.end_time = datetime.now()
        task.status = "failed"
        task.error = error
        
        if isinstance(error, TransientError):
            logger.warning(f"Transient error in task {task.task_id}: {error}")
        else:
            logger.error(f"Fatal error in task {task.task_id}: {error}")
        raise error
        
    async def get_llm_support(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get LLM support for task execution."""
        try:
            if response_format:
                return await self.llm_interface.generate_structured_response(
                    prompt=prompt,
                    response_format=response_format,
                    system_message=system_message
                )
            else:
                return await self.llm_interface.generate_response(
                    prompt=prompt,
                    system_message=system_message
                )
        except Exception as e:
            logger.error(f"Error getting LLM support: {e}")
            raise
            
    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task with preprocessing and postprocessing."""
        start_time = time.time()
        self.log_task_start(task)
        
        try:
            # Preprocess
            preprocess_result = await self.preprocess(task)
            task.metadata.update(preprocess_result)
            
            # Execute
            result = await self.execute(task)
            if not isinstance(result, dict):
                result = {"status": "success", "result": result}
            if "status" not in result:
                result["status"] = "success"
            
            # Postprocess
            final_result = await self.postprocess(task, result)
            if not isinstance(final_result, dict):
                final_result = {"status": "success", "result": final_result}
            if "status" not in final_result:
                final_result["status"] = "success"
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metric
            record_metric(
                agent_name=self.agent_id,
                task_type=task.task_type,
                task_description=task.description,
                status=final_result.get("status", "unknown"),
                duration_ms=duration_ms
            )
            
            self.log_task_end(task, final_result)
            return final_result
            
        except Exception as e:
            # Calculate duration even for failed tasks
            duration_ms = (time.time() - start_time) * 1000
            
            # Record failed metric
            record_metric(
                agent_name=self.agent_id,
                task_type=task.task_type,
                task_description=task.description,
                status=f"error: {str(e)}",
                duration_ms=duration_ms
            )
            
            await self.handle_error(task, e)
            
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        if self.container_manager and self.container_manager.container:
            # Get container status before processing
            status = self.container_manager.get_container_status(self.container_manager.container)
            logger.info(f"Container status before preprocessing: {status}")
            
        # Implement preprocessing logic
        return {}
        
    @abstractmethod
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the task."""
        pass
        
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        if self.container_manager and self.container_manager.container:
            # Get container status after processing
            status = self.container_manager.get_container_status(self.container_manager.container)
            logger.info(f"Container status after processing: {status}")
            
            # Get container logs
            logs = self.container_manager.get_container_logs(self.container_manager.container)
            logger.info(f"Container logs: {logs}")
            
        # Implement postprocessing logic
        return result
        
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare the task before execution."""
        return task 

    def cleanup(self) -> None:
        """Clean up agent resources."""
        if self.container_manager and self.container_manager.container:
            try:
                self.container_manager.stop_agent_container(self.container_manager.container)
                self.container_manager.remove_agent_container(self.container_manager.container)
                logger.info(f"Cleaned up container for agent {self.agent_id}")
            except Exception as e:
                logger.error(f"Failed to clean up container for agent {self.agent_id}: {e}")
                raise FatalError(f"Container cleanup failed: {e}")
                
    def __del__(self):
        """Clean up on deletion."""
        self.cleanup()
        log_hook.remove_agent(self.agent_id)

    def _setup_health_check(self):
        """Set up health check endpoint."""
        @self.api.get("/health")
        async def health_check():
            try:
                # Check if agent can access required directories
                required_dirs = [
                    self.config.get("component_dir", "/app/output"),
                    "/app/logs",
                    "/app/config"
                ]
                
                for directory in required_dirs:
                    if not os.path.exists(directory):
                        raise HTTPException(
                            status_code=503,
                            detail=f"Required directory {directory} not accessible"
                        )
                
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "agent_type": self.__class__.__name__
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Health check failed: {str(e)}"
                )
    
    async def _handle_task_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming task requests."""
        task = Task(**payload)
        return await self.run_task(task)
        
    async def _handle_status_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status updates from other agents."""
        # Implement status update handling logic
        return {"status": "received"}
        
    async def send_message_to_agent(
        self,
        receiver_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a secure message to another agent."""
        try:
            encrypted_message = self.communication.send_message(
                receiver_id,
                message_type,
                payload
            )
            
            # Get receiver's endpoint from service discovery
            receiver_endpoint = await self._get_agent_endpoint(receiver_id)
            
            # Send message using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{receiver_endpoint}/message",
                    json={"message": encrypted_message}
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Failed to send message: {await response.text()}"
                        )
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Failed to send message to {receiver_id}: {e}")
            raise
            
    async def _get_agent_endpoint(self, agent_id: str) -> str:
        """Get the endpoint for an agent from service discovery."""
        # In a real implementation, this would use service discovery
        # For now, we'll use a simple mapping
        agent_host = agent_id.replace("-", "_")
        return f"http://{agent_host}:8000"

    def log(self, message: str, level: str = "info"):
        """Log a message with the agent's context."""
        # Get the agent's log handler
        handler = log_hook.get_handler(self.agent_id)
        if handler:
            handler(message)
        else:
            # Fallback to standard logging
            getattr(self.logger, level)(message)

    @abstractmethod
    async def initialize(self):
        """Initialize the agent."""
        pass
        
    @abstractmethod
    async def run(self):
        """Run the agent."""
        pass
        
    @abstractmethod
    async def stop(self):
        """Stop the agent."""
        pass 