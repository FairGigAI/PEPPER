# Getting Started with PEPPER

This section will guide you through setting up and using PEPPER for the first time.

## Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized deployment)
- A GitHub account (for version control and CI/CD)

## Installation Options

1. [Local Installation](installation.md) - Set up PEPPER on your local machine
2. [Docker Installation](installation.md#docker-installation) - Run PEPPER using Docker
3. [Cloud Deployment](installation.md#cloud-deployment) - Deploy PEPPER to cloud platforms

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/FairGigAI/pepper.git
   cd pepper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the development server:
   ```bash
   python main.py
   ```

## Configuration

Learn about:
- [Environment Variables](configuration.md#environment-variables)
- [Agent Configuration](configuration.md#agent-configuration)
- [Database Setup](configuration.md#database-setup)
- [Security Settings](configuration.md#security-settings)

## Next Steps

1. [Core Concepts](../core_concepts/README.md) - Understand PEPPER's fundamental concepts
2. [User Guides](../user_guides/README.md) - Learn how to use PEPPER effectively
3. [Development](../development/README.md) - Start contributing to PEPPER 