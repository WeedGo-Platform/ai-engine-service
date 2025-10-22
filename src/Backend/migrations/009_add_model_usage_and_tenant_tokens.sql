-- Migration 009: Add model usage tracking and tenant LLM tokens
-- Date: 2025-10-21
-- Description: 
--   1. Add llm_tokens JSONB column to tenants table for per-tenant cloud provider API keys
--   2. Create model_usage_stats table for real-time model usage tracking
--   3. Add tenant inference configuration (provider preference, auto-failover)
--   4. Migrate existing system tokens to the first tenant

-- ============================================================================
-- PART 1: Add llm_tokens to tenants table
-- ============================================================================

-- Add llm_tokens JSONB column to store cloud provider API tokens
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS llm_tokens JSONB DEFAULT '{}'::jsonb;

-- Add inference configuration for per-tenant settings
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS inference_config JSONB DEFAULT '{
  "preferred_provider": "groq",
  "auto_failover": true,
  "provider_models": {
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "deepseek/deepseek-r1",
    "llm7": "gpt-4o-mini"
  }
}'::jsonb;

-- Add comments for documentation
COMMENT ON COLUMN tenants.llm_tokens IS 'Encrypted storage for tenant-specific cloud LLM provider API tokens (groq, openrouter, llm7)';
COMMENT ON COLUMN tenants.inference_config IS 'Tenant inference settings: preferred provider, auto-failover, and active models per provider';

-- ============================================================================
-- PART 2: Create model_usage_stats table for real-time tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Model & Provider Info
    provider VARCHAR(50) NOT NULL, -- 'groq', 'openrouter', 'llm7', 'local'
    model_name VARCHAR(255) NOT NULL,
    
    -- Request Metadata
    request_id VARCHAR(100),
    endpoint VARCHAR(100), -- '/api/chat', '/api/completion', etc.
    user_id UUID, -- Optional: which user made the request
    
    -- Timing
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latency_ms INTEGER, -- Response time in milliseconds
    
    -- Token Usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    
    -- Status
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'rate_limit', 'timeout'
    error_message TEXT,
    
    -- Cost Tracking (optional, for paid tiers)
    estimated_cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    
    -- Additional Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_model_usage_tenant_timestamp 
    ON model_usage_stats(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_usage_provider_model 
    ON model_usage_stats(provider, model_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_usage_status 
    ON model_usage_stats(status, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_usage_tenant_provider 
    ON model_usage_stats(tenant_id, provider, timestamp DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_model_usage_tenant_provider_status 
    ON model_usage_stats(tenant_id, provider, status, timestamp DESC);

-- Add table comment
COMMENT ON TABLE model_usage_stats IS 'Real-time tracking of all LLM model usage across local and cloud providers';
COMMENT ON COLUMN model_usage_stats.provider IS 'LLM provider: groq, openrouter, llm7, or local';
COMMENT ON COLUMN model_usage_stats.status IS 'Request outcome: success, error, rate_limit, timeout';
COMMENT ON COLUMN model_usage_stats.estimated_cost_usd IS 'Estimated cost in USD (for cost tracking and billing)';

-- ============================================================================
-- PART 3: Create materialized view for aggregated stats (performance)
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS model_usage_summary AS
SELECT 
    tenant_id,
    provider,
    model_name,
    DATE(timestamp) as usage_date,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status = 'success') as successful_requests,
    COUNT(*) FILTER (WHERE status = 'error') as failed_requests,
    COUNT(*) FILTER (WHERE status = 'rate_limit') as rate_limited_requests,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(total_tokens) as total_tokens,
    AVG(latency_ms) as avg_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms,
    SUM(estimated_cost_usd) as total_cost_usd,
    MIN(timestamp) as first_request_at,
    MAX(timestamp) as last_request_at
FROM model_usage_stats
GROUP BY tenant_id, provider, model_name, DATE(timestamp);

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_summary_unique 
    ON model_usage_summary(tenant_id, provider, model_name, usage_date);

COMMENT ON MATERIALIZED VIEW model_usage_summary IS 'Daily aggregated model usage statistics for dashboard performance';

-- ============================================================================
-- PART 4: Function to refresh materialized view (call via cron or trigger)
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_model_usage_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY model_usage_summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_model_usage_summary IS 'Refreshes the model usage summary materialized view. Run this periodically (e.g., every hour) via cron.';

-- ============================================================================
-- PART 5: Migrate existing system tokens to first tenant
-- ============================================================================

-- NOTE: This assumes environment variables are set:
-- GROQ_API_KEY, OPENROUTER_API_KEY, LLM7_API_KEY
-- You'll need to run a Python script to actually set these values from env vars

-- Create a placeholder migration function that will be called from Python
CREATE OR REPLACE FUNCTION migrate_system_tokens_to_tenant(
    p_tenant_id UUID,
    p_groq_key TEXT,
    p_openrouter_key TEXT,
    p_llm7_key TEXT
)
RETURNS void AS $$
BEGIN
    UPDATE tenants
    SET llm_tokens = jsonb_build_object(
        'groq', p_groq_key,
        'openrouter', p_openrouter_key,
        'llm7', p_llm7_key,
        'migrated_at', NOW()::text
    )
    WHERE id = p_tenant_id;
    
    RAISE NOTICE 'Migrated system tokens to tenant %', p_tenant_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_system_tokens_to_tenant IS 'Migrates system-level LLM tokens to a specific tenant. Called during initial setup.';

-- ============================================================================
-- PART 6: Helper function to track model usage (called from application)
-- ============================================================================

CREATE OR REPLACE FUNCTION track_model_usage(
    p_tenant_id UUID,
    p_provider VARCHAR(50),
    p_model_name VARCHAR(255),
    p_request_id VARCHAR(100),
    p_endpoint VARCHAR(100),
    p_user_id UUID,
    p_latency_ms INTEGER,
    p_input_tokens INTEGER,
    p_output_tokens INTEGER,
    p_status VARCHAR(20),
    p_error_message TEXT DEFAULT NULL,
    p_estimated_cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_usage_id UUID;
BEGIN
    INSERT INTO model_usage_stats (
        tenant_id,
        provider,
        model_name,
        request_id,
        endpoint,
        user_id,
        latency_ms,
        input_tokens,
        output_tokens,
        status,
        error_message,
        estimated_cost_usd,
        metadata
    ) VALUES (
        p_tenant_id,
        p_provider,
        p_model_name,
        p_request_id,
        p_endpoint,
        p_user_id,
        p_latency_ms,
        p_input_tokens,
        p_output_tokens,
        p_status,
        p_error_message,
        p_estimated_cost_usd,
        p_metadata
    )
    RETURNING id INTO v_usage_id;
    
    RETURN v_usage_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION track_model_usage IS 'Insert a model usage record. Called after each LLM request.';

-- ============================================================================
-- PART 7: View for real-time stats (last 24 hours)
-- ============================================================================

CREATE OR REPLACE VIEW model_usage_stats_24h AS
SELECT 
    tenant_id,
    provider,
    model_name,
    COUNT(*) as requests_24h,
    COUNT(*) FILTER (WHERE status = 'success') as successful_24h,
    COUNT(*) FILTER (WHERE status = 'rate_limit') as rate_limited_24h,
    SUM(total_tokens) as tokens_24h,
    AVG(latency_ms) as avg_latency_24h,
    SUM(estimated_cost_usd) as cost_24h
FROM model_usage_stats
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, provider, model_name;

COMMENT ON VIEW model_usage_stats_24h IS 'Real-time usage stats for the last 24 hours per tenant/provider/model';

-- ============================================================================
-- PART 8: Grant permissions
-- ============================================================================

-- Grant appropriate permissions (adjust based on your user roles)
GRANT SELECT, INSERT ON model_usage_stats TO weedgo;
GRANT SELECT ON model_usage_summary TO weedgo;
GRANT SELECT ON model_usage_stats_24h TO weedgo;
GRANT EXECUTE ON FUNCTION track_model_usage TO weedgo;
GRANT EXECUTE ON FUNCTION refresh_model_usage_summary TO weedgo;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tenants table has new columns
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'tenants' AND column_name IN ('llm_tokens', 'inference_config');

-- Verify model_usage_stats table exists
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'model_usage_stats';

-- Check indexes
-- SELECT indexname FROM pg_indexes WHERE tablename = 'model_usage_stats';

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================================

-- DROP VIEW IF EXISTS model_usage_stats_24h;
-- DROP MATERIALIZED VIEW IF EXISTS model_usage_summary;
-- DROP FUNCTION IF EXISTS track_model_usage;
-- DROP FUNCTION IF EXISTS refresh_model_usage_summary;
-- DROP FUNCTION IF EXISTS migrate_system_tokens_to_tenant;
-- DROP TABLE IF EXISTS model_usage_stats;
-- ALTER TABLE tenants DROP COLUMN IF EXISTS llm_tokens;
-- ALTER TABLE tenants DROP COLUMN IF EXISTS inference_config;
