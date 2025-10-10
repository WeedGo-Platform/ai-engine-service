-- ============================================================================
-- Migration: Alter USERS Table
-- Description: Add all missing columns from legacy database to users table
-- Dependencies: 002_create_custom_types.sql
-- ============================================================================

-- First, alter the role column type from varchar to enum
ALTER TABLE users ALTER COLUMN role TYPE user_role_simple USING role::user_role_simple;
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'customer'::user_role_simple;

-- Alter phone column to match legacy spec
ALTER TABLE users ALTER COLUMN phone TYPE VARCHAR(50);

-- Change permissions default from '[]' to '{}'
ALTER TABLE users ALTER COLUMN permissions SET DEFAULT '{}'::jsonb;

-- Add missing columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS age_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_id UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS default_store_id UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cannsell_certified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cannsell_number VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions_override JSONB DEFAULT '{}'::jsonb;
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_role VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS store_role VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip INET;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_location JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);
CREATE INDEX IF NOT EXISTS idx_users_profile_id ON users(profile_id);
CREATE INDEX IF NOT EXISTS idx_users_role_customer ON users(role) WHERE role = 'customer'::user_role_simple;
CREATE INDEX IF NOT EXISTS idx_users_role_new ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_session_id ON users(session_id);
CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id);
CREATE INDEX IF NOT EXISTS idx_users_store_role ON users(store_id, role) WHERE store_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_tenant_role ON users(tenant_id, role) WHERE tenant_id IS NOT NULL;

-- Add check constraint for tenant requirement
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tenant_required;
ALTER TABLE users ADD CONSTRAINT users_tenant_required CHECK (
    (role = 'super_admin'::user_role_simple AND tenant_id IS NULL) OR
    (role = 'customer'::user_role_simple) OR
    (role IN ('staff'::user_role_simple, 'store_manager'::user_role_simple, 'tenant_admin'::user_role_simple) AND tenant_id IS NOT NULL)
);

-- Add foreign key constraints (will be added after related tables are created)
-- These will be added in a later migration step

COMMENT ON COLUMN users.date_of_birth IS 'User date of birth for age verification';
COMMENT ON COLUMN users.age_verified IS 'Flag indicating user has passed age verification (legal requirement for cannabis)';
COMMENT ON COLUMN users.cannsell_certified IS 'Flag indicating user has Cannsell certification for cannabis sales';
COMMENT ON COLUMN users.cannsell_number IS 'Cannsell certification number';
COMMENT ON COLUMN users.last_login_ip IS 'Last IP address used for login (security tracking)';
COMMENT ON COLUMN users.last_login_location IS 'Geographic location data from last login';
COMMENT ON COLUMN users.login_count IS 'Total number of successful logins';
