# Per-Tenant LLM Configuration Implementation - Phase 1 Complete

## Overview
Implemented per-tenant LLM provider configuration with token management, model selection, and real-time usage tracking infrastructure.

## Completed (Phase 1 of 3)

### ✅ Database Schema
**Migration 009** - `009_add_model_usage_and_tenant_tokens.sql`

#### New Tables
1. **`model_usage_stats`** - Real-time request tracking
   - Tracks every LLM request with full metrics
   - Columns: tenant_id, provider, model_name, tokens, latency, status, cost
   - Indexes optimized for dashboard queries
   
2. **Materialized View: `model_usage_summary`**
   - Daily aggregated statistics for performance
   - Refresh via: `SELECT refresh_model_usage_summary();`
   - Recommended: Hourly cron job
   
3. **View: `model_usage_stats_24h`**
   - Real-time stats for last 24 hours
   - Per tenant/provider/model breakdown

#### Updated Tables
1. **`tenants.llm_tokens`** (JSONB)
   - Secure storage for provider API keys
   - Structure: `{"groq": "gsk_...", "openrouter": "sk-or-...", "llm7": "..."}`
   - Migrated existing system tokens to first tenant
   
2. **`tenants.inference_config`** (JSONB)
   - Provider preferences and model selection
   - Default structure:
   ```json
   {
     "preferred_provider": "groq",
     "auto_failover": true,
     "provider_models": {
       "groq": "llama-3.3-70b-versatile",
       "openrouter": "deepseek/deepseek-r1",
       "llm7": "gpt-4o-mini"
     }
   }
   ```

#### Helper Functions
- `track_model_usage()` - Insert usage record
- `migrate_system_tokens_to_tenant()` - One-time migration
- `refresh_model_usage_summary()` - Update materialized view

### ✅ Backend API Endpoints
**File**: `src/Backend/api/tenant_llm_config.py`

#### Token Management
- `GET /api/tenants/{tenant_id}/llm-tokens`
  - Returns which tokens are configured (not the actual tokens)
  - Security: Never exposes actual API keys
  
- `PUT /api/tenants/{tenant_id}/llm-tokens`
  - Update provider tokens (groq, openrouter, llm7)
  - Validates token format before saving
  - Only updates provided tokens, leaves others unchanged
  
- `POST /api/tenants/{tenant_id}/llm-tokens/test`
  - Test token validity before saving
  - Makes actual API call to verify
  - Returns: valid boolean, message, details

#### Inference Configuration
- `GET /api/tenants/{tenant_id}/inference-config`
  - Get current provider preference and model selection
  - Returns auto-failover setting
  
- `PUT /api/tenants/{tenant_id}/inference-config`
  - Update preferred provider
  - Set active model per provider
  - Toggle auto-failover on/off

#### Model Information
- `GET /api/tenants/{tenant_id}/available-models`
  - Lists all available models per provider
  - Includes model metadata (context length, speed)

### ✅ Frontend Fixes
**File**: `src/Frontend/ai-admin-dashboard/src/components/aiManagement/InferenceTab.tsx`

- Fixed endpoint URL: `/api/admin/router/model-config` → `/api/admin/router/models/config`
- Fixed toggle response handling: `data.status === 'success'` → `data.success`
- Made model configuration display read-only (waiting for Phase 2 router integration)

## Architecture Decisions

### Security
- **Token Storage**: Never return actual tokens via API (security best practice)
- **Token Validation**: Test tokens before saving to prevent invalid configs
- **Per-Tenant Isolation**: Each tenant manages their own tokens

### Performance
- **Materialized View**: Pre-aggregated daily stats for fast dashboard loading
- **Real-time View**: Last 24h stats computed on-the-fly
- **Indexed Queries**: Optimized for common query patterns

### Scalability
- **Real-time Tracking**: Every request logged asynchronously
- **Aggregation Strategy**: Hourly materialized view refresh keeps dashboard fast
- **Storage Growth**: Automatic cleanup strategy needed (future enhancement)

## Remaining Work (Phase 2 & 3)

### Phase 2: Router Integration & Usage Tracking
1. **Update LLM Router** (`core/llm/llm_router_v5.py`)
   - Load tenant-specific tokens from database
   - Respect tenant's preferred provider
   - Auto-failover on rate limits (if enabled)
   - Pass requests to usage tracking service

2. **Create Usage Tracking Service** (`services/model_usage_tracker.py`)
   - Async tracking to avoid blocking requests
   - Call `track_model_usage()` function
   - Calculate costs based on token usage
   - Handle errors gracefully

3. **Provider Rate Limit Monitoring**
   - Track requests per provider per tenant
   - Detect approaching rate limits (e.g., 80% of daily quota)
   - Trigger auto-failover to next provider

### Phase 3: Frontend UI
1. **Token Management Section**
   - Input fields for Groq, OpenRouter, LLM7 tokens
   - "Test Token" button per provider
   - "Save Tokens" with validation feedback
   - Show which tokens are configured

2. **Provider Selection**
   - Radio buttons or cards for provider selection
   - Model dropdown per provider
   - "Auto-failover on rate limit" checkbox
   - Current selection highlighted

3. **Usage Stats Dashboard**
   - Charts showing requests over time
   - Tokens used per model/provider
   - Latency metrics
   - Cost tracking
   - Rate limit status

## Testing

### Database Migration
```bash
cd src/Backend
python3 migrations/run_009_migration.py
```

**Result**: ✅ Migration successful
- Tenant found: Pot Palace Cannabis (ID: 9a7585bf-5156-4fc2-971b-fcf00e174b88)
- Tokens migrated (will be set via UI since env vars not set)

### Verify Schema
```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'tenants' 
AND column_name IN ('llm_tokens', 'inference_config');

-- Check table created
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'model_usage_stats';

-- Check indexes
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'model_usage_stats';
```

### Test Endpoints (After Backend Restart)
```bash
# Get token status
curl http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/llm-tokens

# Update tokens
curl -X PUT http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/llm-tokens \
  -H "Content-Type: application/json" \
  -d '{"groq": "gsk_YOUR_KEY_HERE"}'

# Test token
curl -X POST http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/llm-tokens/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq", "api_key": "gsk_YOUR_KEY_HERE"}'

# Get inference config
curl http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/inference-config

# Update config
curl -X PUT http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/inference-config \
  -H "Content-Type: application/json" \
  -d '{"preferred_provider": "groq", "auto_failover": true, "provider_models": {"groq": "llama-3.3-70b-versatile"}}'

# Get available models
curl http://localhost:5024/api/tenants/9a7585bf-5156-4fc2-971b-fcf00e174b88/available-models
```

## Files Changed

### Backend
- ✅ `src/Backend/migrations/009_add_model_usage_and_tenant_tokens.sql` - Database schema
- ✅ `src/Backend/migrations/run_009_migration.py` - Migration script
- ✅ `src/Backend/api/tenant_llm_config.py` - New endpoint file
- ✅ `src/Backend/api_server.py` - Registered new router

### Frontend
- ✅ `src/Frontend/ai-admin-dashboard/src/components/aiManagement/InferenceTab.tsx` - Bug fixes

## Next Steps

1. **Start Backend Server** with new endpoints:
   ```bash
   cd src/Backend
   python3 -m uvicorn api_server:app --reload --port 5024
   ```

2. **Test Token Management Endpoints** via curl or Postman

3. **Implement Phase 2**: Router integration and usage tracking

4. **Build Phase 3 UI**: Token management and usage dashboard

5. **Set up Cron Job** for materialized view refresh:
   ```bash
   # Add to crontab
   0 * * * * psql -h localhost -p 5434 -U weedgo -d ai_engine -c 'SELECT refresh_model_usage_summary();'
   ```

## Notes

- Token validation uses httpx to make actual API calls
- All database operations use asyncpg for async/await support
- Pydantic models provide automatic validation
- JSONB fields allow flexible schema evolution
- Indexes optimized for dashboard query patterns

## Security Considerations

- ⚠️ Tokens stored in plain text in database (consider encryption at rest)
- ✅ Tokens never returned via API (only status)
- ✅ Token validation prevents saving invalid keys
- ✅ Per-tenant isolation enforced at database level

## Performance Monitoring

Track these metrics after Phase 2 implementation:
- Request latency impact from usage tracking
- Database size growth rate
- Materialized view refresh time
- Cache hit rates

---

**Status**: Phase 1 Complete ✅  
**Next**: Phase 2 - Router Integration  
**Date**: October 21, 2025
