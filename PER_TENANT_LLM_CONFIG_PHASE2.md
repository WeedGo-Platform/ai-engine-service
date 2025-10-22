# Per-Tenant LLM Configuration - Phase 2 Complete

**Status**: ✅ Phase 2 Completed  
**Commit**: 58d5185  
**Date**: 2024

## Phase 2 Overview

Phase 2 implemented the business logic and integration layers for per-tenant LLM configuration:

1. **Model Usage Tracking Service** - Real-time request logging with cost calculation
2. **Tenant-Aware Router** - Extends LLMRouter with per-tenant config and usage tracking

## 🎯 What Was Built

### 1. Model Usage Tracking Service

**File**: `src/Backend/services/model_usage_tracker.py` (550+ lines)

#### Key Components

##### ModelUsageTracker Class
```python
class ModelUsageTracker:
    """
    Async service to track LLM usage in real-time
    
    Features:
    - Connection pooling (2-10 connections)
    - Cost calculation per provider/model
    - Rate limit status checking
    - Tenant usage statistics
    - Non-blocking request tracking
    """
```

**Key Methods**:

1. **`track_request()`** - Log individual requests
   - Parameters: tenant_id, provider, model, endpoint, tokens, latency, status
   - Returns: Usage record UUID
   - Non-blocking (fire-and-forget)
   - Calculates estimated cost using pricing table

2. **`calculate_cost()`** - Estimate request cost
   - Uses `COST_PER_MILLION_TOKENS` pricing table
   - Supports all providers (Groq, OpenRouter, LLM7, Local)
   - Returns Decimal with 6 decimal precision

3. **`get_tenant_usage_stats()`** - Aggregate statistics
   - Time window: configurable (default 24h)
   - Groups by provider and model
   - Includes: requests, tokens, costs, latency, rate limits
   - Returns formatted JSON

4. **`check_rate_limit_status()`** - Monitor quotas
   - Checks requests in time window
   - Calculates usage percentage
   - Status levels: healthy, normal, warning, critical
   - Returns `should_failover` flag

#### Cost Pricing Table

```python
COST_PER_MILLION_TOKENS = {
    'groq': {
        'llama-3.3-70b-versatile': {'input': 0.59, 'output': 0.79},
        'llama-3.1-70b-versatile': {'input': 0.59, 'output': 0.79},
        'mixtral-8x7b-32768': {'input': 0.24, 'output': 0.24},
    },
    'openrouter': {
        'deepseek/deepseek-r1': {'input': 0.55, 'output': 2.19},
        'anthropic/claude-3.5-sonnet': {'input': 3.0, 'output': 15.0},
        'google/gemini-pro-1.5': {'input': 1.25, 'output': 5.0},
    },
    'llm7': {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 5.0, 'output': 15.0},
        'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
    },
    'local': {
        'default': {'input': 0.0, 'output': 0.0}
    }
}
```

#### Global Singleton Pattern

```python
_usage_tracker: Optional[ModelUsageTracker] = None

async def get_usage_tracker() -> ModelUsageTracker:
    """Get or create global usage tracker instance"""
    global _usage_tracker
    
    if _usage_tracker is None:
        _usage_tracker = ModelUsageTracker()
        await _usage_tracker.initialize()
    
    return _usage_tracker
```

**Benefits**:
- Single connection pool shared across app
- Automatic initialization on first use
- Thread-safe async operations

#### Convenience Function

```python
async def track_usage(
    tenant_id: str,
    provider: str,
    model_name: str,
    endpoint: str,
    **kwargs
) -> Optional[str]:
    """
    Quick access function for tracking
    
    Usage:
        await track_usage(
            tenant_id="...",
            provider="groq",
            model_name="llama-3.3-70b-versatile",
            endpoint="/api/chat",
            latency_ms=1500,
            input_tokens=100,
            output_tokens=200,
            status="success"
        )
    """
```

---

### 2. Tenant-Aware LLM Router

**File**: `src/Backend/services/llm_gateway/tenant_router.py` (650+ lines)

#### TenantLLMRouter Class

```python
class TenantLLMRouter:
    """
    Tenant-aware LLM router with per-tenant configuration and usage tracking
    
    Features:
    - Load tenant tokens from database
    - Respect preferred provider setting
    - Auto-failover if enabled
    - Track all requests to database
    - Configuration caching (5min TTL)
    - System provider fallback
    """
```

#### Key Features

##### 1. Configuration Loading

**Method**: `_load_tenant_config(tenant_id: str) -> Dict`

```python
# Returns:
{
    'llm_tokens': {
        'groq': 'gsk_...',
        'openrouter': 'sk-or-...',
        'llm7': 'sk-...'
    },
    'inference_config': {
        'preferred_provider': 'groq',
        'auto_failover': true,
        'preferred_models': {
            'groq': 'llama-3.3-70b-versatile',
            'openrouter': 'deepseek/deepseek-r1',
            'llm7': 'gpt-4o-mini'
        }
    }
}
```

**Features**:
- Loads from `tenants.llm_tokens` and `tenants.inference_config` (JSONB)
- 5-minute cache TTL (configurable)
- Returns defaults if tenant not found
- Graceful error handling

##### 2. Router Creation

**Method**: `_create_tenant_router(tenant_id, tenant_tokens, preferred_models) -> LLMRouter`

**Provider Registration Logic**:

```python
# 1. Register tenant-specific providers (if tokens provided)
if tenant_tokens.get('groq'):
    groq = GroqProvider(api_key=tenant_tokens['groq'])
    if 'groq' in preferred_models:
        groq.set_model(preferred_models['groq'])
    router.register_provider(groq)

# 2. Repeat for OpenRouter and LLM7

# 3. Register system-level providers as fallback
if not tenant_tokens.get('groq'):
    system_groq = GroqProvider()  # Uses GROQ_API_KEY env var
    if system_groq.is_enabled:
        router.register_provider(system_groq)
```

**Fallback Strategy**:
- Tenant tokens take priority
- System tokens used if tenant has none
- Multiple providers registered for auto-failover

##### 3. Tenant Completion

**Method**: `complete_for_tenant(tenant_id, messages, context, endpoint, user_id)`

**Workflow**:

```
1. Load tenant config from database (with caching)
   ↓
2. Create tenant-specific router with appropriate providers
   ↓
3. Call router.complete() with context
   ↓
4. Track request to model_usage_stats table
   ↓
5. Return CompletionResult
```

**Metadata Tracked**:
- Tenant ID, user ID
- Provider, model name
- Input/output tokens
- Latency (ms)
- Cost (calculated)
- Status (success/error/rate_limit)
- Error message (if failed)
- Custom metadata (cached, finish_reason, etc.)

##### 4. Provider Name Normalization

**Method**: `_normalize_provider_name(provider_name: str) -> str`

```python
# Maps friendly names to database format
'OpenRouter (DeepSeek R1)' → 'openrouter'
'Groq (Llama 3.3 70B)'    → 'groq'
'LLM7 GPT-4o Mini'        → 'llm7'
'Local Llama'             → 'local'
```

**Why?**: Ensures consistent provider naming in database

##### 5. Cache Management

**Method**: `invalidate_cache(tenant_id: Optional[str])`

```python
# Invalidate specific tenant
router.invalidate_cache(tenant_id="...")

# Invalidate all tenants
router.invalidate_cache()
```

**Use Cases**:
- After tenant updates tokens via API
- After changing provider preferences
- Troubleshooting/testing

#### Global Singleton Pattern

```python
_tenant_router: Optional[TenantLLMRouter] = None

async def get_tenant_router() -> TenantLLMRouter:
    """Get or create global tenant router instance"""
```

**Benefits**:
- Single database connection pool
- Shared configuration cache
- Efficient resource usage

#### Convenience Function

```python
async def complete_for_tenant(
    tenant_id: str,
    messages: List[Dict],
    task_type: TaskType,
    estimated_tokens: int,
    endpoint: str,
    **kwargs
) -> CompletionResult:
    """
    Quick access for tenant-aware completion
    
    Usage:
        result = await complete_for_tenant(
            tenant_id="...",
            messages=[{"role": "user", "content": "Hello"}],
            task_type=TaskType.CHAT,
            estimated_tokens=100,
            endpoint="/api/chat",
            user_id="..."
        )
    """
```

---

## 📦 Integration with Existing System

### Updated Files

#### 1. `services/llm_gateway/__init__.py`

**Added Exports**:
```python
from .tenant_router import (
    TenantLLMRouter,
    get_tenant_router,
    complete_for_tenant
)

__all__ = [
    # ... existing exports
    "TenantLLMRouter",
    "get_tenant_router",
    "complete_for_tenant",
]
```

---

## 🧪 Testing Guide

### 1. Test Usage Tracker

```python
import asyncio
from services.model_usage_tracker import get_usage_tracker

async def test_tracker():
    tracker = await get_usage_tracker()
    
    # Track a request
    usage_id = await tracker.track_request(
        tenant_id="your-tenant-uuid",
        provider="groq",
        model_name="llama-3.3-70b-versatile",
        endpoint="/api/chat",
        latency_ms=1500,
        input_tokens=100,
        output_tokens=200,
        status="success"
    )
    print(f"Tracked request: {usage_id}")
    
    # Get stats
    stats = await tracker.get_tenant_usage_stats(
        tenant_id="your-tenant-uuid",
        hours=24
    )
    print(f"Usage stats: {stats}")
    
    # Check rate limits
    status = await tracker.check_rate_limit_status(
        tenant_id="your-tenant-uuid",
        provider="groq"
    )
    print(f"Rate limit status: {status}")

asyncio.run(test_tracker())
```

### 2. Test Tenant Router

```python
import asyncio
from services.llm_gateway import (
    complete_for_tenant,
    TaskType
)

async def test_tenant_router():
    result = await complete_for_tenant(
        tenant_id="your-tenant-uuid",
        messages=[
            {"role": "user", "content": "Hello, how are you?"}
        ],
        task_type=TaskType.CHAT,
        estimated_tokens=100,
        endpoint="/api/test"
    )
    
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model}")
    print(f"Response: {result.content}")
    print(f"Tokens: {result.tokens_input} → {result.tokens_output}")
    print(f"Cost: ${result.cost:.6f}")
    print(f"Latency: {result.latency:.2f}s")

asyncio.run(test_tenant_router())
```

### 3. Test with Different Tenant Configs

**Tenant A (has Groq token)**:
```sql
UPDATE tenants
SET llm_tokens = '{"groq": "gsk_...", "openrouter": null, "llm7": null}',
    inference_config = '{"preferred_provider": "groq", "auto_failover": true}'
WHERE id = 'tenant-a-uuid';
```

**Tenant B (has all tokens)**:
```sql
UPDATE tenants
SET llm_tokens = '{"groq": "gsk_...", "openrouter": "sk-or-...", "llm7": "sk-..."}',
    inference_config = '{
        "preferred_provider": "openrouter",
        "auto_failover": true,
        "preferred_models": {
            "groq": "llama-3.3-70b-versatile",
            "openrouter": "deepseek/deepseek-r1",
            "llm7": "gpt-4o-mini"
        }
    }'
WHERE id = 'tenant-b-uuid';
```

**Tenant C (no tokens - will use system defaults)**:
```sql
UPDATE tenants
SET llm_tokens = '{}',
    inference_config = '{"preferred_provider": "groq", "auto_failover": true}'
WHERE id = 'tenant-c-uuid';
```

---

## 📊 Database Queries for Monitoring

### 1. Recent Usage by Tenant

```sql
SELECT 
    provider,
    model_name,
    COUNT(*) as requests,
    SUM(total_tokens) as tokens,
    SUM(estimated_cost_usd) as cost_usd,
    AVG(latency_ms) as avg_latency
FROM model_usage_stats
WHERE tenant_id = 'your-tenant-uuid'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY provider, model_name
ORDER BY requests DESC;
```

### 2. Rate Limit Status

```sql
SELECT 
    provider,
    COUNT(*) as request_count,
    COUNT(*) FILTER (WHERE status = 'rate_limit') as rate_limited
FROM model_usage_stats
WHERE tenant_id = 'your-tenant-uuid'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY provider;
```

### 3. Cost Tracking

```sql
SELECT 
    DATE(timestamp) as date,
    provider,
    SUM(estimated_cost_usd) as daily_cost
FROM model_usage_stats
WHERE tenant_id = 'your-tenant-uuid'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), provider
ORDER BY date DESC, daily_cost DESC;
```

### 4. Error Analysis

```sql
SELECT 
    provider,
    model_name,
    status,
    error_message,
    COUNT(*) as occurrences
FROM model_usage_stats
WHERE tenant_id = 'your-tenant-uuid'
  AND status != 'success'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY provider, model_name, status, error_message
ORDER BY occurrences DESC;
```

---

## 🔗 How It Works Together

### Request Flow

```
User Request
    ↓
API Endpoint (/api/chat)
    ↓
Extract tenant_id from auth/context
    ↓
Call complete_for_tenant()
    ↓
┌─────────────────────────────┐
│   TenantLLMRouter           │
│                             │
│  1. Load tenant config      │ ← Database (tenants table)
│     (with 5min cache)       │
│                             │
│  2. Create router with      │
│     tenant's API tokens     │
│                             │
│  3. Set preferred models    │
│                             │
│  4. Call LLMRouter.complete │
│     (auto-failover enabled) │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│   LLMRouter                 │
│                             │
│  - Score providers          │
│  - Select best match        │
│  - Generate completion      │
│  - Handle failures          │
└─────────────────────────────┘
    ↓
CompletionResult
    ↓
┌─────────────────────────────┐
│   ModelUsageTracker         │
│                             │
│  - Log request              │ → Database (model_usage_stats)
│  - Calculate cost           │
│  - Track latency            │
│  - Store metadata           │
└─────────────────────────────┘
    ↓
Return result to user
```

---

## 🚀 Performance Considerations

### 1. Configuration Caching
- **TTL**: 5 minutes (configurable)
- **Benefit**: Avoid database query on every request
- **Trade-off**: Config changes take up to 5min to apply
- **Solution**: Call `invalidate_cache()` after updates

### 2. Connection Pooling
- **Usage Tracker**: 2-10 connections
- **Tenant Router**: 2-10 connections
- **Total**: 4-20 database connections (shared)

### 3. Non-Blocking Tracking
- Usage tracking is fire-and-forget
- Doesn't block LLM request/response
- Failures logged but don't affect user experience

### 4. Index Usage
All queries use indexed columns:
- `model_usage_stats(tenant_id, timestamp)` - Composite index
- `model_usage_stats(provider)` - Single index
- `model_usage_stats(status)` - Single index

---

## 🎯 Next Steps: Phase 3 (Frontend UI)

### Task 6: Token Management UI
- Input fields for Groq/OpenRouter/LLM7 API tokens
- Test button (validates token before saving)
- Visual feedback for token status
- Save/update functionality

### Task 7: Provider/Model Selection UI
- Provider cards (Groq, OpenRouter, LLM7)
- Model dropdown for each provider
- Auto-failover toggle checkbox
- Active provider visual indicator
- Model capabilities badges

### Task 8: Usage Stats Dashboard
- **Charts**:
  - Requests over time (line chart)
  - Tokens used by provider (bar chart)
  - Cost trend (line chart)
  - Latency distribution (histogram)
- **Tables**:
  - Per-provider breakdown
  - Per-model breakdown
  - Recent requests log
- **Alerts**:
  - Rate limit warnings
  - High cost notifications
  - Error summaries

---

## 📋 Summary

✅ **Completed**:
- Model usage tracking service (550 lines)
- Tenant-aware LLM router (650 lines)
- Integration with existing LLMRouter
- Cost calculation for all providers
- Rate limit monitoring
- Usage statistics aggregation
- Configuration caching
- System provider fallback
- Global singleton patterns
- Comprehensive error handling

🎯 **Ready For**:
- Phase 3: Frontend UI development
- Production deployment (backend complete)
- Real-world testing with multiple tenants

📊 **Metrics**:
- Total new code: ~1,200 lines
- Files created: 2
- Files modified: 1
- Test coverage: Manual testing required
- Documentation: This file + inline comments

---

## 🔧 Troubleshooting

### Issue: "Import asyncpg could not be resolved"
**Solution**: Install asyncpg
```bash
pip install asyncpg
```

### Issue: Tenant config not updating
**Solution**: Invalidate cache
```python
from services.llm_gateway import get_tenant_router

router = await get_tenant_router()
router.invalidate_cache(tenant_id="...")
```

### Issue: No providers registered
**Solution**: Check tenant tokens and system environment variables
```python
# Verify tenant config
config = await router._load_tenant_config(tenant_id="...")
print(f"Tokens: {config['llm_tokens']}")

# Check system env vars
import os
print(f"System GROQ_API_KEY: {os.getenv('GROQ_API_KEY')[:10]}...")
```

### Issue: Usage not tracked
**Solution**: Check database connection and permissions
```sql
-- Verify table exists
SELECT COUNT(*) FROM model_usage_stats;

-- Check recent inserts
SELECT * FROM model_usage_stats ORDER BY timestamp DESC LIMIT 10;
```

---

**Phase 2 Complete** ✅  
**Next**: Phase 3 - Frontend UI Implementation
