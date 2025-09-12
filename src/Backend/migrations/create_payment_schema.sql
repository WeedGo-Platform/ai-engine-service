-- Payment System Schema for WeedGo
-- Supports multiple payment processors: Moneris, Clover, Interac, Nuvei, PayBright

-- Payment Providers Configuration
CREATE TABLE IF NOT EXISTS payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL, -- 'moneris', 'clover', 'interac', 'nuvei', 'paybright'
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    configuration JSONB DEFAULT '{}', -- Store encrypted API keys, merchant IDs, etc.
    supported_currencies TEXT[] DEFAULT ARRAY['CAD'],
    supported_card_types TEXT[] DEFAULT ARRAY['visa', 'mastercard', 'amex'],
    capabilities JSONB DEFAULT '{}', -- refunds, partial_refunds, recurring, etc.
    fee_structure JSONB DEFAULT '{}', -- transaction fees, monthly fees, etc.
    settlement_schedule VARCHAR(50) DEFAULT 'daily', -- daily, weekly, monthly
    webhook_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customer Payment Methods (tokenized)
CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES payment_providers(id),
    type VARCHAR(50) NOT NULL, -- 'card', 'bank_account', 'interac', 'wallet'
    payment_token TEXT, -- Tokenized payment data from provider
    display_name VARCHAR(100), -- e.g., "Visa ending in 4242"
    card_brand VARCHAR(20), -- visa, mastercard, amex
    card_last_four VARCHAR(4),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    billing_address JSONB DEFAULT '{}',
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, payment_token, provider_id)
);

-- Payment Transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_reference VARCHAR(100) UNIQUE NOT NULL, -- Our internal reference
    provider_transaction_id VARCHAR(255), -- Provider's transaction ID
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES tenants(id),
    payment_method_id UUID REFERENCES payment_methods(id),
    provider_id UUID REFERENCES payment_providers(id),
    
    -- Transaction details
    type VARCHAR(50) NOT NULL, -- 'charge', 'refund', 'partial_refund', 'void', 'pre_auth'
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    tax_amount DECIMAL(10,2) DEFAULT 0,
    
    -- Fee tracking
    provider_fee DECIMAL(10,2) DEFAULT 0,
    platform_fee DECIMAL(10,2) DEFAULT 0,
    net_amount DECIMAL(10,2), -- amount - fees
    
    -- Response data
    provider_response JSONB DEFAULT '{}', -- Full response from provider
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- 3D Secure / Authentication
    authentication_status VARCHAR(50), -- 'required', 'completed', 'failed', 'not_required'
    authentication_data JSONB DEFAULT '{}',
    
    -- Risk and fraud
    risk_score INTEGER,
    risk_factors JSONB DEFAULT '{}',
    fraud_status VARCHAR(50), -- 'pass', 'review', 'block'
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    device_fingerprint TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for payment_transactions
CREATE INDEX idx_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_transactions_tenant ON payment_transactions(tenant_id);
CREATE INDEX idx_transactions_status ON payment_transactions(status);
CREATE INDEX idx_transactions_created ON payment_transactions(created_at DESC);
CREATE INDEX idx_transactions_provider_ref ON payment_transactions(provider_transaction_id, provider_id);

-- Refunds and Adjustments
CREATE TABLE IF NOT EXISTS payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(id) ON DELETE CASCADE,
    refund_transaction_id UUID REFERENCES payment_transactions(id),
    amount DECIMAL(10,2) NOT NULL,
    reason VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    provider_refund_id VARCHAR(255),
    initiated_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Payment Settlements (from providers)
CREATE TABLE IF NOT EXISTS payment_settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES payment_providers(id),
    settlement_id VARCHAR(255), -- Provider's settlement/batch ID
    settlement_date DATE NOT NULL,
    
    -- Amounts
    gross_amount DECIMAL(12,2) NOT NULL,
    fee_amount DECIMAL(10,2) DEFAULT 0,
    refund_amount DECIMAL(10,2) DEFAULT 0,
    chargeback_amount DECIMAL(10,2) DEFAULT 0,
    adjustment_amount DECIMAL(10,2) DEFAULT 0,
    net_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    
    -- Transaction counts
    transaction_count INTEGER DEFAULT 0,
    refund_count INTEGER DEFAULT 0,
    chargeback_count INTEGER DEFAULT 0,
    
    -- Bank details
    bank_account_last_four VARCHAR(4),
    deposit_date DATE,
    
    -- Status and files
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'deposited', 'reconciled'
    settlement_report_url TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reconciled_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for payment_settlements
CREATE INDEX idx_settlements_date ON payment_settlements(settlement_date DESC);
CREATE INDEX idx_settlements_provider ON payment_settlements(provider_id, settlement_date DESC);

-- Recurring Payment Subscriptions
CREATE TABLE IF NOT EXISTS payment_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    payment_method_id UUID REFERENCES payment_methods(id),
    provider_id UUID REFERENCES payment_providers(id),
    
    -- Subscription details
    subscription_id VARCHAR(255), -- Provider's subscription ID
    plan_name VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    interval VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
    interval_count INTEGER DEFAULT 1,
    
    -- Status
    status VARCHAR(50) NOT NULL, -- 'active', 'paused', 'cancelled', 'expired'
    trial_end_date DATE,
    current_period_start DATE,
    current_period_end DATE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Billing
    next_billing_date DATE,
    billing_cycles_completed INTEGER DEFAULT 0,
    failed_payment_count INTEGER DEFAULT 0,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for payment_subscriptions
CREATE INDEX idx_subscriptions_tenant ON payment_subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON payment_subscriptions(status);
CREATE INDEX idx_subscriptions_next_billing ON payment_subscriptions(next_billing_date);

-- Webhooks from payment providers
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES payment_providers(id),
    webhook_id VARCHAR(255), -- Provider's webhook ID
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    signature TEXT,
    signature_verified BOOLEAN DEFAULT false,
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for payment_webhooks
CREATE INDEX idx_webhooks_provider ON payment_webhooks(provider_id, received_at DESC);
CREATE INDEX idx_webhooks_processed ON payment_webhooks(processed, received_at);

-- Payment Disputes/Chargebacks
CREATE TABLE IF NOT EXISTS payment_disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(id),
    provider_id UUID REFERENCES payment_providers(id),
    dispute_id VARCHAR(255), -- Provider's dispute ID
    
    type VARCHAR(50) NOT NULL, -- 'chargeback', 'retrieval', 'fraud'
    status VARCHAR(50) NOT NULL, -- 'open', 'under_review', 'won', 'lost'
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    
    reason VARCHAR(255),
    reason_code VARCHAR(50),
    evidence_due_date DATE,
    
    -- Documentation
    merchant_response TEXT,
    evidence_submitted JSONB DEFAULT '{}',
    provider_response JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for payment_disputes
CREATE INDEX idx_disputes_status ON payment_disputes(status);
CREATE INDEX idx_disputes_transaction ON payment_disputes(transaction_id);

-- Payment Analytics/Metrics
CREATE TABLE IF NOT EXISTS payment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    provider_id UUID REFERENCES payment_providers(id),
    
    -- Transaction metrics
    total_transactions INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    failed_transactions INTEGER DEFAULT 0,
    
    -- Amount metrics
    total_amount DECIMAL(12,2) DEFAULT 0,
    total_fees DECIMAL(10,2) DEFAULT 0,
    total_refunds DECIMAL(10,2) DEFAULT 0,
    net_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Performance metrics
    avg_transaction_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    
    -- By payment type
    metrics_by_type JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(date, provider_id)
);

-- Create indexes for payment_metrics
CREATE INDEX idx_metrics_date ON payment_metrics(date DESC);

-- Insert default payment providers
INSERT INTO payment_providers (name, provider_type, is_active, is_default, capabilities, supported_card_types) VALUES
('Moneris', 'moneris', true, true, 
 '{"refunds": true, "partial_refunds": true, "recurring": true, "tokenization": true, "3d_secure": true}',
 ARRAY['visa', 'mastercard', 'amex']),
('Clover', 'clover', true, false,
 '{"refunds": true, "partial_refunds": true, "recurring": false, "tokenization": true, "pos_integration": true}',
 ARRAY['visa', 'mastercard', 'amex', 'discover']),
('Interac e-Transfer', 'interac', true, false,
 '{"refunds": false, "instant_verification": true, "auto_deposit": true}',
 ARRAY[]::TEXT[]),
('Nuvei', 'nuvei', true, false,
 '{"refunds": true, "partial_refunds": true, "recurring": true, "tokenization": true, "3d_secure": true, "alternative_payments": true}',
 ARRAY['visa', 'mastercard', 'amex']),
('PayBright', 'paybright', true, false,
 '{"installments": true, "refunds": true, "instant_approval": true}',
 ARRAY[]::TEXT[])
ON CONFLICT (name) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_payment_providers_updated_at BEFORE UPDATE ON payment_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_methods_updated_at BEFORE UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_subscriptions_updated_at BEFORE UPDATE ON payment_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_disputes_updated_at BEFORE UPDATE ON payment_disputes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();