-- Massive Database Cleanup Script
-- This script removes 78 empty tables and consolidates redundant structures
-- Created: 2025-09-17
-- IMPORTANT: Review before running in production!

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Drop ALL Empty Payment Tables (15 tables)
-- =========================================
DROP TABLE IF EXISTS payment_audit_log CASCADE;
DROP TABLE IF EXISTS payment_credentials CASCADE;
DROP TABLE IF EXISTS payment_disputes CASCADE;
DROP TABLE IF EXISTS payment_fee_splits CASCADE;
DROP TABLE IF EXISTS payment_idempotency_keys CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS payment_metrics CASCADE;
DROP TABLE IF EXISTS payment_provider_health_metrics CASCADE;
DROP TABLE IF EXISTS payment_providers CASCADE;
DROP TABLE IF EXISTS payment_refunds CASCADE;
DROP TABLE IF EXISTS payment_settlements CASCADE;
DROP TABLE IF EXISTS payment_subscriptions CASCADE;
-- Keep payment_transactions as it might be used
DROP TABLE IF EXISTS payment_webhook_routes CASCADE;
DROP TABLE IF EXISTS payment_webhooks CASCADE;

-- =========================================
-- STEP 2: Drop Empty Auth/Token Tables (5 tables)
-- =========================================
DROP TABLE IF EXISTS email_verification_tokens CASCADE;
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS refresh_tokens CASCADE;
DROP TABLE IF EXISTS token_blacklist CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;

-- =========================================
-- STEP 3: Drop Empty Pricing Tables (4 tables)
-- =========================================
DROP TABLE IF EXISTS price_tiers CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS dynamic_pricing_rules CASCADE;
DROP TABLE IF EXISTS customer_pricing_rules CASCADE;

-- =========================================
-- STEP 4: Drop Empty Review System Tables (4 tables)
-- =========================================
-- Keep product_ratings as it has data
DROP TABLE IF EXISTS customer_reviews CASCADE;
DROP TABLE IF EXISTS review_media CASCADE;
DROP TABLE IF EXISTS review_votes CASCADE;
DROP TABLE IF EXISTS review_attributes CASCADE;

-- =========================================
-- STEP 5: Drop Empty Discount/Promotion Tables (4 tables)
-- =========================================
DROP TABLE IF EXISTS discount_codes CASCADE;
DROP TABLE IF EXISTS discount_usage CASCADE;
DROP TABLE IF EXISTS promotions CASCADE;
DROP TABLE IF EXISTS promotion_usage CASCADE;

-- =========================================
-- STEP 6: Drop Empty Translation Tables (6 tables)
-- =========================================
DROP TABLE IF EXISTS translations CASCADE;
DROP TABLE IF EXISTS translation_batches CASCADE;
DROP TABLE IF EXISTS translation_batch_items CASCADE;
DROP TABLE IF EXISTS translation_overrides CASCADE;
DROP TABLE IF EXISTS supported_languages CASCADE;
DROP TABLE IF EXISTS skip_words CASCADE;

-- =========================================
-- STEP 7: Drop Empty AI/ML Tables (6 tables)
-- =========================================
DROP TABLE IF EXISTS model_versions CASCADE;
DROP TABLE IF EXISTS model_deployments CASCADE;
DROP TABLE IF EXISTS model_metrics CASCADE;
DROP TABLE IF EXISTS training_sessions CASCADE;
DROP TABLE IF EXISTS training_examples CASCADE;
DROP TABLE IF EXISTS ai_training_data CASCADE;
DROP TABLE IF EXISTS ai_personalities CASCADE;
DROP TABLE IF EXISTS parameter_accuracy CASCADE;

-- =========================================
-- STEP 8: Drop Empty Accessories Tables (3 tables)
-- =========================================
DROP TABLE IF EXISTS accessories_catalog CASCADE;
DROP TABLE IF EXISTS accessories_inventory CASCADE;
DROP TABLE IF EXISTS accessory_categories CASCADE;

-- =========================================
-- STEP 9: Drop Empty Store Configuration Tables (7 tables)
-- =========================================
DROP TABLE IF EXISTS store_regular_hours CASCADE;
DROP TABLE IF EXISTS store_special_hours CASCADE;
DROP TABLE IF EXISTS store_holiday_hours CASCADE;
DROP TABLE IF EXISTS store_hours_settings CASCADE;
DROP TABLE IF EXISTS store_compliance CASCADE;
DROP TABLE IF EXISTS store_ai_agents CASCADE;
DROP TABLE IF EXISTS holidays CASCADE;

-- =========================================
-- STEP 10: Drop Empty Inventory Tables (5 tables)
-- =========================================
DROP TABLE IF EXISTS ocs_inventory_movements CASCADE;
DROP TABLE IF EXISTS ocs_inventory_snapshots CASCADE;
DROP TABLE IF EXISTS ocs_inventory_reservations CASCADE;
DROP TABLE IF EXISTS inventory_locations CASCADE;
DROP TABLE IF EXISTS location_assignments_log CASCADE;

-- =========================================
-- STEP 11: Drop Empty Tenant Tables (6 tables)
-- =========================================
DROP TABLE IF EXISTS tenant_settings CASCADE;
DROP TABLE IF EXISTS tenant_features CASCADE;
DROP TABLE IF EXISTS tenant_subscriptions CASCADE;
DROP TABLE IF EXISTS tenant_payment_providers CASCADE;
DROP TABLE IF EXISTS tenant_settlement_accounts CASCADE;

-- =========================================
-- STEP 12: Drop Other Empty Tables
-- =========================================
DROP TABLE IF EXISTS bundle_deals CASCADE;
DROP TABLE IF EXISTS conversion_metrics CASCADE;
DROP TABLE IF EXISTS conversation_states CASCADE;
DROP TABLE IF EXISTS delivery_zones CASCADE;
DROP TABLE IF EXISTS product_recommendations CASCADE;
DROP TABLE IF EXISTS recommendation_metrics CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS shelf_locations CASCADE;
DROP TABLE IF EXISTS tax_rates CASCADE;
DROP TABLE IF EXISTS user_addresses CASCADE;
DROP TABLE IF EXISTS age_verification_logs CASCADE;

-- =========================================
-- STEP 13: Merge customer_profiles data into profiles
-- =========================================
-- First, add any missing columns to profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS face_template_hash TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS template_version TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS template_algorithm TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS visit_count INTEGER DEFAULT 0;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS total_purchase_amount NUMERIC(12,2) DEFAULT 0;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS estimated_age_range TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS estimated_gender TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS preferred_brands JSONB DEFAULT '[]'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS thc_preference_range JSONB;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS cbd_preference_range JSONB;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS price_sensitivity TEXT;

-- Migrate the one record from customer_profiles to profiles
UPDATE profiles p
SET
    face_template_hash = cp.face_template_hash,
    template_version = cp.template_version,
    template_algorithm = cp.template_algorithm,
    visit_count = COALESCE(cp.visit_count, 0),
    total_purchase_amount = COALESCE(cp.total_purchase_amount, 0),
    consent_given = COALESCE(cp.consent_given, false),
    consent_date = cp.consent_date,
    estimated_age_range = cp.estimated_age_range,
    estimated_gender = cp.estimated_gender,
    preferred_brands = COALESCE(cp.preferred_brands, '[]'::jsonb),
    thc_preference_range = cp.thc_preference_range,
    cbd_preference_range = cp.cbd_preference_range,
    price_sensitivity = cp.price_sensitivity,
    preferences = COALESCE(p.preferences, '{}')::jsonb || COALESCE(cp.preferences, '{}')::jsonb,
    purchase_history = COALESCE(p.purchase_history, '[]')::jsonb || COALESCE(cp.purchase_history, '[]')::jsonb,
    interaction_count = GREATEST(COALESCE(p.interaction_count, 0), COALESCE(cp.interaction_count, 0))
FROM customer_profiles cp
WHERE p.id::text = cp.customer_id;

-- Now drop customer_profiles
DROP TABLE IF EXISTS customer_profiles CASCADE;

-- =========================================
-- STEP 14: Drop user_profiles (empty and redundant)
-- =========================================
DROP TABLE IF EXISTS user_profiles CASCADE;

-- =========================================
-- STEP 15: Remove customers table (replaced by profiles)
-- =========================================
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
WHERE NOT EXISTS (
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
-- STEP 16: Consolidate Login Tracking
-- =========================================
-- Merge login_attempts into user_login_logs
INSERT INTO user_login_logs (
    user_id, email, ip_address, user_agent,
    login_successful, failure_reason,
    created_at
)
SELECT
    NULL as user_id,
    email,
    ip_address,
    user_agent,
    false as login_successful,
    error_message as failure_reason,
    attempt_time as created_at
FROM login_attempts;

-- Drop login_attempts
DROP TABLE IF EXISTS login_attempts CASCADE;

-- =========================================
-- STEP 17: Drop Redundant Views
-- =========================================
DROP VIEW IF EXISTS admin_users CASCADE;
DROP VIEW IF EXISTS customer_users CASCADE;
DROP VIEW IF EXISTS recent_login_activity CASCADE;

-- =========================================
-- VERIFICATION
-- =========================================
DO $$
DECLARE
    table_count INTEGER;
    empty_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO empty_count
    FROM (
        SELECT table_name
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND (xpath('/row/count/text()',
            query_to_xml(format('SELECT COUNT(*) FROM %I.%I', 'public', t.table_name),
            false, true, ''))::text[])[1]::bigint = 0
    ) empty_tables;

    RAISE NOTICE 'Cleanup complete!';
    RAISE NOTICE 'Tables remaining: %', table_count;
    RAISE NOTICE 'Empty tables remaining: %', empty_count;

    IF empty_count > 10 THEN
        RAISE WARNING 'Still have % empty tables to review', empty_count;
    END IF;
END $$;

COMMIT;

-- =========================================
-- ROLLBACK PLAN
-- =========================================
-- This cleanup is aggressive. Before running:
-- 1. Take a full database backup
-- 2. Test in development first
-- 3. Review each section carefully
--
-- To restore:
-- pg_restore -d ai_engine backup_before_cleanup.sql