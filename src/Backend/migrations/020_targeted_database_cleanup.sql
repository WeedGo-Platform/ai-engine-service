-- Targeted Database Cleanup
-- Description: Remove ALL data except product_catalog and accessories_catalog
-- Author: Claude Code Assistant
-- Date: 2025-09-10
-- WARNING: This will permanently delete all business data!

BEGIN;

-- ===================================================
-- STEP 1: Disable all foreign key constraints
-- ===================================================
SET session_replication_role = replica;

-- ===================================================
-- STEP 2: Remove all user-related data
-- ===================================================

-- Clear user authentication and session data
TRUNCATE TABLE user_sessions CASCADE;
TRUNCATE TABLE login_attempts CASCADE;
TRUNCATE TABLE otp_codes CASCADE;
TRUNCATE TABLE otp_rate_limits CASCADE;
TRUNCATE TABLE email_verification_tokens CASCADE;
TRUNCATE TABLE password_reset_tokens CASCADE;
TRUNCATE TABLE token_blacklist CASCADE;
TRUNCATE TABLE api_keys CASCADE;
TRUNCATE TABLE user_addresses CASCADE;
TRUNCATE TABLE user_profiles CASCADE;

-- Clear RBAC data
TRUNCATE TABLE tenant_users CASCADE;
TRUNCATE TABLE store_users CASCADE;

-- Remove all users (this will cascade to related tables)
TRUNCATE TABLE users CASCADE;

-- ===================================================
-- STEP 3: Remove all customer and order data
-- ===================================================

-- Remove customer data
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE customer_profiles CASCADE;
TRUNCATE TABLE customer_pricing_rules CASCADE;

-- Remove order and transaction data
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE pos_transactions CASCADE;
TRUNCATE TABLE purchase_order_items CASCADE;
TRUNCATE TABLE purchase_orders CASCADE;

-- Remove cart and checkout data
TRUNCATE TABLE cart_sessions CASCADE;
TRUNCATE TABLE checkout_sessions CASCADE;

-- ===================================================
-- STEP 4: Remove all payment data
-- ===================================================

TRUNCATE TABLE payment_transactions CASCADE;
TRUNCATE TABLE payment_refunds CASCADE;
TRUNCATE TABLE payment_disputes CASCADE;
TRUNCATE TABLE payment_fee_splits CASCADE;
TRUNCATE TABLE payment_audit_log CASCADE;
TRUNCATE TABLE payment_credentials CASCADE;
TRUNCATE TABLE payment_idempotency_keys CASCADE;
TRUNCATE TABLE payment_methods CASCADE;
TRUNCATE TABLE payment_metrics CASCADE;
TRUNCATE TABLE payment_provider_health_metrics CASCADE;
TRUNCATE TABLE payment_providers CASCADE;
TRUNCATE TABLE payment_settlements CASCADE;
TRUNCATE TABLE payment_subscriptions CASCADE;
TRUNCATE TABLE payment_webhook_routes CASCADE;
TRUNCATE TABLE payment_webhooks CASCADE;
TRUNCATE TABLE tenant_payment_providers CASCADE;
TRUNCATE TABLE tenant_settlement_accounts CASCADE;

-- ===================================================
-- STEP 5: Remove all inventory and tracking data
-- ===================================================

-- Remove inventory data
TRUNCATE TABLE inventory CASCADE;
TRUNCATE TABLE store_inventory CASCADE;
TRUNCATE TABLE accessories_inventory CASCADE;
TRUNCATE TABLE inventory_movements CASCADE;
TRUNCATE TABLE inventory_transactions CASCADE;
TRUNCATE TABLE inventory_reservations CASCADE;
TRUNCATE TABLE inventory_snapshots CASCADE;

-- Remove batch tracking data
TRUNCATE TABLE batch_tracking CASCADE;

-- ===================================================
-- STEP 6: Remove all business and operational data
-- ===================================================

-- Remove promotions and discounts
TRUNCATE TABLE promotions CASCADE;
TRUNCATE TABLE promotion_usage CASCADE;
TRUNCATE TABLE discount_codes CASCADE;
TRUNCATE TABLE discount_usage CASCADE;
TRUNCATE TABLE bundle_deals CASCADE;

-- Remove pricing data
TRUNCATE TABLE price_history CASCADE;
TRUNCATE TABLE price_tiers CASCADE;
TRUNCATE TABLE dynamic_pricing_rules CASCADE;

-- Remove product business data (not catalogs)
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE products_complete CASCADE;
TRUNCATE TABLE product_recommendations CASCADE;

-- Remove communication and AI data
TRUNCATE TABLE communication_logs CASCADE;
TRUNCATE TABLE conversation_states CASCADE;
TRUNCATE TABLE conversion_metrics CASCADE;
TRUNCATE TABLE ai_conversations CASCADE;
TRUNCATE TABLE ai_personalities CASCADE;
TRUNCATE TABLE ai_training_data CASCADE;
TRUNCATE TABLE chat_interactions CASCADE;
TRUNCATE TABLE model_deployments CASCADE;
TRUNCATE TABLE model_metrics CASCADE;
TRUNCATE TABLE model_versions CASCADE;
TRUNCATE TABLE parameter_accuracy CASCADE;
TRUNCATE TABLE recommendation_metrics CASCADE;
TRUNCATE TABLE training_examples CASCADE;
TRUNCATE TABLE training_sessions CASCADE;

-- Remove delivery and location data
TRUNCATE TABLE delivery_zones CASCADE;

-- Remove import and staging data
TRUNCATE TABLE asn_import_staging CASCADE;

-- Remove translation data
TRUNCATE TABLE translation_batch_items CASCADE;
TRUNCATE TABLE translation_batches CASCADE;
TRUNCATE TABLE translation_overrides CASCADE;
TRUNCATE TABLE translations CASCADE;
TRUNCATE TABLE supported_languages CASCADE;
TRUNCATE TABLE skip_words CASCADE;

-- Remove audit data
TRUNCATE TABLE audit_log CASCADE;

-- ===================================================
-- STEP 7: Remove all tenant and store data
-- ===================================================

-- Remove store-related data
TRUNCATE TABLE store_hours_settings CASCADE;
TRUNCATE TABLE store_holiday_hours CASCADE;
TRUNCATE TABLE store_regular_hours CASCADE;
TRUNCATE TABLE store_special_hours CASCADE;
TRUNCATE TABLE store_settings CASCADE;
TRUNCATE TABLE store_compliance CASCADE;
TRUNCATE TABLE store_ai_agents CASCADE;

-- Remove stores
TRUNCATE TABLE stores CASCADE;

-- Remove tenant data
TRUNCATE TABLE tenant_features CASCADE;
TRUNCATE TABLE tenant_settings CASCADE;
TRUNCATE TABLE tenant_subscriptions CASCADE;
TRUNCATE TABLE tenants CASCADE;

-- Remove suppliers
TRUNCATE TABLE suppliers CASCADE;

-- Remove geographic data
TRUNCATE TABLE provinces_territories CASCADE;
TRUNCATE TABLE holidays CASCADE;
TRUNCATE TABLE tax_rates CASCADE;

-- ===================================================
-- STEP 8: Re-enable foreign key constraints
-- ===================================================
SET session_replication_role = DEFAULT;

COMMIT;

-- ===================================================
-- VERIFICATION: Check what remains
-- ===================================================

SELECT 'CLEANUP COMPLETE - REMAINING DATA:' as status;

SELECT 
    'product_catalog' as table_name,
    COUNT(*) as record_count
FROM product_catalog
UNION ALL
SELECT 
    'accessories_catalog' as table_name,
    COUNT(*) as record_count  
FROM accessories_catalog
UNION ALL
SELECT 
    'accessory_categories' as table_name,
    COUNT(*) as record_count  
FROM accessory_categories
UNION ALL
SELECT 
    'role_permissions' as table_name,
    COUNT(*) as record_count  
FROM role_permissions
UNION ALL
SELECT 
    'users' as table_name,
    COUNT(*) as record_count
FROM users
UNION ALL
SELECT 
    'tenants' as table_name,
    COUNT(*) as record_count
FROM tenants
UNION ALL
SELECT 
    'stores' as table_name,
    COUNT(*) as record_count
FROM stores
UNION ALL
SELECT 
    'customers' as table_name,
    COUNT(*) as record_count
FROM customers
UNION ALL
SELECT 
    'orders' as table_name,
    COUNT(*) as record_count
FROM orders
UNION ALL
SELECT 
    'inventory' as table_name,
    COUNT(*) as record_count
FROM inventory
ORDER BY table_name;