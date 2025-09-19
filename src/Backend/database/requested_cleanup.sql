-- Database Cleanup Script - Following Exact Instructions Only
-- This script removes ONLY the tables explicitly requested by the user
-- Created: 2025-09-17

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Merge customer_profiles data into profiles
-- =========================================
-- Add last_interaction column if needed
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_interaction TIMESTAMP;

-- Migrate the one record from customer_profiles to profiles
-- customer_profiles only has: preferences, purchase_history, interaction_count, last_interaction
UPDATE profiles p
SET
    preferences = COALESCE(p.preferences, '{}')::jsonb || COALESCE(cp.preferences, '{}')::jsonb,
    purchase_history = COALESCE(p.purchase_history, '[]')::jsonb || COALESCE(cp.purchase_history, '[]')::jsonb,
    interaction_count = GREATEST(COALESCE(p.interaction_count, 0), COALESCE(cp.interaction_count, 0)),
    last_interaction = cp.last_interaction
FROM customer_profiles cp
WHERE p.id::text = cp.customer_id;

-- Now drop customer_profiles
DROP TABLE IF EXISTS customer_profiles CASCADE;

-- =========================================
-- STEP 2: Drop user_profiles (empty and redundant)
-- =========================================
DROP TABLE IF EXISTS user_profiles CASCADE;

-- =========================================
-- STEP 3: Remove customers table (replaced by profiles)
-- =========================================
-- Delete orphaned customers with no user_id first
DELETE FROM customers WHERE user_id IS NULL;

-- First ensure all data is in profiles
INSERT INTO profiles (
    user_id, first_name, last_name, phone, date_of_birth,
    address, city, state, postal_code, country,
    loyalty_points, customer_type, preferred_payment_method,
    total_spent, order_count, last_order_date,
    marketing_consent, sms_consent, tags, notes, is_verified,
    created_at, updated_at
)
SELECT
    c.user_id, c.first_name, c.last_name, c.phone, c.date_of_birth,
    c.address, c.city, c.state, c.postal_code, c.country,
    c.loyalty_points, c.customer_type, c.preferred_payment_method,
    c.total_spent, c.order_count, c.last_order_date,
    c.marketing_consent, c.sms_consent, c.tags, c.notes, c.is_verified,
    c.created_at, c.updated_at
FROM customers c
WHERE c.user_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM profiles p WHERE p.user_id = c.user_id
);

-- Update any orphaned customer references in orders to use user_id
UPDATE orders o
SET user_id = c.user_id
FROM customers c
WHERE o.customer_id = c.id
AND o.user_id IS NULL;

-- Drop customers table and its view
DROP VIEW IF EXISTS customers_view CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- =========================================
-- STEP 4: Delete Empty Tenant Tables
-- =========================================
DROP TABLE IF EXISTS tenant_settings CASCADE;
DROP TABLE IF EXISTS tenant_features CASCADE;
DROP TABLE IF EXISTS tenant_subscriptions CASCADE;
DROP TABLE IF EXISTS tenant_payment_providers CASCADE;
DROP TABLE IF EXISTS tenant_settlement_accounts CASCADE;

-- =========================================
-- STEP 5: Consolidate Inventory Tables
-- =========================================
-- Keep only ocs_inventory (main) and ocs_inventory_logs (tracking)
-- Drop the empty inventory management tables
DROP TABLE IF EXISTS ocs_inventory_movements CASCADE;
DROP TABLE IF EXISTS ocs_inventory_snapshots CASCADE;
DROP TABLE IF EXISTS ocs_inventory_reservations CASCADE;
DROP TABLE IF EXISTS inventory_locations CASCADE;
DROP TABLE IF EXISTS location_assignments_log CASCADE;

-- =========================================
-- STEP 6: Unify Login Tracking
-- =========================================
-- Add columns to user_login_logs if they don't exist
ALTER TABLE user_login_logs ADD COLUMN IF NOT EXISTS failure_reason TEXT;

-- Merge login_attempts into user_login_logs
INSERT INTO user_login_logs (
    user_id, ip_address, user_agent,
    login_successful, failure_reason,
    login_timestamp
)
SELECT
    user_id,
    ip_address::inet,
    user_agent,
    success as login_successful,
    error_message as failure_reason,
    timestamp as login_timestamp
FROM login_attempts;

-- Drop login_attempts
DROP TABLE IF EXISTS login_attempts CASCADE;

-- =========================================
-- VERIFICATION
-- =========================================
DO $$
DECLARE
    table_count INTEGER;
    profiles_count INTEGER;
    orders_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO profiles_count
    FROM profiles;

    SELECT COUNT(*) INTO orders_count
    FROM orders;

    RAISE NOTICE 'Cleanup complete!';
    RAISE NOTICE 'Tables remaining: %', table_count;
    RAISE NOTICE 'Profiles records: %', profiles_count;
    RAISE NOTICE 'Orders records: %', orders_count;
END $$;

COMMIT;

-- =========================================
-- ROLLBACK PLAN
-- =========================================
-- This cleanup follows user's explicit instructions only.
-- Before running:
-- 1. Take a full database backup
-- 2. Test in development first
--
-- To restore:
-- pg_restore -d ai_engine backup_before_cleanup.sql