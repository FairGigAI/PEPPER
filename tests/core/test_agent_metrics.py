"""Tests for the metrics collection and reporting functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_metrics import MetricsCollector
from core.config import SystemConfig
from core.exceptions import FatalError

@pytest.fixture
def metrics_config() -> Dict[str, Any]:
    """Create a test metrics configuration."""
    return {
        "log_dir": "logs",
        "metrics_dir": "metrics",
        "retention_days": 30,
        "aggregation_interval": 300,  # 5 minutes
        "max_metrics_per_agent": 1000,
        "compression_enabled": True
    }

@pytest.fixture
def metrics_collector(metrics_config: Dict[str, Any], tmp_path: Path) -> MetricsCollector:
    """Create a test metrics collector instance."""
    # Update paths to use temporary directory
    metrics_config["log_dir"] = str(tmp_path / "logs")
    metrics_config["metrics_dir"] = str(tmp_path / "metrics")
    
    config = SystemConfig(**metrics_config)
    return MetricsCollector(config)

@pytest.mark.asyncio
async def test_metrics_initialization(metrics_collector: MetricsCollector):
    """Test metrics collector initialization."""
    assert metrics_collector.config.log_dir.endswith("logs")
    assert metrics_collector.config.metrics_dir.endswith("metrics")
    assert metrics_collector.config.retention_days == 30

@pytest.mark.asyncio
async def test_metrics_recording(metrics_collector: MetricsCollector):
    """Test metrics recording functionality."""
    # Record test metrics
    await metrics_collector.record_metric(
        agent_id="test-agent",
        metric_name="test_metric",
        value=42.0,
        tags={"test": "value"}
    )
    
    # Verify metric was recorded
    metrics = await metrics_collector.get_metrics("test-agent")
    assert len(metrics) == 1
    assert metrics[0]["name"] == "test_metric"
    assert metrics[0]["value"] == 42.0
    assert metrics[0]["tags"]["test"] == "value"

@pytest.mark.asyncio
async def test_metrics_aggregation(metrics_collector: MetricsCollector):
    """Test metrics aggregation functionality."""
    # Record multiple metrics
    for i in range(5):
        await metrics_collector.record_metric(
            agent_id="test-agent",
            metric_name="test_metric",
            value=float(i),
            timestamp=metrics_collector.get_current_timestamp() - i * 60
        )
    
    # Get aggregated metrics
    aggregated = await metrics_collector.get_aggregated_metrics(
        "test-agent",
        "test_metric",
        "1h"
    )
    assert len(aggregated) > 0
    assert "avg" in aggregated[0]
    assert "min" in aggregated[0]
    assert "max" in aggregated[0]

@pytest.mark.asyncio
async def test_metrics_retention(metrics_collector: MetricsCollector):
    """Test metrics retention functionality."""
    # Record old metric
    old_timestamp = metrics_collector.get_current_timestamp() - (31 * 24 * 60 * 60)  # 31 days ago
    await metrics_collector.record_metric(
        agent_id="test-agent",
        metric_name="old_metric",
        value=42.0,
        timestamp=old_timestamp
    )
    
    # Run retention cleanup
    await metrics_collector.cleanup_old_metrics()
    
    # Verify old metric was removed
    metrics = await metrics_collector.get_metrics("test-agent")
    assert not any(m["name"] == "old_metric" for m in metrics)

@pytest.mark.asyncio
async def test_metrics_compression(metrics_collector: MetricsCollector):
    """Test metrics compression functionality."""
    # Record large number of metrics
    for i in range(100):
        await metrics_collector.record_metric(
            agent_id="test-agent",
            metric_name="test_metric",
            value=float(i),
            tags={"index": str(i)}
        )
    
    # Verify compression
    metrics_file = Path(metrics_collector.config.metrics_dir) / "test-agent.json"
    assert metrics_file.exists()
    assert metrics_file.stat().st_size < 100 * 100  # Should be compressed

@pytest.mark.asyncio
async def test_metrics_error_handling(metrics_collector: MetricsCollector):
    """Test metrics error handling."""
    # Test with invalid agent ID
    with pytest.raises(FatalError):
        await metrics_collector.get_metrics("")
    
    # Test with invalid metric name
    with pytest.raises(FatalError):
        await metrics_collector.record_metric(
            agent_id="test-agent",
            metric_name="",
            value=42.0
        )
    
    # Test with invalid value
    with pytest.raises(FatalError):
        await metrics_collector.record_metric(
            agent_id="test-agent",
            metric_name="test_metric",
            value="invalid"
        )

@pytest.mark.asyncio
async def test_metrics_export(metrics_collector: MetricsCollector, tmp_path: Path):
    """Test metrics export functionality."""
    # Record some test metrics
    for i in range(5):
        await metrics_collector.record_metric(
            agent_id="test-agent",
            metric_name="test_metric",
            value=float(i)
        )
    
    # Export metrics
    export_path = tmp_path / "metrics_export.json"
    await metrics_collector.export_metrics("test-agent", str(export_path))
    
    # Verify export file
    assert export_path.exists()
    assert export_path.stat().st_size > 0 