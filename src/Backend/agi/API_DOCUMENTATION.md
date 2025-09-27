# AGI Platform API Documentation

## Overview
The AGI (Artificial General Intelligence) Platform is a general-purpose AI system that provides intelligent conversation capabilities through multiple models and agents. The system is designed to be modular, scalable, and easily extensible.

## Base URL
```
http://localhost:5024/api/agi
```

## Architecture
- **Port**: 5024
- **Database Schema**: `agi` prefix
- **Redis Keys**: `agi:` prefix
- **Models**: 13 available models (TinyLlama, Qwen, LLaMA, Mistral, etc.)

## Endpoints

### Health Check
```http
GET /api/agi/health
```

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-09-27T06:02:55.222412",
    "version": "1.0.0"
}
```

### Chat Endpoint
```http
POST /api/agi/chat
```

**Request Body**:
```json
{
    "message": "Your question here",
    "session_id": "optional-session-id",
    "tenant_id": "optional-tenant-id",
    "user_id": "optional-user-id",
    "metadata": {},
    "stream": false
}
```

**Response** (non-streaming):
```json
{
    "response": "AI generated response",
    "session_id": "f8c72618-a842-4eae-ab2d-9965e8abb4fb",
    "metadata": {
        "model_used": "auto-selected"
    }
}
```

**Response** (streaming):
Returns Server-Sent Events (SSE) stream:
```
data: {"chunk": "response chunk 1"}
data: {"chunk": "response chunk 2"}
...
```

### List Models
```http
GET /api/agi/models
```

**Response**:
```json
[
    {
        "id": "tinyllama_1_1b_chat_v1_0_q4_k_m",
        "name": "tinyllama_1_1b_chat_v1_0_q4_k_m",
        "size": "tiny",
        "context_length": 8192,
        "loaded": false,
        "capabilities": ["chat", "streaming"]
    },
    ...
]
```

### Load Model
```http
POST /api/agi/models/{model_id}/load
```

**Response**:
```json
{
    "status": "loaded",
    "model_id": "tinyllama_1_1b_chat_v1_0_q4_k_m"
}
```

### Unload Model
```http
DELETE /api/agi/models/{model_id}/unload
```

**Response**:
```json
{
    "status": "unloaded",
    "model_id": "tinyllama_1_1b_chat_v1_0_q4_k_m"
}
```

### List Sessions
```http
GET /api/agi/sessions
```

**Response**:
```json
[
    {
        "session_id": "uuid",
        "tenant_id": "tenant-id",
        "user_id": "user-id",
        "created_at": "2025-09-27T06:00:00",
        "message_count": 5
    }
]
```

### Get Session History
```http
GET /api/agi/sessions/{session_id}/history?limit=10
```

**Response**:
```json
{
    "session_id": "uuid",
    "history": [
        {
            "role": "user",
            "content": "Hello",
            "timestamp": "2025-09-27T06:00:00"
        },
        {
            "role": "assistant",
            "content": "Hi! How can I help you?",
            "timestamp": "2025-09-27T06:00:01"
        }
    ]
}
```

### Delete Session
```http
DELETE /api/agi/sessions/{session_id}
```

**Response**:
```json
{
    "status": "deleted",
    "session_id": "uuid"
}
```

### System Statistics
```http
GET /api/agi/stats
```

**Response**:
```json
{
    "sessions": {
        "active": 2,
        "total_messages": 45
    },
    "models": {
        "total": 13,
        "loaded": 1,
        "models": {...}
    },
    "timestamp": "2025-09-27T06:00:00"
}
```

## WebSocket Endpoint
```ws
ws://localhost:5024/api/agi/ws/{session_id}
```

### Message Format
**Send**:
```json
{
    "type": "chat",
    "message": "Your message here"
}
```

**Receive**:
```json
{
    "type": "response",
    "chunk": "AI response chunk"
}
```

**Completion**:
```json
{
    "type": "response_complete"
}
```

## Model Selection Algorithm

The system automatically selects models based on task complexity:

1. **Simple Q&A**: TinyLlama (0.5-1B parameters)
2. **Analysis**: Qwen 3B
3. **Creative**: Qwen 7B or Mistral 7B
4. **Reasoning**: LLaMA 8B
5. **Code**: DeepSeek Coder 6.7B

## Agent System

The platform includes an agent framework for complex tasks:

- **Planning**: Decomposes complex tasks into steps
- **Execution**: Executes each step sequentially
- **Observation**: Monitors execution progress
- **Reflection**: Learns from execution results

Agents are automatically triggered for:
- Multi-step tasks
- Tasks with "then", "after that", "next" keywords
- Requests longer than 50 words

## Database Schema

All tables use the `agi` schema prefix:

- `agi.sessions`: Conversation sessions
- `agi.conversations`: Message history
- `agi.agents`: Agent configurations
- `agi.tools`: Available tools
- `agi.knowledge_documents`: Document storage
- `agi.episodic_memory`: Agent memories

## Redis Keys

All Redis keys use the `agi:` prefix:

- `agi:session:{session_id}`: Active session data
- `agi:model:{model_id}`: Model cache
- `agi:agent:{agent_id}`: Agent state
- `agi:memory:{memory_id}`: Memory storage

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error Response Format:
```json
{
    "detail": "Error description"
}
```

## Example Usage

### Python
```python
import requests
import json

# Simple chat request
url = "http://localhost:5024/api/agi/chat"
payload = {
    "message": "What is the capital of France?",
    "stream": False
}
response = requests.post(url, json=payload)
print(response.json()["response"])

# Streaming request
payload["stream"] = True
response = requests.post(url, json=payload, stream=True)
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8')[6:])
        print(data.get("chunk", ""), end="")
```

### JavaScript
```javascript
// Simple request
const response = await fetch('http://localhost:5024/api/agi/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'What is the capital of France?',
        stream: false
    })
});
const data = await response.json();
console.log(data.response);

// Streaming request
const streamResponse = await fetch('http://localhost:5024/api/agi/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'What is the capital of France?',
        stream: true
    })
});

const reader = streamResponse.body.getReader();
const decoder = new TextDecoder();
while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    console.log(decoder.decode(value));
}
```

## Notes

- The system follows SOLID principles and Single Responsibility Principle
- All models are loaded on-demand to optimize memory usage
- Session management allows for context-aware conversations
- The orchestrator automatically selects the best model for each task
- No mock data or fallback strategies are implemented per requirements