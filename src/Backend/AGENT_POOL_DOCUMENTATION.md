# Agent Pool Multi-Agent Architecture Documentation

## Overview
The Agent Pool system enables multiple AI agents with different personalities to be loaded and managed efficiently using a shared model architecture. This allows for resource-efficient personality switching without reloading the underlying LLM model.

## Architecture Components

### 1. Agent Pool Manager (`services/agent_pool_manager.py`)
- **Purpose**: Central manager for all agents and personalities
- **Features**:
  - Shared model reference for all agents
  - LRU cache for personality configurations
  - Session-based agent/personality management
  - Hot-swapping personalities without model reload

### 2. Available Agents

#### Dispensary Agent
- **Agent ID**: `dispensary`
- **Personalities**:
  - **Marcel** (`marcel`) - Default personality
  - **Shante** (`shante`) - Alternative personality
  - **Zac** (`zac`) - Alternative personality
- **Purpose**: Cannabis dispensary assistant for product recommendations

#### Assistant Agent
- **Agent ID**: `assistant`
- **Personalities**:
  - **Rhomida** (`rhomida`) - Default personality
- **Purpose**: General assistant functionality

## API Endpoints

### Admin Endpoints

#### Get All Agents
```
GET /api/admin/agents
```
Returns list of available agents.

#### Get Agent Personalities
```
GET /api/admin/agents/{agent_id}/personalities
```
Returns available personalities for a specific agent.

#### Set Agent Personality
```
POST /api/admin/agents/{agent_id}/personality
```
Body: `{"personality_id": "marcel"}`
Sets the active personality for an agent.

### WebSocket Integration

The personality switching is integrated with the WebSocket chat system:

#### Session Update Message
```json
{
  "type": "session_update",
  "session_id": "your-session-id",
  "personality_id": "new-personality-id"
}
```

This message switches the personality for an active chat session while preserving conversation context.

## Usage Examples

### Mobile App Integration

1. **Initial Connection**:
   - App connects to WebSocket with default dispensary/marcel configuration
   - User can access chat settings to see available personalities

2. **Switching Personalities**:
   - User selects different personality in chat settings
   - App sends `session_update` message via WebSocket
   - Personality switches immediately without losing context

3. **Personality Characteristics**:
   - Each personality has unique:
     - Response style
     - Greeting message
     - Knowledge domains
     - Behavioral rules

### Performance Metrics

The system tracks:
- Total requests processed
- Personality switches count
- Cache hit/miss rates
- Active sessions
- Memory usage

Access metrics via:
```
GET /api/agent-pool/metrics  # (if endpoint is registered)
```

## Implementation Benefits

1. **Resource Efficiency**:
   - Single model instance serves all agents
   - Personality configs are lightweight JSON
   - LRU caching reduces file I/O

2. **Scalability**:
   - Can handle up to 1000 concurrent sessions
   - Automatic cleanup of inactive sessions
   - Configurable memory limits

3. **Flexibility**:
   - Hot-swap personalities without restart
   - Preserve or clear context on switch
   - Add new personalities via JSON files

## Configuration

System configuration in `config/system_config.json`:
```json
{
  "performance": {
    "max_memory_gb": 4,
    "enable_hot_swap": true,
    "cache_personalities": true,
    "max_cache_size": 20,
    "max_sessions": 1000
  }
}
```

## Testing

Test personality switching:
```python
# WebSocket test (requires authentication)
{
  "type": "session_update",
  "session_id": "test-123",
  "personality_id": "shante"
}
```

## Future Enhancements

1. **Dynamic Agent Loading**: Load new agents without restart
2. **Personality Blending**: Mix traits from multiple personalities
3. **User-Specific Personalities**: Custom personalities per user
4. **Analytics Dashboard**: Real-time metrics visualization
5. **A/B Testing**: Compare personality performance