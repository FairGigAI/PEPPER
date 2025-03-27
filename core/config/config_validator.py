"""Configuration validator for P.E.P.P.E.R."""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, Field, validator

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .base import BaseAgentConfig, SystemConfig
    from .models import AGENT_CONFIG_TYPES

class ValidationCheckpoint(BaseModel):
    """Represents a validation checkpoint for agent tasks."""
    checkpoint_id: str
    agent_id: str
    task_id: str
    status: str = Field(default="pending")  # pending, approved, rejected
    approved_by: Optional[str] = None
    approval_time: Optional[str] = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConfigValidator:
    """Validates configurations for P.E.P.P.E.R."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the configuration validator.
        
        Args:
            config_dir: Optional directory for storing validation checkpoints
        """
        self.config_dir = config_dir or Path("config")
        self.checkpoints: Dict[str, ValidationCheckpoint] = {}
        self._load_schemas()
        self._load_checkpoints()
        
    def _load_schemas(self) -> None:
        """Load validation schemas."""
        self.schemas = {
            "agent": self._create_agent_schema(),
            "system": self._create_system_schema(),
            "environment": self._create_environment_schema()
        }
        
    def _create_agent_schema(self) -> BaseModel:
        """Create agent configuration schema."""
        class AgentSchema(BaseModel):
            type: str
            enabled: bool
            metadata: Dict[str, Any]
            
            @validator("type")
            def validate_type(cls, v):
                if v not in AGENT_CONFIG_TYPES:
                    raise ValueError(f"Invalid agent type. Must be one of: {list(AGENT_CONFIG_TYPES.keys())}")
                return v
                
            @validator("metadata")
            def validate_metadata(cls, v, values):
                agent_type = values.get("type")
                if agent_type in AGENT_CONFIG_TYPES:
                    agent_config_class = AGENT_CONFIG_TYPES[agent_type]
                    # Validate against the specific agent config model
                    agent_config_class(**v)
                return v
                
        return AgentSchema
        
    def _create_system_schema(self) -> BaseModel:
        """Create system configuration schema."""
        return SystemConfig
        
    def _create_environment_schema(self) -> BaseModel:
        """Create environment configuration schema."""
        class EnvironmentSchema(BaseModel):
            project: Dict[str, Any]
            core: Dict[str, Any]
            github: Dict[str, Any]
            slack: Dict[str, Any]
            openai: Dict[str, Any]
            database: Dict[str, Any]
            docker: Dict[str, Any]
            frontend: Dict[str, Any]
            backend: Dict[str, Any]
            monitoring: Dict[str, Any]
            security: Dict[str, Any]
            features: Dict[str, Any]
            
            @validator("project")
            def validate_project(cls, v):
                required_fields = ["name", "environment", "debug", "log_level"]
                for field in required_fields:
                    if field not in v:
                        raise ValueError(f"Missing required field in project config: {field}")
                return v
                
            @validator("core")
            def validate_core(cls, v):
                required_fields = ["secret_key", "api_key", "encryption_key", "jwt_secret"]
                for field in required_fields:
                    if field not in v:
                        raise ValueError(f"Missing required field in core config: {field}")
                return v
                
            @validator("github")
            def validate_github(cls, v):
                if "access_token" not in v:
                    raise ValueError("Missing required field in GitHub config: access_token")
                return v
                
            @validator("slack")
            def validate_slack(cls, v):
                required_fields = ["bot_token", "signing_secret", "webhook_url"]
                for field in required_fields:
                    if field not in v:
                        raise ValueError(f"Missing required field in Slack config: {field}")
                return v
                
            @validator("openai")
            def validate_openai(cls, v):
                if "api_key" not in v:
                    raise ValueError("Missing required field in OpenAI config: api_key")
                return v
                
            @validator("database")
            def validate_database(cls, v):
                required_fields = ["host", "port", "name", "user", "password"]
                for field in required_fields:
                    if field not in v:
                        raise ValueError(f"Missing required field in database config: {field}")
                return v
                
        return EnvironmentSchema
        
    def validate_config(self, config: Dict[str, Any], config_type: str) -> bool:
        """Validate a configuration dictionary.
        
        Args:
            config: Configuration dictionary to validate
            config_type: Type of configuration to validate
            
        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            if config_type not in self.schemas:
                raise ValueError(f"Invalid configuration type: {config_type}")
                
            schema = self.schemas[config_type]
            schema(**config)
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
            
    def validate_agent_config(self, config: Dict[str, Any]) -> bool:
        """Validate an agent configuration.
        
        Args:
            config: Agent configuration to validate
            
        Returns:
            True if validation succeeds, False otherwise
        """
        return self.validate_config(config, "agent")
        
    def validate_system_config(self, config: Dict[str, Any]) -> bool:
        """Validate a system configuration.
        
        Args:
            config: System configuration to validate
            
        Returns:
            True if validation succeeds, False otherwise
        """
        return self.validate_config(config, "system")
        
    def validate_environment_config(self, config: Dict[str, Any]) -> bool:
        """Validate an environment configuration.
        
        Args:
            config: Environment configuration to validate
            
        Returns:
            True if validation succeeds, False otherwise
        """
        return self.validate_config(config, "environment")
        
    def get_validation_errors(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """Get validation errors for a configuration.
        
        Args:
            config: Configuration to validate
            config_type: Type of configuration
            
        Returns:
            List of validation error messages
        """
        errors = []
        try:
            if config_type not in self.schemas:
                errors.append(f"Invalid configuration type: {config_type}")
                return errors
                
            schema = self.schemas[config_type]
            schema(**config)
        except Exception as e:
            errors.append(str(e))
            
        return errors

    def _load_checkpoints(self) -> None:
        """Load existing checkpoints from disk."""
        checkpoint_file = self.config_dir / "checkpoints.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.checkpoints = {
                        k: ValidationCheckpoint(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load checkpoints: {e}")
                
    def _save_checkpoints(self) -> None:
        """Save checkpoints to disk."""
        checkpoint_file = self.config_dir / "checkpoints.json"
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(
                    {k: v.dict() for k, v in self.checkpoints.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save checkpoints: {e}")
            
    def create_checkpoint(
        self,
        agent_id: str,
        task_id: str,
        validation_rules: Dict[str, Any]
    ) -> str:
        """Create a new validation checkpoint.
        
        Args:
            agent_id: ID of the agent
            task_id: ID of the task
            validation_rules: Rules for validation
            
        Returns:
            ID of the created checkpoint
        """
        checkpoint_id = f"{agent_id}_{task_id}_{int(time.time())}"
        checkpoint = ValidationCheckpoint(
            checkpoint_id=checkpoint_id,
            agent_id=agent_id,
            task_id=task_id,
            validation_rules=validation_rules
        )
        self.checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoints()
        return checkpoint_id
        
    def approve_checkpoint(self, checkpoint_id: str, approved_by: str) -> bool:
        """Approve a validation checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to approve
            approved_by: ID of the approver
            
        Returns:
            True if approval succeeds, False otherwise
        """
        if checkpoint_id not in self.checkpoints:
            return False
            
        checkpoint = self.checkpoints[checkpoint_id]
        checkpoint.status = "approved"
        checkpoint.approved_by = approved_by
        checkpoint.approval_time = datetime.now().isoformat()
        self._save_checkpoints()
        return True
        
    def reject_checkpoint(self, checkpoint_id: str, approved_by: str) -> bool:
        """Reject a validation checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to reject
            approved_by: ID of the rejector
            
        Returns:
            True if rejection succeeds, False otherwise
        """
        if checkpoint_id not in self.checkpoints:
            return False
            
        checkpoint = self.checkpoints[checkpoint_id]
        checkpoint.status = "rejected"
        checkpoint.approved_by = approved_by
        checkpoint.approval_time = datetime.now().isoformat()
        self._save_checkpoints()
        return True
        
    def get_checkpoint_status(self, checkpoint_id: str) -> Optional[str]:
        """Get the status of a validation checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint
            
        Returns:
            Status of the checkpoint if found, None otherwise
        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        return checkpoint.status if checkpoint else None
        
    def validate_throttle_settings(self, config: Dict[str, Any]) -> bool:
        """Validate build throttle settings.
        
        Args:
            config: Configuration containing throttle settings
            
        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            throttle = config.get("build_throttle", 1.0)
            if not isinstance(throttle, (int, float)) or throttle < 0.1 or throttle > 2.0:
                raise ValueError(f"Invalid throttle value: {throttle}")
            return True
        except Exception as e:
            logger.error(f"Throttle validation failed: {e}")
            return False
            
    def validate_approval_settings(self, config: Dict[str, Any]) -> bool:
        """Validate approval settings.
        
        Args:
            config: Configuration containing approval settings
            
        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            requires_approval = config.get("requires_approval", True)
            approval_agent = config.get("approval_agent")
            
            if requires_approval and not approval_agent:
                raise ValueError("approval_agent must be specified when requires_approval is True")
                
            if approval_agent and approval_agent not in ["pm_agent", "orchestrator"]:
                raise ValueError(f"Invalid approval agent: {approval_agent}")
                
            return True
        except Exception as e:
            logger.error(f"Approval settings validation failed: {e}")
            return False 