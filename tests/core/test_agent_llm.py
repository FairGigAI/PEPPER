"""Tests for the LLM interface functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from core.agent_llm import LLMInterface
from core.config import SystemConfig
from core.exceptions import FatalError

@pytest.fixture
def llm_config() -> Dict[str, Any]:
    """Create a test LLM configuration."""
    return {
        "model": "test-model",
        "temperature": 0.7,
        "max_tokens": 1000,
        "timeout": 30,
        "retry_attempts": 3,
        "api_key": "test-key",
        "api_base": "http://test.api",
        "api_version": "v1"
    }

@pytest.fixture
def llm_interface(llm_config: Dict[str, Any]) -> LLMInterface:
    """Create a test LLM interface instance."""
    config = SystemConfig(**llm_config)
    return LLMInterface(config)

@pytest.mark.asyncio
async def test_llm_initialization(llm_interface: LLMInterface):
    """Test LLM interface initialization."""
    assert llm_interface.config.model == "test-model"
    assert llm_interface.config.temperature == 0.7
    assert llm_interface.config.max_tokens == 1000

@pytest.mark.asyncio
async def test_llm_completion(llm_interface: LLMInterface):
    """Test LLM completion functionality."""
    prompt = "Test prompt"
    response = await llm_interface.get_completion(prompt)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_llm_chat(llm_interface: LLMInterface):
    """Test LLM chat functionality."""
    messages = [
        {"role": "system", "content": "You are a test assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    response = await llm_interface.chat(messages)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_llm_embedding(llm_interface: LLMInterface):
    """Test LLM embedding functionality."""
    text = "Test text for embedding"
    embedding = await llm_interface.get_embedding(text)
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0

@pytest.mark.asyncio
async def test_llm_error_handling(llm_interface: LLMInterface):
    """Test LLM error handling."""
    # Test with invalid API key
    llm_interface.config.api_key = "invalid-key"
    with pytest.raises(FatalError):
        await llm_interface.get_completion("Test prompt")
    
    # Test with invalid model
    llm_interface.config.model = "invalid-model"
    with pytest.raises(FatalError):
        await llm_interface.get_completion("Test prompt")

@pytest.mark.asyncio
async def test_llm_rate_limiting(llm_interface: LLMInterface):
    """Test LLM rate limiting."""
    # Make multiple requests quickly
    prompts = [f"Test prompt {i}" for i in range(5)]
    tasks = [llm_interface.get_completion(prompt) for prompt in prompts]
    
    # Should handle rate limiting gracefully
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(r, str) or isinstance(r, Exception) for r in responses)

@pytest.mark.asyncio
async def test_llm_context_management(llm_interface: LLMInterface):
    """Test LLM context management."""
    # Test with long context
    long_prompt = "Test " * 1000
    response = await llm_interface.get_completion(long_prompt)
    assert response is not None
    
    # Test with context truncation
    very_long_prompt = "Test " * 10000
    response = await llm_interface.get_completion(very_long_prompt)
    assert response is not None 