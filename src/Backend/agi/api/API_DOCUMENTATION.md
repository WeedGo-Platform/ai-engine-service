# AGI System API Documentation

## Overview
The AGI System API provides a comprehensive interface for interacting with the Artificial General Intelligence platform. The API is available at `http://localhost:5024/api/agi/*`.

## Base URL
```
http://localhost:5024/api/agi
```

## Authentication
Currently, the API does not require authentication. This will be added in future versions.

## Endpoints

### Conversation Endpoints

#### Create Conversation
```http
POST /api/agi/conversation
```

**Request Body:**
```json
{
  "user_id": "string",
  "message": "string",
  "context": {},
  "stream": false
}
```

**Response:**
```json
{
  "session_id": "string",
  "response": "string",
  "metadata": {}
}
```

#### Continue Conversation
```http
POST /api/agi/conversation/{session_id}
```

**Request Body:**
```json
{
  "message": "string",
  "context": {},
  "stream": false
}
```

#### Get Conversation History
```http
GET /api/agi/conversation/{session_id}
```

**Response:**
```json
{
  "session_id": "string",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string",
      "timestamp": "string"
    }
  ],
  "metadata": {}
}
```

#### Clear Conversation
```http
DELETE /api/agi/conversation/{session_id}
```

### WebSocket Connection
```ws
ws://localhost:5024/api/agi/ws/{session_id}
```

Send messages in JSON format:
```json
{
  "message": "string",
  "context": {}
}
```

### Tool Endpoints

#### List Available Tools
```http
GET /api/agi/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "string",
      "description": "string",
      "category": "string",
      "enabled": true
    }
  ]
}
```

#### Execute Tool
```http
POST /api/agi/tools/execute
```

**Request Body:**
```json
{
  "tool_name": "string",
  "parameters": {}
}
```

#### Get Tool Details
```http
GET /api/agi/tools/{tool_name}
```

### Analytics Endpoints

#### Get Metrics
```http
GET /api/agi/analytics/metrics?metric_type={type}&session_id={id}&hours={24}
```

**Query Parameters:**
- `metric_type` (optional): Type of metric to filter
- `session_id` (optional): Session ID to filter
- `hours` (optional, default=24): Time window in hours

**Response:**
```json
{
  "metrics": [
    {
      "type": "string",
      "value": 0.0,
      "timestamp": "string",
      "session_id": "string",
      "metadata": {}
    }
  ],
  "time_window": {
    "start": "string",
    "end": "string",
    "hours": 24
  }
}
```

#### Get Session Analytics
```http
GET /api/agi/analytics/session/{session_id}
```

**Response:**
```json
{
  "session_id": "string",
  "summary": {
    "duration_seconds": 0,
    "request_count": 0,
    "total_tokens": 0,
    "error_count": 0,
    "error_rate": 0.0,
    "tool_usage": {},
    "avg_tokens_per_request": 0
  },
  "analysis": {
    "sentiment": {},
    "complexity": {},
    "quality": {},
    "topics": []
  }
}
```

#### Get System Insights
```http
GET /api/agi/analytics/insights?hours={24}
```

**Response:**
```json
{
  "insights": [
    {
      "type": "anomaly|trend|recommendation",
      "priority": "high|medium|low",
      "title": "string",
      "description": "string",
      "data": {},
      "timestamp": "string"
    }
  ],
  "generated_at": "string",
  "time_window_hours": 24
}
```

#### Get System Statistics
```http
GET /api/agi/analytics/system-stats?hours={24}
```

### Persona Management Endpoints

#### List Personas
```http
GET /api/agi/personas
```

**Response:**
```json
{
  "personas": [
    {
      "name": "string",
      "role": "string",
      "system_prompt": "string",
      "characteristics": {},
      "language_style": {},
      "constraints": [],
      "examples": []
    }
  ],
  "count": 0
}
```

#### Get Persona
```http
GET /api/agi/personas/{persona_name}
```

#### Create Persona
```http
POST /api/agi/personas
```

**Request Body:**
```json
{
  "name": "string",
  "role": "string",
  "system_prompt": "string",
  "characteristics": {},
  "language_style": {},
  "constraints": [],
  "examples": []
}
```

#### Delete Persona
```http
DELETE /api/agi/personas/{persona_name}
```

### Template Management Endpoints

#### List Templates
```http
GET /api/agi/templates
```

**Response:**
```json
{
  "templates": [
    {
      "name": "string",
      "template": "string",
      "description": "string",
      "variables": [],
      "metadata": {}
    }
  ],
  "count": 0
}
```

#### Get Template
```http
GET /api/agi/templates/{template_name}
```

#### Create Template
```http
POST /api/agi/templates
```

**Request Body:**
```json
{
  "name": "string",
  "template": "string",
  "description": "string",
  "variables": [],
  "metadata": {}
}
```

#### Render Template
```http
POST /api/agi/templates/{template_name}/render
```

**Request Body:**
```json
{
  "key": "value"
}
```

**Response:**
```json
{
  "template": "string",
  "rendered": "string",
  "variables": {}
}
```

#### Delete Template
```http
DELETE /api/agi/templates/{template_name}
```

### Admin Endpoints

#### Health Check
```http
GET /api/agi/admin/health
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "string",
  "components": {
    "database": "string",
    "models": "string",
    "tools": "string",
    "orchestrator": "string"
  }
}
```

#### Reload Models
```http
POST /api/agi/admin/reload-models
```

#### Reload Tools
```http
POST /api/agi/admin/reload-tools
```

#### Get Database Statistics
```http
GET /api/agi/admin/database-stats
```

**Response:**
```json
{
  "tables": [
    {
      "schemaname": "string",
      "tablename": "string",
      "size": "string",
      "inserts": 0,
      "updates": 0,
      "deletes": 0
    }
  ],
  "connections": {
    "total_connections": 0,
    "active_connections": 0,
    "idle_connections": 0
  }
}
```

#### Flush Metrics Buffer
```http
POST /api/agi/admin/flush-metrics
```

#### Clear Sessions
```http
POST /api/agi/admin/clear-sessions
```

#### Get Configuration
```http
GET /api/agi/admin/config
```

**Response:**
```json
{
  "environment": "string",
  "database": {
    "host": "string",
    "port": 0,
    "database": "string",
    "pool_size": 0
  },
  "services": {
    "enable_rag": true,
    "enable_memory": true,
    "enable_tools": true,
    "enable_analytics": true
  },
  "models": {
    "default_model": "string",
    "fallback_model": "string",
    "temperature": 0.0,
    "max_tokens": 0
  },
  "rag": {
    "chunk_size": 0,
    "chunk_overlap": 0,
    "top_k": 0
  }
}
```

### General Statistics
```http
GET /api/agi/stats
```

**Response:**
```json
{
  "sessions": {
    "active": 0,
    "total_messages": 0
  },
  "models": {
    "total_models": 0,
    "active_models": 0,
    "available_models": []
  },
  "tools": {
    "count": 0,
    "available": []
  },
  "timestamp": "string"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## WebSocket Protocol

The WebSocket endpoint at `/api/agi/ws/{session_id}` supports real-time bidirectional communication.

### Message Format

**Client to Server:**
```json
{
  "message": "User's message",
  "context": {
    "key": "value"
  }
}
```

**Server to Client:**
```json
{
  "type": "response|error|status",
  "content": "Response content",
  "metadata": {}
}
```

### Connection Flow

1. Connect to WebSocket endpoint with session ID
2. Send JSON messages
3. Receive streaming responses
4. Connection automatically handles heartbeat/keepalive

## Rate Limiting

Currently no rate limiting is implemented. This will be added in future versions.

## Examples

### Python Example

```python
import requests
import json

# Create a new conversation
response = requests.post(
    "http://localhost:5024/api/agi/conversation",
    json={
        "user_id": "user123",
        "message": "Hello, how can you help me?",
        "stream": False
    }
)

data = response.json()
session_id = data["session_id"]

# Continue conversation
response = requests.post(
    f"http://localhost:5024/api/agi/conversation/{session_id}",
    json={
        "message": "Tell me about AI",
        "stream": False
    }
)
```

### JavaScript Example

```javascript
// Using fetch API
const response = await fetch('http://localhost:5024/api/agi/conversation', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user123',
    message: 'Hello, how can you help me?',
    stream: false
  })
});

const data = await response.json();
const sessionId = data.session_id;

// WebSocket connection
const ws = new WebSocket(`ws://localhost:5024/api/agi/ws/${sessionId}`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: 'Tell me about AI',
    context: {}
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### cURL Examples

```bash
# Create conversation
curl -X POST http://localhost:5024/api/agi/conversation \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "Hello", "stream": false}'

# List personas
curl http://localhost:5024/api/agi/personas

# Get system health
curl http://localhost:5024/api/agi/admin/health

# Get metrics for last 24 hours
curl "http://localhost:5024/api/agi/analytics/metrics?hours=24"
```

## Streaming Responses

For endpoints that support streaming (`stream: true`), responses are sent as Server-Sent Events (SSE):

```
data: {"content": "Partial response...", "done": false}
data: {"content": "More content...", "done": false}
data: {"content": "Final content", "done": true}
```

## Next Steps

- Add authentication and API keys
- Implement rate limiting
- Add request/response validation
- Add OpenAPI/Swagger documentation
- Add GraphQL endpoint
- Add batch processing endpoints