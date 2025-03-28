# Contributing to PEPPER

Thank you for your interest in contributing to PEPPER! This guide will help you get started.

## Development Setup

1. **Prerequisites**
   - Python 3.11+
   - Docker and Docker Compose
   - Git

2. **Local Development**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/pepper.git
   cd pepper

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Set up pre-commit hooks
   pre-commit install
   ```

3. **Running Tests**
   ```bash
   # Run all tests
   pytest

   # Run specific test file
   pytest tests/test_feature.py

   # Run with coverage
   pytest --cov=pepper tests/
   ```

## Code Style

1. **Python Code**
   - Follow PEP 8 guidelines
   - Use type hints
   - Document all public functions and classes
   - Keep functions focused and small

2. **Documentation**
   - Write clear, concise documentation
   - Include code examples
   - Keep documentation up to date
   - Follow the established documentation structure

3. **Git Workflow**
   - Create feature branches from `main`
   - Use descriptive commit messages
   - Keep commits focused and atomic
   - Rebase before merging

## Pull Request Process

1. **Before Submitting**
   - Update documentation
   - Add/update tests
   - Run all tests locally
   - Check code style

2. **PR Description**
   - Describe the changes
   - Link related issues
   - Include screenshots if UI changes
   - List any breaking changes

3. **Review Process**
   - Address all review comments
   - Keep the PR focused
   - Update as needed
   - Request re-review when ready

## Project Structure

1. **Core Components**
   - `core/agents/`: Agent implementations
   - `core/config/`: Configuration management
   - `core/services/`: Core services
   - `core/utils/`: Utility functions

2. **Integrations**
   - `integrations/github/`: GitHub integration
   - `integrations/slack/`: Slack integration

3. **API**
   - `api/routes/`: API endpoints
   - `api/models/`: Data models

4. **Infrastructure**
   - `infrastructure/docker/`: Docker configurations
   - `infrastructure/monitoring/`: Monitoring setup

## Getting Help

1. **Questions**
   - Check existing documentation
   - Search closed issues
   - Ask in discussions
   - Join our community chat

2. **Bugs**
   - Check if already reported
   - Include reproduction steps
   - Add system information
   - Attach relevant logs

3. **Feature Requests**
   - Check roadmap
   - Explain use case
   - Consider scope
   - Be specific

## Release Process

1. **Versioning**
   - Follow semantic versioning
   - Update changelog
   - Tag releases
   - Update documentation

2. **Deployment**
   - Run all tests
   - Check dependencies
   - Update version numbers
   - Create release notes

## Code of Conduct

1. **Guidelines**
   - Be respectful
   - Be inclusive
   - Be professional
   - Help others

2. **Reporting**
   - Report violations
   - Provide details
   - Maintain privacy
   - Follow up

Thank you for contributing to PEPPER! 