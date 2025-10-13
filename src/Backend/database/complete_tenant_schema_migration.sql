-- ============================================================================
-- Complete Tenant Schema Migration (Schema Only, No Data)
-- Description: Updates tenants table and creates all missing tenant-related tables
-- Date: October 12, 2025
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- STEP 1: Alter main tenants table to add missing columns
-- ============================================================================

ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS company_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS business_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS gst_hst_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS address JSONB,
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS website VARCHAR(500),
ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(100) DEFAULT 'community_and_new_business',
ADD COLUMN IF NOT EXISTS max_stores INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS billing_info JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS payment_provider_settings JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'CAD',
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add indexes for tenant table
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_subscription_tier ON tenants(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_tenants_contact_email ON tenants(contact_email);
CREATE INDEX IF NOT EXISTS idx_tenants_company_name ON tenants(company_name);

-- ============================================================================
-- STEP 2: Create tenant_settings table
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_id ON tenant_settings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_key ON tenant_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_type ON tenant_settings(setting_type);

COMMENT ON TABLE tenant_settings IS 'Tenant-specific configuration settings';
COMMENT ON COLUMN tenant_settings.setting_key IS 'Unique setting identifier within tenant';
COMMENT ON COLUMN tenant_settings.setting_value IS 'JSON setting value for flexibility';
COMMENT ON COLUMN tenant_settings.setting_type IS 'Category: general, payment, compliance, features';

-- ============================================================================
-- STEP 3: Create tenant_features table
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tenant_features_tenant_id ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_features_enabled ON tenant_features(is_enabled);
CREATE INDEX IF NOT EXISTS idx_tenant_features_name ON tenant_features(feature_name);

COMMENT ON TABLE tenant_features IS 'Feature flags and configurations per tenant';
COMMENT ON COLUMN tenant_features.feature_name IS 'Feature identifier (e.g., online_ordering, pos_system)';
COMMENT ON COLUMN tenant_features.configuration IS 'Feature-specific JSON configuration';
COMMENT ON COLUMN tenant_features.expires_at IS 'Optional feature expiration for trials';

-- ============================================================================
-- STEP 4: Create tenant_subscriptions table
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_status ON tenant_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_period_end ON tenant_subscriptions(current_period_end);

COMMENT ON TABLE tenant_subscriptions IS 'Tenant subscription and billing records';
COMMENT ON COLUMN tenant_subscriptions.plan_type IS 'Subscription tier level';
COMMENT ON COLUMN tenant_subscriptions.current_period_end IS 'When current billing period ends';

-- ============================================================================
-- STEP 5: Create tenant_payment_providers table
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tenant_payment_providers_tenant_id ON tenant_payment_providers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_payment_providers_active ON tenant_payment_providers(is_active);
CREATE INDEX IF NOT EXISTS idx_tenant_payment_providers_default ON tenant_payment_providers(is_default);

COMMENT ON TABLE tenant_payment_providers IS 'Payment provider configurations per tenant';
COMMENT ON COLUMN tenant_payment_providers.provider_name IS 'Provider: clover, moneris, stripe, etc.';
COMMENT ON COLUMN tenant_payment_providers.configuration IS 'Encrypted provider-specific settings';
COMMENT ON COLUMN tenant_payment_providers.credentials IS 'Encrypted API keys and secrets';

-- ============================================================================
-- STEP 6: Create tenant_settlement_accounts table
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tenant_settlement_accounts_tenant_id ON tenant_settlement_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settlement_accounts_provider_id ON tenant_settlement_accounts(payment_provider_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settlement_accounts_status ON tenant_settlement_accounts(verification_status);

COMMENT ON TABLE tenant_settlement_accounts IS 'Bank/settlement accounts for tenant payouts';
COMMENT ON COLUMN tenant_settlement_accounts.account_number IS 'Encrypted account number';
COMMENT ON COLUMN tenant_settlement_accounts.routing_number IS 'Encrypted routing/transit number';
COMMENT ON COLUMN tenant_settlement_accounts.verification_status IS 'Verification state: pending, verified, failed';

-- ============================================================================
-- STEP 7: Create update triggers for new tables
-- ============================================================================

-- Trigger for tenant_settings
CREATE TRIGGER update_tenant_settings_updated_at
BEFORE UPDATE ON tenant_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for tenant_features
CREATE TRIGGER update_tenant_features_updated_at
BEFORE UPDATE ON tenant_features
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for tenant_subscriptions
CREATE TRIGGER update_tenant_subscriptions_updated_at
BEFORE UPDATE ON tenant_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for tenant_payment_providers
CREATE TRIGGER update_tenant_payment_providers_updated_at
BEFORE UPDATE ON tenant_payment_providers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for tenant_settlement_accounts
CREATE TRIGGER update_tenant_settlement_accounts_updated_at
BEFORE UPDATE ON tenant_settlement_accounts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 8: Verification
-- ============================================================================

DO $$
DECLARE
    tenant_table_count INTEGER;
    tenant_column_count INTEGER;
BEGIN
    -- Count tenant-related tables
    SELECT COUNT(*) INTO tenant_table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name IN (
        'tenants',
        'tenant_settings',
        'tenant_features',
        'tenant_subscriptions',
        'tenant_payment_providers',
        'tenant_settlement_accounts'
    );

    -- Count columns in tenants table
    SELECT COUNT(*) INTO tenant_column_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'tenants';

    RAISE NOTICE '============================================';
    RAISE NOTICE 'MIGRATION COMPLETE';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tenant-related tables: %', tenant_table_count;
    RAISE NOTICE 'Columns in tenants table: %', tenant_column_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Expected:';
    RAISE NOTICE '  - 6 tenant tables';
    RAISE NOTICE '  - 21 columns in tenants table';
    RAISE NOTICE '';

    IF tenant_table_count = 6 THEN
        RAISE NOTICE '✓ All tenant tables created';
    ELSE
        RAISE WARNING '⚠ Expected 6 tables, found %', tenant_table_count;
    END IF;

    IF tenant_column_count >= 21 THEN
        RAISE NOTICE '✓ All tenant columns added';
    ELSE
        RAISE WARNING '⚠ Expected >= 21 columns, found %', tenant_column_count;
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Post-Migration Notes
-- ============================================================================

-- The following tables have been created/updated (SCHEMA ONLY):
--   1. tenants (updated with 16 new columns)
--   2. tenant_settings (new)
--   3. tenant_features (new)
--   4. tenant_subscriptions (new)
--   5. tenant_payment_providers (new)
--   6. tenant_settlement_accounts (new)
--
-- NO DATA HAS BEEN MIGRATED
--
-- Next steps:
--   1. Populate tenants with proper business information
--   2. Configure default features for each tenant
--   3. Set up payment providers as needed
--   4. Create subscription records
--   5. Test tenant repository queries
-- ============================================================================
