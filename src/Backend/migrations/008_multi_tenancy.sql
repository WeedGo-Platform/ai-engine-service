-- Migration: Multi-Tenancy Support
-- Description: Add support for multiple tenants, stores, and subscription management
-- Date: 2025-09-08
-- Version: 1.0.0

-- =====================================================
-- 1. PROVINCES AND TERRITORIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS provinces_territories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(2) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('province', 'territory')),
    tax_rate DECIMAL(5,2) DEFAULT 13.00,
    cannabis_tax_rate DECIMAL(5,2),
    min_age INTEGER DEFAULT 19,
    regulatory_body VARCHAR(255),
    license_prefix VARCHAR(10),
    delivery_allowed BOOLEAN DEFAULT true,
    pickup_allowed BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for province/territory lookups
CREATE INDEX idx_provinces_territories_code ON provinces_territories(code);

-- Insert Canadian provinces and territories
INSERT INTO provinces_territories (code, name, type, tax_rate, min_age, regulatory_body) VALUES
    ('ON', 'Ontario', 'province', 13.00, 19, 'AGCO'),
    ('BC', 'British Columbia', 'province', 12.00, 19, 'LCRB'),
    ('AB', 'Alberta', 'province', 5.00, 18, 'AGLC'),
    ('QC', 'Quebec', 'province', 14.975, 21, 'SQDC'),
    ('MB', 'Manitoba', 'province', 12.00, 19, 'LGCA'),
    ('SK', 'Saskatchewan', 'province', 11.00, 19, 'SLGA'),
    ('NS', 'Nova Scotia', 'province', 15.00, 19, 'NSLC'),
    ('NB', 'New Brunswick', 'province', 15.00, 19, 'Cannabis NB'),
    ('NL', 'Newfoundland and Labrador', 'province', 15.00, 19, 'NLC'),
    ('PE', 'Prince Edward Island', 'province', 15.00, 19, 'PEILCC'),
    ('NT', 'Northwest Territories', 'territory', 5.00, 19, 'NTLCC'),
    ('YT', 'Yukon', 'territory', 5.00, 19, 'YLC'),
    ('NU', 'Nunavut', 'territory', 5.00, 19, 'NULC')
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- 2. TENANTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    business_number VARCHAR(100),
    gst_hst_number VARCHAR(15),
    address JSONB DEFAULT '{}'::JSONB,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    website VARCHAR(255),
    logo_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled', 'trial')),
    subscription_tier VARCHAR(20) DEFAULT 'community' CHECK (subscription_tier IN ('community', 'basic', 'small_business', 'enterprise')),
    max_stores INTEGER DEFAULT 1,
    billing_info JSONB DEFAULT '{}'::JSONB,
    currency VARCHAR(3) DEFAULT 'CAD',
    settings JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tenant lookups
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_subscription_tier ON tenants(subscription_tier);

-- =====================================================
-- 3. STORES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    province_territory_id UUID NOT NULL REFERENCES provinces_territories(id),
    store_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address JSONB DEFAULT '{}'::JSONB,
    phone VARCHAR(50),
    email VARCHAR(255),
    hours JSONB DEFAULT '{}'::JSONB,
    timezone VARCHAR(50) DEFAULT 'America/Toronto',
    license_number VARCHAR(100),
    license_expiry DATE,
    tax_rate DECIMAL(5,2),
    delivery_radius_km INTEGER DEFAULT 10,
    delivery_enabled BOOLEAN DEFAULT true,
    pickup_enabled BOOLEAN DEFAULT true,
    kiosk_enabled BOOLEAN DEFAULT false,
    pos_enabled BOOLEAN DEFAULT true,
    ecommerce_enabled BOOLEAN DEFAULT true,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    settings JSONB DEFAULT '{}'::JSONB,
    pos_integration JSONB DEFAULT '{}'::JSONB,
    seo_config JSONB DEFAULT '{}'::JSONB,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for store lookups
CREATE INDEX idx_stores_tenant ON stores(tenant_id);
CREATE INDEX idx_stores_province_territory ON stores(province_territory_id);
CREATE INDEX idx_stores_status ON stores(status);
CREATE INDEX idx_stores_location ON stores(latitude, longitude);

-- =====================================================
-- 4. TENANT USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'manager')),
    permissions JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, user_id)
);

-- Create indexes for tenant user lookups
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX idx_tenant_users_active ON tenant_users(is_active);

-- =====================================================
-- 5. STORE USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS store_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'supervisor', 'staff', 'cashier')),
    cannsell_certification VARCHAR(100),
    certification_expiry DATE,
    permissions JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, user_id)
);

-- Create indexes for store user lookups
CREATE INDEX idx_store_users_store ON store_users(store_id);
CREATE INDEX idx_store_users_user ON store_users(user_id);
CREATE INDEX idx_store_users_active ON store_users(is_active);

-- =====================================================
-- 6. AI PERSONALITIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_personalities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    personality_type VARCHAR(50),
    avatar_url VARCHAR(500),
    voice_config JSONB DEFAULT '{}'::JSONB,
    traits JSONB DEFAULT '{}'::JSONB,
    greeting_message TEXT,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for AI personality lookups
CREATE INDEX idx_ai_personalities_tenant ON ai_personalities(tenant_id);
CREATE INDEX idx_ai_personalities_store ON ai_personalities(store_id);
CREATE INDEX idx_ai_personalities_active ON ai_personalities(is_active);

-- =====================================================
-- 7. STORE AI AGENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS store_ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('budtender', 'support', 'analytics', 'inventory')),
    personality_id UUID REFERENCES ai_personalities(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for AI agent lookups
CREATE INDEX idx_store_ai_agents_store ON store_ai_agents(store_id);
CREATE INDEX idx_store_ai_agents_active ON store_ai_agents(is_active);

-- =====================================================
-- 8. TENANT SUBSCRIPTIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('community', 'basic', 'small_business', 'enterprise')),
    store_limit INTEGER,
    ai_personalities_per_store INTEGER DEFAULT 1,
    billing_cycle VARCHAR(10) CHECK (billing_cycle IN ('monthly', 'annual')),
    price_cad DECIMAL(10,2) DEFAULT 0,
    features JSONB DEFAULT '{}'::JSONB,
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    next_billing_date DATE,
    trial_ends_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for subscription lookups
CREATE INDEX idx_tenant_subscriptions_tenant ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_tenant_subscriptions_status ON tenant_subscriptions(status);
CREATE INDEX idx_tenant_subscriptions_billing ON tenant_subscriptions(next_billing_date) WHERE status = 'active';

-- =====================================================
-- 9. TENANT FEATURES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    configuration JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature_key)
);

-- Create indexes for feature lookups
CREATE INDEX idx_tenant_features_tenant ON tenant_features(tenant_id);
CREATE INDEX idx_tenant_features_key ON tenant_features(feature_key);

-- =====================================================
-- 10. TENANT SETTINGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, category, key)
);

-- Create indexes for settings lookups
CREATE INDEX idx_tenant_settings_tenant ON tenant_settings(tenant_id);
CREATE INDEX idx_tenant_settings_category ON tenant_settings(category);

-- =====================================================
-- 11. STORE SETTINGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS store_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, category, key)
);

-- Create indexes for store settings lookups
CREATE INDEX idx_store_settings_store ON store_settings(store_id);
CREATE INDEX idx_store_settings_category ON store_settings(category);

-- =====================================================
-- 12. STORE INVENTORY TABLE (Replaces inventory table)
-- =====================================================
CREATE TABLE IF NOT EXISTS store_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    quantity_on_hand INTEGER DEFAULT 0 CHECK (quantity_on_hand >= 0),
    quantity_available INTEGER DEFAULT 0 CHECK (quantity_available >= 0),
    quantity_reserved INTEGER DEFAULT 0 CHECK (quantity_reserved >= 0),
    min_stock_level INTEGER DEFAULT 10,
    max_stock_level INTEGER DEFAULT 100,
    is_available BOOLEAN DEFAULT true,
    override_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, sku),
    CONSTRAINT fk_store_inventory_sku FOREIGN KEY (sku) 
        REFERENCES product_catalog(ocs_variant_number) ON UPDATE CASCADE
);

-- Create indexes for inventory lookups
CREATE INDEX idx_store_inventory_store ON store_inventory(store_id);
CREATE INDEX idx_store_inventory_sku ON store_inventory(sku);
CREATE INDEX idx_store_inventory_available ON store_inventory(is_available);

-- =====================================================
-- 13. STORE COMPLIANCE TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS store_compliance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    compliance_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('compliant', 'non_compliant', 'pending')),
    last_inspection DATE,
    next_inspection DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for compliance lookups
CREATE INDEX idx_store_compliance_store ON store_compliance(store_id);
CREATE INDEX idx_store_compliance_status ON store_compliance(status);

-- =====================================================
-- 14. ALTER EXISTING TABLES
-- =====================================================

-- Add tenant and store columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS default_store_id UUID REFERENCES stores(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS cannsell_certified BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS cannsell_number VARCHAR(100);

-- Add tenant and store columns to orders table
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id),
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS ai_agent_id UUID REFERENCES store_ai_agents(id),
ADD COLUMN IF NOT EXISTS tax_breakdown JSONB,
ADD COLUMN IF NOT EXISTS cannabis_tax DECIMAL(10,2);

-- Add tenant and store columns to cart_sessions table
ALTER TABLE cart_sessions
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id),
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS ai_personality_id UUID REFERENCES ai_personalities(id),
ADD COLUMN IF NOT EXISTS tax_calculation JSONB;

-- Add tenant and store columns to customers table
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS primary_store_id UUID REFERENCES stores(id),
ADD COLUMN IF NOT EXISTS age_verified_date DATE,
ADD COLUMN IF NOT EXISTS province VARCHAR(2);

-- Add tenant and store columns to purchase_orders table
ALTER TABLE purchase_orders
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id),
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS ocs_order_number VARCHAR(100);

-- Add tenant column to suppliers table
ALTER TABLE suppliers
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS is_ocs BOOLEAN DEFAULT false;

-- Add store column to batch_tracking table
ALTER TABLE batch_tracking
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);

-- Add store column to inventory_transactions table
ALTER TABLE inventory_transactions
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);

-- Add tenant and store columns to ai_conversations table
ALTER TABLE ai_conversations
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id),
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
ADD COLUMN IF NOT EXISTS personality_id UUID REFERENCES ai_personalities(id),
ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES store_ai_agents(id);

-- Add tenant and store columns to audit_log table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
        ALTER TABLE audit_log
        ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
        ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);
    END IF;
END $$;

-- Add tenant column to api_keys table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_keys') THEN
        ALTER TABLE api_keys
        ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id),
        ADD COLUMN IF NOT EXISTS allowed_stores UUID[];
    END IF;
END $$;

-- =====================================================
-- 15. CREATE UPDATE TIMESTAMP TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for all new tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stores_updated_at BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_users_updated_at BEFORE UPDATE ON tenant_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_users_updated_at BEFORE UPDATE ON store_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_personalities_updated_at BEFORE UPDATE ON ai_personalities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_ai_agents_updated_at BEFORE UPDATE ON store_ai_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_subscriptions_updated_at BEFORE UPDATE ON tenant_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_features_updated_at BEFORE UPDATE ON tenant_features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_settings_updated_at BEFORE UPDATE ON tenant_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_settings_updated_at BEFORE UPDATE ON store_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_inventory_updated_at BEFORE UPDATE ON store_inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_compliance_updated_at BEFORE UPDATE ON store_compliance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 16. INSERT DEFAULT TENANT FOR TESTING
-- =====================================================

-- Insert a default tenant for testing
INSERT INTO tenants (name, code, company_name, status, subscription_tier, max_stores)
VALUES ('Demo Dispensary', 'DEMO', 'Demo Dispensary Inc.', 'active', 'community', 1)
ON CONFLICT (code) DO NOTHING;

-- Migration complete
-- Note: Run this migration with caution in production environments
-- Consider backing up your database before applying these changes