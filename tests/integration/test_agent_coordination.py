"""Integration tests for agent coordination."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_orchestrator import AgentOrchestrator
from core.task_router import TaskRouter
from core.exceptions import FatalError, TransientError

@pytest.fixture
async def task_router():
    """Create a task router for testing."""
    return TaskRouter()

@pytest.fixture
async def coordinated_orchestrator(tmp_path):
    """Create an orchestrator with task routing for testing."""
    orchestrator = AgentOrchestrator()
    router = TaskRouter()
    
    # Configure and register agents
    frontend_config = {
        "agent_id": "test_frontend",
        "component_dir": str(tmp_path / "components"),
        "default_framework": "react",
        "build_throttle": 1.0
    }
    
    backend_config = {
        "agent_id": "test_backend",
        "api_dir": str(tmp_path / "api"),
        "default_framework": "fastapi"
    }
    
    # Register agents with router
    await router.register_agent("frontend", frontend_config)
    await router.register_agent("backend", backend_config)
    
    # Set up orchestrator with router
    orchestrator.set_task_router(router)
    
    return orchestrator

@pytest.mark.asyncio
async def test_task_routing(coordinated_orchestrator: AgentOrchestrator):
    """Test task routing between agents."""
    # Create tasks for different agents
    tasks = [
        {
            "task_id": "test-001",
            "task_type": "frontend.create_component",
            "description": "Frontend task",
            "metadata": {"component": "TestComponent"}
        },
        {
            "task_id": "test-002",
            "task_type": "backend.create_endpoint",
            "description": "Backend task",
            "metadata": {"endpoint": "/api/test"}
        }
    ]
    
    # Route tasks
    results = await asyncio.gather(
        *[coordinated_orchestrator.route_task(task) for task in tasks]
    )
    
    # Verify routing
    assert results[0]["agent_id"] == "frontend"
    assert results[1]["agent_id"] == "backend"

@pytest.mark.asyncio
async def test_task_dependencies(coordinated_orchestrator: AgentOrchestrator):
    """Test handling of task dependencies."""
    # Create dependent tasks
    backend_task = {
        "task_id": "test-003",
        "task_type": "backend.create_endpoint",
        "description": "Create API endpoint",
        "metadata": {"endpoint": "/api/data"}
    }
    
    frontend_task = {
        "task_id": "test-004",
        "task_type": "frontend.create_component",
        "description": "Create component using API",
        "metadata": {
            "component": "DataComponent",
            "depends_on": "test-003"
        }
    }
    
    # Execute tasks
    backend_result = await coordinated_orchestrator.route_task(backend_task)
    frontend_result = await coordinated_orchestrator.route_task(frontend_task)
    
    # Verify dependency handling
    assert frontend_result["status"] == "waiting"
    assert frontend_result["waiting_for"] == "test-003"
    
    # Complete backend task
    await coordinated_orchestrator.complete_task("test-003")
    
    # Verify frontend task can proceed
    frontend_status = await coordinated_orchestrator.get_task_status("test-004")
    assert frontend_status["status"] == "in_progress"

@pytest.mark.asyncio
async def test_task_prioritization(coordinated_orchestrator: AgentOrchestrator):
    """Test task prioritization."""
    # Create tasks with different priorities
    tasks = [
        {
            "task_id": "test-005",
            "task_type": "frontend.create_component",
            "description": "Low priority task",
            "priority": 1,
            "metadata": {"component": "LowPriority"}
        },
        {
            "task_id": "test-006",
            "task_type": "frontend.create_component",
            "description": "High priority task",
            "priority": 3,
            "metadata": {"component": "HighPriority"}
        }
    ]
    
    # Route tasks
    results = await asyncio.gather(
        *[coordinated_orchestrator.route_task(task) for task in tasks]
    )
    
    # Verify prioritization
    assert results[1]["priority"] > results[0]["priority"]
    assert results[1]["status"] == "in_progress"
    assert results[0]["status"] == "queued"

@pytest.mark.asyncio
async def test_task_failure_handling(coordinated_orchestrator: AgentOrchestrator):
    """Test handling of task failures."""
    # Create task that will fail
    failing_task = {
        "task_id": "test-007",
        "task_type": "backend.create_endpoint",
        "description": "Task that will fail",
        "metadata": {
            "endpoint": "/api/fail",
            "force_failure": True
        }
    }
    
    # Route and execute task
    result = await coordinated_orchestrator.route_task(failing_task)
    
    # Verify failure handling
    assert result["status"] == "failed"
    assert "error" in result
    
    # Verify retry mechanism
    retry_status = await coordinated_orchestrator.get_task_status("test-007")
    assert retry_status["retry_count"] > 0

@pytest.mark.asyncio
async def test_task_cancellation(coordinated_orchestrator: AgentOrchestrator):
    """Test task cancellation."""
    # Create long-running task
    long_task = {
        "task_id": "test-008",
        "task_type": "backend.create_endpoint",
        "description": "Long running task",
        "metadata": {
            "endpoint": "/api/long",
            "simulate_delay": 5
        }
    }
    
    # Start task
    result = await coordinated_orchestrator.route_task(long_task)
    
    # Cancel task
    await coordinated_orchestrator.cancel_task("test-008")
    
    # Verify cancellation
    task_status = await coordinated_orchestrator.get_task_status("test-008")
    assert task_status["status"] == "cancelled"
    assert task_status["cancelled_at"] is not None 