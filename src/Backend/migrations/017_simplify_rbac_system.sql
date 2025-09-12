-- Migration: Simplify RBAC System
-- Description: Consolidate roles into 4 simple types and migrate existing data
-- Author: Claude Code Assistant
-- Date: 2025-09-10

BEGIN;

-- ===================================================
-- STEP 1: Create new simplified role enum
-- ===================================================

-- Create new role type
CREATE TYPE user_role_simple AS ENUM (
    'super_admin',    -- Platform/system management
    'tenant_admin',   -- Full tenant control  
    'store_manager',  -- Store operations
    'staff'           -- Day-to-day operations
);

-- ===================================================
-- STEP 2: Add new columns to users table
-- ===================================================

-- Add new role column
ALTER TABLE users ADD COLUMN role_new user_role_simple;

-- Add store_id for store-specific roles
ALTER TABLE users ADD COLUMN store_id uuid REFERENCES stores(id) ON DELETE SET NULL;

-- Add permissions for fine-grained overrides
ALTER TABLE users ADD COLUMN permissions_override jsonb DEFAULT '{}';

-- ===================================================
-- STEP 3: Migrate existing data
-- ===================================================

-- Map existing roles to new simplified structure
UPDATE users SET role_new = CASE
    WHEN role = 'super_admin' THEN 'super_admin'::user_role_simple
    WHEN role = 'admin' THEN 'tenant_admin'::user_role_simple
    WHEN role = 'manager' THEN 'store_manager'::user_role_simple
    ELSE 'staff'::user_role_simple
END;

-- Handle tenant_users table mappings
UPDATE users 
SET role_new = CASE 
    WHEN tu.role = 'owner' THEN 'tenant_admin'::user_role_simple
    WHEN tu.role = 'admin' THEN 'tenant_admin'::user_role_simple
    WHEN tu.role = 'manager' THEN 'store_manager'::user_role_simple
    ELSE 'staff'::user_role_simple
END,
tenant_id = tu.tenant_id
FROM tenant_users tu 
WHERE users.id = tu.user_id;

-- Handle store_users table mappings  
UPDATE users 
SET role_new = CASE
    WHEN su.role = 'manager' THEN 'store_manager'::user_role_simple
    WHEN su.role = 'supervisor' THEN 'store_manager'::user_role_simple
    ELSE 'staff'::user_role_simple
END,
store_id = su.store_id
FROM store_users su
WHERE users.id = su.user_id;

-- Ensure super_admin has no tenant restriction
UPDATE users 
SET tenant_id = NULL 
WHERE role_new = 'super_admin';

-- ===================================================
-- STEP 4: Assign default tenants for users without one
-- ===================================================

-- Get a default tenant for assignment
WITH default_tenant AS (
    SELECT id as tenant_id 
    FROM tenants 
    WHERE name = 'WeedGo Community' 
    LIMIT 1
)
UPDATE users 
SET tenant_id = default_tenant.tenant_id
FROM default_tenant
WHERE users.tenant_id IS NULL 
  AND users.role_new != 'super_admin';

-- ===================================================
-- STEP 5: Create constraints and indexes
-- ===================================================

-- Make role_new required
ALTER TABLE users ALTER COLUMN role_new SET NOT NULL;

-- Add constraint: non-super-admin users must have tenant
ALTER TABLE users ADD CONSTRAINT users_tenant_required 
CHECK (
    (role_new = 'super_admin' AND tenant_id IS NULL) OR 
    (role_new != 'super_admin' AND tenant_id IS NOT NULL)
);

-- Add constraint: store_manager with store must have tenant matching store's tenant
-- (We'll implement this after we have store-tenant relationships)

-- Add indexes for performance
CREATE INDEX idx_users_role_new ON users(role_new);
CREATE INDEX idx_users_tenant_role ON users(tenant_id, role_new) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_users_store_role ON users(store_id, role_new) WHERE store_id IS NOT NULL;

-- ===================================================
-- STEP 6: Create role permission definitions
-- ===================================================

CREATE TABLE role_permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    role user_role_simple NOT NULL,
    resource_type varchar(50) NOT NULL,
    action varchar(50) NOT NULL,
    granted boolean DEFAULT true,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(role, resource_type, action)
);

-- Insert default permissions
INSERT INTO role_permissions (role, resource_type, action) VALUES
-- Super Admin - full access
('super_admin', '*', '*'),

-- Tenant Admin - full tenant access
('tenant_admin', 'tenant', 'read'),
('tenant_admin', 'tenant', 'update'),
('tenant_admin', 'store', 'create'),
('tenant_admin', 'store', 'read'),
('tenant_admin', 'store', 'update'),
('tenant_admin', 'store', 'delete'),
('tenant_admin', 'user', 'create'),
('tenant_admin', 'user', 'read'),
('tenant_admin', 'user', 'update'),
('tenant_admin', 'user', 'delete'),
('tenant_admin', 'product', 'create'),
('tenant_admin', 'product', 'read'),
('tenant_admin', 'product', 'update'),
('tenant_admin', 'product', 'delete'),
('tenant_admin', 'inventory', 'read'),
('tenant_admin', 'inventory', 'update'),
('tenant_admin', 'order', 'read'),
('tenant_admin', 'order', 'update'),
('tenant_admin', 'report', 'read'),

-- Store Manager - store-level access
('store_manager', 'store', 'read'),
('store_manager', 'store', 'update'),
('store_manager', 'user', 'read'),
('store_manager', 'product', 'read'),
('store_manager', 'inventory', 'read'),
('store_manager', 'inventory', 'update'),
('store_manager', 'order', 'read'),
('store_manager', 'order', 'update'),
('store_manager', 'report', 'read'),

-- Staff - basic operations
('staff', 'product', 'read'),
('staff', 'inventory', 'read'),
('staff', 'order', 'read'),
('staff', 'order', 'create');

-- ===================================================
-- STEP 7: Create helper functions
-- ===================================================

-- Function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(
    user_id_param uuid,
    resource_type_param varchar,
    action_param varchar
) RETURNS boolean AS $$
DECLARE
    user_rec record;
    has_perm boolean := false;
BEGIN
    -- Get user info
    SELECT role_new, tenant_id, store_id, permissions_override
    INTO user_rec
    FROM users 
    WHERE id = user_id_param AND active = true;
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check override permissions first
    IF user_rec.permissions_override ? (resource_type_param || ':' || action_param) THEN
        RETURN (user_rec.permissions_override->>(resource_type_param || ':' || action_param))::boolean;
    END IF;
    
    -- Check role-based permissions
    SELECT granted INTO has_perm
    FROM role_permissions 
    WHERE role = user_rec.role_new 
      AND (resource_type = resource_type_param OR resource_type = '*')
      AND (action = action_param OR action = '*')
    ORDER BY 
        CASE WHEN resource_type = '*' THEN 1 ELSE 0 END,
        CASE WHEN action = '*' THEN 1 ELSE 0 END
    LIMIT 1;
    
    RETURN COALESCE(has_perm, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get user context (for API responses)
CREATE OR REPLACE FUNCTION get_user_context(user_id_param uuid)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'user', jsonb_build_object(
            'id', u.id,
            'email', u.email,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'role', u.role_new,
            'tenant_id', u.tenant_id,
            'store_id', u.store_id,
            'active', u.active
        ),
        'tenant', CASE 
            WHEN u.tenant_id IS NOT NULL THEN jsonb_build_object(
                'id', t.id,
                'name', t.name
            )
            ELSE NULL
        END,
        'store', CASE 
            WHEN u.store_id IS NOT NULL THEN jsonb_build_object(
                'id', s.id,
                'name', s.name,
                'store_code', s.store_code
            )
            ELSE NULL
        END,
        'permissions', (
            SELECT jsonb_agg(resource_type || ':' || action)
            FROM role_permissions 
            WHERE role = u.role_new AND granted = true
        )
    ) INTO result
    FROM users u
    LEFT JOIN tenants t ON u.tenant_id = t.id
    LEFT JOIN stores s ON u.store_id = s.id
    WHERE u.id = user_id_param;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ===================================================
-- VERIFICATION QUERIES
-- ===================================================

-- Check migration results
SELECT 
    'Migration Summary' as status,
    COUNT(*) as total_users,
    COUNT(CASE WHEN role_new = 'super_admin' THEN 1 END) as super_admins,
    COUNT(CASE WHEN role_new = 'tenant_admin' THEN 1 END) as tenant_admins,
    COUNT(CASE WHEN role_new = 'store_manager' THEN 1 END) as store_managers,
    COUNT(CASE WHEN role_new = 'staff' THEN 1 END) as staff
FROM users;