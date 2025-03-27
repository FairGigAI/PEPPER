# Configuration Guide

## Overview

PEPPER uses a combination of environment variables and configuration files to manage settings. This guide covers all configuration options and their usage.

## Configuration Files

### 1. Environment Variables (.env)

The `.env` file contains sensitive information and environment-specific settings:

```env
# API Keys
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
SLACK_TOKEN=your_token_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pepper
DB_USER=user
DB_PASSWORD=password

# Logging
LOG_LEVEL=INFO
LOG_FILE=pepper.log

# Application Settings
DEBUG=False
ENVIRONMENT=production
```

### 2. Project Configuration (pepper.yaml)

The `pepper.yaml` file defines project-specific settings:

```yaml
project:
  name: my-project
  description: Project description
  version: 0.1.0

agents:
  orchestrator:
    enabled: true
    max_tasks: 10
    timeout: 300

  documentation:
    enabled: true
    format: markdown
    auto_update: true

  development:
    enabled: true
    language: python
    framework: fastapi

tasks:
  max_concurrent: 5
  timeout: 3600
  retry_attempts: 3

monitoring:
  enabled: true
  metrics_interval: 60
  alert_threshold: 90
```

## Agent Configuration

### Project Orchestrator AI (POA)

```yaml
orchestrator:
  enabled: true
  max_tasks: 10
  timeout: 300
  validation:
    enabled: true
    strict_mode: true
    auto_correct: false
```

### Documentation Agent

```yaml
documentation:
  enabled: true
  format: markdown
  auto_update: true
  templates:
    enabled: true
    custom_path: ./templates
```

### Development Agent

```yaml
development:
  enabled: true
  language: python
  framework: fastapi
  testing:
    enabled: true
    coverage_threshold: 80
```

## Task Management

### Task Configuration

```yaml
tasks:
  max_concurrent: 5
  timeout: 3600
  retry_attempts: 3
  priority_levels:
    - critical
    - high
    - medium
    - low
```

### Workflow Settings

```yaml
workflow:
  stages:
    - planning
    - development
    - testing
    - review
    - deployment
  transitions:
    auto_approve: false
    require_review: true
```

## Monitoring and Logging

### Logging Configuration

```yaml
logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  handlers:
    - file
    - console
    - syslog
```

### Monitoring Settings

```yaml
monitoring:
  enabled: true
  metrics_interval: 60
  alert_threshold: 90
  notifications:
    email: true
    slack: true
```

## Security Settings

### Authentication

```yaml
security:
  auth:
    enabled: true
    method: oauth2
    providers:
      - github
      - google
```

### Authorization

```yaml
security:
  roles:
    admin:
      permissions: ["*"]
    developer:
      permissions: ["read", "write", "execute"]
    viewer:
      permissions: ["read"]
```

## Best Practices

1. **Environment Variables**
   - Keep sensitive data in `.env`
   - Use different files for different environments
   - Never commit `.env` to version control

2. **Configuration Files**
   - Use YAML for complex configurations
   - Keep configurations modular
   - Document all options

3. **Security**
   - Rotate API keys regularly
   - Use environment-specific credentials
   - Implement proper access controls

## Troubleshooting

### Common Issues

1. **Configuration Loading**
   - Check file permissions
   - Verify YAML syntax
   - Validate environment variables

2. **Agent Configuration**
   - Check agent dependencies
   - Verify API keys
   - Review timeout settings

3. **Task Management**
   - Check concurrent task limits
   - Review timeout values
   - Verify priority settings

## Next Steps

- [Getting Started](Getting-Started) - Learn how to use PEPPER
- [Development Environment](Development-Environment) - Set up development environment
- [API Documentation](API-Documentation) - Learn about the API 