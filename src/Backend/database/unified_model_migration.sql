-- Unified Model Migration Script
-- This script migrates from separate users/customers tables to a unified model
-- Created: 2025-09-17

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Create backup tables
-- =========================================
CREATE TABLE IF NOT EXISTS backup_users AS SELECT * FROM users;
CREATE TABLE IF NOT EXISTS backup_customers AS SELECT * FROM customers;
CREATE TABLE IF NOT EXISTS backup_customer_profiles AS SELECT * FROM customer_profiles;
CREATE TABLE IF NOT EXISTS backup_user_profiles AS SELECT * FROM user_profiles;

-- =========================================
-- STEP 2: Drop the auto-create customer trigger
-- =========================================
DROP TRIGGER IF EXISTS create_customer_on_user_insert ON users;
DROP FUNCTION IF EXISTS create_customer_for_user();

-- =========================================
-- STEP 3: Create new unified profiles table
-- =========================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Basic Information (from users/customers)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    date_of_birth DATE,

    -- Address Information (from customers)
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',

    -- Business/CRM Data (from customers)
    loyalty_points INTEGER DEFAULT 0,
    customer_type VARCHAR(50) DEFAULT 'regular',
    preferred_payment_method VARCHAR(50),
    total_spent NUMERIC(12,2) DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    last_order_date TIMESTAMP,

    -- Preferences and AI Data (from user_profiles/customer_profiles)
    preferences JSONB DEFAULT '{}'::jsonb,
    needs JSONB DEFAULT '[]'::jsonb,
    experience_level VARCHAR(50),
    medical_conditions JSONB DEFAULT '[]'::jsonb,
    preferred_categories JSONB DEFAULT '[]'::jsonb,
    preferred_effects JSONB DEFAULT '[]'::jsonb,
    price_range JSONB,
    purchase_history JSONB DEFAULT '[]'::jsonb,
    interaction_count INTEGER DEFAULT 0,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50),

    -- Marketing and Consent (from both)
    marketing_consent BOOLEAN DEFAULT false,
    sms_consent BOOLEAN DEFAULT false,

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    is_verified BOOLEAN DEFAULT false,

    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint on user_id for 1:1 relationship
    CONSTRAINT unique_user_profile UNIQUE(user_id)
);

-- Create indexes for performance
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_customer_type ON profiles(customer_type);
CREATE INDEX idx_profiles_loyalty_points ON profiles(loyalty_points);
CREATE INDEX idx_profiles_last_order_date ON profiles(last_order_date DESC);
CREATE INDEX idx_profiles_preferences_gin ON profiles USING gin(preferences);
CREATE INDEX idx_profiles_purchase_history_gin ON profiles USING gin(purchase_history);

-- =========================================
-- STEP 4: Migrate data from customers to profiles
-- =========================================
INSERT INTO profiles (
    user_id,
    first_name,
    last_name,
    phone,
    date_of_birth,
    address,
    city,
    state,
    postal_code,
    country,
    loyalty_points,
    customer_type,
    preferred_payment_method,
    total_spent,
    order_count,
    last_order_date,
    marketing_consent,
    sms_consent,
    tags,
    notes,
    is_verified,
    created_at,
    updated_at
)
SELECT
    COALESCE(c.user_id, u.id) as user_id,
    COALESCE(c.first_name, u.first_name),
    COALESCE(c.last_name, u.last_name),
    COALESCE(c.phone, u.phone),
    COALESCE(c.date_of_birth, u.date_of_birth),
    c.address,
    c.city,
    c.state,
    c.postal_code,
    c.country,
    c.loyalty_points,
    c.customer_type,
    c.preferred_payment_method,
    c.total_spent,
    c.order_count,
    c.last_order_date,
    COALESCE(c.marketing_consent, u.marketing_consent),
    c.sms_consent,
    c.tags,
    c.notes,
    c.is_verified,
    LEAST(c.created_at, u.created_at),
    GREATEST(c.updated_at, u.updated_at)
FROM users u
LEFT JOIN customers c ON u.id = c.user_id
WHERE u.id IS NOT NULL;

-- Migrate orphaned customer records (customers without user_id)
INSERT INTO users (
    email,
    password_hash,
    first_name,
    last_name,
    phone,
    date_of_birth,
    marketing_consent,
    role,
    created_at,
    updated_at
)
SELECT
    c.email,
    '$2b$10$dummy.hash.for.orphaned.customers', -- These will need password reset
    c.first_name,
    c.last_name,
    c.phone,
    c.date_of_birth,
    c.marketing_consent,
    'customer'::user_role_simple,
    c.created_at,
    c.updated_at
FROM customers c
WHERE c.user_id IS NULL
RETURNING id, email;

-- Add profiles for orphaned customers that were just created
INSERT INTO profiles (
    user_id,
    first_name,
    last_name,
    phone,
    date_of_birth,
    address,
    city,
    state,
    postal_code,
    country,
    loyalty_points,
    customer_type,
    preferred_payment_method,
    total_spent,
    order_count,
    last_order_date,
    marketing_consent,
    sms_consent,
    tags,
    notes,
    is_verified,
    created_at,
    updated_at
)
SELECT
    u.id as user_id,
    c.first_name,
    c.last_name,
    c.phone,
    c.date_of_birth,
    c.address,
    c.city,
    c.state,
    c.postal_code,
    c.country,
    c.loyalty_points,
    c.customer_type,
    c.preferred_payment_method,
    c.total_spent,
    c.order_count,
    c.last_order_date,
    c.marketing_consent,
    c.sms_consent,
    c.tags,
    c.notes,
    c.is_verified,
    c.created_at,
    c.updated_at
FROM customers c
JOIN users u ON u.email = c.email
WHERE c.user_id IS NULL;

-- =========================================
-- STEP 5: Migrate customer_profiles data
-- =========================================
UPDATE profiles p
SET
    preferences = COALESCE(cp.preferences, p.preferences),
    purchase_history = COALESCE(cp.purchase_history, p.purchase_history),
    interaction_count = GREATEST(cp.interaction_count, p.interaction_count)
FROM customer_profiles cp
JOIN customers c ON cp.customer_id = c.id::varchar
WHERE p.user_id = c.user_id;

-- =========================================
-- STEP 6: Update foreign key references
-- =========================================

-- Update orders table to reference users instead of customers
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_customer_id_fkey;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_user_id_fkey;

-- Populate user_id from customer relationship if not already set
UPDATE orders o
SET user_id = c.user_id
FROM customers c
WHERE o.customer_id = c.id
AND o.user_id IS NULL;

-- Add foreign key constraint to users (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'orders_user_id_fkey'
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT orders_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- =========================================
-- STEP 7: Create views for backward compatibility
-- =========================================

-- Create a view that mimics the old customers table structure
CREATE OR REPLACE VIEW customers_view AS
SELECT
    p.id as id,
    p.user_id,
    u.email,
    p.first_name,
    p.last_name,
    p.phone,
    p.date_of_birth,
    p.address,
    p.city,
    p.state,
    p.postal_code,
    p.country,
    p.loyalty_points,
    p.customer_type,
    p.preferred_payment_method,
    p.total_spent,
    p.order_count,
    p.marketing_consent,
    p.sms_consent,
    p.tags,
    p.notes,
    u.active as is_active,
    p.is_verified,
    p.created_at,
    p.updated_at,
    p.last_order_date,
    u.tenant_id
FROM profiles p
JOIN users u ON p.user_id = u.id;

-- =========================================
-- STEP 8: Clean up users table (remove duplicate fields)
-- =========================================
-- We'll keep only authentication-related fields in users table
-- These fields are now in profiles: first_name, last_name, phone, date_of_birth, marketing_consent

-- Note: We're keeping these fields temporarily for the transition
-- They can be dropped later after all code is updated

-- =========================================
-- STEP 9: Create trigger for updated_at
-- =========================================
CREATE TRIGGER update_profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================
-- STEP 10: Grant permissions
-- =========================================
GRANT ALL ON profiles TO weedgo;
GRANT SELECT ON customers_view TO weedgo;

-- =========================================
-- VERIFICATION QUERIES
-- =========================================
DO $$
DECLARE
    users_count INTEGER;
    profiles_count INTEGER;
    orphaned_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO users_count FROM users;
    SELECT COUNT(*) INTO profiles_count FROM profiles;
    SELECT COUNT(*) INTO orphaned_count FROM users u
    LEFT JOIN profiles p ON u.id = p.user_id
    WHERE p.id IS NULL;

    RAISE NOTICE 'Users: %, Profiles: %, Orphaned Users: %',
                 users_count, profiles_count, orphaned_count;

    IF orphaned_count > 0 THEN
        RAISE WARNING 'There are % users without profiles!', orphaned_count;
    END IF;
END $$;

COMMIT;

-- =========================================
-- ROLLBACK SCRIPT (Save separately)
-- =========================================
/*
-- To rollback this migration, run:
BEGIN TRANSACTION;

-- Restore original tables
DROP TABLE IF EXISTS profiles CASCADE;
DROP VIEW IF EXISTS customers_view;

-- Restore customers table from backup
DROP TABLE IF EXISTS customers;
CREATE TABLE customers AS SELECT * FROM backup_customers;

-- Restore customer_profiles from backup
DROP TABLE IF EXISTS customer_profiles;
CREATE TABLE customer_profiles AS SELECT * FROM backup_customer_profiles;

-- Restore user_profiles from backup
DROP TABLE IF EXISTS user_profiles;
CREATE TABLE user_profiles AS SELECT * FROM backup_user_profiles;

-- Restore foreign keys and triggers
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_user_id_fkey;
ALTER TABLE orders DROP COLUMN IF EXISTS user_id;
ALTER TABLE orders ADD CONSTRAINT orders_customer_id_fkey
FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL;

-- Recreate the auto-create trigger
CREATE OR REPLACE FUNCTION create_customer_for_user()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.role = 'customer' AND NOT EXISTS (SELECT 1 FROM customers WHERE user_id = NEW.id) THEN
        INSERT INTO customers (user_id, email, first_name, last_name, phone)
        VALUES (NEW.id, NEW.email, NEW.first_name, NEW.last_name, NEW.phone);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_customer_on_user_insert
AFTER INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION create_customer_for_user();

COMMIT;
*/