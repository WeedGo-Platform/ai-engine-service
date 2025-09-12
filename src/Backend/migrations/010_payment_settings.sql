-- Migration: Payment Provider and POS Terminal Settings
-- Description: Add payment provider settings for tenants and POS payment terminal settings for stores
-- Date: 2025-09-09
-- Version: 1.0.0

-- =====================================================
-- 1. ADD PAYMENT PROVIDER SETTINGS TO TENANTS
-- =====================================================
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS payment_provider_settings JSONB DEFAULT '{}'::JSONB;

-- Add comment for documentation
COMMENT ON COLUMN tenants.payment_provider_settings IS 'Payment provider configuration including Stripe, Square, Moneris settings';

-- =====================================================
-- 2. ADD POS PAYMENT TERMINAL SETTINGS TO STORES
-- =====================================================
ALTER TABLE stores 
ADD COLUMN IF NOT EXISTS pos_payment_terminal_settings JSONB DEFAULT '{}'::JSONB;

-- Add comment for documentation
COMMENT ON COLUMN stores.pos_payment_terminal_settings IS 'POS payment terminal configuration including terminal IDs, types, and settings';

-- =====================================================
-- 3. CREATE INDEXES FOR JSONB QUERIES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_tenants_payment_providers 
ON tenants USING gin (payment_provider_settings);

CREATE INDEX IF NOT EXISTS idx_stores_pos_terminals 
ON stores USING gin (pos_payment_terminal_settings);

-- =====================================================
-- 4. PAYMENT PROVIDERS TABLE (for reference/validation)
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    supported_countries TEXT[] DEFAULT ARRAY['CA'],
    supported_currencies TEXT[] DEFAULT ARRAY['CAD', 'USD'],
    payment_methods TEXT[] DEFAULT ARRAY['credit_card', 'debit_card'],
    configuration_schema JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert supported payment providers
INSERT INTO payment_providers (name, code, payment_methods, configuration_schema) VALUES
    ('Stripe', 'stripe', 
     ARRAY['credit_card', 'debit_card', 'apple_pay', 'google_pay'],
     '{"required": ["account_id", "publishable_key", "secret_key"], "optional": ["webhook_endpoint"]}'::JSONB),
    ('Square', 'square', 
     ARRAY['credit_card', 'debit_card', 'tap_to_pay'],
     '{"required": ["location_id", "access_token"], "optional": ["webhook_signature_key"]}'::JSONB),
    ('Moneris', 'moneris', 
     ARRAY['credit_card', 'debit_card', 'interac'],
     '{"required": ["store_id", "api_token"], "optional": ["terminal_id"]}'::JSONB),
    ('PayPal', 'paypal', 
     ARRAY['paypal', 'credit_card', 'debit_card'],
     '{"required": ["client_id", "client_secret"], "optional": ["webhook_id"]}'::JSONB),
    ('Interac', 'interac', 
     ARRAY['interac_online', 'interac_etransfer'],
     '{"required": ["merchant_id", "api_key"], "optional": ["terminal_id"]}'::JSONB)
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- 5. POS TERMINAL TYPES TABLE (for reference/validation)
-- =====================================================
CREATE TABLE IF NOT EXISTS pos_terminal_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    supported_providers TEXT[] DEFAULT ARRAY['moneris'],
    capabilities TEXT[] DEFAULT ARRAY['tap', 'chip', 'swipe'],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert common POS terminal types
INSERT INTO pos_terminal_types (name, code, manufacturer, model, supported_providers, capabilities) VALUES
    ('Moneris Move 5000', 'moneris_move5000', 'Moneris', 'Move 5000', 
     ARRAY['moneris'], ARRAY['tap', 'chip', 'swipe', 'contactless']),
    ('Moneris Desk 5000', 'moneris_desk5000', 'Moneris', 'Desk 5000', 
     ARRAY['moneris'], ARRAY['tap', 'chip', 'swipe']),
    ('Square Terminal', 'square_terminal', 'Square', 'Terminal', 
     ARRAY['square'], ARRAY['tap', 'chip', 'swipe', 'contactless']),
    ('Square Reader', 'square_reader', 'Square', 'Reader', 
     ARRAY['square'], ARRAY['tap', 'chip', 'contactless']),
    ('Stripe Terminal', 'stripe_terminal', 'Stripe', 'WisePOS E', 
     ARRAY['stripe'], ARRAY['tap', 'chip', 'swipe', 'contactless']),
    ('Clover Flex', 'clover_flex', 'Clover', 'Flex', 
     ARRAY['stripe', 'square'], ARRAY['tap', 'chip', 'swipe', 'contactless'])
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- 6. PAYMENT TRANSACTIONS TABLE (audit trail)
-- =====================================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    terminal_id VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    payment_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded', 'partially_refunded')),
    provider_response JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for payment transactions
CREATE INDEX idx_payment_transactions_tenant ON payment_transactions(tenant_id);
CREATE INDEX idx_payment_transactions_store ON payment_transactions(store_id);
CREATE INDEX idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_provider ON payment_transactions(provider);
CREATE INDEX idx_payment_transactions_created ON payment_transactions(created_at DESC);

-- =====================================================
-- 7. SAMPLE CONFIGURATIONS (as comments for reference)
-- =====================================================
-- Sample tenant payment_provider_settings:
-- {
--   "stripe": {
--     "enabled": true,
--     "account_id": "acct_xxx",
--     "publishable_key": "pk_live_xxx",
--     "secret_key": "encrypted:sk_live_xxx",
--     "webhook_endpoint": "whsec_xxx",
--     "payment_methods": ["card", "apple_pay", "google_pay"]
--   },
--   "moneris": {
--     "enabled": true,
--     "store_id": "store123",
--     "api_token": "encrypted:token_xxx",
--     "test_mode": false
--   },
--   "default_provider": "stripe",
--   "fallback_provider": "moneris",
--   "currency": "CAD",
--   "auto_capture": true,
--   "receipt_email": true
-- }

-- Sample store pos_payment_terminal_settings:
-- {
--   "terminals": [
--     {
--       "id": "term_001",
--       "name": "Front Counter",
--       "type": "moneris_move5000",
--       "serial_number": "SN123456",
--       "ip_address": "192.168.1.100",
--       "port": 3000,
--       "status": "active",
--       "last_seen": "2025-09-09T10:30:00Z"
--     },
--     {
--       "id": "term_002",
--       "name": "Mobile POS",
--       "type": "square_reader",
--       "serial_number": "SQ789012",
--       "bluetooth_id": "XX:XX:XX:XX:XX:XX",
--       "status": "active"
--     }
--   ],
--   "default_terminal": "term_001",
--   "payment_methods": ["tap", "chip", "swipe", "cash"],
--   "tip_options": [15, 18, 20, 0],
--   "tip_enabled": true,
--   "receipt_settings": {
--     "print_customer_copy": true,
--     "print_merchant_copy": false,
--     "email_receipt": true,
--     "sms_receipt": false
--   },
--   "offline_mode": {
--     "enabled": true,
--     "max_offline_amount": 500,
--     "sync_interval_minutes": 5
--   }
-- }

-- =====================================================
-- 8. FUNCTIONS FOR PAYMENT SETTINGS MANAGEMENT
-- =====================================================

-- Function to validate payment provider settings
CREATE OR REPLACE FUNCTION validate_payment_settings(settings JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if at least one provider is enabled
    IF NOT EXISTS (
        SELECT 1 
        FROM jsonb_each(settings) AS provider(key, value)
        WHERE provider.key != 'default_provider' 
        AND provider.key != 'fallback_provider'
        AND provider.key != 'currency'
        AND (provider.value->>'enabled')::boolean = true
    ) THEN
        RAISE EXCEPTION 'At least one payment provider must be enabled';
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Function to encrypt sensitive payment data
CREATE OR REPLACE FUNCTION encrypt_payment_data(data TEXT)
RETURNS TEXT AS $$
BEGIN
    -- This is a placeholder - implement actual encryption
    -- In production, use pgcrypto or external encryption service
    RETURN 'encrypted:' || data;
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive payment data
CREATE OR REPLACE FUNCTION decrypt_payment_data(data TEXT)
RETURNS TEXT AS $$
BEGIN
    -- This is a placeholder - implement actual decryption
    -- In production, use pgcrypto or external encryption service
    IF data LIKE 'encrypted:%' THEN
        RETURN substring(data from 11);
    END IF;
    RETURN data;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. UPDATE TRIGGERS
-- =====================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_payment_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF (OLD.payment_provider_settings IS DISTINCT FROM NEW.payment_provider_settings) THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenant_payment_settings_timestamp
BEFORE UPDATE ON tenants
FOR EACH ROW
EXECUTE FUNCTION update_payment_settings_timestamp();

-- Trigger for stores POS settings
CREATE OR REPLACE FUNCTION update_pos_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF (OLD.pos_payment_terminal_settings IS DISTINCT FROM NEW.pos_payment_terminal_settings) THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_store_pos_settings_timestamp
BEFORE UPDATE ON stores
FOR EACH ROW
EXECUTE FUNCTION update_pos_settings_timestamp();