# P.E.P.P.E.R. Configuration System

This directory contains all configuration files for the P.E.P.P.E.R. system. The configuration system is designed to be flexible, type-safe, and version-controlled.

## Directory Structure

```
config/
├── project_config.yaml      # Main project configuration
└── agents/                 # Agent-specific configurations
    ├── frontend_agent.yaml
    ├── backend_agent.yaml
    ├── qa_agent.yaml
    └── pm_agent.yaml
```

## Configuration Files

### project_config.yaml
The main project configuration file that contains:
- System-wide settings
- Task definitions and dependencies
- LLM configuration
- Monitoring settings
- Default agent configurations

### Agent Configurations
Each agent has its own configuration file in the `agents/` directory that contains:
- Agent-specific capabilities
- Retry strategies
- Framework support
- Custom metadata

## Configuration Validation

The configuration system uses Pydantic models for validation:
- All configurations must match their defined schemas
- Required fields are enforced
- Type checking is performed
- Default values are provided where appropriate

## Version Control

Configuration files are versioned using semantic versioning:
- Major version: Breaking changes
- Minor version: New features
- Patch version: Bug fixes

## Configuration Loading

The `ConfigLoader` class handles:
- Loading and merging configurations
- Validation of all settings
- Fallback to default values
- Version compatibility checks

## Example Usage

```python
from core.config_models import ConfigLoader

# Initialize the config loader
config_loader = ConfigLoader()

# Get agent configuration
agent_config = config_loader.get_agent_config("frontend_agent")
```

## Configuration Schema

### Base Agent Configuration
```yaml
type: str                    # Agent type
capabilities: List[str]      # Agent capabilities
retry: RetryConfig          # Retry settings
output_dir: Optional[str]    # Output directory
supported_frameworks: List[str]  # Supported frameworks
metadata: Dict[str, Any]    # Custom metadata
```

### Retry Configuration
```yaml
retries: int                # Number of retry attempts
delay: float                # Initial delay in seconds
max_delay: float           # Maximum delay in seconds
backoff_strategy: str      # Backoff strategy (fixed/linear/exponential)
```

## Best Practices

1. **Configuration Updates**
   - Always update the version number when making changes
   - Document breaking changes in the changelog
   - Test configuration changes before deployment

2. **Agent Configurations**
   - Keep agent-specific settings in their respective files
   - Use the project config for shared settings
   - Document any custom metadata fields

3. **Validation**
   - Add new validation rules in `config_models.py`
   - Test validation with edge cases
   - Provide clear error messages

4. **Security**
   - Never commit sensitive data in config files
   - Use environment variables for secrets
   - Validate all user inputs

## Troubleshooting

Common issues and solutions:

1. **Configuration Loading Errors**
   - Check file permissions
   - Verify YAML syntax
   - Ensure all required fields are present

2. **Validation Errors**
   - Review the error message for specific field issues
   - Check type compatibility
   - Verify enum values are correct

3. **Version Compatibility**
   - Check version numbers match
   - Review changelog for breaking changes
   - Update configuration files as needed

## Future Enhancements

Planned improvements:
- [ ] Configuration hot-reloading
- [ ] Configuration encryption
- [ ] Remote configuration support
- [ ] Configuration backup and restore
- [ ] Configuration migration tools 