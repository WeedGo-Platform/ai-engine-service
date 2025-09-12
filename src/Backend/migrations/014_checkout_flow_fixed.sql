-- Migration: Complete Checkout Flow Support (Fixed)
-- Description: Adds tables for checkout sessions with proper references

-- Drop existing problematic objects if they exist
DROP TABLE IF EXISTS checkout_sessions CASCADE;
DROP TABLE IF EXISTS inventory_reservations CASCADE;
DROP TABLE IF EXISTS discount_usage CASCADE;

-- Checkout sessions table
CREATE TABLE checkout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    cart_session_id UUID REFERENCES cart_sessions(id),
    user_id UUID REFERENCES users(id),
    tenant_id UUID REFERENCES tenants(id),
    store_id UUID REFERENCES stores(id),
    
    -- Customer information (for guest checkout)
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_first_name VARCHAR(100),
    customer_last_name VARCHAR(100),
    
    -- Delivery/pickup information
    fulfillment_type VARCHAR(50) NOT NULL DEFAULT 'delivery' CHECK (fulfillment_type IN ('delivery', 'pickup', 'shipping')),
    delivery_address JSONB,
    pickup_store_id UUID REFERENCES stores(id),
    pickup_datetime TIMESTAMP WITH TIME ZONE,
    delivery_datetime TIMESTAMP WITH TIME ZONE,
    delivery_instructions TEXT,
    
    -- Pricing breakdown
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
    service_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tip_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    
    -- Applied discounts/coupons
    coupon_code VARCHAR(50),
    discount_id UUID,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending',
    payment_intent_id VARCHAR(255),
    
    -- Compliance
    age_verified BOOLEAN DEFAULT FALSE,
    age_verification_method VARCHAR(50),
    id_verification_token VARCHAR(255),
    medical_card_verified BOOLEAN DEFAULT FALSE,
    medical_card_number VARCHAR(100),
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'processing', 'completed', 'failed', 'abandoned', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 minutes'),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for checkout sessions
CREATE INDEX idx_checkout_sessions_session_id ON checkout_sessions(session_id);
CREATE INDEX idx_checkout_sessions_user_id ON checkout_sessions(user_id);
CREATE INDEX idx_checkout_sessions_status ON checkout_sessions(status);
CREATE INDEX idx_checkout_sessions_expires_at ON checkout_sessions(expires_at) WHERE status = 'draft';
CREATE INDEX idx_checkout_sessions_tenant_store ON checkout_sessions(tenant_id, store_id);

-- Discount usage tracking (work with existing discount_codes table)
CREATE TABLE discount_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_code_id UUID REFERENCES discount_codes(id) NOT NULL,
    user_id UUID REFERENCES users(id),
    order_id UUID REFERENCES orders(id),
    checkout_session_id UUID REFERENCES checkout_sessions(id),
    
    discount_amount DECIMAL(10, 2) NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for discount usage
CREATE INDEX idx_discount_usage_discount ON discount_usage(discount_code_id);
CREATE INDEX idx_discount_usage_user ON discount_usage(user_id);
CREATE INDEX idx_discount_usage_order ON discount_usage(order_id);

-- Inventory reservations during checkout
CREATE TABLE inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkout_session_id UUID REFERENCES checkout_sessions(id) NOT NULL,
    product_id UUID REFERENCES products(id) NOT NULL,
    variant_id UUID REFERENCES product_variants(id),
    
    quantity INTEGER NOT NULL,
    reserved_until TIMESTAMP WITH TIME ZONE NOT NULL,
    released BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for inventory reservations
CREATE INDEX idx_inventory_reservations_session ON inventory_reservations(checkout_session_id);
CREATE INDEX idx_inventory_reservations_product ON inventory_reservations(product_id);
CREATE INDEX idx_inventory_reservations_expires ON inventory_reservations(reserved_until) WHERE released = FALSE;

-- Add missing columns to discount_codes if they don't exist
DO $$ 
BEGIN
    -- Add description column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'discount_codes' AND column_name = 'description') THEN
        ALTER TABLE discount_codes ADD COLUMN description TEXT;
    END IF;
    
    -- Add discount_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'discount_codes' AND column_name = 'discount_type') THEN
        ALTER TABLE discount_codes ADD COLUMN discount_type VARCHAR(50) DEFAULT 'percentage' 
            CHECK (discount_type IN ('percentage', 'fixed', 'bogo', 'free_delivery'));
    END IF;
    
    -- Add discount_value column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'discount_codes' AND column_name = 'discount_value') THEN
        ALTER TABLE discount_codes ADD COLUMN discount_value DECIMAL(10, 2) DEFAULT 0;
    END IF;
    
    -- Add minimum_purchase column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'discount_codes' AND column_name = 'minimum_purchase') THEN
        ALTER TABLE discount_codes ADD COLUMN minimum_purchase DECIMAL(10, 2) DEFAULT 0;
    END IF;
    
    -- Add is_active column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'discount_codes' AND column_name = 'is_active') THEN
        ALTER TABLE discount_codes ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON checkout_sessions TO weedgo;
GRANT SELECT, UPDATE ON discount_codes TO weedgo;
GRANT SELECT, INSERT ON discount_usage TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_reservations TO weedgo;

-- Comments
COMMENT ON TABLE checkout_sessions IS 'Stores checkout session data including cart, customer info, and pricing';
COMMENT ON TABLE discount_usage IS 'Tracks usage of discount codes';
COMMENT ON TABLE inventory_reservations IS 'Temporary inventory reservations during checkout';