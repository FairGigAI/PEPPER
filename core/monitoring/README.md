# PEPPER Monitoring Module

This module provides monitoring and metrics collection functionality for PEPPER.

## Features

- Task execution metrics recording
- Agent performance monitoring
- System health tracking
- Resource usage monitoring

## Usage

```python
from core.monitoring import record_metric

# Record a task execution metric
record_metric(
    agent_name="frontend_agent",
    task_type="component_creation",
    task_description="Create login form component",
    status="success",
    duration_ms=150.5,
    metadata={"component_type": "form", "framework": "react"}
)
```

## Future Enhancements

1. Time-series database integration
2. Real-time dashboard updates
3. Alert system
4. Performance analysis
5. Resource usage tracking 