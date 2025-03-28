# User Guide

This guide provides detailed information on how to use PEPPER effectively for your project management needs.

## Getting Started

### Basic Commands

```bash
# Start PEPPER
pepper start

# Stop PEPPER
pepper stop

# Check status
pepper status

# View help
pepper --help
```

### Agent Management

```bash
# List all agents
pepper agent list

# Check agent status
pepper agent status <agent_id>

# Restart agent
pepper agent restart <agent_id>

# View agent logs
pepper agent logs <agent_id>
```

### Task Management

```bash
# Create new task
pepper task create --title "Document API" --type documentation

# List tasks
pepper task list

# View task details
pepper task view <task_id>

# Update task status
pepper task update <task_id> --status in_progress

# Delete task
pepper task delete <task_id>
```

## Working with Agents

### Documentation Agent

The Documentation Agent handles all documentation-related tasks:

```bash
# Generate documentation
pepper doc generate --type api --output docs/api

# Update documentation
pepper doc update --file docs/api/endpoints.md

# Review documentation
pepper doc review --file docs/api/endpoints.md

# Validate documentation
pepper doc validate --dir docs
```

### GitHub Agent

The GitHub Agent manages version control operations:

```bash
# Create pull request
pepper github pr create --title "Update API docs" --branch feature/docs

# List issues
pepper github issue list

# Create issue
pepper github issue create --title "Documentation needed" --body "Please document the API"

# Merge pull request
pepper github pr merge <pr_number>
```

### Slack Bot Agent

The Slack Bot Agent handles communication:

```bash
# Send message
pepper slack send --channel general --message "Documentation updated"

# Create thread
pepper slack thread create --channel general --message "New feature discussion"

# List channels
pepper slack channel list

# Set up notifications
pepper slack notify --event task_completed --channel updates
```

## Task Workflows

### Creating a Documentation Task

1. Create the task:
```bash
pepper task create \
  --title "Document User Authentication" \
  --type documentation \
  --priority high \
  --description "Create comprehensive documentation for the authentication system"
```

2. Assign to Documentation Agent:
```bash
pepper task assign <task_id> --agent documentation_agent
```

3. Monitor progress:
```bash
pepper task view <task_id>
```

4. Review and approve:
```bash
pepper task approve <task_id>
```

### Managing GitHub Integration

1. Create feature branch:
```bash
pepper github branch create --name feature/auth-docs
```

2. Make changes and commit:
```bash
pepper github commit --message "Add authentication documentation"
```

3. Create pull request:
```bash
pepper github pr create \
  --title "Add Authentication Documentation" \
  --body "Added comprehensive documentation for the authentication system"
```

4. Merge changes:
```bash
pepper github pr merge <pr_number>
```

## Configuration

### Agent Configuration

Edit agent configuration files in `config/agents/`:

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
```

### Task Templates

Create task templates in `config/tasks/`:

```yaml
# config/tasks/documentation_template.yaml
template_id: api_docs
template_type: documentation
config:
  required_fields:
    - endpoint
    - method
    - parameters
  output_format: markdown
```

## Monitoring and Maintenance

### System Health

```bash
# Check system health
pepper system health

# View resource usage
pepper system resources

# Check performance metrics
pepper system metrics
```

### Logs and Debugging

```bash
# View main logs
pepper logs

# View specific agent logs
pepper logs --agent documentation_agent

# View task logs
pepper logs --task <task_id>

# Debug mode
pepper start --debug
```

## Best Practices

### Task Management

1. **Clear Task Descriptions**
   - Use descriptive titles
   - Include detailed requirements
   - Specify dependencies
   - Set realistic deadlines

2. **Task Organization**
   - Use appropriate priorities
   - Group related tasks
   - Maintain task hierarchy
   - Regular task review

3. **Progress Tracking**
   - Regular status updates
   - Document blockers
   - Track time spent
   - Monitor dependencies

### Documentation

1. **Documentation Structure**
   - Clear organization
   - Consistent formatting
   - Regular updates
   - Version control

2. **Content Quality**
   - Accurate information
   - Clear explanations
   - Code examples
   - Visual aids

3. **Review Process**
   - Peer review
   - Technical accuracy
   - Completeness check
   - Regular updates

### Communication

1. **Slack Usage**
   - Appropriate channels
   - Clear messages
   - Thread organization
   - Regular updates

2. **GitHub Integration**
   - Clear commit messages
   - Detailed PR descriptions
   - Issue tracking
   - Branch management

## Troubleshooting

### Common Issues

1. **Agent Not Responding**
   ```bash
   # Check agent status
   pepper agent status <agent_id>
   
   # Restart agent
   pepper agent restart <agent_id>
   
   # View agent logs
   pepper agent logs <agent_id>
   ```

2. **Task Stuck**
   ```bash
   # Check task status
   pepper task view <task_id>
   
   # Check dependencies
   pepper task dependencies <task_id>
   
   # Force task completion
   pepper task complete <task_id> --force
   ```

3. **GitHub Integration Issues**
   ```bash
   # Verify GitHub token
   pepper github verify
   
   # Test GitHub connection
   pepper github test
   
   # Reset GitHub integration
   pepper github reset
   ```

## Next Steps

1. Read the [Core Concepts](core_concepts/index.md) documentation
2. Explore [Advanced Features](advanced_features.md)
3. Join the [Community](community.md)
4. Contribute to PEPPER 