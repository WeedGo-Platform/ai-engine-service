-- Migration: Cleanup Old RBAC Tables
-- Description: Remove redundant tenant_users and store_users tables after successful migration
-- Author: Claude Code Assistant
-- Date: 2025-09-10

BEGIN;

-- ===================================================
-- STEP 1: Verify migration completed successfully
-- ===================================================

-- Check all users have new roles assigned
DO $$
DECLARE
    unassigned_count integer;
BEGIN
    SELECT COUNT(*) INTO unassigned_count 
    FROM users 
    WHERE role_new IS NULL;
    
    IF unassigned_count > 0 THEN
        RAISE EXCEPTION 'Migration not complete: % users missing new roles', unassigned_count;
    END IF;
    
    RAISE NOTICE 'Migration verification passed: All users have new roles assigned';
END $$;

-- ===================================================
-- STEP 2: Drop old tables (they're now redundant)
-- ===================================================

-- Drop tenant_users table (data migrated to users.tenant_id + users.role_new)
DROP TABLE IF EXISTS tenant_users CASCADE;

-- Drop store_users table (data migrated to users.store_id + users.role_new)  
DROP TABLE IF EXISTS store_users CASCADE;

-- ===================================================
-- STEP 3: Replace old role column with new one
-- ===================================================

-- Drop old role column
ALTER TABLE users DROP COLUMN role;

-- Rename role_new to role
ALTER TABLE users RENAME COLUMN role_new TO role;

-- ===================================================
-- STEP 4: Add final constraints and optimizations
-- ===================================================

-- Add foreign key constraint for store_id
ALTER TABLE users ADD CONSTRAINT users_store_fkey 
FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL;

-- Add check constraint to ensure store users belong to same tenant as store
-- (Will add this after we establish store-tenant relationships)

-- Update indexes
DROP INDEX IF EXISTS idx_users_role_new;
CREATE INDEX idx_users_role ON users(role);

-- ===================================================
-- STEP 5: Create a view for backwards compatibility
-- ===================================================

-- Create view that mimics old tenant_users structure for any legacy code
CREATE VIEW tenant_users_view AS
SELECT 
    gen_random_uuid() as id,
    tenant_id,
    id as user_id,
    CASE 
        WHEN role = 'tenant_admin' THEN 'admin'
        WHEN role = 'store_manager' THEN 'manager'
        ELSE 'member'
    END as role,
    permissions_override as permissions,
    active as is_active,
    created_at,
    updated_at
FROM users 
WHERE tenant_id IS NOT NULL;

-- Create view that mimics old store_users structure
CREATE VIEW store_users_view AS  
SELECT
    gen_random_uuid() as id,
    store_id,
    id as user_id,
    CASE
        WHEN role = 'store_manager' THEN 'manager'
        ELSE 'staff'
    END as role,
    cannsell_number as cannsell_certification,
    NULL::date as certification_expiry,
    permissions_override as permissions,
    active as is_active,
    created_at,
    updated_at
FROM users
WHERE store_id IS NOT NULL;

-- ===================================================
-- STEP 6: Update helper functions
-- ===================================================

-- Update get_user_context function to use new role column
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
            'role', u.role,
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
            WHERE role = u.role AND granted = true
        )
    ) INTO result
    FROM users u
    LEFT JOIN tenants t ON u.tenant_id = t.id
    LEFT JOIN stores s ON u.store_id = s.id
    WHERE u.id = user_id_param;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Update user_has_permission function to use new role column
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
    SELECT role, tenant_id, store_id, permissions_override
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
    WHERE role = user_rec.role 
      AND (resource_type = resource_type_param OR resource_type = '*')
      AND (action = action_param OR action = '*')
    ORDER BY 
        CASE WHEN resource_type = '*' THEN 1 ELSE 0 END,
        CASE WHEN action = '*' THEN 1 ELSE 0 END
    LIMIT 1;
    
    RETURN COALESCE(has_perm, false);
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ===================================================
-- VERIFICATION
-- ===================================================

-- Final verification
SELECT 
    'Cleanup Complete' as status,
    COUNT(*) as total_users,
    COUNT(CASE WHEN role = 'super_admin' THEN 1 END) as super_admins,
    COUNT(CASE WHEN role = 'tenant_admin' THEN 1 END) as tenant_admins,
    COUNT(CASE WHEN role = 'store_manager' THEN 1 END) as store_managers,
    COUNT(CASE WHEN role = 'staff' THEN 1 END) as staff
FROM users;

-- Test user context function
SELECT 'Testing user context for super admin:' as test;
SELECT get_user_context((SELECT id FROM users WHERE email = 'admin@potpalace.ca'));

SELECT 'Testing user context for tenant admin:' as test;
SELECT get_user_context((SELECT id FROM users WHERE email = 'tenant.admin@leafygreens.ca'));