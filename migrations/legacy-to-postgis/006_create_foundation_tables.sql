-- ============================================================================
-- Migration: Create Foundation Tables
-- Description: Create core reference and profile tables
-- Dependencies: 005_alter_orders_table.sql
-- ============================================================================

-- Provinces and Territories Table (Canadian regions for compliance)
CREATE TABLE IF NOT EXISTS provinces_territories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(2) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    name_fr VARCHAR(100),
    tax_rate NUMERIC(5,2),
    cannabis_legal BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provinces_territories_code ON provinces_territories(code);

-- Provincial Suppliers Table
CREATE TABLE IF NOT EXISTS provincial_suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province_territory_id UUID NOT NULL REFERENCES provinces_territories(id),
    name VARCHAR(255) NOT NULL,
    supplier_code VARCHAR(50) UNIQUE,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    api_endpoint VARCHAR(500),
    api_credentials JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provincial_suppliers_province ON provincial_suppliers(province_territory_id);
CREATE INDEX IF NOT EXISTS idx_provincial_suppliers_active ON provincial_suppliers(is_active);

-- User Profiles Table (Extended user information)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    preferences JSONB DEFAULT '{}'::jsonb,
    loyalty_points INTEGER DEFAULT 0,
    loyalty_tier VARCHAR(50),
    referral_code VARCHAR(50) UNIQUE,
    referred_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_referral_code ON profiles(referral_code);
CREATE INDEX IF NOT EXISTS idx_profiles_loyalty_tier ON profiles(loyalty_tier);

-- Update users table to add FK to profiles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'users_profile_id_fkey'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_profile_id_fkey
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL;
    END IF;
END $$;

-- User Addresses Table
CREATE TABLE IF NOT EXISTS user_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label VARCHAR(50),
    street_address VARCHAR(500) NOT NULL,
    unit VARCHAR(50),
    city VARCHAR(100) NOT NULL,
    province_territory_id UUID REFERENCES provinces_territories(id),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) DEFAULT 'CA',
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    is_default BOOLEAN DEFAULT false,
    is_billing BOOLEAN DEFAULT false,
    is_shipping BOOLEAN DEFAULT true,
    delivery_instructions TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_addresses_user_id ON user_addresses(user_id);
CREATE INDEX IF NOT EXISTS idx_user_addresses_default ON user_addresses(user_id, is_default);
CREATE INDEX IF NOT EXISTS idx_user_addresses_location ON user_addresses(latitude, longitude);

-- System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    value_type VARCHAR(50) DEFAULT 'json',
    description TEXT,
    category VARCHAR(100),
    is_public BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);

-- Store Settings Table
CREATE TABLE IF NOT EXISTS store_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    value_type VARCHAR(50) DEFAULT 'json',
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, key)
);

CREATE INDEX IF NOT EXISTS idx_store_settings_store_id ON store_settings(store_id);
CREATE INDEX IF NOT EXISTS idx_store_settings_key ON store_settings(key);

-- Holidays Table
CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    province_territory_id UUID REFERENCES provinces_territories(id),
    is_statutory BOOLEAN DEFAULT false,
    is_recurring BOOLEAN DEFAULT true,
    recurrence_rule VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(date);
CREATE INDEX IF NOT EXISTS idx_holidays_province ON holidays(province_territory_id);

-- Role Permissions Table (RBAC)
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    permission VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    action VARCHAR(50),
    conditions JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role, permission, resource, action)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission);

COMMENT ON TABLE provinces_territories IS 'Canadian provinces and territories for regulatory compliance';
COMMENT ON TABLE provincial_suppliers IS 'Provincial cannabis suppliers (e.g., OCS, SQDC, AGLC)';
COMMENT ON TABLE profiles IS 'Extended user profile information and preferences';
COMMENT ON TABLE user_addresses IS 'User delivery and billing addresses';
COMMENT ON TABLE system_settings IS 'Global system configuration settings';
COMMENT ON TABLE store_settings IS 'Store-specific configuration overrides';
COMMENT ON TABLE holidays IS 'Statutory and observance holidays affecting store hours';
COMMENT ON TABLE role_permissions IS 'Role-based access control permission definitions';
