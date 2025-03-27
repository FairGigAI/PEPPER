# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized deployment)
- GitHub account (for integration features)

## Installation Methods

### 1. Using pip (Recommended)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PEPPER
pip install pepper
```

### 2. From Source

```bash
# Clone the repository
git clone https://github.com/FairGigAI/PEPPER.git
cd PEPPER

# Install in development mode
pip install -e .
```

### 3. Using Docker

```bash
# Build the image
docker build -t pepper .

# Run the container
docker run -d --name pepper pepper
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your settings:
   ```env
   # API Keys
   OPENAI_API_KEY=your_key_here
   GITHUB_TOKEN=your_token_here

   # Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=pepper
   DB_USER=user
   DB_PASSWORD=password

   # Other Settings
   LOG_LEVEL=INFO
   DEBUG=False
   ```

## Verification

1. Check installation:
   ```bash
   pepper --version
   ```

2. Run tests:
   ```bash
   pepper test
   ```

3. Start PEPPER:
   ```bash
   pepper start
   ```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check Python version compatibility
   - Verify all dependencies are installed

2. **Configuration Issues**
   - Validate environment variables
   - Check file permissions
   - Verify network connectivity

3. **Docker Issues**
   - Check Docker daemon status
   - Verify port availability
   - Check container logs

### Getting Help

- [Support](Support) - Get help with issues
- [FAQ](FAQ) - Common questions and answers
- [GitHub Issues](https://github.com/FairGigAI/PEPPER/issues) - Report bugs

## Next Steps

- [Getting Started](Getting-Started) - Learn how to use PEPPER
- [Configuration](Configuration) - Advanced configuration options
- [Development Setup](Development-Environment) - Set up development environment 