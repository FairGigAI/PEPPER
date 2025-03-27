# Quick Start Guide

This guide will help you get up and running with PEPPER quickly.

## Prerequisites

- Python 3.8+
- Git
- Docker (optional)

## 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/FairGigAI/pepper.git
cd pepper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
```

## 2. Configure Environment

Edit `.env` with your essential settings:

```env
# Core Settings
CORE_SECRET_KEY=your_secret_key
DEBUG=true

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pepper_db
DB_USER=pepper_user
DB_PASSWORD=your_password

# OpenAI (for AI features)
OPENAI_API_KEY=your_openai_key

# Optional: Slack Integration
SLACK_BOT_TOKEN=your_slack_token
SLACK_DEFAULT_CHANNEL=#pepper-updates
```

## 3. Start the Application

```bash
# Start the development server
python main.py
```

## 4. Basic Usage

### Create a New Project

```python
from pepper.core import ProjectManager

# Initialize project manager
pm = ProjectManager()

# Create a new project
project = pm.create_project(
    name="My First Project",
    description="A test project",
    start_date="2024-03-20"
)
```

### Add Tasks

```python
# Create a task
task = project.add_task(
    title="Setup Development Environment",
    description="Set up the development environment for the project",
    priority="high",
    due_date="2024-03-25"
)
```

### Assign Agents

```python
# Assign an agent to the task
task.assign_agent("documentation_agent")
```

### Monitor Progress

```python
# Get project status
status = project.get_status()
print(f"Project Progress: {status.progress}%")

# Get task status
task_status = task.get_status()
print(f"Task Status: {task_status}")
```

## 5. Next Steps

1. **Explore Core Concepts**
   - Learn about [Agents](../core_concepts/agents.md)
   - Understand [Task Management](../core_concepts/tasks.md)
   - Discover the [Feedback System](../core_concepts/feedback_system.md)

2. **Configure Advanced Features**
   - Set up [Slack Integration](../user_guides/admin_guide.md#slack-integration)
   - Configure [GitHub Integration](../user_guides/admin_guide.md#github-integration)
   - Enable [Automated Testing](../development/testing.md)

3. **Start Contributing**
   - Read the [Contributing Guide](../development/contributing.md)
   - Set up [Development Environment](../development/README.md)
   - Join our [Community](https://discord.gg/pepper)

## Common Tasks

### Creating Documentation

```python
from pepper.agents import DocumentationAgent

# Initialize documentation agent
doc_agent = DocumentationAgent()

# Generate documentation
doc_agent.generate_doc(
    project_id=project.id,
    doc_type="markdown",
    template="project_template"
)
```

### Managing Milestones

```python
# Create a milestone
milestone = project.add_milestone(
    name="Phase 1 Complete",
    description="Complete all Phase 1 tasks",
    due_date="2024-04-01"
)

# Track progress
progress = milestone.get_progress()
print(f"Milestone Progress: {progress}%")
```

### Using the Feedback System

```python
# Submit feedback
project.submit_feedback(
    task_id=task.id,
    rating=5,
    comment="Great progress!",
    category="performance"
)

# Get feedback summary
summary = project.get_feedback_summary()
print(f"Average Rating: {summary.average_rating}")
```

## Getting Help

- Check the [Documentation](../README.md)
- Join our [Discord Community](https://discord.gg/pepper)
- Open an [Issue](https://github.com/FairGigAI/pepper/issues) 