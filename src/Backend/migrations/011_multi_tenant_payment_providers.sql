-- Migration: Multi-Tenant Payment Provider Support
-- Description: Add support for tenant-specific payment provider configurations and secure credential storage
-- Date: 2025-09-09
-- Version: 1.0.0

-- =====================================================
-- 1. PAYMENT CREDENTIALS TABLE (Secure Storage)
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_credentials (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    credential_type VARCHAR(50) NOT NULL,
    encrypted_data TEXT NOT NULL,
    encryption_metadata JSONB NOT NULL,
    description TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create indexes for credential lookups
CREATE INDEX idx_payment_credentials_tenant ON payment_credentials(tenant_id, provider, is_active);
CREATE INDEX idx_payment_credentials_type ON payment_credentials(credential_type, is_active);
CREATE INDEX idx_payment_credentials_expires ON payment_credentials(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_payment_credentials_active ON payment_credentials(is_active, tenant_id);

-- =====================================================
-- 2. TENANT PAYMENT PROVIDERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    credential_id VARCHAR(64) REFERENCES payment_credentials(id),
    
    -- Provider specific identifiers
    merchant_id VARCHAR(255),
    store_id VARCHAR(255),
    location_id VARCHAR(255),
    terminal_id VARCHAR(255),
    
    -- Configuration
    environment VARCHAR(20) DEFAULT 'sandbox' CHECK (environment IN ('sandbox', 'production')),
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    
    -- OAuth tokens (for providers like Clover, Square)
    oauth_access_token TEXT,
    oauth_refresh_token TEXT,
    oauth_expires_at TIMESTAMP WITH TIME ZONE,
    oauth_scope TEXT,
    
    -- Webhook configuration
    webhook_endpoint_id VARCHAR(255),
    webhook_signing_secret TEXT,
    webhook_events TEXT[],
    
    -- Fee configuration
    platform_fee_percentage DECIMAL(5,4) DEFAULT 0.0200, -- 2% default
    platform_fee_fixed DECIMAL(10,2) DEFAULT 0.00,
    
    -- Capabilities and limits
    capabilities JSONB DEFAULT '{}'::JSONB,
    daily_limit DECIMAL(12,2),
    transaction_limit DECIMAL(10,2),
    
    -- Metadata
    settings JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unavailable', 'unknown')),
    
    UNIQUE(tenant_id, provider_id, environment)
);

-- Create indexes
CREATE INDEX idx_tenant_payment_providers_tenant ON tenant_payment_providers(tenant_id, is_active);
CREATE INDEX idx_tenant_payment_providers_provider ON tenant_payment_providers(provider_id, is_active);
CREATE INDEX idx_tenant_payment_providers_primary ON tenant_payment_providers(tenant_id, is_primary) WHERE is_primary = true;
CREATE INDEX idx_tenant_payment_providers_health ON tenant_payment_providers(health_status, last_health_check);

-- =====================================================
-- 3. PAYMENT AUDIT LOG TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    details JSONB DEFAULT '{}'::JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit log
CREATE INDEX idx_payment_audit_tenant ON payment_audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_payment_audit_action ON payment_audit_log(action, created_at DESC);
CREATE INDEX idx_payment_audit_entity ON payment_audit_log(entity_type, entity_id);
CREATE INDEX idx_payment_audit_created ON payment_audit_log(created_at DESC);

-- =====================================================
-- 4. PAYMENT PROVIDER HEALTH METRICS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_provider_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_provider_id UUID REFERENCES tenant_payment_providers(id) ON DELETE CASCADE,
    
    -- Metrics
    response_time_ms INTEGER,
    status_code INTEGER,
    is_successful BOOLEAN,
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Request details
    endpoint VARCHAR(255),
    method VARCHAR(10),
    
    -- Timestamp
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_health_metrics_provider ON payment_provider_health_metrics(tenant_provider_id, checked_at DESC);
CREATE INDEX idx_health_metrics_success ON payment_provider_health_metrics(is_successful, checked_at DESC);

-- =====================================================
-- 5. IDEMPOTENCY KEYS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_idempotency_keys (
    idempotency_key VARCHAR(255) PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    request_hash VARCHAR(64) NOT NULL,
    response JSONB,
    status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

-- Create indexes
CREATE INDEX idx_idempotency_tenant ON payment_idempotency_keys(tenant_id, created_at DESC);
CREATE INDEX idx_idempotency_expires ON payment_idempotency_keys(expires_at);
CREATE INDEX idx_idempotency_status ON payment_idempotency_keys(status, created_at DESC);

-- =====================================================
-- 6. PAYMENT WEBHOOKS ROUTING TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_webhook_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_provider_id UUID REFERENCES tenant_payment_providers(id) ON DELETE CASCADE,
    webhook_url_path VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_webhook_routes_path ON payment_webhook_routes(webhook_url_path) WHERE is_active = true;
CREATE INDEX idx_webhook_routes_tenant ON payment_webhook_routes(tenant_id, provider);

-- =====================================================
-- 7. TENANT SETTLEMENT ACCOUNTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_settlement_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    
    -- Bank account details (encrypted)
    account_holder_name VARCHAR(255),
    account_type VARCHAR(20) CHECK (account_type IN ('checking', 'savings')),
    routing_number_encrypted TEXT,
    account_number_encrypted TEXT,
    
    -- Settlement configuration
    settlement_schedule VARCHAR(20) DEFAULT 'daily' CHECK (settlement_schedule IN ('instant', 'daily', 'weekly', 'monthly')),
    minimum_payout_amount DECIMAL(10,2) DEFAULT 0.00,
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_method VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    suspended_at TIMESTAMP WITH TIME ZONE,
    suspension_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, provider_id)
);

-- Create indexes
CREATE INDEX idx_settlement_accounts_tenant ON tenant_settlement_accounts(tenant_id, is_active);
CREATE INDEX idx_settlement_accounts_verified ON tenant_settlement_accounts(is_verified, tenant_id);

-- =====================================================
-- 8. MODIFY PAYMENT_TRANSACTIONS TABLE
-- =====================================================
ALTER TABLE payment_transactions 
ADD COLUMN IF NOT EXISTS tenant_provider_id UUID REFERENCES tenant_payment_providers(id),
ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255),
ADD COLUMN IF NOT EXISTS platform_fee DECIMAL(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS tenant_net_amount DECIMAL(10,2);

-- Add index for tenant provider
CREATE INDEX IF NOT EXISTS idx_payment_transactions_tenant_provider 
ON payment_transactions(tenant_provider_id, created_at DESC);

-- Add index for idempotency
CREATE INDEX IF NOT EXISTS idx_payment_transactions_idempotency 
ON payment_transactions(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- =====================================================
-- 9. PLATFORM FEE SPLITS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_fee_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    -- Amounts
    gross_amount DECIMAL(10,2) NOT NULL,
    provider_fee DECIMAL(10,2) DEFAULT 0.00,
    platform_fee DECIMAL(10,2) DEFAULT 0.00,
    tenant_net_amount DECIMAL(10,2) NOT NULL,
    
    -- Fee breakdown
    platform_percentage_fee DECIMAL(10,2) DEFAULT 0.00,
    platform_fixed_fee DECIMAL(10,2) DEFAULT 0.00,
    
    -- Settlement status
    platform_fee_collected BOOLEAN DEFAULT false,
    platform_fee_collected_at TIMESTAMP WITH TIME ZONE,
    tenant_settled BOOLEAN DEFAULT false,
    tenant_settled_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(transaction_id)
);

-- Create indexes
CREATE INDEX idx_fee_splits_tenant ON payment_fee_splits(tenant_id, created_at DESC);
CREATE INDEX idx_fee_splits_settlement ON payment_fee_splits(tenant_settled, platform_fee_collected);

-- =====================================================
-- 10. FUNCTIONS FOR MULTI-TENANT SUPPORT
-- =====================================================

-- Function to get primary payment provider for tenant
CREATE OR REPLACE FUNCTION get_tenant_primary_provider(
    p_tenant_id UUID,
    p_provider_type VARCHAR(50) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_provider_id UUID;
BEGIN
    SELECT tpp.id INTO v_provider_id
    FROM tenant_payment_providers tpp
    JOIN payment_providers pp ON tpp.provider_id = pp.id
    WHERE tpp.tenant_id = p_tenant_id
    AND tpp.is_active = true
    AND tpp.is_primary = true
    AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
    LIMIT 1;
    
    -- If no primary, get first active
    IF v_provider_id IS NULL THEN
        SELECT tpp.id INTO v_provider_id
        FROM tenant_payment_providers tpp
        JOIN payment_providers pp ON tpp.provider_id = pp.id
        WHERE tpp.tenant_id = p_tenant_id
        AND tpp.is_active = true
        AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
        ORDER BY tpp.created_at
        LIMIT 1;
    END IF;
    
    RETURN v_provider_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate platform fees
CREATE OR REPLACE FUNCTION calculate_platform_fee(
    p_amount DECIMAL(10,2),
    p_percentage_fee DECIMAL(5,4),
    p_fixed_fee DECIMAL(10,2)
) RETURNS TABLE(
    platform_fee DECIMAL(10,2),
    tenant_net DECIMAL(10,2)
) AS $$
BEGIN
    platform_fee := ROUND((p_amount * p_percentage_fee) + p_fixed_fee, 2);
    tenant_net := p_amount - platform_fee;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to validate idempotency key
CREATE OR REPLACE FUNCTION check_idempotency_key(
    p_key VARCHAR(255),
    p_tenant_id UUID,
    p_request_hash VARCHAR(64)
) RETURNS JSONB AS $$
DECLARE
    v_result RECORD;
BEGIN
    -- Check for existing key
    SELECT status, response, request_hash
    INTO v_result
    FROM payment_idempotency_keys
    WHERE idempotency_key = p_key
    AND tenant_id = p_tenant_id
    AND expires_at > CURRENT_TIMESTAMP;
    
    IF v_result.status IS NOT NULL THEN
        -- Key exists, check if same request
        IF v_result.request_hash = p_request_hash THEN
            -- Same request, return cached response
            RETURN v_result.response;
        ELSE
            -- Different request with same key
            RAISE EXCEPTION 'Idempotency key already used for different request';
        END IF;
    END IF;
    
    -- Key doesn't exist, insert it
    INSERT INTO payment_idempotency_keys (
        idempotency_key, tenant_id, request_hash, status
    ) VALUES (
        p_key, p_tenant_id, p_request_hash, 'processing'
    );
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 11. TRIGGERS
-- =====================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers to new tables
CREATE TRIGGER update_payment_credentials_updated_at
BEFORE UPDATE ON payment_credentials
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_payment_providers_updated_at
BEFORE UPDATE ON tenant_payment_providers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_webhook_routes_updated_at
BEFORE UPDATE ON payment_webhook_routes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_settlement_accounts_updated_at
BEFORE UPDATE ON tenant_settlement_accounts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 12. ROW LEVEL SECURITY POLICIES
-- =====================================================

-- Enable RLS on sensitive tables
ALTER TABLE payment_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_payment_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_settlement_accounts ENABLE ROW LEVEL SECURITY;

-- Create policies for tenant isolation
CREATE POLICY tenant_isolation_payment_credentials ON payment_credentials
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM tenant_users 
        WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

CREATE POLICY tenant_isolation_tenant_payment_providers ON tenant_payment_providers
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM tenant_users 
        WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

-- =====================================================
-- 13. CLEANUP FUNCTIONS
-- =====================================================

-- Function to cleanup expired idempotency keys
CREATE OR REPLACE FUNCTION cleanup_expired_idempotency_keys()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_idempotency_keys
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old audit logs (keep 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_audit_log
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;