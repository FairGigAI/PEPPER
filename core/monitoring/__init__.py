"""Monitoring module for PEPPER."""

from typing import Optional
from datetime import datetime
from loguru import logger

def record_metric(
    agent_name: str,
    task_type: str,
    task_description: str,
    status: str,
    duration_ms: float,
    metadata: Optional[dict] = None
) -> None:
    """Record a metric for monitoring and analysis.
    
    Args:
        agent_name: Name of the agent executing the task
        task_type: Type of task being executed
        task_description: Description of the task
        status: Status of the task execution
        duration_ms: Duration of the task in milliseconds
        metadata: Optional additional metadata
    """
    try:
        # Create metric record
        metric = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "task_type": task_type,
            "task_description": task_description,
            "status": status,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }
        
        # Log the metric
        logger.info(f"Metric recorded: {metric}")
        
        # TODO: In the future, this could:
        # 1. Store metrics in a time-series database
        # 2. Send metrics to a monitoring service
        # 3. Update real-time dashboards
        # 4. Trigger alerts based on thresholds
        
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        # Don't raise the exception - we don't want metric recording to break the main flow
