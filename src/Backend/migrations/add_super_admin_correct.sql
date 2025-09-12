-- =====================================================
-- Add Super Admin User (Correct Implementation)
-- Email: admin@weedgo.ca  
-- Password: your_password_here
-- Date: 2025-01-11
-- =====================================================

BEGIN;

-- Create super admin user with proper role enum
-- Password hash is for 'your_password_here'
-- Note: super_admin role MUST have NULL tenant_id per constraint
INSERT INTO users (
    id,
    email,
    password_hash,
    first_name,
    last_name,
    role,  -- This is the user_role_simple enum
    active,
    email_verified,
    tenant_id,  -- MUST be NULL for super_admin
    created_at,
    updated_at
) VALUES (
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'admin@weedgo.ca',
    '$2b$12$qGed8TgtYgNsF2PH6V/AqeDv8V/jXMTmTyRbRhm/1UdxqrBh1737u',
    'System',
    'Administrator',
    'super_admin'::user_role_simple,  -- Using the enum type
    true,
    true,
    NULL,  -- NULL for super_admin as required by constraint
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    password_hash = '$2b$12$qGed8TgtYgNsF2PH6V/AqeDv8V/jXMTmTyRbRhm/1UdxqrBh1737u',
    role = 'super_admin'::user_role_simple,
    active = true,
    email_verified = true,
    tenant_id = NULL,
    updated_at = NOW();

COMMIT;

-- Verify the super admin was created
SELECT 
    u.id,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.role,
    u.active,
    u.email_verified,
    u.tenant_id,
    CASE 
        WHEN u.role = 'super_admin' THEN 'Full System Access'
        ELSE 'Limited Access'
    END as access_level
FROM users u
WHERE u.email = 'admin@weedgo.ca';

-- Display login credentials
SELECT 
    '✅ Super Admin Created Successfully!' as status,
    'admin@weedgo.ca' as email,
    'your_password_here' as password,
    'super_admin' as role,
    'Use these credentials to login to the admin dashboard' as instructions;