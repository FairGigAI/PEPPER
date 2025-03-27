"""Integration tests for system security."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_orchestrator import AgentOrchestrator
from core.agent_communication import SecureCommunication
from core.exceptions import FatalError, SecurityError

@pytest.fixture
async def security_orchestrator(tmp_path):
    """Create an orchestrator for security testing."""
    orchestrator = AgentOrchestrator()
    
    # Configure for security testing
    orchestrator.config.security = {
        "encryption_enabled": True,
        "auth_required": True,
        "max_login_attempts": 3,
        "session_timeout": 300,
        "allowed_origins": ["http://localhost:3000"]
    }
    
    return orchestrator

@pytest.mark.asyncio
async def test_authentication(security_orchestrator: AgentOrchestrator):
    """Test authentication mechanisms."""
    # Test valid authentication
    valid_credentials = {
        "username": "test_user",
        "password": "test_password",
        "api_key": "valid_api_key"
    }
    
    auth_result = await security_orchestrator.authenticate(valid_credentials)
    assert auth_result["status"] == "success"
    assert "token" in auth_result
    
    # Test invalid authentication
    invalid_credentials = {
        "username": "test_user",
        "password": "wrong_password",
        "api_key": "invalid_api_key"
    }
    
    with pytest.raises(SecurityError):
        await security_orchestrator.authenticate(invalid_credentials)

@pytest.mark.asyncio
async def test_authorization(security_orchestrator: AgentOrchestrator):
    """Test authorization mechanisms."""
    # Create test user with specific permissions
    user = {
        "user_id": "test_user",
        "permissions": ["read", "write"],
        "roles": ["developer"]
    }
    
    # Test authorized access
    authorized_task = {
        "task_id": "test-001",
        "task_type": "test.authorized",
        "description": "Authorized task",
        "metadata": {
            "required_permission": "read"
        }
    }
    
    result = await security_orchestrator.authorize_task(user, authorized_task)
    assert result["status"] == "authorized"
    
    # Test unauthorized access
    unauthorized_task = {
        "task_id": "test-002",
        "task_type": "test.unauthorized",
        "description": "Unauthorized task",
        "metadata": {
            "required_permission": "admin"
        }
    }
    
    with pytest.raises(SecurityError):
        await security_orchestrator.authorize_task(user, unauthorized_task)

@pytest.mark.asyncio
async def test_encryption(security_orchestrator: AgentOrchestrator):
    """Test data encryption."""
    # Create sensitive data
    sensitive_data = {
        "api_key": "secret_key_123",
        "user_credentials": {
            "username": "test_user",
            "password": "test_password"
        }
    }
    
    # Test encryption
    encrypted_data = await security_orchestrator.encrypt_data(sensitive_data)
    assert encrypted_data != sensitive_data
    assert "encrypted" in encrypted_data
    
    # Test decryption
    decrypted_data = await security_orchestrator.decrypt_data(encrypted_data)
    assert decrypted_data == sensitive_data

@pytest.mark.asyncio
async def test_input_validation(security_orchestrator: AgentOrchestrator):
    """Test input validation and sanitization."""
    # Test SQL injection attempt
    malicious_input = {
        "task_id": "test-003",
        "task_type": "test.sql_injection",
        "description": "'; DROP TABLE users; --",
        "metadata": {
            "query": "SELECT * FROM users WHERE id = '1' OR '1'='1'"
        }
    }
    
    with pytest.raises(SecurityError):
        await security_orchestrator.validate_input(malicious_input)
    
    # Test XSS attempt
    xss_input = {
        "task_id": "test-004",
        "task_type": "test.xss",
        "description": "<script>alert('xss')</script>",
        "metadata": {
            "content": "<img src='x' onerror='alert(1)'>"
        }
    }
    
    with pytest.raises(SecurityError):
        await security_orchestrator.validate_input(xss_input)

@pytest.mark.asyncio
async def test_rate_limiting(security_orchestrator: AgentOrchestrator):
    """Test rate limiting mechanisms."""
    # Create multiple rapid requests
    requests = []
    for i in range(10):
        request = {
            "task_id": f"test-{i+5}",
            "task_type": "test.rate_limit",
            "description": f"Rate limit test {i}",
            "metadata": {
                "client_ip": "127.0.0.1"
            }
        }
        requests.append(request)
    
    # Execute requests
    results = await asyncio.gather(
        *[security_orchestrator.process_request(request) for request in requests],
        return_exceptions=True
    )
    
    # Verify rate limiting
    rate_limited = sum(1 for r in results if isinstance(r, dict) and r["status"] == "rate_limited")
    assert rate_limited > 0

@pytest.mark.asyncio
async def test_session_management(security_orchestrator: AgentOrchestrator):
    """Test session management and timeout."""
    # Create session
    session = await security_orchestrator.create_session({
        "user_id": "test_user",
        "ip_address": "127.0.0.1"
    })
    
    # Verify session creation
    assert session["status"] == "active"
    assert "session_id" in session
    
    # Test session timeout
    await asyncio.sleep(301)  # Wait for session timeout
    
    # Verify session expiration
    session_status = await security_orchestrator.get_session_status(session["session_id"])
    assert session_status["status"] == "expired" 