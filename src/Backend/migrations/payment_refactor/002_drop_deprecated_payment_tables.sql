-- Migration: 002_drop_deprecated_payment_tables.sql
-- Purpose: Drop 10 deprecated payment tables that are not needed for cannabis retail POS
-- Date: 2025-01-18
-- WARNING: This drops tables permanently. Run 001_backup_payment_schema.sql first!

BEGIN;

-- Drop tables in dependency order (children first, parents last)
-- This handles foreign key constraints properly

-- 1. Drop fee/settlement related tables
DROP TABLE IF EXISTS payment_fee_splits CASCADE;
DROP TABLE IF EXISTS payment_settlements CASCADE;

-- 2. Drop over-engineered monitoring tables
DROP TABLE IF EXISTS payment_metrics CASCADE;
DROP TABLE IF EXISTS payment_provider_health_metrics CASCADE;

-- 3. Drop unused feature tables
DROP TABLE IF EXISTS payment_subscriptions CASCADE;
DROP TABLE IF EXISTS payment_disputes CASCADE;

-- 4. Drop redundant configuration tables
DROP TABLE IF EXISTS payment_webhook_routes CASCADE;

-- 5. Drop redundant tracking tables
DROP TABLE IF EXISTS payment_idempotency_keys CASCADE;
DROP TABLE IF EXISTS payment_audit_log CASCADE;

-- 6. Drop credentials table (will be merged into store_payment_providers)
DROP TABLE IF EXISTS payment_credentials CASCADE;

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
