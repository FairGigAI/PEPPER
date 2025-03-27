"""Test suite package."""

import pytest
from pathlib import Path

# Test configuration
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_CONFIG_DIR = TEST_DIR / "config"

# Create test directories if they don't exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_CONFIG_DIR.mkdir(exist_ok=True)

# Test fixtures
@pytest.fixture
def test_data_dir():
    """Provide test data directory."""
    return TEST_DATA_DIR

@pytest.fixture
def test_config_dir():
    """Provide test configuration directory."""
    return TEST_CONFIG_DIR
