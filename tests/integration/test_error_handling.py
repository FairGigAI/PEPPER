"""Integration tests for error handling."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_orchestrator import AgentOrchestrator
from core.exceptions import FatalError, TransientError
from core.agent_communication import SecureCommunication
from core.agent_metrics import MetricsCollector

@pytest.fixture
async def error_test_orchestrator(tmp_path):
    """Create an orchestrator for error testing."""
    orchestrator = AgentOrchestrator()
    
    # Configure with error-prone settings
    orchestrator.config.error_handling = {
        "max_retries": 3,
        "retry_delay": 1,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 10
    }
    
    return orchestrator

@pytest.mark.asyncio
async def test_transient_error_handling(error_test_orchestrator: AgentOrchestrator):
    """Test handling of transient errors."""
    # Create task that will fail transiently
    task = {
        "task_id": "test-001",
        "task_type": "test.transient_error",
        "description": "Task with transient error",
        "metadata": {
            "fail_count": 2,
            "success_after": 2
        }
    }
    
    # Execute task
    result = await error_test_orchestrator.assign_task("test_agent", task)
    
    # Verify retry behavior
    assert result["status"] == "success"
    assert result["retry_count"] == 2

@pytest.mark.asyncio
async def test_fatal_error_handling(error_test_orchestrator: AgentOrchestrator):
    """Test handling of fatal errors."""
    # Create task that will fail fatally
    task = {
        "task_id": "test-002",
        "task_type": "test.fatal_error",
        "description": "Task with fatal error",
        "metadata": {
            "error_type": "fatal",
            "error_message": "Critical system error"
        }
    }
    
    # Execute task
    with pytest.raises(FatalError):
        await error_test_orchestrator.assign_task("test_agent", task)
    
    # Verify error state
    task_status = await error_test_orchestrator.get_task_status("test-002")
    assert task_status["status"] == "failed"
    assert task_status["error_type"] == "fatal"

@pytest.mark.asyncio
async def test_circuit_breaker(error_test_orchestrator: AgentOrchestrator):
    """Test circuit breaker functionality."""
    # Create multiple failing tasks
    tasks = []
    for i in range(6):  # Exceeds circuit breaker threshold
        task = {
            "task_id": f"test-{i+3}",
            "task_type": "test.failing",
            "description": f"Failing task {i}",
            "metadata": {"force_failure": True}
        }
        tasks.append(task)
    
    # Execute tasks
    results = await asyncio.gather(
        *[error_test_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify circuit breaker activation
    circuit_status = await error_test_orchestrator.get_circuit_status("test_agent")
    assert circuit_status["is_open"]
    assert circuit_status["failure_count"] >= 5

@pytest.mark.asyncio
async def test_error_metrics(error_test_orchestrator: AgentOrchestrator):
    """Test error metrics collection."""
    # Create failing task
    task = {
        "task_id": "test-009",
        "task_type": "test.error_metrics",
        "description": "Task for error metrics",
        "metadata": {"error_type": "transient"}
    }
    
    # Execute task
    try:
        await error_test_orchestrator.assign_task("test_agent", task)
    except TransientError:
        pass
    
    # Verify error metrics
    metrics = await error_test_orchestrator.get_agent_metrics("test_agent")
    assert metrics["error_count"] > 0
    assert metrics["transient_error_count"] > 0

@pytest.mark.asyncio
async def test_error_recovery(error_test_orchestrator: AgentOrchestrator):
    """Test system recovery after errors."""
    # Create task that will fail and recover
    task = {
        "task_id": "test-010",
        "task_type": "test.recovery",
        "description": "Task with recovery",
        "metadata": {
            "fail_stages": ["init", "process"],
            "recover_after": 2
        }
    }
    
    # Execute task
    result = await error_test_orchestrator.assign_task("test_agent", task)
    
    # Verify recovery
    assert result["status"] == "success"
    assert result["recovery_steps"] == ["init", "process"]
    assert result["final_state"] == "recovered"

@pytest.mark.asyncio
async def test_error_propagation(error_test_orchestrator: AgentOrchestrator):
    """Test error propagation across components."""
    # Create task that will cause cascading failures
    task = {
        "task_id": "test-011",
        "task_type": "test.cascade",
        "description": "Task with cascading errors",
        "metadata": {
            "components": ["frontend", "backend", "database"],
            "failure_point": "backend"
        }
    }
    
    # Execute task
    result = await error_test_orchestrator.assign_task("test_agent", task)
    
    # Verify error propagation
    assert result["status"] == "failed"
    assert "backend" in result["error_chain"]
    assert "frontend" in result["affected_components"]
    assert "database" not in result["affected_components"] 