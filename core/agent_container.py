"""Container management for P.E.P.P.E.R."""

import os
import docker
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from loguru import logger

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import ConfigLoader, SystemConfig
    from .exceptions import ContainerError

# Runtime imports
from .exceptions import ContainerError

class ContainerManager:
    """Manages Docker containers for P.E.P.P.E.R. agents."""
    
    def __init__(self, config: 'ConfigLoader'):
        """Initialize the container manager.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.client = docker.from_env()
        self.containers: Dict[str, docker.models.containers.Container] = {}
        
    async def create_container(self, agent_name: str, image: str, **kwargs) -> docker.models.containers.Container:
        """Create a new container for an agent.
        
        Args:
            agent_name: Name of the agent
            image: Docker image to use
            **kwargs: Additional container configuration
            
        Returns:
            Created container instance
            
        Raises:
            ContainerError: If container creation fails
        """
        try:
            container = self.client.containers.run(
                image=image,
                name=f"pepper-{agent_name}",
                detach=True,
                **kwargs
            )
            self.containers[agent_name] = container
            logger.info(f"Created container for agent {agent_name}")
            return container
        except Exception as e:
            raise ContainerError(f"Failed to create container for {agent_name}: {e}")
            
    async def stop_container(self, agent_name: str) -> None:
        """Stop a container for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Raises:
            ContainerError: If container stop fails
        """
        try:
            if agent_name in self.containers:
                container = self.containers[agent_name]
                container.stop()
                container.remove()
                del self.containers[agent_name]
                logger.info(f"Stopped container for agent {agent_name}")
        except Exception as e:
            raise ContainerError(f"Failed to stop container for {agent_name}: {e}")
            
    async def get_container_logs(self, agent_name: str) -> str:
        """Get logs from a container.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Container logs
            
        Raises:
            ContainerError: If log retrieval fails
        """
        try:
            if agent_name in self.containers:
                container = self.containers[agent_name]
                return container.logs().decode('utf-8')
            return ""
        except Exception as e:
            raise ContainerError(f"Failed to get logs for {agent_name}: {e}")
            
    async def get_container_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of a container.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Container status information
            
        Raises:
            ContainerError: If status retrieval fails
        """
        try:
            if agent_name in self.containers:
                container = self.containers[agent_name]
                return {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown"
                }
            return {}
        except Exception as e:
            raise ContainerError(f"Failed to get status for {agent_name}: {e}")
            
    async def list_containers(self) -> List[Dict[str, Any]]:
        """List all P.E.P.P.E.R. containers.
        
        Returns:
            List of container information
            
        Raises:
            ContainerError: If container listing fails
        """
        try:
            containers = self.client.containers.list(
                filters={"name": "pepper-"}
            )
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else "unknown"
                }
                for c in containers
            ]
        except Exception as e:
            raise ContainerError(f"Failed to list containers: {e}")
            
    async def cleanup(self) -> None:
        """Clean up all containers.
        
        Raises:
            ContainerError: If cleanup fails
        """
        try:
            for agent_name in list(self.containers.keys()):
                await self.stop_container(agent_name)
            logger.info("Cleaned up all containers")
        except Exception as e:
            raise ContainerError(f"Failed to cleanup containers: {e}") 