# Configuration Guide

This guide explains how to configure PEPPER for your specific needs.

## Environment Variables

PEPPER uses environment variables for configuration. The main configuration file is `.env`, which should be created from `.env.example`.

### Core Configuration

```env
# Project Settings
PROJECT_NAME=pepper
ENVIRONMENT=development  # development, staging, production
DEBUG=true
LOG_LEVEL=INFO

# Security
CORE_SECRET_KEY=your_core_secret_key
CORE_API_KEY=your_core_api_key
CORE_ENCRYPTION_KEY=your_encryption_key
CORE_JWT_SECRET=your_jwt_secret
```

### Database Configuration

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pepper_db
DB_USER=pepper_user
DB_PASSWORD=your_db_password
DB_SSL_MODE=prefer

# Redis (for task queue)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
```

### API Configuration

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# GitHub
GITHUB_ACCESS_TOKEN=your_github_access_token
GITHUB_APP_ID=your_github_app_id
GITHUB_APP_PRIVATE_KEY=your_github_app_private_key

# Slack
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_DEFAULT_CHANNEL=#agent-updates
```

## Agent Configuration

Agents are configured through YAML files in the `config/agents/` directory.

### Documentation Agent

```yaml
# config/agents/documentation_agent.yaml
agent_id: documentation_agent
type: documentation
config:
  output_dir: docs
  templates_dir: templates
  supported_doc_types:
    - markdown
    - html
    - pdf
  validation_rules:
    required_sections:
      - Overview
      - Usage
      - Configuration
    min_content_length: 100
    require_code_examples: true
```

### GitHub Agent

```yaml
# config/agents/github_agent.yaml
agent_id: github_agent
type: github
config:
  default_branch: main
  auto_merge: false
  require_review: true
  commit_message_template: |
    {type}({scope}): {description}
    
    {body}
    
    {footer}
```

### Slack Bot Agent

```yaml
# config/agents/slack_bot_agent.yaml
agent_id: slack_bot_agent
type: slack
config:
  default_channel: #agent-updates
  enable_threads: false
  notification_rules:
    task_completion: true
    milestone_updates: true
    error_alerts: true
```

## Database Setup

### PostgreSQL

1. **Create Database**
   ```sql
   CREATE DATABASE pepper_db;
   CREATE USER pepper_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE pepper_db TO pepper_user;
   ```

2. **Run Migrations**
   ```bash
   python -m pepper.db.migrate
   ```

### Redis

1. **Install Redis**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

2. **Configure Redis**
   ```bash
   # Edit redis.conf
   sudo nano /etc/redis/redis.conf
   
   # Set password
   requirepass your_redis_password
   ```

## Security Settings

### SSL/TLS Configuration

```env
# SSL Settings
SECURITY_SSL_ENABLED=true
SECURITY_SSL_CERT_PATH=/path/to/cert.pem
SECURITY_SSL_KEY_PATH=/path/to/key.pem
```

### Rate Limiting

```env
# Rate Limiting
SECURITY_RATE_LIMIT_REQUESTS=100
SECURITY_RATE_LIMIT_PERIOD=60
```

### CORS Settings

```env
# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Feature Flags

Enable or disable features using environment variables:

```env
# Feature Flags
FEATURE_ENABLE_SLACK_THREADS=false
FEATURE_ENABLE_ASYNC_TASKS=true
FEATURE_ENABLE_METRICS_COLLECTION=true
FEATURE_ENABLE_ERROR_REPORTING=true
FEATURE_ENABLE_EMAIL_SUMMARY=true
FEATURE_ENABLE_AUTO_DEPLOYMENT=false
FEATURE_ENABLE_AUTO_TESTING=true
```

## Monitoring Configuration

### Prometheus

```env
# Prometheus
PROMETHEUS_MULTIPROC_DIR=/tmp
```

### Grafana

```env
# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### Alert Manager

```env
# Alert Manager
ALERTMANAGER_SMTP_HOST=smtp.gmail.com
ALERTMANAGER_SMTP_PORT=587
ALERTMANAGER_SMTP_USERNAME=your_email@gmail.com
ALERTMANAGER_SMTP_PASSWORD=your_app_specific_password
```

## Validation

To validate your configuration:

```bash
# Check environment variables
python -m pepper.config.validate_env

# Check agent configurations
python -m pepper.config.validate_agents

# Check database connection
python -m pepper.db.check_connection
```

## Troubleshooting

### Common Issues

1. **Database Connection**
   - Verify PostgreSQL is running
   - Check credentials in `.env`
   - Ensure database exists

2. **Redis Connection**
   - Verify Redis is running
   - Check Redis connection string

3. **API Keys**
   - Verify all required API keys are set
   - Check key permissions

### Getting Help

- Check the [Troubleshooting Guide](../user_guides/troubleshooting.md)
- Open an issue on [GitHub](https://github.com/FairGigAI/pepper/issues)
- Join our [Discord Community](https://discord.gg/pepper) 