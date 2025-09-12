-- =====================================================
-- Migration: Remove tenant_users and store_users tables
-- Date: 2025-01-11
-- Description: Consolidate all user management into single users table
-- =====================================================

BEGIN;

-- Step 1: Drop views that depend on these tables
DROP VIEW IF EXISTS admin_users CASCADE;
DROP VIEW IF EXISTS customer_users CASCADE;

-- Step 2: Drop foreign key constraints from other tables that reference tenant_users or store_users
ALTER TABLE IF EXISTS audit_log DROP CONSTRAINT IF EXISTS audit_log_tenant_user_id_fkey;
ALTER TABLE IF EXISTS audit_log DROP CONSTRAINT IF EXISTS audit_log_store_user_id_fkey;

-- Step 3: Drop the tenant_users table
DROP TABLE IF EXISTS tenant_users CASCADE;

-- Step 4: Drop the store_users table  
DROP TABLE IF EXISTS store_users CASCADE;

-- Step 5: Ensure users table has necessary columns for tenant and store associations
-- These columns should already exist, but let's make sure
ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS tenant_role VARCHAR(50),
    ADD COLUMN IF NOT EXISTS store_role VARCHAR(50),
    ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';

-- Step 6: Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_tenant_role ON users(tenant_role);
CREATE INDEX IF NOT EXISTS idx_users_store_role ON users(store_role);

-- Step 7: Create new simplified views
-- Admin users view (super_admin and tenant_admin roles)
CREATE OR REPLACE VIEW admin_users AS
SELECT 
    u.*,
    t.name as tenant_name,
    s.name as store_name
FROM users u
LEFT JOIN tenants t ON u.tenant_id = t.id
LEFT JOIN stores s ON u.store_id = s.id
WHERE u.role IN ('super_admin', 'tenant_admin', 'store_manager');

-- Customer users view
CREATE OR REPLACE VIEW customer_users AS
SELECT 
    u.id,
    u.email,
    u.password_hash,
    u.first_name,
    u.last_name,
    u.phone,
    u.date_of_birth,
    u.age_verified,
    u.active,
    u.email_verified,
    u.phone_verified,
    u.marketing_consent as user_marketing_consent,
    u.terms_accepted,
    u.profile_id,
    u.session_id,
    u.last_login,
    u.tenant_id,
    u.default_store_id,
    u.store_id,
    u.role,
    u.cannsell_certified,
    u.cannsell_number,
    u.permissions_override,
    u.created_at,
    u.updated_at,
    c.loyalty_points,
    c.preferred_payment_method,
    c.marketing_consent as customer_marketing_consent
FROM users u
LEFT JOIN customers c ON c.user_id = u.id
WHERE u.role = 'customer';

-- Step 8: Add comment to document the change
COMMENT ON TABLE users IS 'Unified user table containing all user types - replaces separate tenant_users and store_users tables';

COMMIT;

-- Verify the tables were removed
SELECT 
    'Tables Removed' as status,
    COUNT(*) as remaining_user_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tenant_users', 'store_users');

-- Show current user table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('role', 'tenant_id', 'store_id', 'tenant_role', 'store_role', 'permissions')
ORDER BY ordinal_position;