-- Restore Tenant Tables
-- This script recreates the tenant management tables

BEGIN TRANSACTION;

-- =========================================
-- Restore tenant management tables
-- =========================================

-- 1. Tenant settings
CREATE TABLE IF NOT EXISTS tenant_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB,
    setting_type VARCHAR(50), -- 'general', 'payment', 'compliance', 'features'
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, setting_key)
);

-- 2. Tenant features
CREATE TABLE IF NOT EXISTS tenant_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT false,
    configuration JSONB DEFAULT '{}'::jsonb,
    enabled_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature_name)
);

-- 3. Tenant subscriptions
CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    plan_name VARCHAR(100) NOT NULL,
    plan_type VARCHAR(50), -- 'basic', 'pro', 'enterprise'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'suspended', 'cancelled'
    billing_cycle VARCHAR(20), -- 'monthly', 'yearly'
    price_per_cycle DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'CAD',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancelled_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tenant payment providers
CREATE TABLE IF NOT EXISTS tenant_payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    provider_name VARCHAR(50) NOT NULL, -- 'clover', 'moneris', 'stripe'
    provider_type VARCHAR(50) NOT NULL, -- 'online', 'pos', 'both'
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    configuration JSONB, -- Encrypted provider-specific config
    credentials JSONB, -- Encrypted credentials
    supported_methods JSONB DEFAULT '["card", "cash"]'::jsonb,
    fee_structure JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, provider_name, provider_type)
);

-- 5. Tenant settlement accounts
CREATE TABLE IF NOT EXISTS tenant_settlement_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    payment_provider_id UUID REFERENCES tenant_payment_providers(id) ON DELETE CASCADE,
    account_type VARCHAR(50), -- 'bank', 'card', 'digital_wallet'
    account_name VARCHAR(200),
    account_number VARCHAR(100), -- Encrypted
    routing_number VARCHAR(100), -- Encrypted
    currency VARCHAR(3) DEFAULT 'CAD',
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    verification_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'verified', 'failed'
    verified_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_id ON tenant_settings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_key ON tenant_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_tenant_features_tenant_id ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_features_enabled ON tenant_features(is_enabled);
CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_status ON tenant_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_tenant_payment_providers_tenant_id ON tenant_payment_providers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_payment_providers_active ON tenant_payment_providers(is_active);
CREATE INDEX IF NOT EXISTS idx_tenant_settlement_accounts_tenant_id ON tenant_settlement_accounts(tenant_id);

-- Insert default settings for existing tenants
INSERT INTO tenant_settings (tenant_id, setting_key, setting_value, setting_type)
SELECT
    id,
    'default_settings',
    '{"initialized": true, "version": "1.0"}'::jsonb,
    'general'
FROM tenants
WHERE NOT EXISTS (
    SELECT 1 FROM tenant_settings WHERE tenant_id = tenants.id AND setting_key = 'default_settings'
);

-- Insert default features for existing tenants
INSERT INTO tenant_features (tenant_id, feature_name, is_enabled)
SELECT
    t.id,
    f.feature,
    true
FROM tenants t
CROSS JOIN (
    VALUES
        ('online_ordering'),
        ('pos_system'),
        ('inventory_management'),
        ('customer_profiles'),
        ('loyalty_program')
) AS f(feature)
WHERE NOT EXISTS (
    SELECT 1 FROM tenant_features WHERE tenant_id = t.id AND feature_name = f.feature
);

COMMIT;

-- Verify restoration
DO $$
DECLARE
    table_count INTEGER;
    settings_count INTEGER;
    features_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name IN (
        'tenant_settings',
        'tenant_features',
        'tenant_subscriptions',
        'tenant_payment_providers',
        'tenant_settlement_accounts'
    );

    SELECT COUNT(*) INTO settings_count FROM tenant_settings;
    SELECT COUNT(*) INTO features_count FROM tenant_features;

    RAISE NOTICE 'Restored % tenant tables', table_count;
    RAISE NOTICE 'Created % tenant settings records', settings_count;
    RAISE NOTICE 'Created % tenant features records', features_count;
END $$;