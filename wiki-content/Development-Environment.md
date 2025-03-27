# Development Environment Setup

## Overview

This guide will help you set up a professional development environment for contributing to PEPPER. We'll cover all necessary tools, configurations, and best practices.

## Prerequisites

### Required Software
- Python 3.8+
- Git
- Docker
- VS Code (recommended) or PyCharm
- Node.js 16+ (for frontend development)

### Required Accounts
- GitHub account
- Docker Hub account
- FairGigAI developer account

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/FairGigAI/PEPPER.git
cd PEPPER
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Configure Git

```bash
# Set up Git configuration
git config user.name "Your Name"
git config user.email "your.email@fairgigai.com"

# Set up pre-commit hooks
pre-commit install
```

### 4. Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Required variables:
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
DOCKER_USERNAME=your_username
```

## IDE Setup

### VS Code Configuration

1. Install recommended extensions:
   - Python
   - Pylance
   - Docker
   - GitLens
   - Python Test Explorer

2. Configure settings.json:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm Configuration

1. Enable Python linting
2. Configure Black formatter
3. Set up test configurations
4. Enable Git integration

## Development Workflow

### 1. Branch Management

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/your-bugfix-name

# Create release branch
git checkout -b release/v1.0.0
```

### 2. Code Style

- Follow PEP 8 guidelines
- Use Black for formatting
- Use isort for import sorting
- Run pylint for code quality

### 3. Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=pepper tests/
```

### 4. Documentation

```bash
# Generate documentation
mkdocs build

# Serve documentation locally
mkdocs serve

# Check documentation
mkdocs build --strict
```

## Docker Development

### 1. Build Development Image

```bash
docker build -t pepper-dev -f Dockerfile.dev .
```

### 2. Run Development Container

```bash
docker-compose -f docker-compose.dev.yml up
```

### 3. Access Container

```bash
docker exec -it pepper-dev bash
```

## Debugging

### 1. Python Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger
```

### 2. Docker Debugging

```bash
# View logs
docker-compose logs -f

# Access container
docker exec -it container_name bash
```

## Performance Optimization

### 1. Profiling

```bash
# Run cProfile
python -m cProfile -o profile.stats main.py

# View results
python -m pstats profile.stats
```

### 2. Memory Profiling

```bash
# Install memory profiler
pip install memory_profiler

# Profile function
@memory_profiler.profile
def your_function():
    pass
```

## Security Best Practices

1. **API Keys**
   - Never commit API keys
   - Use environment variables
   - Rotate keys regularly

2. **Dependencies**
   - Keep dependencies updated
   - Use security scanning tools
   - Review dependency licenses

3. **Code Security**
   - Follow OWASP guidelines
   - Use security linters
   - Regular security audits

## Troubleshooting

### Common Issues

1. **Docker Issues**
   - Check Docker daemon
   - Verify port availability
   - Check container logs

2. **Python Issues**
   - Verify virtual environment
   - Check Python version
   - Update dependencies

3. **Git Issues**
   - Check Git credentials
   - Verify remote URLs
   - Check branch status

## Support

For development support:
- Email: dev-support@fairgigai.com
- [Internal Documentation](https://docs.fairgigai.com/pepper/dev)
- [Development Team](https://fairgigai.com/team) 