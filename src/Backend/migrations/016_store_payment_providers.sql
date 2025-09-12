-- =====================================================
-- Migration: Create store-specific payment provider configuration
-- Purpose: Enable each store to have its own payment processing settings
-- Author: System
-- Date: 2024
-- =====================================================

BEGIN;

-- =====================================================
-- Step 1: Create store_payment_providers table
-- =====================================================

CREATE TABLE IF NOT EXISTS store_payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Provider information
    provider_type VARCHAR(50) NOT NULL, -- stripe, square, clover, paypal, moneris
    provider_name VARCHAR(100),
    
    -- Encrypted credentials
    encrypted_credentials TEXT NOT NULL,
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    supported_methods TEXT[] DEFAULT ARRAY['credit_card', 'debit_card'],
    method_settings JSONB DEFAULT '{}',
    
    -- Fee structure
    fee_structure JSONB DEFAULT '{
        "transaction_fee_percent": 2.9,
        "transaction_fee_fixed": 0.30,
        "monthly_fee": 0,
        "setup_fee": 0,
        "chargeback_fee": 15.00,
        "refund_fee": 0
    }',
    
    -- Status
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    is_test_mode BOOLEAN DEFAULT false,
    
    -- Webhooks
    webhook_endpoint VARCHAR(500),
    webhook_secret VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(store_id, provider_type, provider_name)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_store ON store_payment_providers(store_id);
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_type ON store_payment_providers(provider_type);
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_primary ON store_payment_providers(store_id, is_primary) WHERE is_primary = true;
CREATE INDEX IF NOT EXISTS idx_store_payment_providers_active ON store_payment_providers(store_id, is_active) WHERE is_active = true;

-- =====================================================
-- Step 2: Create store_payment_terminals table (for POS)
-- =====================================================

CREATE TABLE IF NOT EXISTS store_payment_terminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES store_payment_providers(id) ON DELETE CASCADE,
    
    -- Terminal information
    terminal_id VARCHAR(100) NOT NULL,
    terminal_name VARCHAR(100),
    terminal_type VARCHAR(50), -- countertop, mobile, virtual
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    
    -- Location within store
    location VARCHAR(100),
    register_number VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(store_id, terminal_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_store_payment_terminals_store ON store_payment_terminals(store_id);
CREATE INDEX IF NOT EXISTS idx_store_payment_terminals_provider ON store_payment_terminals(provider_id);

-- =====================================================
-- Step 3: Create store_payment_methods table
-- =====================================================

CREATE TABLE IF NOT EXISTS store_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Method information
    method_type VARCHAR(50) NOT NULL, -- credit_card, debit_card, cash, bank_transfer, etc
    method_name VARCHAR(100),
    
    -- Configuration
    is_enabled BOOLEAN DEFAULT true,
    min_amount DECIMAL(10, 2),
    max_amount DECIMAL(10, 2),
    
    -- Provider mapping
    provider_id UUID REFERENCES store_payment_providers(id),
    
    -- Display settings
    display_order INTEGER DEFAULT 0,
    display_name VARCHAR(100),
    display_icon VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(store_id, method_type)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_store_payment_methods_store ON store_payment_methods(store_id);
CREATE INDEX IF NOT EXISTS idx_store_payment_methods_enabled ON store_payment_methods(store_id, is_enabled);

-- =====================================================
-- Step 4: Update payment_transactions for store context
-- =====================================================

-- Add store_id to payment_transactions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payment_transactions' 
        AND column_name = 'store_id'
    ) THEN
        ALTER TABLE payment_transactions 
        ADD COLUMN store_id UUID REFERENCES stores(id);
        
        -- Create index
        CREATE INDEX idx_payment_transactions_store 
        ON payment_transactions(store_id);
    END IF;
END $$;

-- Add provider_id to payment_transactions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payment_transactions' 
        AND column_name = 'provider_id'
    ) THEN
        ALTER TABLE payment_transactions 
        ADD COLUMN provider_id UUID REFERENCES store_payment_providers(id);
        
        -- Create index
        CREATE INDEX idx_payment_transactions_provider 
        ON payment_transactions(provider_id);
    END IF;
END $$;

-- =====================================================
-- Step 5: Create store_payment_reconciliation table
-- =====================================================

CREATE TABLE IF NOT EXISTS store_payment_reconciliation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES store_payment_providers(id),
    
    -- Reconciliation period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Transaction counts
    transaction_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    refunded_count INTEGER DEFAULT 0,
    
    -- Amounts
    gross_amount DECIMAL(12, 2) DEFAULT 0,
    fee_amount DECIMAL(10, 2) DEFAULT 0,
    net_amount DECIMAL(12, 2) DEFAULT 0,
    refunded_amount DECIMAL(12, 2) DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, reconciled, disputed
    reconciled_by UUID REFERENCES users(id),
    reconciled_at TIMESTAMP WITH TIME ZONE,
    
    -- Notes
    notes TEXT,
    discrepancies JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(store_id, provider_id, period_start, period_end)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payment_reconciliation_store ON store_payment_reconciliation(store_id);
CREATE INDEX IF NOT EXISTS idx_payment_reconciliation_period ON store_payment_reconciliation(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_payment_reconciliation_status ON store_payment_reconciliation(status);

-- =====================================================
-- Step 6: Migrate existing payment configurations
-- =====================================================

-- Migrate tenant payment providers to store payment providers
DO $$
DECLARE
    store_record RECORD;
    provider_record RECORD;
BEGIN
    -- For each store
    FOR store_record IN SELECT id, tenant_id FROM stores WHERE status = 'active'
    LOOP
        -- Get tenant payment providers
        FOR provider_record IN 
            SELECT * FROM tenant_payment_providers 
            WHERE tenant_id = store_record.tenant_id AND is_active = true
        LOOP
            -- Create store payment provider if not exists
            INSERT INTO store_payment_providers (
                store_id,
                provider_type,
                provider_name,
                encrypted_credentials,
                settings,
                is_primary,
                is_active
            )
            SELECT 
                store_record.id,
                provider_record.provider_type,
                provider_record.provider_name,
                provider_record.encrypted_credentials,
                provider_record.settings,
                provider_record.is_primary,
                provider_record.is_active
            WHERE NOT EXISTS (
                SELECT 1 FROM store_payment_providers
                WHERE store_id = store_record.id 
                AND provider_type = provider_record.provider_type
            );
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Migrated tenant payment providers to store payment providers';
END $$;

-- =====================================================
-- Step 7: Create triggers for updated_at
-- =====================================================

-- Trigger for store_payment_providers
CREATE OR REPLACE FUNCTION update_store_payment_providers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_store_payment_providers_updated_at
    BEFORE UPDATE ON store_payment_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_store_payment_providers_updated_at();

-- Trigger for store_payment_terminals
CREATE OR REPLACE FUNCTION update_store_payment_terminals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_store_payment_terminals_updated_at
    BEFORE UPDATE ON store_payment_terminals
    FOR EACH ROW
    EXECUTE FUNCTION update_store_payment_terminals_updated_at();

-- Trigger for store_payment_methods
CREATE OR REPLACE FUNCTION update_store_payment_methods_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_store_payment_methods_updated_at
    BEFORE UPDATE ON store_payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_store_payment_methods_updated_at();

-- =====================================================
-- Step 8: Create views for payment analytics
-- =====================================================

-- View for store payment summary
CREATE OR REPLACE VIEW store_payment_summary AS
SELECT 
    s.id as store_id,
    s.name as store_name,
    COUNT(DISTINCT spp.id) as provider_count,
    COUNT(DISTINCT spm.id) as enabled_methods,
    COUNT(pt.id) as total_transactions,
    SUM(pt.amount) as total_amount,
    AVG(pt.amount) as average_transaction
FROM stores s
LEFT JOIN store_payment_providers spp ON s.id = spp.store_id AND spp.is_active = true
LEFT JOIN store_payment_methods spm ON s.id = spm.store_id AND spm.is_enabled = true
LEFT JOIN payment_transactions pt ON s.id = pt.store_id
GROUP BY s.id, s.name;

-- View for provider performance
CREATE OR REPLACE VIEW store_provider_performance AS
SELECT 
    spp.store_id,
    spp.provider_type,
    COUNT(pt.id) as transaction_count,
    SUM(CASE WHEN pt.status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN pt.status = 'failed' THEN 1 ELSE 0 END) as failure_count,
    AVG(CASE WHEN pt.status = 'success' THEN pt.processing_time END) as avg_processing_time,
    SUM(pt.amount) as total_processed
FROM store_payment_providers spp
LEFT JOIN payment_transactions pt ON spp.id = pt.provider_id
GROUP BY spp.store_id, spp.provider_type;

-- =====================================================
-- Step 9: Grant permissions
-- =====================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON store_payment_providers TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON store_payment_terminals TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON store_payment_methods TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON store_payment_reconciliation TO weedgo;
GRANT SELECT ON store_payment_summary TO weedgo;
GRANT SELECT ON store_provider_performance TO weedgo;

-- =====================================================
-- Migration complete
-- =====================================================

COMMIT;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 016_store_payment_providers completed successfully';
    RAISE NOTICE 'Store-specific payment provider configuration is now available';
END $$;