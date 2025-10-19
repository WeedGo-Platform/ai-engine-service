-- Migration: 001_backup_payment_schema.sql
-- Purpose: Backup existing payment tables before refactoring
-- Date: 2025-01-18
-- Status: Safe to run (no data loss)

BEGIN;

-- Create backup schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS payment_backup;

-- Backup all 16 existing payment tables (even though they're empty)
-- This allows rollback if needed

-- 1. Core tables
CREATE TABLE payment_backup.payment_transactions AS SELECT * FROM payment_transactions;
CREATE TABLE payment_backup.payment_providers AS SELECT * FROM payment_providers;
CREATE TABLE payment_backup.payment_methods AS SELECT * FROM payment_methods;
CREATE TABLE payment_backup.tenant_payment_providers AS SELECT * FROM tenant_payment_providers;
CREATE TABLE payment_backup.payment_refunds AS SELECT * FROM payment_refunds;
CREATE TABLE payment_backup.payment_webhooks AS SELECT * FROM payment_webhooks;

-- 2. Tables being removed
CREATE TABLE payment_backup.payment_fee_splits AS SELECT * FROM payment_fee_splits;
CREATE TABLE payment_backup.payment_settlements AS SELECT * FROM payment_settlements;
CREATE TABLE payment_backup.payment_metrics AS SELECT * FROM payment_metrics;
CREATE TABLE payment_backup.payment_provider_health_metrics AS SELECT * FROM payment_provider_health_metrics;
CREATE TABLE payment_backup.payment_subscriptions AS SELECT * FROM payment_subscriptions;
CREATE TABLE payment_backup.payment_disputes AS SELECT * FROM payment_disputes;
CREATE TABLE payment_backup.payment_webhook_routes AS SELECT * FROM payment_webhook_routes;
CREATE TABLE payment_backup.payment_idempotency_keys AS SELECT * FROM payment_idempotency_keys;
CREATE TABLE payment_backup.payment_audit_log AS SELECT * FROM payment_audit_log;
CREATE TABLE payment_backup.payment_credentials AS SELECT * FROM payment_credentials;

-- Create migration log table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log migration start
INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('001_backup_payment_schema', 'completed', NOW(), NOW());

-- Verification: Count rows in each backup table
DO $$
DECLARE
    backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO backup_count FROM payment_backup.payment_transactions;
    RAISE NOTICE 'Backed up % payment_transactions rows', backup_count;

    SELECT COUNT(*) INTO backup_count FROM payment_backup.payment_providers;
    RAISE NOTICE 'Backed up % payment_providers rows', backup_count;

    SELECT COUNT(*) INTO backup_count FROM payment_backup.payment_methods;
    RAISE NOTICE 'Backed up % payment_methods rows', backup_count;
END $$;

COMMIT;

-- Success message
SELECT 'Migration 001_backup_payment_schema completed successfully. All 16 payment tables backed up to payment_backup schema.' AS message;
