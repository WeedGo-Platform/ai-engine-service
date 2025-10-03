# Unified Chat System Migration Guide

## Overview

This document guides the migration from the legacy chat endpoints to the new unified chat system. The unified system follows SOLID principles, provides better maintainability, and offers enhanced features while maintaining backwards compatibility.

## Architecture Overview

### New Components

```
services/chat/
├── __init__.py              # Module exports
├── interfaces.py            # Protocol definitions (SOLID interfaces)
├── models.py                # Pydantic data models
├── chat_service.py          # Core ChatService implementation
├── adapters.py              # Adapter pattern implementations
└── container.py             # Dependency injection container

api/
├── unified_chat_router.py   # New REST API endpoints
├── unified_chat_websocket.py # New WebSocket handler
├── compatibility_layer.py   # Legacy endpoint wrappers
└── chat_integration.py      # Integration helpers
```

### Design Principles Applied

1. **Single Responsibility Principle (SRP)**
   - Each class has one reason to change
   - ChatService coordinates, adapters translate, providers store

2. **Open/Closed Principle (OCP)**
   - Open for extension via interfaces
   - Closed for modification of core logic

3. **Liskov Substitution Principle (LSP)**
   - Protocol types ensure substitutability
   - Mock implementations possible for testing

4. **Interface Segregation Principle (ISP)**
   - Small, focused interfaces (IChatProcessor, ISessionManager, etc.)
   - Clients depend only on methods they use

5. **Dependency Inversion Principle (DIP)**
   - High-level ChatService depends on abstractions (interfaces)
   - Low-level implementations injected via container

6. **DRY (Don't Repeat Yourself)**
   - All endpoints route through ChatService
   - No duplicated message processing logic

7. **KISS (Keep It Simple, Stupid)**
   - Clear separation of concerns
   - Straightforward data flow

## Migration Steps

### Phase 1: Initialize System (No Breaking Changes)

#### 1.1 Update Server Initialization

**File:** `main_server.py` or `api_server.py`

**Before:**
```python
# Existing code
agent_pool = get_agent_pool()
```

**After:**
```python
# Add these imports at the top
from api.chat_integration import (
    initialize_unified_chat_system,
    register_unified_chat_routes
)

# Existing code
agent_pool = get_agent_pool()

# Add after agent pool initialization
try:
    # Initialize unified chat system
    initialize_unified_chat_system()
    logger.info("✅ Unified chat system initialized")

    # Register all routes (new + legacy compatibility)
    register_unified_chat_routes(app)
    logger.info("✅ Chat routes registered")
except Exception as e:
    logger.error(f"Failed to initialize unified chat: {str(e)}")
    raise
```

#### 1.2 Verify Installation

Check logs for:
```
✅ Unified chat system initialized successfully
   - ChatService: True
   - Agent Pool: True
✅ Registered unified REST API routes: /api/v1/chat/*
✅ Registered legacy compatibility routes
✅ Registered unified WebSocket endpoint: /api/v1/chat/ws
```

Test health endpoint:
```bash
curl http://localhost:5024/api/v1/chat/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "unified-chat-api",
  "version": "1.0.0",
  "initialized": true
}
```

### Phase 2: Parallel Testing

#### 2.1 Test New Endpoints Alongside Legacy

**Legacy endpoint (still works):**
```bash
curl -X POST http://localhost:5024/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want sativa pre-rolls", "session_id": "test-123"}'
```

**New endpoint (recommended):**
```bash
curl -X POST http://localhost:5024/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want sativa pre-rolls",
    "session_id": "test-123",
    "agent_id": "dispensary",
    "personality_id": "marcel",
    "use_tools": true
  }'
```

#### 2.2 WebSocket Testing

**Legacy WebSocket (still works):**
```javascript
const ws = new WebSocket('ws://localhost:5024/chat/ws');
```

**New WebSocket (recommended):**
```javascript
const ws = new WebSocket('ws://localhost:5024/api/v1/chat/ws');

ws.onopen = () => {
  // Connection message received automatically with session_id
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  message: 'I want sativa pre-rolls',
  user_id: 'user123'
}));

// Update agent/personality mid-conversation
ws.send(JSON.stringify({
  type: 'session_update',
  agent: 'wellness',
  personality: 'sara'
}));
```

### Phase 3: Frontend Migration

#### 3.1 Update ChatWidget (ai-admin-dashboard)

**File:** `src/Frontend/ai-admin-dashboard/src/components/ChatWidget.tsx`

**Changes Required:**

1. **Update WebSocket URL** (Line ~66):
```typescript
// OLD
const wsUrl = `ws://localhost:5024/chat/ws`;

// NEW
const wsUrl = `ws://localhost:5024/api/v1/chat/ws`;
```

2. **Update Message Format** (Lines ~600-610):
```typescript
// OLD
const messageData = {
  type: 'message',
  message: inputValue,
  session_id: sessionIdRef.current
};

// NEW (add optional parameters)
const messageData = {
  type: 'message',
  message: inputValue,
  session_id: sessionIdRef.current,
  user_id: userId,  // if available
  use_tools: true,
  use_context: true
};
```

3. **Handle New Response Format**:
```typescript
// Response structure is the same, but now includes metadata
interface ChatResponse {
  type: 'message';
  content: string;
  products: Product[];
  quick_actions: QuickAction[];
  metadata: {
    model: string;
    tokens_used: number;
    response_time: number;
    tool_calls: string[];
    intent?: string;
    confidence?: number;
  };
  timestamp: string;
}
```

#### 3.2 Update REST API Calls

If using REST endpoints instead of WebSocket:

```typescript
// OLD
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message, session_id })
});

// NEW
const response = await fetch('/api/v1/chat/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message,
    session_id,
    agent_id: 'dispensary',
    personality_id: 'marcel',
    use_tools: true,
    max_tokens: 500
  })
});
```

### Phase 4: Advanced Features

#### 4.1 Explicit Session Management

Create sessions explicitly:
```typescript
// Create a new session
const createSession = async () => {
  const response = await fetch('/api/v1/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_id: 'dispensary',
      personality_id: 'marcel',
      user_id: userId,
      language: 'en'
    })
  });

  const data = await response.json();
  return data.session_id;
};
```

Update session configuration:
```typescript
// Switch agent mid-conversation
const switchAgent = async (sessionId: string, newAgent: string) => {
  await fetch(`/api/v1/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_id: newAgent,
      personality_id: 'sara'
    })
  });
};
```

#### 4.2 Streaming Responses (SSE)

```typescript
const streamMessage = async (message: string, sessionId: string) => {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.type === 'text') {
          updateUIWithText(data.content);
        } else if (data.type === 'product') {
          addProduct(data.content);
        } else if (data.type === 'done') {
          completeResponse();
        }
      }
    }
  }
};
```

#### 4.3 History Management

```typescript
// Get user's conversation history
const getUserHistory = async (userId: string) => {
  const response = await fetch(
    `/api/v1/chat/history/${userId}?limit=20&offset=0`
  );
  return response.json();
};

// Get session conversation
const getSessionHistory = async (sessionId: string) => {
  const response = await fetch(
    `/api/v1/chat/sessions/${sessionId}/history?limit=50`
  );
  return response.json();
};
```

### Phase 5: Monitoring & Validation

#### 5.1 Monitor Deprecation Warnings

Check logs for warnings like:
```
WARNING - Legacy /api/chat endpoint called - consider migrating to /api/v1/chat/message
```

#### 5.2 Track Endpoint Usage

Add middleware to track which endpoints are being used:

```python
# In api_server.py or main_server.py
@app.middleware("http")
async def track_endpoint_usage(request: Request, call_next):
    path = request.url.path

    # Track legacy endpoint usage
    if path.startswith("/api/chat") and not path.startswith("/api/v1/chat"):
        logger.warning(f"Legacy endpoint used: {path}")
        # Could also increment a counter/metric here

    response = await call_next(request)
    return response
```

#### 5.3 Health Checks

Regular health check:
```bash
# Check unified chat system
curl http://localhost:5024/api/v1/chat/health

# Get deprecation information
curl http://localhost:5024/api/deprecation-notice
```

### Phase 6: Complete Migration

#### 6.1 Verify All Clients Updated

Before removing legacy endpoints:
- [ ] ChatWidget updated to use new WebSocket URL
- [ ] All REST API calls updated
- [ ] Mobile app updated (if applicable)
- [ ] No deprecation warnings in logs for 1 week
- [ ] All integration tests passing

#### 6.2 Remove Legacy Endpoints

Once validation is complete:

1. **Stop including compatibility router:**
```python
# In chat_integration.py - comment out or remove
# app.include_router(compat_router)
```

2. **Remove old endpoint files:**
```bash
# Backup first
mv api/chat_endpoints.py api/chat_endpoints.py.backup

# In api_server.py, remove old endpoint definitions
# (search for @app.post("/api/chat"))
```

3. **Update documentation** to remove references to old endpoints

## API Reference

### REST Endpoints

#### POST /api/v1/chat/message
Send a chat message and receive response.

**Request:**
```json
{
  "message": "I want sativa pre-rolls",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "store_id": "optional-store-id",
  "language": "en",
  "agent_id": "dispensary",
  "personality_id": "marcel",
  "use_tools": true,
  "use_context": true,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "text": "I found some great sativa pre-rolls!",
  "products": [...],
  "quick_actions": [...],
  "metadata": {
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 450,
    "response_time": 2.35,
    "tool_calls": ["SmartProductSearch"],
    "intent": "product_search",
    "confidence": 0.95
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### POST /api/v1/chat/stream
Stream response using Server-Sent Events.

Same request format as `/message`, but returns SSE stream.

#### POST /api/v1/chat/sessions
Create a new session.

**Request:**
```json
{
  "agent_id": "dispensary",
  "personality_id": "marcel",
  "user_id": "optional-user-id",
  "language": "en"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-02T16:00:00Z",
  "agent_id": "dispensary",
  "personality_id": "marcel"
}
```

#### PATCH /api/v1/chat/sessions/{session_id}
Update session configuration.

**Request:**
```json
{
  "agent_id": "wellness",
  "personality_id": "sara"
}
```

#### GET /api/v1/chat/sessions/{session_id}
Get session details.

#### DELETE /api/v1/chat/sessions/{session_id}
Delete a session.

#### GET /api/v1/chat/sessions
List sessions (optionally filtered by user_id).

#### GET /api/v1/chat/history/{user_id}
Get user's conversation history across all sessions.

Query params:
- `limit`: Max messages (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)

#### GET /api/v1/chat/sessions/{session_id}/history
Get conversation history for a specific session.

Query params:
- `limit`: Max messages (default: 50, max: 100)

### WebSocket Protocol

#### Connection
```
WS /api/v1/chat/ws?session_id=optional-session-id
```

#### Message Types

**Send Message:**
```json
{
  "type": "message",
  "message": "I want sativa pre-rolls",
  "user_id": "optional",
  "use_tools": true
}
```

**Update Session:**
```json
{
  "type": "session_update",
  "agent": "wellness",
  "personality": "sara"
}
```

**Heartbeat:**
```json
{
  "type": "heartbeat"
}
```

#### Received Messages

**Connection Established:**
```json
{
  "type": "connection",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connected successfully",
  "timestamp": "2025-10-02T16:00:00Z"
}
```

**Typing Indicator:**
```json
{
  "type": "typing",
  "typing": true,
  "timestamp": "2025-10-02T16:00:01Z"
}
```

**Message Response:**
```json
{
  "type": "message",
  "content": "I found some great sativa pre-rolls!",
  "products": [...],
  "quick_actions": [...],
  "metadata": {...},
  "timestamp": "2025-10-02T16:00:03Z"
}
```

**Session Updated:**
```json
{
  "type": "session_updated",
  "message": "Session updated successfully",
  "agent": "wellness",
  "personality": "sara",
  "timestamp": "2025-10-02T16:00:04Z"
}
```

**Error:**
```json
{
  "type": "error",
  "error": "Failed to process message",
  "error_code": "PROCESSING_ERROR",
  "timestamp": "2025-10-02T16:00:05Z"
}
```

## Benefits of New System

### For Developers

1. **Single Source of Truth**
   - All chat logic flows through ChatService
   - No duplicate code across endpoints

2. **Better Testing**
   - Dependency injection enables easy mocking
   - Unit tests can test service logic without HTTP layer

3. **Type Safety**
   - Pydantic models validate all input/output
   - TypeScript-like experience in Python

4. **API Documentation**
   - Automatic OpenAPI docs at /docs
   - All endpoints documented with examples

5. **Maintainability**
   - SOLID principles make changes easier
   - Clear separation of concerns

### For Users

1. **Consistency**
   - All endpoints follow same patterns
   - Predictable error handling

2. **Features**
   - Explicit session management
   - Streaming support
   - Better metadata in responses

3. **Performance**
   - More efficient resource usage
   - Better connection management

4. **Reliability**
   - Improved error handling
   - Better logging and monitoring

## Troubleshooting

### Issue: "Agent pool not initialized"

**Solution:** Ensure agent pool is initialized before calling `initialize_unified_chat_system()`:
```python
agent_pool = get_agent_pool()
initialize_unified_chat_system()  # Calls get_agent_pool() internally
```

### Issue: "Session not found"

**Cause:** Session ID doesn't exist or was deleted.

**Solution:** Create a new session or omit session_id to auto-create.

### Issue: Legacy endpoints not working

**Cause:** Compatibility layer not registered.

**Solution:** Ensure `register_unified_chat_routes(app)` is called, which includes compatibility routes.

### Issue: WebSocket disconnects immediately

**Cause:** May be connection issue or error during initialization.

**Solution:** Check logs for error messages. Ensure agent pool is initialized.

### Issue: No products returned

**Cause:** SmartProductSearch tool may not be executing.

**Solution:** Verify `use_tools=true` in request and check logs for tool execution.

## Support & Resources

- **API Documentation:** http://localhost:5024/docs
- **Deprecation Info:** GET /api/deprecation-notice
- **Health Check:** GET /api/v1/chat/health
- **Migration Helper:** `python -c "from api.chat_integration import migrate_from_legacy_to_unified; migrate_from_legacy_to_unified()"`

## Timeline

- **Phase 1-3 (Week 1):** Initialize system, parallel testing
- **Phase 4 (Week 2):** Frontend migration, feature adoption
- **Phase 5 (Week 3-4):** Monitoring, validation
- **Phase 6 (Week 5+):** Complete migration, remove legacy endpoints

## Success Criteria

- [ ] Zero deprecation warnings in logs
- [ ] All integration tests passing with new endpoints
- [ ] Frontend using new WebSocket endpoint
- [ ] REST API calls updated
- [ ] Session management working correctly
- [ ] Product search returning results
- [ ] Agent/personality switching working
- [ ] Streaming responses functional
- [ ] No regressions in user experience
