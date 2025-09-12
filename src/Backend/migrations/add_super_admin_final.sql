-- =====================================================
-- Add Super Admin User (Final Version)
-- Email: admin@weedgo.ca  
-- Password: Password1$
-- Date: 2025-01-11
-- =====================================================

BEGIN;

-- Create system tenant
INSERT INTO tenants (
    id,
    name,
    code,
    company_name,
    contact_email,
    status,
    subscription_tier,
    max_stores,
    created_at,
    updated_at
) VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'WeedGo System',
    'WEEDGO',
    'WeedGo Technologies Inc.',
    'admin@weedgo.ca',
    'active',
    'enterprise',
    999,
    NOW(),
    NOW()
) ON CONFLICT (code) DO UPDATE SET
    status = 'active',
    subscription_tier = 'enterprise',
    updated_at = NOW();

-- Create super admin user
-- Password hash is for 'Password1$'
INSERT INTO users (
    id,
    email,
    password_hash,
    first_name,
    last_name,
    active,
    email_verified,
    tenant_id,
    created_at,
    updated_at
) VALUES (
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'admin@weedgo.ca',
    '$2b$12$qGed8TgtYgNsF2PH6V/AqeDv8V/jXMTmTyRbRhm/1UdxqrBh1737u',
    'System',
    'Administrator',
    true,
    true,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    password_hash = '$2b$12$qGed8TgtYgNsF2PH6V/AqeDv8V/jXMTmTyRbRhm/1UdxqrBh1737u',
    active = true,
    email_verified = true,
    updated_at = NOW();

-- Add user to tenant_users with 'owner' role (highest available in tenant_users)
INSERT INTO tenant_users (
    id,
    tenant_id,
    user_id,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    'c0000000-0000-0000-0000-000000000001'::uuid,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'owner',  -- Using 'owner' as highest role in tenant_users
    true,
    NOW(),
    NOW()
) ON CONFLICT (tenant_id, user_id) DO UPDATE SET
    role = 'owner',
    is_active = true,
    updated_at = NOW();

COMMIT;

-- Verify the super admin was created
SELECT 
    u.id,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.active,
    u.email_verified,
    t.name as tenant_name,
    t.code as tenant_code,
    t.subscription_tier,
    tu.role as tenant_role
FROM users u
JOIN tenant_users tu ON tu.user_id = u.id
JOIN tenants t ON t.id = tu.tenant_id
WHERE u.email = 'admin@weedgo.ca';

-- Display login credentials
SELECT 
    '✅ Super Admin Created Successfully!' as status,
    'admin@weedgo.ca' as email,
    'Password1$' as password,
    'Use this to login to the admin dashboard' as note;