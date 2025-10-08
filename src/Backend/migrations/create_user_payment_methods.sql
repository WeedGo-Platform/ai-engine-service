-- Create user_payment_methods table for customer payment preferences
CREATE TABLE IF NOT EXISTS user_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('cash', 'card', 'etransfer')),

    -- Card details (only for stored cards)
    card_brand VARCHAR(20),
    last4 VARCHAR(4),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    payment_token TEXT,  -- For tokenized cards

    -- Metadata
    nickname VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX idx_user_payment_methods_user_id ON user_payment_methods(user_id);
CREATE INDEX idx_user_payment_methods_user_default ON user_payment_methods(user_id, is_default) WHERE is_default = TRUE;
CREATE INDEX idx_user_payment_methods_active ON user_payment_methods(user_id, is_active) WHERE is_active = TRUE;

-- Ensure only one default payment method per user
CREATE UNIQUE INDEX idx_user_payment_methods_one_default
    ON user_payment_methods(user_id)
    WHERE is_default = TRUE AND is_active = TRUE;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_payment_methods_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_payment_methods_updated_at
    BEFORE UPDATE ON user_payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_user_payment_methods_updated_at();

-- Add index for order lookups
CREATE INDEX IF NOT EXISTS idx_orders_payment_method_id ON orders(payment_method_id);

COMMENT ON TABLE user_payment_methods IS 'Customer payment methods for user profiles - supports cash, cards, and e-transfer';
COMMENT ON COLUMN user_payment_methods.type IS 'Payment method type: cash, card, or etransfer';
COMMENT ON COLUMN user_payment_methods.payment_token IS 'Tokenized card data from payment provider (null for cash/etransfer)';
