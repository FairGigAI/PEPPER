"""Configuration validator for P.E.P.P.E.R."""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union, List, Type
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, ValidationError, Field

# Type checking imports to avoid circular dependencies
from .base import BaseAgentConfig, SystemConfig
from .models import AGENT_CONFIG_TYPES

class ValidationError(Exception):
    """Custom validation error with detailed information."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        """Initialize validation error.
        
        Args:
            message: Error message
            errors: List of validation errors
        """
        self.message = message
        self.errors = errors
        super().__init__(message)

class ConfigValidator:
    """Validates configuration files and values."""
    
    def __init__(self, config_dir: Union[str, Path]):
        """Initialize the validator.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate a configuration file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            True if validation succeeds, False otherwise
            
        Raises:
            ValidationError: If validation fails with details
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}", [])
            
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix in ('.yaml', '.yml'):
                    config_data = yaml.safe_load(f)
                elif file_path.suffix == '.json':
                    config_data = json.load(f)
                else:
                    raise ValidationError(
                        f"Unsupported file type: {file_path.suffix}",
                        [{"loc": ["file_type"], "msg": f"Unsupported file type: {file_path.suffix}"}]
                    )
                    
            return self.validate_config(config_data, file_path.name)
        except Exception as e:
            raise ValidationError(f"Failed to validate file {file_path}: {str(e)}", [])
            
    def validate_config(self, config_data: Dict[str, Any], config_type: str) -> bool:
        """Validate configuration data.
        
        Args:
            config_data: Configuration data to validate
            config_type: Type of configuration (e.g., 'system', 'agent')
            
        Returns:
            True if validation succeeds, False otherwise
            
        Raises:
            ValidationError: If validation fails with details
        """
        try:
            if config_type == 'system':
                SystemConfig(**config_data)
            elif config_type.startswith('agent'):
                agent_type = config_data.get('type')
                if agent_type not in AGENT_CONFIG_TYPES:
                    raise ValidationError(
                        f"Invalid agent type: {agent_type}",
                        [{"loc": ["type"], "msg": f"Invalid agent type: {agent_type}"}]
                    )
                agent_config_class = AGENT_CONFIG_TYPES[agent_type]
                agent_config_class(**config_data)
            elif config_type == 'feature_flags':
                self._validate_feature_flags(config_data)
            elif config_type == 'secrets':
                self._validate_secrets(config_data)
            elif config_type == 'environment':
                self._validate_environment(config_data)
            else:
                raise ValidationError(
                    f"Unknown configuration type: {config_type}",
                    [{"loc": ["config_type"], "msg": f"Unknown configuration type: {config_type}"}]
                )
            return True
        except ValidationError as e:
            raise ValidationError(f"Validation failed for {config_type}: {str(e)}", e.errors())
            
    def _validate_feature_flags(self, flags: Dict[str, Any]) -> None:
        """Validate feature flags configuration.
        
        Args:
            flags: Feature flags to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(flags, dict):
            raise ValidationError(
                "Feature flags must be a dictionary",
                [{"loc": ["feature_flags"], "msg": "Feature flags must be a dictionary"}]
            )
            
        for flag_name, flag_value in flags.items():
            if not isinstance(flag_name, str):
                raise ValidationError(
                    f"Invalid feature flag name: {flag_name}",
                    [{"loc": ["feature_flags", flag_name], "msg": "Feature flag name must be a string"}]
                )
            if not isinstance(flag_value, bool):
                raise ValidationError(
                    f"Invalid feature flag value for {flag_name}",
                    [{"loc": ["feature_flags", flag_name], "msg": "Feature flag value must be a boolean"}]
                )
                
    def _validate_secrets(self, secrets: Dict[str, Any]) -> None:
        """Validate secrets configuration.
        
        Args:
            secrets: Secrets to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(secrets, dict):
            raise ValidationError(
                "Secrets must be a dictionary",
                [{"loc": ["secrets"], "msg": "Secrets must be a dictionary"}]
            )
            
        for secret_name, secret_value in secrets.items():
            if not isinstance(secret_name, str):
                raise ValidationError(
                    f"Invalid secret name: {secret_name}",
                    [{"loc": ["secrets", secret_name], "msg": "Secret name must be a string"}]
                )
            if not isinstance(secret_value, str):
                raise ValidationError(
                    f"Invalid secret value for {secret_name}",
                    [{"loc": ["secrets", secret_name], "msg": "Secret value must be a string"}]
                )
                
    def _validate_environment(self, env_config: Dict[str, Any]) -> None:
        """Validate environment configuration.
        
        Args:
            env_config: Environment configuration to validate
            
        Raises:
            ValidationError: If validation fails
        """
        required_fields = {'environment', 'debug', 'log_level'}
        missing_fields = required_fields - set(env_config.keys())
        if missing_fields:
            raise ValidationError(
                f"Missing required environment fields: {missing_fields}",
                [{"loc": ["environment", field], "msg": f"Missing required field: {field}"} for field in missing_fields]
            )
            
        if env_config['environment'] not in {'development', 'production', 'staging'}:
            raise ValidationError(
                f"Invalid environment value: {env_config['environment']}",
                [{"loc": ["environment", "environment"], "msg": "Environment must be one of: development, production, staging"}]
            )
            
        if not isinstance(env_config['debug'], bool):
            raise ValidationError(
                "Debug must be a boolean",
                [{"loc": ["environment", "debug"], "msg": "Debug must be a boolean"}]
            )
            
        if env_config['log_level'] not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
            raise ValidationError(
                f"Invalid log level: {env_config['log_level']}",
                [{"loc": ["environment", "log_level"], "msg": "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"}]
            )
            
    def validate_all_configs(self) -> bool:
        """Validate all configuration files.
        
        Returns:
            True if all validations succeed, False otherwise
            
        Raises:
            ValidationError: If any validation fails
        """
        try:
            # Validate system config
            system_config_path = self.config_dir / 'system.yaml'
            if system_config_path.exists():
                self.validate_file(system_config_path)
                
            # Validate agent configs
            agents_dir = self.config_dir / 'agents'
            if agents_dir.exists():
                for config_file in agents_dir.glob('*.yaml'):
                    self.validate_file(config_file)
                    
            # Validate feature flags
            flags_file = self.config_dir / 'feature_flags.yaml'
            if flags_file.exists():
                self.validate_file(flags_file)
                
            # Validate secrets
            secrets_file = self.config_dir / 'secrets.yaml'
            if secrets_file.exists():
                self.validate_file(secrets_file)
                
            # Validate environment config
            env_file = self.config_dir / 'environment.yaml'
            if env_file.exists():
                self.validate_file(env_file)
                
            return True
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e.message}")
            for error in e.errors:
                logger.error(f"  - {error['loc']}: {error['msg']}")
            raise
            
    def get_schema(self, config_type: str) -> Dict[str, Any]:
        """Get JSON schema for a configuration type.
        
        Args:
            config_type: Type of configuration to get schema for
            
        Returns:
            JSON schema for the configuration type
            
        Raises:
            ValidationError: If schema type is unknown
        """
        if config_type in self.schema_cache:
            return self.schema_cache[config_type]
            
        if config_type == 'system':
            schema = SystemConfig.schema()
        elif config_type.startswith('agent'):
            agent_type = config_type.split('_', 1)[1]
            if agent_type not in AGENT_CONFIG_TYPES:
                raise ValidationError(
                    f"Unknown agent type: {agent_type}",
                    [{"loc": ["agent_type"], "msg": f"Unknown agent type: {agent_type}"}]
                )
            schema = AGENT_CONFIG_TYPES[agent_type].schema()
        else:
            raise ValidationError(
                f"Unknown configuration type: {config_type}",
                [{"loc": ["config_type"], "msg": f"Unknown configuration type: {config_type}"}]
            )
            
        self.schema_cache[config_type] = schema
        return schema