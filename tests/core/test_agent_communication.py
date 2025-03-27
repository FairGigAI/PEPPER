"""Tests for the secure communication functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_communication import SecureCommunication, Message
from core.config import SystemConfig
from core.exceptions import FatalError

@pytest.fixture
def communication_config() -> Dict[str, Any]:
    """Create a test communication configuration."""
    return {
        "encryption_key": "test-key-123",
        "algorithm": "AES-256-GCM",
        "timeout": 30,
        "max_message_size": 1024 * 1024,  # 1MB
        "retry_attempts": 3,
        "compression_enabled": True
    }

@pytest.fixture
def secure_communication(communication_config: Dict[str, Any]) -> SecureCommunication:
    """Create a test secure communication instance."""
    config = SystemConfig(**communication_config)
    return SecureCommunication(config)

@pytest.mark.asyncio
async def test_communication_initialization(secure_communication: SecureCommunication):
    """Test secure communication initialization."""
    assert secure_communication.config.algorithm == "AES-256-GCM"
    assert secure_communication.config.timeout == 30
    assert secure_communication.config.max_message_size == 1024 * 1024

@pytest.mark.asyncio
async def test_message_encryption(secure_communication: SecureCommunication):
    """Test message encryption and decryption."""
    # Create test message
    message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content="Test message content",
        message_type="test"
    )
    
    # Encrypt message
    encrypted = await secure_communication.encrypt_message(message)
    assert encrypted is not None
    assert encrypted != message.content
    
    # Decrypt message
    decrypted = await secure_communication.decrypt_message(encrypted)
    assert decrypted == message.content

@pytest.mark.asyncio
async def test_message_compression(secure_communication: SecureCommunication):
    """Test message compression."""
    # Create large message
    large_content = "Test " * 1000
    message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content=large_content,
        message_type="test"
    )
    
    # Compress message
    compressed = await secure_communication.compress_message(message)
    assert len(compressed) < len(message.content)
    
    # Decompress message
    decompressed = await secure_communication.decompress_message(compressed)
    assert decompressed == message.content

@pytest.mark.asyncio
async def test_message_validation(secure_communication: SecureCommunication):
    """Test message validation."""
    # Test valid message
    valid_message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content="Test message",
        message_type="test"
    )
    assert await secure_communication.validate_message(valid_message)
    
    # Test message too large
    large_message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content="Test " * (1024 * 1024 + 1),  # Exceeds max size
        message_type="test"
    )
    with pytest.raises(FatalError):
        await secure_communication.validate_message(large_message)

@pytest.mark.asyncio
async def test_message_routing(secure_communication: SecureCommunication):
    """Test message routing functionality."""
    # Create test message
    message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content="Test message",
        message_type="test"
    )
    
    # Route message
    result = await secure_communication.route_message(message)
    assert result["status"] == "success"
    assert result["message_id"] is not None

@pytest.mark.asyncio
async def test_error_handling(secure_communication: SecureCommunication):
    """Test error handling."""
    # Test with invalid encryption key
    secure_communication.config.encryption_key = "invalid-key"
    with pytest.raises(FatalError):
        await secure_communication.encrypt_message(
            Message(
                sender_id="test-sender",
                receiver_id="test-receiver",
                content="Test message",
                message_type="test"
            )
        )
    
    # Test with invalid message format
    with pytest.raises(FatalError):
        await secure_communication.validate_message(
            Message(
                sender_id="",  # Invalid empty sender
                receiver_id="test-receiver",
                content="Test message",
                message_type="test"
            )
        )

@pytest.mark.asyncio
async def test_message_retry(secure_communication: SecureCommunication):
    """Test message retry functionality."""
    # Create test message
    message = Message(
        sender_id="test-sender",
        receiver_id="test-receiver",
        content="Test message",
        message_type="test"
    )
    
    # Simulate failed delivery
    secure_communication.config.retry_attempts = 3
    result = await secure_communication.send_with_retry(message)
    assert result["attempts"] <= 3
    assert result["status"] in ["success", "failed"] 