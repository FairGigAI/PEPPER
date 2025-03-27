"""Base configuration models for PEPPER."""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    retries: int = Field(default=3)
    delay: float = Field(default=1.0)
    max_delay: float = Field(default=32.0)
    backoff_strategy: str = Field(default="exponential")

class BaseAgentConfig(BaseModel):
    """Base configuration for all agents."""
    agent_id: str
    type: str
    capabilities: List[str] = Field(default_factory=list)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    output_dir: Optional[str] = None
    supported_frameworks: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SystemConfig(BaseModel):
    """System-wide configuration."""
    project_name: str
    environment: str
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str
    api_key: str
    encryption_key: str
    max_retries: int = 3
    timeout: float = 30.0
    cache_dir: Optional[str] = None
    temp_dir: Optional[str] = None 