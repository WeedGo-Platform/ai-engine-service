-- Migration: 002_drop_deprecated_payment_tables.sql
-- Purpose: Drop 10 deprecated payment tables that are not needed for cannabis retail POS
-- Date: 2025-01-18
-- WARNING: This drops tables permanently. Run 001_backup_payment_schema.sql first!

BEGIN;

-- Drop tables in dependency order (children first, parents last)
-- This handles foreign key constraints properly

-- 1. Drop fee/settlement related tables
DROP TABLE IF EXISTS payment_fee_splits CASCADE;
RAISE NOTICE 'Dropped payment_fee_splits - fee structure removed (not needed for transaction processing)';

DROP TABLE IF EXISTS payment_settlements CASCADE;
RAISE NOTICE 'Dropped payment_settlements - settlements handled by payment processors';

-- 2. Drop over-engineered monitoring tables
DROP TABLE IF EXISTS payment_metrics CASCADE;
RAISE NOTICE 'Dropped payment_metrics - can be calculated from payment_transactions via analytics queries';

DROP TABLE IF EXISTS payment_provider_health_metrics CASCADE;
RAISE NOTICE 'Dropped payment_provider_health_metrics - over-engineering for 3 providers, use manual monitoring';

-- 3. Drop unused feature tables
DROP TABLE IF EXISTS payment_subscriptions CASCADE;
RAISE NOTICE 'Dropped payment_subscriptions - cannabis retail does not use subscription billing';

DROP TABLE IF EXISTS payment_disputes CASCADE;
RAISE NOTICE 'Dropped payment_disputes - can be handled via payment_transactions status field';

-- 4. Drop redundant configuration tables
DROP TABLE IF EXISTS payment_webhook_routes CASCADE;
RAISE NOTICE 'Dropped payment_webhook_routes - routes can be stored in provider configuration JSONB';

-- 5. Drop redundant tracking tables
DROP TABLE IF EXISTS payment_idempotency_keys CASCADE;
RAISE NOTICE 'Dropped payment_idempotency_keys - idempotency_key is already a column in payment_transactions';

DROP TABLE IF EXISTS payment_audit_log CASCADE;
RAISE NOTICE 'Dropped payment_audit_log - application logging + payment_transactions + payment_webhooks is sufficient';

-- 6. Drop credentials table (will be merged into store_payment_providers)
DROP TABLE IF EXISTS payment_credentials CASCADE;
RAISE NOTICE 'Dropped payment_credentials - credentials will be merged into store_payment_providers table';

-- Log migration
INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('002_drop_deprecated_payment_tables', 'completed', NOW(), NOW());

COMMIT;

-- Verification: Check remaining payment tables
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public'
ORDER BY tablename;

-- Success message
SELECT 'Migration 002_drop_deprecated_payment_tables completed successfully. 10 deprecated tables removed. Remaining: payment_transactions, payment_providers, payment_methods, payment_refunds, payment_webhooks, tenant_payment_providers.' AS message;
