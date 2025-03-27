"""Test configuration and fixtures for PEPPER."""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from core.agent_base import BaseAgent, Task
from core.config_models import DocumentationAgentConfig

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create a mock configuration for testing."""
    return {
        "output_dir": "docs",
        "templates_dir": "templates",
        "supported_doc_types": ["markdown", "sop"],
        "metadata": {
            "default_template": "standard",
            "version": "1.0.0",
            "author": "PEPPER Team"
        },
        "validation_rules": {
            "max_section_depth": 3,
            "required_sections": ["overview", "usage"],
            "min_content_length": 100
        }
    }

@pytest.fixture
def doc_agent_config(mock_config: Dict[str, Any]) -> DocumentationAgentConfig:
    """Create a DocumentationAgentConfig instance for testing."""
    return DocumentationAgentConfig(**mock_config)

@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        task_id="test-001",
        task_type="documentation.generate",
        description="Generate API documentation",
        priority=1,
        metadata={
            "doc_type": "markdown",
            "template": "api_doc",
            "sections": ["overview", "endpoints", "models"],
            "output_format": "markdown"
        }
    )

@pytest.fixture
def sample_markdown_content() -> str:
    """Create sample markdown content for testing."""
    return """# Test Documentation

## Overview
This is a test documentation file.

## Usage
Here's how to use this component:

```python
from pepper import DocumentationAgent

agent = DocumentationAgent("test_agent")
await agent.execute(task)
```

## Configuration
The agent can be configured using YAML files.
""" 