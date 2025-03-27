"""LLM interface for OpenAI API integration."""

import os
from typing import Optional, Dict, Any
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

class LLMInterface:
    """Interface for interacting with OpenAI's API."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize the LLM interface.
        
        Args:
            model: OpenAI model to use (defaults to GPT-4 or GPT-3.5-turbo)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        load_dotenv()
        
        # Get API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Set model with fallback
        self.model = model or self._get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized LLM interface with model: {self.model}")
        
    def _get_default_model(self) -> str:
        """Get the default model based on availability."""
        try:
            # Try to get GPT-4
            self.client.models.retrieve("gpt-4")
            return "gpt-4"
        except Exception:
            logger.warning("GPT-4 not available, falling back to GPT-3.5-turbo")
            return "gpt-3.5-turbo"
            
    def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response using the OpenAI API.
        
        Args:
            prompt: The user's prompt
            system_message: Optional system message to set context
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            Generated response text
        """
        try:
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
                
            # Add user message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            # Extract and return the response
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
            
    def generate_structured_response(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured response following a specific format.
        
        Args:
            prompt: The user's prompt
            response_format: Dictionary describing the expected response format
            system_message: Optional system message to set context
            
        Returns:
            Structured response as a dictionary
        """
        # Create format description
        format_desc = "\n".join([
            f"- {key}: {desc}"
            for key, desc in response_format.items()
        ])
        
        # Create system message with format requirements
        format_system_message = f"""
        You are a helpful assistant that provides structured responses.
        Your response must follow this format:
        {format_desc}
        
        Provide the response as a JSON object with the specified fields.
        """
        
        # Combine with user's system message if provided
        if system_message:
            format_system_message = f"{system_message}\n\n{format_system_message}"
            
        # Generate response
        response = self.generate_response(
            prompt=prompt,
            system_message=format_system_message
        )
        
        # TODO: Add response validation and parsing
        return response  # For now, return raw response
        
    # TODO: Add Claude integration
    """
    def set_backend(self, backend: str = "openai"):
        \"\"\"Switch between different LLM backends.
        
        Args:
            backend: Backend to use ("openai" or "claude")
        \"\"\"
        if backend == "claude":
            # Initialize Claude client
            pass
        elif backend == "openai":
            # Initialize OpenAI client
            pass
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    """ 