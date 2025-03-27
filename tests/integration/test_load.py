"""Integration tests for system load handling."""

import pytest
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List
from core.agent_orchestrator import AgentOrchestrator
from core.agent_metrics import MetricsCollector
from core.exceptions import FatalError

@pytest.fixture
async def load_orchestrator(tmp_path):
    """Create an orchestrator for load testing."""
    orchestrator = AgentOrchestrator()
    
    # Configure for load testing
    orchestrator.config.load = {
        "max_concurrent_tasks": 100,
        "task_timeout": 60,
        "resource_limits": {
            "cpu": "80%",
            "memory": "8GB",
            "network": "1Gbps"
        },
        "enable_load_monitoring": True
    }
    
    return orchestrator

@pytest.mark.asyncio
async def test_concurrent_task_load(load_orchestrator: AgentOrchestrator):
    """Test system under concurrent task load."""
    # Create large number of concurrent tasks
    tasks = []
    for i in range(50):
        task = {
            "task_id": f"test-{i+1}",
            "task_type": "test.concurrent",
            "description": f"Concurrent task {i}",
            "metadata": {
                "operation": "compute",
                "duration": 1
            }
        }
        tasks.append(task)
    
    # Execute tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    end_time = time.time()
    
    # Verify load handling
    total_time = end_time - start_time
    success_count = sum(1 for r in results if isinstance(r, dict) and r["status"] == "success")
    assert success_count > 0
    assert total_time < 30  # Should complete within 30 seconds

@pytest.mark.asyncio
async def test_memory_load(load_orchestrator: AgentOrchestrator):
    """Test system under memory load."""
    # Create memory-intensive tasks
    tasks = []
    for i in range(10):
        task = {
            "task_id": f"test-{i+51}",
            "task_type": "test.memory",
            "description": f"Memory load task {i}",
            "metadata": {
                "operation": "memory_intensive",
                "data_size": "500MB"
            }
        }
        tasks.append(task)
    
    # Execute tasks
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify memory handling
    metrics = await load_orchestrator.get_system_metrics()
    assert metrics["memory_usage"] < 8 * 1024 * 1024 * 1024  # Less than 8GB
    assert metrics["memory_pressure"] < 80  # Less than 80% pressure

@pytest.mark.asyncio
async def test_cpu_load(load_orchestrator: AgentOrchestrator):
    """Test system under CPU load."""
    # Create CPU-intensive tasks
    tasks = []
    for i in range(20):
        task = {
            "task_id": f"test-{i+61}",
            "task_type": "test.cpu",
            "description": f"CPU load task {i}",
            "metadata": {
                "operation": "cpu_intensive",
                "iterations": 1000000
            }
        }
        tasks.append(task)
    
    # Execute tasks
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify CPU handling
    metrics = await load_orchestrator.get_system_metrics()
    assert metrics["cpu_usage"] < 80  # Less than 80% CPU usage
    assert metrics["cpu_throttling"] < 20  # Less than 20% throttling

@pytest.mark.asyncio
async def test_network_load(load_orchestrator: AgentOrchestrator):
    """Test system under network load."""
    # Create network-intensive tasks
    tasks = []
    for i in range(30):
        task = {
            "task_id": f"test-{i+81}",
            "task_type": "test.network",
            "description": f"Network load task {i}",
            "metadata": {
                "operation": "network_intensive",
                "endpoints": ["/api/test1", "/api/test2"],
                "requests": 100
            }
        }
        tasks.append(task)
    
    # Execute tasks
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify network handling
    metrics = await load_orchestrator.get_system_metrics()
    assert metrics["network_throughput"] < 1024 * 1024 * 1024  # Less than 1Gbps
    assert metrics["network_errors"] == 0

@pytest.mark.asyncio
async def test_disk_load(load_orchestrator: AgentOrchestrator, tmp_path: Path):
    """Test system under disk I/O load."""
    # Create disk-intensive tasks
    tasks = []
    for i in range(15):
        task = {
            "task_id": f"test-{i+111}",
            "task_type": "test.disk",
            "description": f"Disk load task {i}",
            "metadata": {
                "operation": "disk_intensive",
                "file_size": "100MB",
                "iterations": 10
            }
        }
        tasks.append(task)
    
    # Execute tasks
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    
    # Verify disk handling
    metrics = await load_orchestrator.get_system_metrics()
    assert metrics["disk_io"] < 100 * 1024 * 1024  # Less than 100MB/s
    assert metrics["disk_queue_length"] < 100

@pytest.mark.asyncio
async def test_sustained_load(load_orchestrator: AgentOrchestrator):
    """Test system under sustained load."""
    # Create sustained load tasks
    tasks = []
    for i in range(5):
        task = {
            "task_id": f"test-{i+126}",
            "task_type": "test.sustained",
            "description": f"Sustained load task {i}",
            "metadata": {
                "operation": "mixed",
                "duration": 30,
                "intensity": "high"
            }
        }
        tasks.append(task)
    
    # Execute tasks for extended period
    start_time = time.time()
    results = await asyncio.gather(
        *[load_orchestrator.assign_task("test_agent", task) for task in tasks],
        return_exceptions=True
    )
    end_time = time.time()
    
    # Verify sustained load handling
    total_time = end_time - start_time
    assert total_time >= 30  # Should run for at least 30 seconds
    assert all(r["status"] == "success" for r in results if isinstance(r, dict)) 