-- Migration: Add 'customer' role to user_role_simple enum
-- Author: System
-- Date: 2025-09-11
-- Description: Adds explicit 'customer' role to differentiate from admin roles

-- Part 1: Add the enum value (must be committed first)
ALTER TYPE user_role_simple ADD VALUE IF NOT EXISTS 'customer';

-- Note: Run the following commands after the above is committed

-- Update all users without a role to 'customer'
UPDATE users 
SET role = 'customer'
WHERE role IS NULL;

-- Add a default value for the role column for future customer registrations
ALTER TABLE users 
ALTER COLUMN role SET DEFAULT 'customer';

-- Create an index for better query performance on customer lookups
CREATE INDEX IF NOT EXISTS idx_users_role_customer 
ON users(role) 
WHERE role = 'customer';

-- Update the constraint to include customer role
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tenant_required;
ALTER TABLE users ADD CONSTRAINT users_tenant_required 
CHECK (
    (role = 'super_admin' AND tenant_id IS NULL) OR 
    (role = 'customer') OR
    (role IN ('staff', 'store_manager', 'tenant_admin') AND tenant_id IS NOT NULL)
);

-- Create a view for easy customer queries
CREATE OR REPLACE VIEW customer_users AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.phone,
    u.date_of_birth,
    u.age_verified,
    u.active,
    u.created_at,
    u.last_login,
    u.tenant_id,
    u.default_store_id,
    c.customer_type,
    c.loyalty_points,
    c.total_spent,
    c.order_count,
    c.marketing_consent,
    c.primary_store_id
FROM users u
LEFT JOIN customers c ON u.id = c.user_id
WHERE u.role = 'customer';

-- Create a view for admin users
CREATE OR REPLACE VIEW admin_users AS
SELECT 
    u.*,
    CASE 
        WHEN u.role = 'super_admin' THEN 'System Administrator'
        WHEN u.role = 'tenant_admin' THEN 'Tenant Administrator'
        WHEN u.role = 'store_manager' THEN 'Store Manager'
        WHEN u.role = 'staff' THEN 'Staff Member'
    END as role_description
FROM users u
WHERE u.role IN ('staff', 'store_manager', 'tenant_admin', 'super_admin');

-- Verification
SELECT DISTINCT role, COUNT(*) FROM users GROUP BY role ORDER BY role;