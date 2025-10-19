-- Migration: 999_rollback.sql
-- Purpose: Rollback payment refactor to original schema
-- Date: 2025-01-18
-- WARNING: Only use this if migration failed or needs to be reverted

BEGIN;

-- ============================================================================
-- STEP 1: Drop new tables
-- ============================================================================

DROP TABLE IF EXISTS payment_refunds CASCADE;
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS payment_webhooks CASCADE;
DROP TABLE IF EXISTS store_payment_providers CASCADE;
DROP TABLE IF EXISTS payment_providers CASCADE;

RAISE NOTICE 'Dropped new payment tables';

-- ============================================================================
-- STEP 2: Restore from backups
-- ============================================================================

-- Restore core tables
CREATE TABLE payment_providers AS SELECT * FROM payment_backup.payment_providers;
CREATE TABLE payment_transactions AS SELECT * FROM payment_backup.payment_transactions;
CREATE TABLE payment_methods AS SELECT * FROM payment_backup.payment_methods;
CREATE TABLE tenant_payment_providers AS SELECT * FROM payment_backup.tenant_payment_providers;
CREATE TABLE payment_refunds AS SELECT * FROM payment_backup.payment_refunds;
CREATE TABLE payment_webhooks AS SELECT * FROM payment_backup.payment_webhooks;

-- Restore removed tables
CREATE TABLE payment_fee_splits AS SELECT * FROM payment_backup.payment_fee_splits;
CREATE TABLE payment_settlements AS SELECT * FROM payment_backup.payment_settlements;
CREATE TABLE payment_metrics AS SELECT * FROM payment_backup.payment_metrics;
CREATE TABLE payment_provider_health_metrics AS SELECT * FROM payment_backup.payment_provider_health_metrics;
CREATE TABLE payment_subscriptions AS SELECT * FROM payment_backup.payment_subscriptions;
CREATE TABLE payment_disputes AS SELECT * FROM payment_backup.payment_disputes;
CREATE TABLE payment_webhook_routes AS SELECT * FROM payment_backup.payment_webhook_routes;
CREATE TABLE payment_idempotency_keys AS SELECT * FROM payment_backup.payment_idempotency_keys;
CREATE TABLE payment_audit_log AS SELECT * FROM payment_backup.payment_audit_log;
CREATE TABLE payment_credentials AS SELECT * FROM payment_backup.payment_credentials;

RAISE NOTICE 'Restored all 16 payment tables from backups';

-- ============================================================================
-- STEP 3: Recreate primary keys and constraints
-- ============================================================================

-- You'll need to add back all original constraints here
-- This is a simplified version - full constraints would need to be restored
ALTER TABLE payment_providers ADD PRIMARY KEY (id);
ALTER TABLE payment_transactions ADD PRIMARY KEY (id);
ALTER TABLE payment_methods ADD PRIMARY KEY (id);
ALTER TABLE payment_refunds ADD PRIMARY KEY (id);
ALTER TABLE payment_webhooks ADD PRIMARY KEY (id);

RAISE NOTICE 'Recreated primary keys';

-- ============================================================================
-- STEP 4: Log rollback
-- ============================================================================

INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('999_rollback', 'completed', NOW(), NOW());

COMMIT;

-- Verification
SELECT
    tablename
FROM pg_tables
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public'
ORDER BY tablename;

SELECT 'Rollback completed. All 16 payment tables restored from backups.' AS message;
