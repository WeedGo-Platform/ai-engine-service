-- =====================================================
-- PURGE ALL DATA FROM DATABASE
-- This script will DELETE ALL DATA but preserve schema
-- Date: 2025-01-11
-- =====================================================

-- Disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- Start transaction
BEGIN;

-- Truncate all tables with CASCADE to handle foreign keys
-- This will reset all auto-increment sequences as well

-- Core Business Tables
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE products_complete CASCADE;
TRUNCATE TABLE product_catalog_ocs CASCADE;
TRUNCATE TABLE inventory CASCADE;
TRUNCATE TABLE store_inventory CASCADE;
TRUNCATE TABLE inventory_movements CASCADE;
TRUNCATE TABLE inventory_transactions CASCADE;
TRUNCATE TABLE inventory_reservations CASCADE;
TRUNCATE TABLE inventory_snapshots CASCADE;

-- Purchase Orders
TRUNCATE TABLE purchase_orders CASCADE;
TRUNCATE TABLE purchase_order_items CASCADE;
TRUNCATE TABLE suppliers CASCADE;

-- Promotions & Pricing
TRUNCATE TABLE promotions CASCADE;
TRUNCATE TABLE promotion_usage CASCADE;
TRUNCATE TABLE discount_codes CASCADE;
TRUNCATE TABLE discount_usage CASCADE;
TRUNCATE TABLE bundle_deals CASCADE;
TRUNCATE TABLE price_tiers CASCADE;
TRUNCATE TABLE price_history CASCADE;
TRUNCATE TABLE dynamic_pricing_rules CASCADE;
TRUNCATE TABLE customer_pricing_rules CASCADE;

-- Accessories
TRUNCATE TABLE accessories_catalog CASCADE;
TRUNCATE TABLE accessories_inventory CASCADE;
TRUNCATE TABLE accessory_categories CASCADE;

-- Cart & Checkout
TRUNCATE TABLE cart_sessions CASCADE;
TRUNCATE TABLE checkout_sessions CASCADE;

-- Customers
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE customer_profiles CASCADE;
TRUNCATE TABLE user_addresses CASCADE;

-- Users & Auth
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE user_profiles CASCADE;
TRUNCATE TABLE user_sessions CASCADE;
TRUNCATE TABLE tenant_users CASCADE;
TRUNCATE TABLE store_users CASCADE;
TRUNCATE TABLE login_attempts CASCADE;
TRUNCATE TABLE otp_codes CASCADE;
TRUNCATE TABLE otp_rate_limits CASCADE;
TRUNCATE TABLE email_verification_tokens CASCADE;
TRUNCATE TABLE password_reset_tokens CASCADE;
TRUNCATE TABLE token_blacklist CASCADE;
TRUNCATE TABLE api_keys CASCADE;

-- Voice Auth
TRUNCATE TABLE voice_profiles CASCADE;
TRUNCATE TABLE voice_auth_logs CASCADE;

-- Age Verification
TRUNCATE TABLE age_verification_logs CASCADE;

-- Roles & Permissions
TRUNCATE TABLE role_permissions CASCADE;

-- Tenants & Stores
TRUNCATE TABLE tenants CASCADE;
TRUNCATE TABLE stores CASCADE;
TRUNCATE TABLE store_settings CASCADE;
TRUNCATE TABLE store_hours_settings CASCADE;
TRUNCATE TABLE store_regular_hours CASCADE;
TRUNCATE TABLE store_special_hours CASCADE;
TRUNCATE TABLE store_holiday_hours CASCADE;
TRUNCATE TABLE store_compliance CASCADE;
TRUNCATE TABLE store_ai_agents CASCADE;
TRUNCATE TABLE tenant_settings CASCADE;
TRUNCATE TABLE tenant_features CASCADE;
TRUNCATE TABLE tenant_subscriptions CASCADE;

-- Payment System
TRUNCATE TABLE payment_transactions CASCADE;
TRUNCATE TABLE payment_methods CASCADE;
TRUNCATE TABLE payment_providers CASCADE;
TRUNCATE TABLE payment_credentials CASCADE;
TRUNCATE TABLE payment_settlements CASCADE;
TRUNCATE TABLE payment_webhooks CASCADE;
TRUNCATE TABLE payment_webhook_routes CASCADE;
TRUNCATE TABLE payment_refunds CASCADE;
TRUNCATE TABLE payment_disputes CASCADE;
TRUNCATE TABLE payment_subscriptions CASCADE;
TRUNCATE TABLE payment_audit_log CASCADE;
TRUNCATE TABLE payment_metrics CASCADE;
TRUNCATE TABLE payment_fee_splits CASCADE;
TRUNCATE TABLE payment_idempotency_keys CASCADE;
TRUNCATE TABLE payment_provider_health_metrics CASCADE;
TRUNCATE TABLE tenant_payment_providers CASCADE;
TRUNCATE TABLE tenant_settlement_accounts CASCADE;

-- POS
TRUNCATE TABLE pos_transactions CASCADE;

-- AI & Analytics
TRUNCATE TABLE ai_conversations CASCADE;
TRUNCATE TABLE ai_personalities CASCADE;
TRUNCATE TABLE ai_training_data CASCADE;
TRUNCATE TABLE chat_interactions CASCADE;
TRUNCATE TABLE conversation_states CASCADE;
TRUNCATE TABLE recommendation_metrics CASCADE;
TRUNCATE TABLE product_recommendations CASCADE;
TRUNCATE TABLE conversion_metrics CASCADE;
TRUNCATE TABLE training_sessions CASCADE;
TRUNCATE TABLE training_examples CASCADE;
TRUNCATE TABLE model_deployments CASCADE;
TRUNCATE TABLE model_versions CASCADE;
TRUNCATE TABLE model_metrics CASCADE;
TRUNCATE TABLE parameter_accuracy CASCADE;

-- Translations
TRUNCATE TABLE translations CASCADE;
TRUNCATE TABLE translation_batches CASCADE;
TRUNCATE TABLE translation_batch_items CASCADE;
TRUNCATE TABLE translation_overrides CASCADE;
TRUNCATE TABLE supported_languages CASCADE;

-- Other
TRUNCATE TABLE provinces_territories CASCADE;
TRUNCATE TABLE holidays CASCADE;
TRUNCATE TABLE delivery_zones CASCADE;
TRUNCATE TABLE tax_rates CASCADE;
TRUNCATE TABLE audit_log CASCADE;
TRUNCATE TABLE communication_logs CASCADE;
TRUNCATE TABLE batch_tracking CASCADE;
TRUNCATE TABLE asn_import_staging CASCADE;
TRUNCATE TABLE skip_words CASCADE;

-- Reset all sequences to 1
DO $$ 
DECLARE
    seq RECORD;
BEGIN
    FOR seq IN 
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format('ALTER SEQUENCE %I RESTART WITH 1', seq.sequence_name);
    END LOOP;
END $$;

-- Commit transaction
COMMIT;

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Verify all tables are empty
SELECT 
    'Data purge complete!' as status,
    COUNT(*) as total_tables,
    SUM(n_live_tup) as total_records
FROM pg_stat_user_tables
WHERE schemaname = 'public';