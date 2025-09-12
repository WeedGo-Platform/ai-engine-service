-- Complete Database Cleanup
-- Description: Remove ALL data except product_catalog and accessories_catalog
-- Author: Claude Code Assistant
-- Date: 2025-09-10
-- WARNING: This will permanently delete all business data!

BEGIN;

-- ===================================================
-- STEP 1: Disable all foreign key constraints temporarily
-- ===================================================

-- This will help avoid constraint violations during cleanup
SET session_replication_role = replica;

-- ===================================================
-- STEP 2: Remove all user-related data
-- ===================================================

-- Drop all user sessions and authentication data
TRUNCATE TABLE user_sessions CASCADE;
TRUNCATE TABLE login_attempts CASCADE;
TRUNCATE TABLE otp_codes CASCADE;
TRUNCATE TABLE email_verification_tokens CASCADE;
TRUNCATE TABLE password_reset_tokens CASCADE;
TRUNCATE TABLE token_blacklist CASCADE;
TRUNCATE TABLE api_keys CASCADE;
TRUNCATE TABLE user_addresses CASCADE;
TRUNCATE TABLE user_profiles CASCADE;

-- Remove all users (this will cascade to related tables)
TRUNCATE TABLE users CASCADE;

-- ===================================================
-- STEP 3: Remove all customer and order data
-- ===================================================

-- Remove customer-related data
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE customer_addresses CASCADE;
TRUNCATE TABLE customer_preferences CASCADE;

-- Remove all order and transaction data
TRUNCATE TABLE order_items CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE purchase_order_items CASCADE;
TRUNCATE TABLE purchase_orders CASCADE;

-- Remove cart and checkout data
TRUNCATE TABLE cart_items CASCADE;
TRUNCATE TABLE cart_sessions CASCADE;
TRUNCATE TABLE checkout_sessions CASCADE;

-- Remove payment data
TRUNCATE TABLE payments CASCADE;
TRUNCATE TABLE payment_transactions CASCADE;
TRUNCATE TABLE payment_refunds CASCADE;
TRUNCATE TABLE payment_audit_log CASCADE;
TRUNCATE TABLE payment_credentials CASCADE;
TRUNCATE TABLE tenant_payment_providers CASCADE;

-- ===================================================
-- STEP 4: Remove all inventory and tracking data
-- ===================================================

-- Remove all inventory data
TRUNCATE TABLE inventory CASCADE;
TRUNCATE TABLE store_inventory CASCADE;
TRUNCATE TABLE inventory_movements CASCADE;
TRUNCATE TABLE inventory_transactions CASCADE;
TRUNCATE TABLE inventory_reservations CASCADE;
TRUNCATE TABLE inventory_snapshots CASCADE;

-- Remove batch tracking data
TRUNCATE TABLE batch_tracking CASCADE;
TRUNCATE TABLE batch_movements CASCADE;

-- Remove receiving data
TRUNCATE TABLE receive_po_items CASCADE;
TRUNCATE TABLE receive_pos CASCADE;

-- ===================================================
-- STEP 5: Remove all business and operational data
-- ===================================================

-- Remove promotions and pricing
TRUNCATE TABLE promotions CASCADE;
TRUNCATE TABLE promotion_items CASCADE;
TRUNCATE TABLE discount_usage CASCADE;
TRUNCATE TABLE product_recommendations CASCADE;

-- Remove communication and interaction data
TRUNCATE TABLE communication_logs CASCADE;
TRUNCATE TABLE conversation_states CASCADE;
TRUNCATE TABLE conversion_metrics CASCADE;

-- Remove analytics and metrics
TRUNCATE TABLE location_access_logs CASCADE;
TRUNCATE TABLE user_interaction_logs CASCADE;

-- ===================================================
-- STEP 6: Remove all tenant and store data
-- ===================================================

-- Remove store-related data
TRUNCATE TABLE store_hours CASCADE;
TRUNCATE TABLE store_payment_providers CASCADE;

-- Remove stores (this will cascade to store_users if any remain)
TRUNCATE TABLE stores CASCADE;

-- Remove tenant data
TRUNCATE TABLE tenant_subscriptions CASCADE;
TRUNCATE TABLE tenants CASCADE;

-- Remove provinces/territories if they exist
TRUNCATE TABLE provinces_territories CASCADE;

-- ===================================================
-- STEP 7: Remove RBAC and permission data
-- ===================================================

-- Remove role permissions and any user context
TRUNCATE TABLE role_permissions CASCADE;

-- ===================================================
-- STEP 8: Remove any remaining business data
-- ===================================================

-- Remove any remaining product-related business data (but keep catalogs)
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE products_complete CASCADE;

-- Remove hardware and device data
TRUNCATE TABLE hardware_devices CASCADE;
TRUNCATE TABLE usb_devices CASCADE;

-- Remove any translation or localization data
TRUNCATE TABLE translations CASCADE;

-- Remove any supplier data
TRUNCATE TABLE suppliers CASCADE;
TRUNCATE TABLE supplier_products CASCADE;

-- ===================================================
-- STEP 9: Reset sequences and clean up
-- ===================================================

-- Re-enable foreign key constraints
SET session_replication_role = DEFAULT;

-- Reset any sequences that might exist
-- (Most tables use UUIDs, but some might have sequences)

-- ===================================================
-- VERIFICATION: Check what remains
-- ===================================================

-- Show remaining table counts
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
UNION ALL
SELECT 
    'store_inventory' as table_name,
    COUNT(*) as record_count
FROM store_inventory
ORDER BY table_name;

COMMIT;

-- ===================================================
-- FINAL VERIFICATION
-- ===================================================

-- List all tables with their row counts to verify cleanup
SELECT 
    schemaname,
    tablename,
    n_tup_ins - n_tup_del as row_count
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
  AND (n_tup_ins - n_tup_del) > 0
ORDER BY row_count DESC;

-- Show specifically what's left in key tables
SELECT 'REMAINING DATA SUMMARY:' as status;
SELECT 'Product Catalog Records:', COUNT(*) FROM product_catalog;
SELECT 'Accessories Catalog Records:', COUNT(*) FROM accessories_catalog;
SELECT 'Users (should be 0):', COUNT(*) FROM users;
SELECT 'Tenants (should be 0):', COUNT(*) FROM tenants;
SELECT 'Stores (should be 0):', COUNT(*) FROM stores;
SELECT 'Orders (should be 0):', COUNT(*) FROM orders;