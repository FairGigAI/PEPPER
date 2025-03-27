"""Tests for the base agent functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_base import BaseAgent, Task
from core.config import BaseAgentConfig
from core.exceptions import FatalError, TransientError

class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    async def handle_task(self, task: Task) -> Dict[str, Any]:
        """Handle a test task."""
        if task.task_type == "test.success":
            return {"status": "success", "result": "test passed"}
        elif task.task_type == "test.error":
            raise FatalError("Test error")
        elif task.task_type == "test.transient":
            raise TransientError("Test transient error")
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")

@pytest.fixture
def test_agent_config() -> Dict[str, Any]:
    """Create a test agent configuration."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "description": "A test agent implementation",
        "version": "1.0.0",
        "capabilities": ["test.success", "test.error", "test.transient"],
        "max_retries": 3,
        "timeout": 30,
        "log_level": "DEBUG"
    }

@pytest.fixture
def test_agent(test_agent_config: Dict[str, Any]) -> TestAgent:
    """Create a test agent instance."""
    config = BaseAgentConfig(**test_agent_config)
    return TestAgent("test_agent", config)

@pytest.mark.asyncio
async def test_agent_initialization(test_agent: TestAgent):
    """Test agent initialization."""
    assert test_agent.agent_id == "test_agent"
    assert test_agent.config.name == "Test Agent"
    assert test_agent.config.version == "1.0.0"
    assert "test.success" in test_agent.config.capabilities

@pytest.mark.asyncio
async def test_agent_task_handling(test_agent: TestAgent):
    """Test task handling functionality."""
    # Test successful task
    success_task = Task(
        task_id="test-001",
        task_type="test.success",
        description="Test successful task"
    )
    result = await test_agent.handle_task(success_task)
    assert result["status"] == "success"
    assert result["result"] == "test passed"
    
    # Test error task
    error_task = Task(
        task_id="test-002",
        task_type="test.error",
        description="Test error task"
    )
    with pytest.raises(FatalError):
        await test_agent.handle_task(error_task)
    
    # Test transient error task
    transient_task = Task(
        task_id="test-003",
        task_type="test.transient",
        description="Test transient error task"
    )
    with pytest.raises(TransientError):
        await test_agent.handle_task(transient_task)

@pytest.mark.asyncio
async def test_agent_capability_checking(test_agent: TestAgent):
    """Test capability checking functionality."""
    # Test supported capability
    assert test_agent.can_handle_task("test.success")
    
    # Test unsupported capability
    assert not test_agent.can_handle_task("test.unsupported")

@pytest.mark.asyncio
async def test_agent_metrics(test_agent: TestAgent):
    """Test metrics collection and reporting."""
    # Record some test metrics
    test_agent.update_metrics({
        "tasks_processed": 1,
        "success_rate": 1.0,
        "average_processing_time": 0.5
    })
    
    # Get metrics
    metrics = test_agent.get_metrics()
    assert metrics["tasks_processed"] == 1
    assert metrics["success_rate"] == 1.0
    assert metrics["average_processing_time"] == 0.5

@pytest.mark.asyncio
async def test_agent_lifecycle(test_agent: TestAgent):
    """Test agent lifecycle management."""
    # Start agent
    await test_agent.start()
    assert test_agent.is_running
    
    # Stop agent
    await test_agent.stop()
    assert not test_agent.is_running 