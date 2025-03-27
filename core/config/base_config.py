"""Base configuration models for PEPPER."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

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