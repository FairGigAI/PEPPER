"""Configuration management for P.E.P.P.E.R."""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pathlib import Path
from loguru import logger

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .loader import ConfigLoader
    from .validator import ConfigValidator
    from .base import BaseAgentConfig, SystemConfig
    from .models import AGENT_CONFIG_TYPES

class Config:
    """Manages all configuration-related operations for P.E.P.P.E.R."""
    
    _instance = None
    
    def __new__(cls, config_dir: Optional[str] = None):
        """Create a singleton instance of the configuration manager.
        
        Args:
            config_dir: Optional directory containing configuration files
            
        Returns:
            Singleton instance of the Config class
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Optional directory containing configuration files
        """
        if not hasattr(self, "initialized"):
            self.config_dir = Path(config_dir) if config_dir else Path("config")
            self.config_loader = ConfigLoader(self.config_dir)
            self.config_validator = ConfigValidator(self.config_dir)
            self.initialized = True
            
    def get_system_config(self) -> Optional[SystemConfig]:
        """Get system configuration.
        
        Returns:
            System configuration if available, None otherwise
        """
        return self.config_loader.get_system_config()
        
    def get_agent_config(self, agent_type: str) -> Optional[BaseAgentConfig]:
        """Get configuration for a specific agent.
        
        Args:
            agent_type: Type of agent to get configuration for
            
        Returns:
            Agent configuration if available, None otherwise
        """
        return self.config_loader.get_agent_config(agent_type)
        
    def get_env_var(self, var_name: str, default: Any = None) -> Any:
        """Get an environment variable.
        
        Args:
            var_name: Name of the environment variable
            default: Default value if variable is not found
            
        Returns:
            Value of the environment variable or default value
        """
        return self.config_loader.get_env_var(var_name, default)
        
    def get_secret(self, secret_name: str) -> str:
        """Get a secret from environment variables.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Value of the secret
            
        Raises:
            ValueError: If secret is not found
        """
        return self.config_loader.get_secret(secret_name)
        
    def get_feature_flag(self, flag_name: str) -> bool:
        """Get a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            Value of the feature flag
        """
        return self.config_loader.get_feature_flag(flag_name)
        
    def is_development(self) -> bool:
        """Check if running in development mode.
        
        Returns:
            True if in development mode, False otherwise
        """
        return self.config_loader.is_development()
        
    def is_production(self) -> bool:
        """Check if running in production mode.
        
        Returns:
            True if in production mode, False otherwise
        """
        return self.config_loader.is_production()
        
    def is_debug(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns:
            True if debug mode is enabled, False otherwise
        """
        return self.config_loader.is_debug()
        
    def get_log_level(self) -> str:
        """Get the configured log level.
        
        Returns:
            Configured log level
        """
        return self.config_loader.get_log_level()
        
    def update_agent_config(self, agent_type: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific agent.
        
        Args:
            agent_type: Type of agent to update configuration for
            config: New configuration values
            
        Returns:
            True if update succeeds, False otherwise
        """
        if agent_type not in AGENT_CONFIG_TYPES:
            logger.error(f"Invalid agent type: {agent_type}")
            return False
            
        try:
            # Validate the new configuration
            agent_config_class = AGENT_CONFIG_TYPES[agent_type]
            agent_config_class(**config)
            
            # Update the configuration
            return self.config_loader.update_agent_config(agent_type, config)
        except Exception as e:
            logger.error(f"Failed to update agent config: {e}")
            return False
        
    def update_system_config(self, config: Dict[str, Any]) -> bool:
        """Update system configuration.
        
        Args:
            config: New system configuration values
            
        Returns:
            True if update succeeds, False otherwise
        """
        try:
            # Validate the new configuration
            SystemConfig(**config)
            
            # Update the configuration
            return self.config_loader.update_system_config(config)
        except Exception as e:
            logger.error(f"Failed to update system config: {e}")
            return False
        
    def update_environment_config(self, config: Dict[str, Any]) -> bool:
        """Update environment configuration.
        
        Args:
            config: New environment configuration values
            
        Returns:
            True if update succeeds, False otherwise
        """
        try:
            # Validate the new configuration
            if not self.config_validator.validate_environment_config(config):
                return False
                
            # Update the configuration
            return self.config_loader.update_environment_config(config)
        except Exception as e:
            logger.error(f"Failed to update environment config: {e}")
            return False
        
    def update_feature_flags(self, flags: Dict[str, bool]) -> bool:
        """Update feature flags.
        
        Args:
            flags: New feature flag values
            
        Returns:
            True if update succeeds, False otherwise
        """
        try:
            return self.config_loader.update_feature_flags(flags)
        except Exception as e:
            logger.error(f"Failed to update feature flags: {e}")
            return False
        
    def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """Update a secret value.
        
        Args:
            secret_name: Name of the secret to update
            secret_value: New value for the secret
            
        Returns:
            True if update succeeds, False otherwise
        """
        try:
            return self.config_loader.update_secret(secret_name, secret_value)
        except Exception as e:
            logger.error(f"Failed to update secret: {e}")
            return False
        
    def backup_configs(self) -> bool:
        """Backup current configurations.
        
        Returns:
            True if backup succeeds, False otherwise
        """
        try:
            return self.config_loader.backup_configs()
        except Exception as e:
            logger.error(f"Failed to backup configs: {e}")
            return False
        
    def restore_configs(self) -> bool:
        """Restore configurations from backup.
        
        Returns:
            True if restore succeeds, False otherwise
        """
        try:
            return self.config_loader.restore_configs()
        except Exception as e:
            logger.error(f"Failed to restore configs: {e}")
            return False
        
    def validate_config(self, config: Dict[str, Any], config_type: str) -> bool:
        """Validate a configuration dictionary.
        
        Args:
            config: Configuration to validate
            config_type: Type of configuration to validate
            
        Returns:
            True if validation succeeds, False otherwise
        """
        return self.config_validator.validate_config(config, config_type)
        
    def get_validation_errors(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """Get validation errors for a configuration.
        
        Args:
            config: Configuration to validate
            config_type: Type of configuration to validate
            
        Returns:
            List of validation error messages
        """
        return self.config_validator.get_validation_errors(config, config_type)
        
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations.
        
        Returns:
            Dictionary containing all configurations
        """
        return self.config_loader.get_all_configs() 