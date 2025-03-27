# Installation Guide

This guide provides detailed instructions for installing PEPPER in various environments.

## Local Installation

### System Requirements

- Python 3.8 or higher
- Git
- PostgreSQL 13 or higher (recommended)
- Redis 6 or higher (for task queue)

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/FairGigAI/pepper.git
   cd pepper
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   
   # Install dependencies
   pip install -e ".[dev]"
   ```

3. **Configure Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your settings
   # Required variables:
   # - CORE_SECRET_KEY
   # - DB_PASSWORD
   # - OPENAI_API_KEY
   # - SLACK_BOT_TOKEN (if using Slack integration)
   ```

4. **Set Up Database**
   ```bash
   # Create database
   createdb pepper_db
   
   # Run migrations
   python -m pepper.db.migrate
   ```

5. **Start the Application**
   ```bash
   # Start the development server
   python main.py
   ```

## Docker Installation

### Prerequisites

- Docker 20.10 or higher
- Docker Compose 2.0 or higher

### Using Docker Compose

1. **Clone and Configure**
   ```bash
   git clone https://github.com/FairGigAI/pepper.git
   cd pepper
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Build and Start**
   ```bash
   docker-compose up -d
   ```

3. **Check Status**
   ```bash
   docker-compose ps
   ```

### Manual Docker Build

1. **Build the Image**
   ```bash
   docker build -t pepper:latest .
   ```

2. **Run the Container**
   ```bash
   docker run -d \
     --name pepper \
     -p 8000:8000 \
     --env-file .env \
     pepper:latest
   ```

## Cloud Deployment

### AWS Deployment

1. **Set Up AWS CLI**
   ```bash
   aws configure
   ```

2. **Deploy Using AWS CDK**
   ```bash
   # Install AWS CDK
   npm install -g aws-cdk
   
   # Deploy infrastructure
   cd infrastructure/aws
   cdk deploy
   ```

### Google Cloud Platform

1. **Set Up gcloud CLI**
   ```bash
   gcloud init
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy pepper \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## Verification

After installation, verify the setup:

1. **Check API Health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Access Web Interface**
   - Open `http://localhost:8000` in your browser
   - Log in with default credentials (if applicable)

3. **Test Agent System**
   ```bash
   python -m pepper.test_agents
   ```

## Troubleshooting

### Common Issues

1. **Database Connection**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Redis Connection**
   - Verify Redis is running
   - Check Redis connection string in `.env`

3. **Port Conflicts**
   - Check if port 8000 is available
   - Modify port in `.env` if needed

### Getting Help

- Check the [Troubleshooting Guide](../user_guides/troubleshooting.md)
- Open an issue on [GitHub](https://github.com/FairGigAI/pepper/issues)
- Join our [Discord Community](https://discord.gg/pepper) 