"""Configuration package for P.E.P.P.E.R."""

from .base import BaseAgentConfig, SystemConfig, RetryConfig
from .loader import ConfigLoader
from .models import (
    FrontendAgentConfig,
    BackendAgentConfig,
    QAAgentConfig,
    PMAgentConfig,
    GitHubAgentConfig,
    DocumentationAgentConfig,
    TimelineEstimatorAgentConfig,
    AGENT_CONFIG_TYPES
)

__all__ = [
    # Base configurations
    'BaseAgentConfig',
    'SystemConfig',
    'RetryConfig',
    
    # Configuration loader
    'ConfigLoader',
    
    # Agent-specific configurations
    'FrontendAgentConfig',
    'BackendAgentConfig',
    'QAAgentConfig',
    'PMAgentConfig',
    'GitHubAgentConfig',
    'DocumentationAgentConfig',
    'TimelineEstimatorAgentConfig',
    
    # Registry
    'AGENT_CONFIG_TYPES'
]
