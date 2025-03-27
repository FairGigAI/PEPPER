"""Integration tests for system performance."""

import pytest
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List
from core.agent_orchestrator import AgentOrchestrator
from core.agent_metrics import MetricsCollector
from core.exceptions import FatalError

@pytest.fixture
async def performance_orchestrator(tmp_path):
    """Create an orchestrator for performance testing."""
    orchestrator = AgentOrchestrator()
    
    # Configure for performance testing
    orchestrator.config.performance = {
        "max_concurrent_tasks": 10,
        "task_timeout": 30,
        "metrics_interval": 1,
        "enable_performance_tracking": True
    }
    
    return orchestrator

@pytest.mark.asyncio
async def test_task_execution_time(performance_orchestrator: AgentOrchestrator):
    """Test task execution time performance."""
    # Create test task
    task = {
        "task_id": "test-001",
        "task_type": "test.performance",
        "description": "Performance test task",
        "metadata": {
            "operation": "compute",
            "complexity": "medium"
        }
    }
    
    # Measure execution time
    start_time = time.time()
    result = await performance_orchestrator.assign_task("test_agent", task)
    end_time = time.time()
    
    # Verify performance metrics
    execution_time = end_time - start_time
    assert execution_time < 5.0  # Should complete within 5 seconds
    assert "performance_metrics" in result
    assert "cpu_usage" in result["performance_metrics"]
    assert "memory_usage" in result["performance_metrics"]

@pytest.mark.asyncio
async def test_concurrent_task_performance(performance_orchestrator: AgentOrchestrator):
    """Test performance with concurrent tasks."""
    # Create multiple tasks
    tasks = []
    for i in range(5):
        task = {
            "task_id": f"test-{i+2}",
            "task_type": "test.concurrent",
            "description": f"Concurrent task {i}",
            "metadata": {
                "operation": "io_bound",
                "duration": 1
            }
        }
        tasks.append(task)
    
    # Execute tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(
        *[performance_orchestrator.assign_task("test_agent", task) for task in tasks]
    )
    end_time = time.time()
    
    # Verify concurrent execution performance
    total_time = end_time - start_time
    assert total_time < 3.0  # Should complete within 3 seconds
    assert all(r["status"] == "success" for r in results)

@pytest.mark.asyncio
async def test_memory_usage(performance_orchestrator: AgentOrchestrator):
    """Test memory usage under load."""
    # Create memory-intensive task
    task = {
        "task_id": "test-007",
        "task_type": "test.memory",
        "description": "Memory usage test",
        "metadata": {
            "operation": "memory_intensive",
            "data_size": "1GB"
        }
    }
    
    # Execute task and monitor memory
    result = await performance_orchestrator.assign_task("test_agent", task)
    
    # Verify memory metrics
    metrics = result["performance_metrics"]
    assert metrics["peak_memory_usage"] < 2 * 1024 * 1024 * 1024  # Less than 2GB
    assert metrics["memory_leak"] == 0

@pytest.mark.asyncio
async def test_cpu_utilization(performance_orchestrator: AgentOrchestrator):
    """Test CPU utilization under load."""
    # Create CPU-intensive task
    task = {
        "task_id": "test-008",
        "task_type": "test.cpu",
        "description": "CPU usage test",
        "metadata": {
            "operation": "cpu_intensive",
            "iterations": 1000000
        }
    }
    
    # Execute task and monitor CPU
    result = await performance_orchestrator.assign_task("test_agent", task)
    
    # Verify CPU metrics
    metrics = result["performance_metrics"]
    assert metrics["cpu_usage"] < 80  # Less than 80% CPU usage
    assert metrics["cpu_throttling"] == 0

@pytest.mark.asyncio
async def test_io_performance(performance_orchestrator: AgentOrchestrator, tmp_path: Path):
    """Test I/O performance."""
    # Create I/O-intensive task
    test_file = tmp_path / "test_data.txt"
    test_file.write_text("x" * (1024 * 1024))  # 1MB file
    
    task = {
        "task_id": "test-009",
        "task_type": "test.io",
        "description": "I/O performance test",
        "metadata": {
            "operation": "io_intensive",
            "file_path": str(test_file),
            "iterations": 100
        }
    }
    
    # Execute task and monitor I/O
    result = await performance_orchestrator.assign_task("test_agent", task)
    
    # Verify I/O metrics
    metrics = result["performance_metrics"]
    assert metrics["io_operations"] > 0
    assert metrics["io_throughput"] > 0
    assert metrics["io_latency"] < 100  # Less than 100ms

@pytest.mark.asyncio
async def test_network_performance(performance_orchestrator: AgentOrchestrator):
    """Test network performance."""
    # Create network-intensive task
    task = {
        "task_id": "test-010",
        "task_type": "test.network",
        "description": "Network performance test",
        "metadata": {
            "operation": "network_intensive",
            "endpoints": ["/api/test1", "/api/test2"],
            "requests": 100
        }
    }
    
    # Execute task and monitor network
    result = await performance_orchestrator.assign_task("test_agent", task)
    
    # Verify network metrics
    metrics = result["performance_metrics"]
    assert metrics["network_requests"] == 100
    assert metrics["network_latency"] < 200  # Less than 200ms
    assert metrics["network_errors"] == 0 