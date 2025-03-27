"""Agent-specific configuration models for PEPPER."""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

from .base import BaseAgentConfig, RetryConfig

class FrontendAgentConfig(BaseAgentConfig):
    """Configuration for frontend agent."""
    type: str = "frontend"
    default_framework: str = Field(default="react")
    component_templates: Dict[str, str] = Field(default_factory=dict)
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    build_tools: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)

class BackendAgentConfig(BaseAgentConfig):
    """Configuration for backend agent."""
    type: str = "backend"
    default_framework: str = Field(default="fastapi")
    database_type: str = Field(default="postgresql")
    api_version: str = Field(default="1.0.0")
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    middleware: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)

class QAAgentConfig(BaseAgentConfig):
    """Configuration for QA agent."""
    type: str = "qa"
    test_framework: str = Field(default="pytest")
    coverage_threshold: float = Field(default=80.0)
    test_patterns: List[str] = Field(default_factory=list)
    excluded_paths: List[str] = Field(default_factory=list)
    reporting_format: str = Field(default="html")

class PMAgentConfig(BaseAgentConfig):
    """Configuration for project management agent."""
    type: str = "pm"
    project_tools: List[str] = Field(default_factory=list)
    reporting_frequency: str = Field(default="daily")
    metrics: List[str] = Field(default_factory=list)
    stakeholders: List[Dict[str, str]] = Field(default_factory=list)

class GitHubAgentConfig(BaseAgentConfig):
    """Configuration for GitHub integration agent."""
    type: str = "github"
    repository: str
    branch: str = Field(default="main")
    access_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    auto_merge: bool = False
    required_checks: List[str] = Field(default_factory=list)

class DocumentationAgentConfig(BaseAgentConfig):
    """Configuration for documentation agent."""
    type: str = "docs"
    doc_format: str = Field(default="markdown")
    output_dir: str = Field(default="docs")
    templates_dir: Optional[str] = None
    auto_generate: bool = True
    include_diagrams: bool = True

class TimelineEstimatorAgentConfig(BaseAgentConfig):
    """Configuration for timeline estimation agent."""
    type: str = "timeline"
    estimation_model: str = Field(default="basic")
    confidence_threshold: float = Field(default=0.8)
    historical_data: Optional[Dict[str, Any]] = None
    risk_factors: List[Dict[str, float]] = Field(default_factory=list)

# Registry of all agent config types
AGENT_CONFIG_TYPES = {
    "frontend": FrontendAgentConfig,
    "backend": BackendAgentConfig,
    "qa": QAAgentConfig,
    "pm": PMAgentConfig,
    "github": GitHubAgentConfig,
    "docs": DocumentationAgentConfig,
    "timeline": TimelineEstimatorAgentConfig
} 