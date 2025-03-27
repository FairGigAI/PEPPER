"""LLM interface for P.E.P.P.E.R."""

import os
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from openai import AsyncOpenAI
from loguru import logger

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import ConfigLoader, SystemConfig

class LLMInterface:
    """Interface for interacting with language models."""
    
    def __init__(self, config_loader: Optional['ConfigLoader'] = None):
        """Initialize the LLM interface.
        
        Args:
            config_loader: Optional ConfigLoader instance for configuration
        """
        self.config_loader = config_loader
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            # Get API key from config or environment
            api_key = None
            if self.config_loader:
                system_config = self.config_loader.get_system_config()
                if system_config:
                    api_key = system_config.openai_api_key
                    
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
                
            if not api_key:
                raise ValueError("OpenAI API key not found")
                
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("LLM interface initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM interface: {e}")
            raise
            
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: str = "gpt-4"
    ) -> str:
        """Generate a response from the language model.
        
        Args:
            prompt: The input prompt
            system_message: Optional system message to set context
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            model: Model to use for generation
            
        Returns:
            Generated response text
        """
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
            
    async def analyze_code(
        self,
        code: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze code using the language model.
        
        Args:
            code: Code to analyze
            context: Optional context about the code
            
        Returns:
            Analysis results
        """
        try:
            prompt = f"Analyze the following code:\n\n{code}"
            if context:
                prompt = f"Context: {context}\n\n{prompt}"
                
            response = await self.generate_response(
                prompt=prompt,
                system_message="You are a code analysis expert. Analyze the provided code and return a structured analysis.",
                temperature=0.3
            )
            
            # TODO: Parse response into structured format
            return {"analysis": response}
            
        except Exception as e:
            logger.error(f"Failed to analyze code: {e}")
            raise
            
    async def suggest_improvements(
        self,
        code: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get improvement suggestions for code.
        
        Args:
            code: Code to improve
            analysis: Optional previous analysis
            
        Returns:
            List of improvement suggestions
        """
        try:
            prompt = f"Suggest improvements for the following code:\n\n{code}"
            if analysis:
                prompt = f"Previous analysis: {analysis}\n\n{prompt}"
                
            response = await self.generate_response(
                prompt=prompt,
                system_message="You are a code improvement expert. Provide specific, actionable suggestions for improving the code.",
                temperature=0.5
            )
            
            # TODO: Parse response into structured format
            return [suggestion.strip() for suggestion in response.split("\n") if suggestion.strip()]
            
        except Exception as e:
            logger.error(f"Failed to generate improvement suggestions: {e}")
            raise
            
    async def explain_code(
        self,
        code: str,
        level: str = "intermediate"
    ) -> str:
        """Generate an explanation of code.
        
        Args:
            code: Code to explain
            level: Explanation level (beginner/intermediate/advanced)
            
        Returns:
            Code explanation
        """
        try:
            prompt = f"Explain the following code at a {level} level:\n\n{code}"
            
            response = await self.generate_response(
                prompt=prompt,
                system_message=f"You are a code explanation expert. Explain the code at a {level} level.",
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate code explanation: {e}")
            raise 