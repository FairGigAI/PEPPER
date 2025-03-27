"""Integration tests for agent workflows."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_orchestrator import AgentOrchestrator
from agents.specialized.frontend import FrontendAgent
from agents.specialized.backend import BackendAgent
from core.config_models import (
    FrontendAgentConfig,
    BackendAgentConfig
)
from core.exceptions import FatalError, TransientError

@pytest.fixture
async def orchestrator(tmp_path):
    """Create an orchestrator for testing."""
    orchestrator = AgentOrchestrator()
    
    # Configure agents
    frontend_config = FrontendAgentConfig(
        agent_id="test_frontend",
        component_dir=str(tmp_path / "components"),
        default_framework="react",
        build_throttle=1.0
    )
    
    backend_config = BackendAgentConfig(
        agent_id="test_backend",
        api_dir=str(tmp_path / "api"),
        default_framework="fastapi"
    )
    
    # Register agents
    await orchestrator.register_agent(
        "frontend",
        FrontendAgent("test_frontend", frontend_config)
    )
    
    await orchestrator.register_agent(
        "backend",
        BackendAgent("test_backend", backend_config)
    )
    
    return orchestrator

@pytest.mark.asyncio
async def test_component_creation_workflow(orchestrator: AgentOrchestrator):
    """Test complete component creation workflow."""
    # Create frontend component task
    frontend_task = {
        "task_id": "test-001",
        "task_type": "frontend.create_component",
        "description": "Create a new React component",
        "metadata": {
            "component_name": "TestComponent",
            "framework": "react",
            "props": ["title", "content"],
            "styling": "css"
        }
    }
    
    # Create backend API task
    backend_task = {
        "task_id": "test-002",
        "task_type": "backend.create_endpoint",
        "description": "Create a new API endpoint",
        "metadata": {
            "endpoint": "/api/test",
            "method": "GET",
            "response_type": "json"
        }
    }
    
    # Execute workflow
    frontend_result = await orchestrator.assign_task("frontend", frontend_task)
    backend_result = await orchestrator.assign_task("backend", backend_task)
    
    # Verify results
    assert frontend_result["status"] == "success"
    assert backend_result["status"] == "success"
    assert "component_path" in frontend_result
    assert "endpoint_url" in backend_result

@pytest.mark.asyncio
async def test_validation_workflow(orchestrator: AgentOrchestrator):
    """Test validation workflow between agents."""
    # Create frontend component
    frontend_task = {
        "task_id": "test-003",
        "task_type": "frontend.create_component",
        "description": "Create a component for validation",
        "metadata": {
            "component_name": "ValidatedComponent",
            "framework": "react",
            "props": ["data"],
            "validation": True
        }
    }
    
    # Create backend validation endpoint
    backend_task = {
        "task_id": "test-004",
        "task_type": "backend.create_validator",
        "description": "Create validation endpoint",
        "metadata": {
            "endpoint": "/api/validate",
            "method": "POST",
            "validation_rules": {
                "data": "required|string|min:3"
            }
        }
    }
    
    # Execute workflow
    frontend_result = await orchestrator.assign_task("frontend", frontend_task)
    backend_result = await orchestrator.assign_task("backend", backend_task)
    
    # Test validation
    validation_result = await orchestrator.validate_workflow(
        frontend_result["component_path"],
        backend_result["endpoint_url"]
    )
    
    assert validation_result["status"] == "success"
    assert "validation_errors" in validation_result
    assert len(validation_result["validation_errors"]) == 0

@pytest.mark.asyncio
async def test_throttled_workflow(orchestrator: AgentOrchestrator):
    """Test throttled workflow execution."""
    # Create multiple frontend tasks
    tasks = []
    for i in range(5):
        task = {
            "task_id": f"test-{i+5}",
            "task_type": "frontend.create_component",
            "description": f"Create component {i}",
            "metadata": {
                "component_name": f"ThrottledComponent{i}",
                "framework": "react",
                "props": ["data"]
            }
        }
        tasks.append(task)
    
    # Execute tasks concurrently
    results = await asyncio.gather(
        *[orchestrator.assign_task("frontend", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify throttling
    success_count = sum(1 for r in results if isinstance(r, dict) and r["status"] == "success")
    assert success_count <= 3  # Should be throttled

@pytest.mark.asyncio
async def test_approval_workflow(orchestrator: AgentOrchestrator):
    """Test approval workflow between agents."""
    # Create frontend component requiring approval
    frontend_task = {
        "task_id": "test-010",
        "task_type": "frontend.create_component",
        "description": "Create component requiring approval",
        "metadata": {
            "component_name": "ApprovedComponent",
            "framework": "react",
            "props": ["data"],
            "requires_approval": True
        }
    }
    
    # Create backend API requiring approval
    backend_task = {
        "task_id": "test-011",
        "task_type": "backend.create_endpoint",
        "description": "Create endpoint requiring approval",
        "metadata": {
            "endpoint": "/api/approved",
            "method": "POST",
            "requires_approval": True
        }
    }
    
    # Execute workflow
    frontend_result = await orchestrator.assign_task("frontend", frontend_task)
    backend_result = await orchestrator.assign_task("backend", backend_task)
    
    # Verify pending approval
    assert frontend_result["status"] == "pending_approval"
    assert backend_result["status"] == "pending_approval"
    
    # Approve tasks
    await orchestrator.approve_task(frontend_result["task_id"])
    await orchestrator.approve_task(backend_result["task_id"])
    
    # Verify completion
    frontend_status = await orchestrator.get_task_status(frontend_result["task_id"])
    backend_status = await orchestrator.get_task_status(backend_result["task_id"])
    
    assert frontend_status["status"] == "completed"
    assert backend_status["status"] == "completed" 