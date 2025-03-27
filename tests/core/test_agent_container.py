"""Tests for the container management functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_container import ContainerManager
from core.config import SystemConfig
from core.exceptions import FatalError

@pytest.fixture
def container_config() -> Dict[str, Any]:
    """Create a test container configuration."""
    return {
        "docker_host": "unix:///var/run/docker.sock",
        "network_name": "pepper-network",
        "default_image": "pepper-base:latest",
        "timeout": 30,
        "max_containers": 10,
        "container_prefix": "pepper-test",
        "resource_limits": {
            "memory": "1g",
            "cpu": "1.0"
        }
    }

@pytest.fixture
def container_manager(container_config: Dict[str, Any]) -> ContainerManager:
    """Create a test container manager instance."""
    config = SystemConfig(**container_config)
    return ContainerManager(config)

@pytest.mark.asyncio
async def test_container_initialization(container_manager: ContainerManager):
    """Test container manager initialization."""
    assert container_manager.config.docker_host == "unix:///var/run/docker.sock"
    assert container_manager.config.network_name == "pepper-network"
    assert container_manager.config.default_image == "pepper-base:latest"

@pytest.mark.asyncio
async def test_container_creation(container_manager: ContainerManager):
    """Test container creation functionality."""
    container_id = await container_manager.create_container(
        image="pepper-base:latest",
        name="test-container",
        environment={"TEST_VAR": "test_value"}
    )
    assert container_id is not None
    
    # Clean up
    await container_manager.remove_container(container_id)

@pytest.mark.asyncio
async def test_container_execution(container_manager: ContainerManager):
    """Test container execution functionality."""
    # Create and start container
    container_id = await container_manager.create_container(
        image="pepper-base:latest",
        name="test-container"
    )
    
    # Execute command
    result = await container_manager.execute_command(
        container_id,
        ["echo", "test"]
    )
    assert result["exit_code"] == 0
    assert "test" in result["output"]
    
    # Clean up
    await container_manager.remove_container(container_id)

@pytest.mark.asyncio
async def test_container_networking(container_manager: ContainerManager):
    """Test container networking functionality."""
    # Create network
    network_id = await container_manager.create_network("test-network")
    assert network_id is not None
    
    # Create container with network
    container_id = await container_manager.create_container(
        image="pepper-base:latest",
        name="test-container",
        network_id=network_id
    )
    
    # Verify network connection
    networks = await container_manager.get_container_networks(container_id)
    assert network_id in networks
    
    # Clean up
    await container_manager.remove_container(container_id)
    await container_manager.remove_network(network_id)

@pytest.mark.asyncio
async def test_container_resource_limits(container_manager: ContainerManager):
    """Test container resource limits."""
    container_id = await container_manager.create_container(
        image="pepper-base:latest",
        name="test-container",
        resource_limits={
            "memory": "512m",
            "cpu": "0.5"
        }
    )
    
    # Verify resource limits
    container_info = await container_manager.get_container_info(container_id)
    assert container_info["memory_limit"] == "512m"
    assert container_info["cpu_limit"] == "0.5"
    
    # Clean up
    await container_manager.remove_container(container_id)

@pytest.mark.asyncio
async def test_container_error_handling(container_manager: ContainerManager):
    """Test container error handling."""
    # Test with invalid image
    with pytest.raises(FatalError):
        await container_manager.create_container(
            image="invalid-image:latest",
            name="test-container"
        )
    
    # Test with invalid container ID
    with pytest.raises(FatalError):
        await container_manager.execute_command(
            "invalid-id",
            ["echo", "test"]
        )

@pytest.mark.asyncio
async def test_container_cleanup(container_manager: ContainerManager):
    """Test container cleanup functionality."""
    # Create multiple containers
    container_ids = []
    for i in range(3):
        container_id = await container_manager.create_container(
            image="pepper-base:latest",
            name=f"test-container-{i}"
        )
        container_ids.append(container_id)
    
    # Clean up all containers
    await container_manager.cleanup_containers()
    
    # Verify containers are removed
    for container_id in container_ids:
        with pytest.raises(FatalError):
            await container_manager.get_container_info(container_id) 