"""Configuration loader for P.E.P.P.E.R."""

import os
import json
import yaml
import shutil
from typing import Dict, Any, Optional, Union, Type, TypeVar, List
from pathlib import Path
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

# Type checking imports to avoid circular dependencies
from .base import BaseAgentConfig, SystemConfig
from .validator import ConfigValidator
from .models import AGENT_CONFIG_TYPES

T = TypeVar('T')

class ConfigFileHandler(FileSystemEventHandler):
    """Handler for config file changes."""
    
    def __init__(self, loader: 'ConfigLoader'):
        """Initialize the file handler.
        
        Args:
            loader: ConfigLoader instance to notify of changes
        """
        self.loader = loader
        
    def on_modified(self, event):
        """Handle file modification events.
        
        Args:
            event: File system event
        """
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"Config file changed: {event.src_path}")
            self.loader.reload_config()

class ConfigLoader:
    """Loads and manages configuration for P.E.P.P.E.R."""
    
    def __init__(
        self,
        config_dir: Optional[Union[str, Path]] = None,
        env_file: Optional[Union[str, Path]] = None,
        watch_changes: bool = True
    ):
        """Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
            env_file: Path to environment file
            watch_changes: Whether to watch for config file changes
        """
        self.config_dir = Path(config_dir or os.getenv('CONFIG_DIR', 'config'))
        self.env_file = Path(env_file or os.getenv('ENV_FILE', '.env'))
        self.watch_changes = watch_changes
        
        self.config: Dict[str, Any] = {}
        self.system_config: Optional[SystemConfig] = None
        self.agent_configs: Dict[str, BaseAgentConfig] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.secrets: Dict[str, str] = {}
        
        self.validator = ConfigValidator(self.config_dir)
        self.observer = None
        
        self.load_config()
        if watch_changes:
            self.start_watching()
            
    def load_config(self) -> None:
        """Load all configuration files."""
        try:
            # Load environment variables
            self._load_env()
            
            # Load system config
            self._load_system_config()
            
            # Load agent configs
            self._load_agent_configs()
            
            # Load feature flags
            self._load_feature_flags()
            
            # Load secrets
            self._load_secrets()
            
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
            
    def _load_env(self) -> None:
        """Load environment variables."""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                        
    def _load_system_config(self) -> None:
        """Load system configuration."""
        system_config_path = self.config_dir / 'system.yaml'
        if system_config_path.exists():
            with open(system_config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                self.system_config = SystemConfig(**config_data)
                
    def _load_agent_configs(self) -> None:
        """Load agent configurations."""
        agents_dir = self.config_dir / 'agents'
        if agents_dir.exists():
            for config_file in agents_dir.glob('*.yaml'):
                try:
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                        agent_type = config_data.get('type')
                        if agent_type in AGENT_CONFIG_TYPES:
                            agent_config_class = AGENT_CONFIG_TYPES[agent_type]
                            agent_config = agent_config_class(**config_data)
                            self.agent_configs[agent_config.agent_id] = agent_config
                        else:
                            logger.warning(f"Unknown agent type in {config_file}: {agent_type}")
                except Exception as e:
                    logger.error(f"Failed to load agent config {config_file}: {e}")
                    
    def _load_feature_flags(self) -> None:
        """Load feature flags."""
        flags_file = self.config_dir / 'feature_flags.yaml'
        if flags_file.exists():
            with open(flags_file, 'r') as f:
                self.feature_flags = yaml.safe_load(f) or {}
                
    def _load_secrets(self) -> None:
        """Load secrets."""
        secrets_file = self.config_dir / 'secrets.yaml'
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                self.secrets = yaml.safe_load(f) or {}
                    
    def get_agent_config(self, agent_id: str) -> Optional[BaseAgentConfig]:
        """Get configuration for a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent configuration if found, None otherwise
        """
        return self.agent_configs.get(agent_id)
        
    def get_system_config(self) -> Optional[SystemConfig]:
        """Get system configuration.
        
        Returns:
            System configuration if loaded, None otherwise
        """
        return self.system_config
        
    def get_env_var(self, var_name: str, default: Any = None) -> Any:
        """Get an environment variable.
        
        Args:
            var_name: Name of the environment variable
            default: Default value if variable is not found
            
        Returns:
            Value of the environment variable or default value
        """
        return os.getenv(var_name, default)
        
    def get_secret(self, secret_name: str) -> str:
        """Get a secret value.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Value of the secret
            
        Raises:
            ValueError: If secret is not found
        """
        if secret_name not in self.secrets:
            raise ValueError(f"Secret not found: {secret_name}")
        return self.secrets[secret_name]
        
    def get_feature_flag(self, flag_name: str) -> bool:
        """Get a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            Value of the feature flag
        """
        return self.feature_flags.get(flag_name, False)
        
    def is_development(self) -> bool:
        """Check if running in development mode.
        
        Returns:
            True if in development mode, False otherwise
        """
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'
        
    def is_production(self) -> bool:
        """Check if running in production mode.
        
        Returns:
            True if in production mode, False otherwise
        """
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
        
    def is_debug(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns:
            True if debug mode is enabled, False otherwise
        """
        return os.getenv('DEBUG', 'false').lower() == 'true'
        
    def get_log_level(self) -> str:
        """Get the configured log level.
        
        Returns:
            Configured log level
        """
        return os.getenv('LOG_LEVEL', 'INFO')
        
    def update_agent_config(self, agent_type: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific agent.
        
        Args:
            agent_type: Type of agent to update configuration for
            config: New configuration values
            
        Returns:
            True if update succeeds, False otherwise
        """
        try:
            if agent_type not in AGENT_CONFIG_TYPES:
                logger.error(f"Invalid agent type: {agent_type}")
                return False
                
            agent_config_class = AGENT_CONFIG_TYPES[agent_type]
            agent_config = agent_config_class(**config)
            
            # Save to file
            config_file = self.config_dir / 'agents' / f"{agent_type}.yaml"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            # Update in memory
            self.agent_configs[agent_config.agent_id] = agent_config
            return True
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
            system_config = SystemConfig(**config)
            
            # Save to file
            config_file = self.config_dir / 'system.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            # Update in memory
            self.system_config = system_config
            return True
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
            # Save to file
            config_file = self.config_dir / 'environment.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
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
            # Save to file
            config_file = self.config_dir / 'feature_flags.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(flags, f, default_flow_style=False)
                
            # Update in memory
            self.feature_flags = flags
            return True
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
            # Save to file
            config_file = self.config_dir / 'secrets.yaml'
            self.secrets[secret_name] = secret_value
            with open(config_file, 'w') as f:
                yaml.dump(self.secrets, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to update secret: {e}")
            return False
            
    def backup_configs(self) -> bool:
        """Backup current configurations.
        
        Returns:
            True if backup succeeds, False otherwise
        """
        try:
            backup_dir = self.config_dir / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all config files
            for file in self.config_dir.glob('*.yaml'):
                shutil.copy2(file, backup_dir)
                
            # Copy agent configs
            agents_dir = self.config_dir / 'agents'
            if agents_dir.exists():
                backup_agents_dir = backup_dir / 'agents'
                backup_agents_dir.mkdir(exist_ok=True)
                for file in agents_dir.glob('*.yaml'):
                    shutil.copy2(file, backup_agents_dir)
                    
            return True
        except Exception as e:
            logger.error(f"Failed to backup configs: {e}")
            return False
            
    def restore_configs(self) -> bool:
        """Restore configurations from backup.
        
        Returns:
            True if restore succeeds, False otherwise
        """
        try:
            backup_dir = self.config_dir / 'backups'
            if not backup_dir.exists():
                logger.error("No backup directory found")
                return False
                
            # Get latest backup
            backups = sorted(backup_dir.iterdir(), reverse=True)
            if not backups:
                logger.error("No backups found")
                return False
                
            latest_backup = backups[0]
            
            # Restore all config files
            for file in latest_backup.glob('*.yaml'):
                shutil.copy2(file, self.config_dir)
                
            # Restore agent configs
            backup_agents_dir = latest_backup / 'agents'
            if backup_agents_dir.exists():
                agents_dir = self.config_dir / 'agents'
                agents_dir.mkdir(exist_ok=True)
                for file in backup_agents_dir.glob('*.yaml'):
                    shutil.copy2(file, agents_dir)
                    
            # Reload configurations
            self.load_config()
            return True
        except Exception as e:
            logger.error(f"Failed to restore configs: {e}")
            return False
        
    def reload_config(self) -> None:
        """Reload all configuration files."""
        logger.info("Reloading configuration...")
        self.load_config()
        
    def start_watching(self) -> None:
        """Start watching for configuration file changes."""
        self.observer = Observer()
        self.observer.schedule(
            ConfigFileHandler(self),
            str(self.config_dir),
            recursive=True
        )
        self.observer.start()
        logger.info("Started watching for config changes")
        
    def stop_watching(self) -> None:
        """Stop watching for configuration file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching for config changes")
            
    def __del__(self):
        """Cleanup when the loader is destroyed."""
        self.stop_watching()
        
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations.
        
        Returns:
            Dictionary containing all configurations
        """
        return {
            "system": self.system_config.dict() if self.system_config else None,
            "agents": {
                agent_id: config.dict()
                for agent_id, config in self.agent_configs.items()
            },
            "feature_flags": self.feature_flags,
            "environment": {
                "development": self.is_development(),
                "production": self.is_production(),
                "debug": self.is_debug(),
                "log_level": self.get_log_level()
            }
        } 