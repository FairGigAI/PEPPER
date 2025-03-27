# PEPPER LLM Interface

This module provides an interface for interacting with language models in PEPPER.

## Features

- OpenAI integration
- Code analysis
- Improvement suggestions
- Code explanation
- Customizable model parameters

## Usage

```python
from core.llm_interface import LLMInterface

# Initialize the interface
llm = LLMInterface()

# Generate a response
response = await llm.generate_response(
    prompt="What is PEPPER?",
    system_message="You are a helpful assistant."
)

# Analyze code
analysis = await llm.analyze_code(
    code="def hello(): print('Hello, World!')",
    context="Simple greeting function"
)

# Get improvement suggestions
suggestions = await llm.suggest_improvements(
    code="def add(a,b): return a+b",
    analysis=analysis
)

# Explain code
explanation = await llm.explain_code(
    code="def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)",
    level="intermediate"
)
```

## Configuration

The LLM interface can be configured using environment variables:

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

## Future Enhancements

1. Support for additional LLM providers
2. Caching of responses
3. Rate limiting
4. Cost tracking
5. Response validation 