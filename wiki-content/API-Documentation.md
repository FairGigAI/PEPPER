# API Documentation

## Overview

PEPPER provides a comprehensive API for interacting with its AI agents and services. This documentation covers all available endpoints, authentication, and usage examples.

## Authentication

All API requests require authentication using an API key:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Base URL

```
WIP
```

## Endpoints

### Project Management

#### Create Project
```http
POST /projects
Content-Type: application/json

{
    "name": "string",
    "description": "string",
    "settings": {
        "language": "string",
        "framework": "string"
    }
}
```

#### Get Project
```http
GET /projects/{project_id}
```

#### Update Project
```http
PUT /projects/{project_id}
Content-Type: application/json

{
    "name": "string",
    "description": "string",
    "settings": {
        "language": "string",
        "framework": "string"
    }
}
```

### Task Management

#### Create Task
```http
POST /projects/{project_id}/tasks
Content-Type: application/json

{
    "title": "string",
    "description": "string",
    "priority": "high|medium|low",
    "assignee": "string"
}
```

#### Get Task
```http
GET /projects/{project_id}/tasks/{task_id}
```

#### Update Task Status
```http
PUT /projects/{project_id}/tasks/{task_id}/status
Content-Type: application/json

{
    "status": "in_progress|completed|blocked"
}
```

### Agent Interactions

#### Get Agent Status
```http
GET /agents/{agent_id}/status
```

#### Send Message to Agent
```http
POST /agents/{agent_id}/messages
Content-Type: application/json

{
    "message": "string",
    "context": {
        "project_id": "string",
        "task_id": "string"
    }
}
```

## Rate Limiting

- 100 requests per minute per API key
- 1000 requests per hour per API key

## Error Handling

All errors follow this format:

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    }
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## SDK Examples

### Python
```python
from pepper import PepperClient

client = PepperClient(api_key="YOUR_API_KEY")

# Create a project
project = client.create_project(
    name="My Project",
    description="Project description",
    settings={"language": "python"}
)

# Create a task
task = client.create_task(
    project_id=project.id,
    title="Implement feature",
    description="Feature description",
    priority="high"
)
```

### JavaScript
```javascript
const PepperClient = require('pepper-client');

const client = new PepperClient({
    apiKey: 'YOUR_API_KEY'
});

// Create a project
const project = await client.createProject({
    name: 'My Project',
    description: 'Project description',
    settings: {
        language: 'javascript'
    }
});

// Create a task
const task = await client.createTask(project.id, {
    title: 'Implement feature',
    description: 'Feature description',
    priority: 'high'
});
```

## Best Practices

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly

2. **Error Handling**
   - Implement proper error handling
   - Use exponential backoff
   - Log errors appropriately

3. **Rate Limiting**
   - Monitor rate limits
   - Implement retry logic
   - Cache responses when possible

## Support

For API support:
- Email: api-support@fairgigai.com
- [API Status Page](WIP)
- [API Documentation](WIP) 