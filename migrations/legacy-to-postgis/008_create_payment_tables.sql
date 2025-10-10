-- ============================================================================
-- Migration: Create Payment Processing Tables
-- Description: Create comprehensive payment processing infrastructure
-- Dependencies: 007_create_inventory_tables.sql
-- ============================================================================

-- Payment Providers Configuration
CREATE TABLE IF NOT EXISTS payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_sandbox BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 100,
    supported_currencies TEXT[] DEFAULT '{CAD}'::TEXT[],
    supported_payment_methods TEXT[] DEFAULT '{}'::TEXT[],
    configuration JSONB DEFAULT '{}'::jsonb,
    rate_limits JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_providers_active ON payment_providers(is_active, priority);

-- Payment Credentials (encrypted)
CREATE TABLE IF NOT EXISTS payment_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES payment_providers(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    credential_type VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    additional_credentials JSONB,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_rotated_at TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_payment_credentials_provider ON payment_credentials(provider_id);
CREATE INDEX IF NOT EXISTS idx_payment_credentials_store ON payment_credentials(store_id);

-- Payment Methods (customer saved payment methods)
CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL,
    provider_id UUID REFERENCES payment_providers(id),
    token VARCHAR(255),
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    billing_address JSONB,
    is_default BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_default ON payment_methods(user_id, is_default);

-- Payment Transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id UUID REFERENCES stores(id),
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    transaction_type VARCHAR(50) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    provider_transaction_id VARCHAR(255),
    provider_response JSONB,
    payment_method_id UUID REFERENCES payment_methods(id),
    error_code VARCHAR(100),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_provider ON payment_transactions(provider_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_created ON payment_transactions(created_at DESC);

-- Payment Refunds
CREATE TABLE IF NOT EXISTS payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(id),
    refund_amount NUMERIC(10,2) NOT NULL,
    refund_reason VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    provider_refund_id VARCHAR(255),
    provider_response JSONB,
    requested_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_payment_refunds_transaction ON payment_refunds(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_status ON payment_refunds(status);

-- Payment Disputes (chargebacks)
CREATE TABLE IF NOT EXISTS payment_disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(id),
    dispute_type VARCHAR(50),
    dispute_amount NUMERIC(10,2) NOT NULL,
    dispute_reason TEXT,
    status VARCHAR(50) DEFAULT 'open',
    provider_dispute_id VARCHAR(255),
    evidence JSONB,
    due_date DATE,
    resolved_at TIMESTAMP WITHOUT TIME ZONE,
    resolution VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_disputes_transaction ON payment_disputes(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_status ON payment_disputes(status);

-- Payment Idempotency Keys (prevent duplicate payments)
CREATE TABLE IF NOT EXISTS payment_idempotency_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    transaction_id UUID REFERENCES payment_transactions(id),
    request_hash TEXT,
    response_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payment_idempotency_expires ON payment_idempotency_keys(expires_at);

-- Payment Settlements (batch settlements from providers)
CREATE TABLE IF NOT EXISTS payment_settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    settlement_date DATE NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,
    fee_amount NUMERIC(12,2) DEFAULT 0.00,
    net_amount NUMERIC(12,2) NOT NULL,
    transaction_count INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    provider_settlement_id VARCHAR(255),
    settlement_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_settlements_provider ON payment_settlements(provider_id);
CREATE INDEX IF NOT EXISTS idx_payment_settlements_date ON payment_settlements(settlement_date DESC);

-- Payment Fee Splits (marketplace fee distribution)
CREATE TABLE IF NOT EXISTS payment_fee_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(id),
    recipient_type VARCHAR(50) NOT NULL,
    recipient_id UUID,
    split_type VARCHAR(50) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    percentage NUMERIC(5,2),
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_fee_splits_transaction ON payment_fee_splits(transaction_id);

-- Payment Subscriptions
CREATE TABLE IF NOT EXISTS payment_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_method_id UUID REFERENCES payment_methods(id),
    plan_name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    billing_interval VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    current_period_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMP WITHOUT TIME ZONE,
    provider_subscription_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_subscriptions_user ON payment_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_subscriptions_status ON payment_subscriptions(status);

-- Payment Webhooks (provider webhook events)
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES payment_providers(id),
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255),
    payload JSONB NOT NULL,
    signature VARCHAR(500),
    is_verified BOOLEAN DEFAULT false,
    is_processed BOOLEAN DEFAULT false,
    processing_attempts INTEGER DEFAULT 0,
    processed_at TIMESTAMP WITHOUT TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_webhooks_provider ON payment_webhooks(provider_id);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_type ON payment_webhooks(event_type);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_processed ON payment_webhooks(is_processed);

-- Payment Webhook Routes (routing rules for webhook events)
CREATE TABLE IF NOT EXISTS payment_webhook_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    event_type VARCHAR(100) NOT NULL,
    handler_function VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_webhook_routes_provider ON payment_webhook_routes(provider_id, event_type);

-- Payment Audit Log
CREATE TABLE IF NOT EXISTS payment_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(id),
    action VARCHAR(100) NOT NULL,
    actor_type VARCHAR(50),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    old_value JSONB,
    new_value JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_audit_log_transaction ON payment_audit_log(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_log_user ON payment_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_log_created ON payment_audit_log(created_at DESC);

-- Payment Metrics (analytics)
CREATE TABLE IF NOT EXISTS payment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    store_id UUID REFERENCES stores(id),
    provider_id UUID REFERENCES payment_providers(id),
    total_transactions INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    failed_transactions INTEGER DEFAULT 0,
    total_amount NUMERIC(12,2) DEFAULT 0.00,
    total_fees NUMERIC(12,2) DEFAULT 0.00,
    average_transaction_value NUMERIC(10,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_date, store_id, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_payment_metrics_date ON payment_metrics(metric_date DESC);
CREATE INDEX IF NOT EXISTS idx_payment_metrics_store ON payment_metrics(store_id);

-- Payment Provider Health Metrics
CREATE TABLE IF NOT EXISTS payment_provider_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES payment_providers(id),
    check_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    is_available BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_provider_health_provider ON payment_provider_health_metrics(provider_id);
CREATE INDEX IF NOT EXISTS idx_payment_provider_health_time ON payment_provider_health_metrics(check_time DESC);

COMMENT ON TABLE payment_providers IS 'Payment gateway provider configurations';
COMMENT ON TABLE payment_credentials IS 'Encrypted API credentials for payment providers';
COMMENT ON TABLE payment_methods IS 'Customer saved payment methods (cards, accounts)';
COMMENT ON TABLE payment_transactions IS 'All payment transaction records';
COMMENT ON TABLE payment_refunds IS 'Refund transactions';
COMMENT ON TABLE payment_disputes IS 'Chargeback and dispute tracking';
COMMENT ON TABLE payment_idempotency_keys IS 'Prevents duplicate payment processing';
COMMENT ON TABLE payment_webhooks IS 'Incoming webhook events from payment providers';
