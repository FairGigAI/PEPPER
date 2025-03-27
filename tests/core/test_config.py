"""Tests for the configuration system."""

import pytest
import asyncio
from pathlib import Path
import yaml
from core.config import (
    ConfigLoader,
    ConfigurationValidator,
    ConfigManager,
    ConfigUpdater
)

@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def config_loader(config_dir):
    """Create a config loader for testing."""
    return ConfigLoader(config_dir)

@pytest.fixture
def config_validator(config_dir):
    """Create a config validator for testing."""
    return ConfigurationValidator(config_dir)

def test_config_loader_initialization(config_loader):
    """Test config loader initialization."""
    assert config_loader is not None
    assert hasattr(config_loader, 'configs')

def test_config_validator_initialization(config_validator):
    """Test config validator initialization."""
    assert config_validator is not None
    assert hasattr(config_validator, 'checkpoints')

@pytest.mark.asyncio
async def test_config_hot_reloading(config_loader, config_dir):
    """Test configuration hot-reloading."""
    # Create initial config file
    config_file = config_dir / "test_config.yaml"
    initial_config = {
        "test_key": "initial_value",
        "nested": {
            "key": "value"
        }
    }
    config_file.write_text(yaml.dump(initial_config))
    
    # Load initial config
    await config_loader.load_config("test_config")
    assert config_loader.configs["test_config"]["test_key"] == "initial_value"
    
    # Update config file
    updated_config = {
        "test_key": "updated_value",
        "nested": {
            "key": "new_value"
        }
    }
    config_file.write_text(yaml.dump(updated_config))
    
    # Wait for hot reload
    await asyncio.sleep(0.1)  # Give time for file system to update
    
    # Verify config was updated
    assert config_loader.configs["test_config"]["test_key"] == "updated_value"
    assert config_loader.configs["test_config"]["nested"]["key"] == "new_value"

def test_config_snapshot(config_loader):
    """Test configuration snapshot creation and restoration."""
    # Create test config
    test_config = {
        "test_key": "value",
        "nested": {
            "key": "value"
        }
    }
    config_loader.configs["test_config"] = test_config
    
    # Create snapshot
    snapshot = config_loader.create_snapshot("test_config")
    assert snapshot is not None
    assert snapshot["test_key"] == "value"
    
    # Modify config
    config_loader.configs["test_config"]["test_key"] = "modified"
    
    # Restore snapshot
    config_loader.restore_snapshot("test_config", snapshot)
    assert config_loader.configs["test_config"]["test_key"] == "value"

def test_config_validation_checkpoints(config_validator):
    """Test validation checkpoints."""
    # Create test config
    test_config = {
        "test_key": "value",
        "nested": {
            "key": "value"
        }
    }
    
    # Create checkpoint
    checkpoint = config_validator.create_checkpoint("test_config", test_config)
    assert checkpoint is not None
    assert checkpoint["config"]["test_key"] == "value"
    
    # Validate against checkpoint
    assert config_validator.validate_against_checkpoint("test_config", test_config, checkpoint)
    
    # Test invalid config
    invalid_config = {
        "test_key": "invalid",
        "nested": {
            "key": "value"
        }
    }
    assert not config_validator.validate_against_checkpoint("test_config", invalid_config, checkpoint) 