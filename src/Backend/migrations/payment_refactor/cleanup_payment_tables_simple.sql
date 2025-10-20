-- Simple Payment Tables Cleanup
-- Removes orphaned payment tables, leaves 6 core tables
-- Date: 2025-01-19

BEGIN;

-- Step 1: Drop the 10 orphaned tables that are no longer used
DROP TABLE IF EXISTS payment_fee_splits CASCADE;
DROP TABLE IF EXISTS payment_settlements CASCADE;
DROP TABLE IF EXISTS payment_metrics CASCADE;
DROP TABLE IF EXISTS payment_provider_health_metrics CASCADE;
DROP TABLE IF EXISTS payment_subscriptions CASCADE;
DROP TABLE IF EXISTS payment_disputes CASCADE;
DROP TABLE IF EXISTS payment_webhook_routes CASCADE;
DROP TABLE IF EXISTS payment_idempotency_keys CASCADE;
DROP TABLE IF EXISTS payment_audit_log CASCADE;
DROP TABLE IF EXISTS payment_credentials CASCADE;

-- Step 2: Drop tenant_payment_providers (will be replaced by store_payment_providers)
DROP TABLE IF EXISTS tenant_payment_providers CASCADE;

-- Step 3: Check remaining tables
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public'
ORDER BY tablename;

-- Step 4: Create store_payment_providers if it doesn't exist
CREATE TABLE IF NOT EXISTS store_payment_providers (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    store_id UUID REFERENCES stores(id) NOT NULL,
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,

    -- Credentials (merged from payment_credentials table)
    credentials_encrypted TEXT,
    encryption_metadata JSONB NOT NULL DEFAULT '{}',

    -- Configuration
    configuration JSONB DEFAULT '{}',
    oauth_tokens JSONB, -- For Clover OAuth flow

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,

    -- Constraints
    UNIQUE(store_id, provider_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_store_active ON store_payment_providers(store_id, is_active);
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_default ON store_payment_providers(is_default) WHERE is_default = true;
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_store ON store_payment_providers(store_id);

COMMIT;

-- Summary
SELECT
    COUNT(*) AS payment_tables_count,
    string_agg(tablename, ', ' ORDER BY tablename) AS tables
FROM pg_tables
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public';
