# Installation Guide

This guide will help you set up PEPPER in your environment. Follow these steps to get started.

## Prerequisites

Before installing PEPPER, ensure you have:

1. Python 3.8 or higher
2. Git
3. A virtual environment (recommended)
4. Required system dependencies

### System Dependencies

#### Windows
```bash
# Install Python 3.8 or higher from python.org
# Install Git from git-scm.com
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python git
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and Git
sudo apt install python3 python3-pip python3-venv git
```

## Installation Steps

### 1. Clone the Repository

```bash
# Clone the PEPPER repository
git clone https://github.com/yourusername/pepper.git

# Navigate to the project directory
cd pepper
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install PEPPER and its dependencies
pip install -e .
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# Use your preferred text editor to modify the values
```

Required environment variables:

```env
# Project Configuration
PROJECT_NAME=pepper
CORE_SECRET_KEY=your_secret_key

# GitHub Configuration
GITHUB_ACCESS_TOKEN=your_github_token
GITHUB_REPOSITORY=your_repository

# Slack Configuration
SLACK_BOT_TOKEN=your_slack_token
SLACK_CHANNEL=your_channel

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key

# Database Configuration
DATABASE_URL=your_database_url
```

### 5. Initialize the Database

```bash
# Initialize the database
pepper db init

# Run migrations
pepper db migrate
```

### 6. Start PEPPER

```bash
# Start PEPPER
pepper start
```

## Configuration

### Agent Configuration

Agents are configured using YAML files in the `config/agents` directory. Example configuration:

```yaml
# config/agents/documentation_agent.yaml
agent_id: documentation_agent
agent_type: documentation
config:
  output_dir: docs
  templates_dir: templates
  supported_doc_types:
    - markdown
    - rst
  validation_rules:
    - check_links
    - check_images
```

### Task Configuration

Tasks are configured using YAML files in the `config/tasks` directory. Example configuration:

```yaml
# config/tasks/documentation_task.yaml
task_id: doc_task_1
task_type: documentation
priority: high
dependencies: []
config:
  template: api_docs
  output_format: markdown
  validation_level: strict
```

## Verification

### 1. Check Installation

```bash
# Check PEPPER version
pepper --version

# Check agent status
pepper agent status

# Check system health
pepper system health
```

### 2. Run Tests

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=pepper tests/
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check database URL in `.env`
   - Ensure database is running
   - Verify credentials

2. **Agent Initialization Failure**
   - Check agent configuration files
   - Verify required dependencies
   - Check log files

3. **Environment Variable Issues**
   - Verify `.env` file exists
   - Check variable names
   - Ensure proper formatting

### Logs

Logs are stored in the `logs` directory:

```bash
# View main log
tail -f logs/pepper.log

# View agent logs
tail -f logs/agents/*.log
```

## Next Steps

After installation:

1. Read the [Core Concepts](core_concepts/index.md) documentation
2. Configure your agents
3. Create your first tasks
4. Monitor system performance

For more information, see the [User Guide](user_guide.md). 