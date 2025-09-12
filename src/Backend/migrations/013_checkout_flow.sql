-- Migration: Complete Checkout Flow Support
-- Description: Adds tables for checkout sessions, tax calculations, delivery fees, and discounts

-- Checkout sessions table
CREATE TABLE IF NOT EXISTS checkout_sessions (
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
    fulfillment_type VARCHAR(50) NOT NULL CHECK (fulfillment_type IN ('delivery', 'pickup', 'shipping')),
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

-- Tax rates table (by province/state)
CREATE TABLE IF NOT EXISTS tax_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province_territory_id UUID REFERENCES provinces_territories(id),
    tenant_id UUID REFERENCES tenants(id),
    
    -- Tax rates
    federal_tax_rate DECIMAL(5, 4) DEFAULT 0, -- GST/HST
    provincial_tax_rate DECIMAL(5, 4) DEFAULT 0, -- PST
    cannabis_excise_duty DECIMAL(10, 2) DEFAULT 0, -- Per gram or percentage
    excise_calculation_method VARCHAR(50) DEFAULT 'percentage', -- 'percentage' or 'per_gram'
    
    -- Additional fees
    environmental_fee DECIMAL(10, 2) DEFAULT 0,
    recycling_fee DECIMAL(10, 2) DEFAULT 0,
    
    -- Effective dates
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tax rates
CREATE INDEX idx_tax_rates_province ON tax_rates(province_territory_id, is_active);
CREATE INDEX idx_tax_rates_tenant ON tax_rates(tenant_id, is_active);
CREATE INDEX idx_tax_rates_effective ON tax_rates(effective_from, effective_to);

-- Delivery zones table
CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) NOT NULL,
    tenant_id UUID REFERENCES tenants(id) NOT NULL,
    
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50) NOT NULL CHECK (zone_type IN ('radius', 'polygon', 'postal_codes')),
    
    -- Zone definition (depends on type)
    radius_km DECIMAL(5, 2), -- For radius type
    polygon_coordinates JSONB, -- For polygon type (GeoJSON)
    postal_codes TEXT[], -- For postal code type
    
    -- Delivery fees and rules
    base_delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
    free_delivery_minimum DECIMAL(10, 2), -- Minimum order for free delivery
    delivery_time_minutes INTEGER DEFAULT 60,
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    available_days INTEGER[] DEFAULT ARRAY[0,1,2,3,4,5,6], -- 0=Sunday, 6=Saturday
    delivery_hours JSONB, -- {"monday": {"start": "09:00", "end": "21:00"}, ...}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for delivery zones
CREATE INDEX idx_delivery_zones_store ON delivery_zones(store_id, is_active);
CREATE INDEX idx_delivery_zones_tenant ON delivery_zones(tenant_id, is_active);

-- Discount/coupon codes table
CREATE TABLE IF NOT EXISTS discount_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    store_id UUID REFERENCES stores(id), -- NULL means all stores
    
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    discount_type VARCHAR(50) NOT NULL CHECK (discount_type IN ('percentage', 'fixed', 'bogo', 'free_delivery')),
    discount_value DECIMAL(10, 2) NOT NULL,
    
    -- Conditions
    minimum_purchase DECIMAL(10, 2) DEFAULT 0,
    maximum_discount DECIMAL(10, 2), -- Cap for percentage discounts
    applicable_categories TEXT[], -- Product categories this applies to
    applicable_products UUID[], -- Specific product IDs
    
    -- Usage limits
    usage_limit INTEGER, -- Total uses allowed
    usage_limit_per_customer INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    
    -- Validity period
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    requires_account BOOLEAN DEFAULT FALSE,
    first_time_only BOOLEAN DEFAULT FALSE,
    combinable BOOLEAN DEFAULT FALSE, -- Can be combined with other discounts
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Indexes for discount codes
CREATE INDEX idx_discount_codes_code ON discount_codes(code) WHERE is_active = TRUE;
CREATE INDEX idx_discount_codes_tenant ON discount_codes(tenant_id, is_active);
CREATE INDEX idx_discount_codes_validity ON discount_codes(valid_from, valid_until);

-- Discount usage tracking
CREATE TABLE IF NOT EXISTS discount_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_id UUID REFERENCES discount_codes(id) NOT NULL,
    user_id UUID REFERENCES users(id),
    order_id UUID REFERENCES orders(id),
    checkout_session_id UUID REFERENCES checkout_sessions(id),
    
    discount_amount DECIMAL(10, 2) NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for discount usage
CREATE INDEX idx_discount_usage_discount ON discount_usage(discount_id);
CREATE INDEX idx_discount_usage_user ON discount_usage(user_id);
CREATE INDEX idx_discount_usage_order ON discount_usage(order_id);

-- Inventory reservations during checkout
CREATE TABLE IF NOT EXISTS inventory_reservations (
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

-- Saved addresses for users
CREATE TABLE IF NOT EXISTS user_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    
    address_type VARCHAR(50) DEFAULT 'delivery' CHECK (address_type IN ('delivery', 'billing')),
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Address fields
    label VARCHAR(100), -- e.g., "Home", "Office"
    street_address VARCHAR(255) NOT NULL,
    unit_number VARCHAR(50),
    city VARCHAR(100) NOT NULL,
    province_state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) DEFAULT 'CA',
    
    -- Additional info
    delivery_instructions TEXT,
    phone_number VARCHAR(50),
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validation_data JSONB, -- Store geocoding results
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user addresses
CREATE INDEX idx_user_addresses_user ON user_addresses(user_id);
CREATE INDEX idx_user_addresses_default ON user_addresses(user_id, is_default) WHERE is_default = TRUE;

-- Functions for checkout flow

-- Function to calculate taxes
CREATE OR REPLACE FUNCTION calculate_checkout_taxes(
    p_checkout_id UUID,
    p_subtotal DECIMAL
) RETURNS JSONB AS $$
DECLARE
    v_tax_rate RECORD;
    v_province_id UUID;
    v_federal_tax DECIMAL;
    v_provincial_tax DECIMAL;
    v_excise_duty DECIMAL;
    v_total_tax DECIMAL;
BEGIN
    -- Get province from checkout session
    SELECT 
        COALESCE(
            s.province_territory_id,
            (checkout_sessions.delivery_address->>'province_id')::UUID
        ) INTO v_province_id
    FROM checkout_sessions
    LEFT JOIN stores s ON checkout_sessions.pickup_store_id = s.id
    WHERE checkout_sessions.id = p_checkout_id;
    
    -- Get applicable tax rates
    SELECT * INTO v_tax_rate
    FROM tax_rates
    WHERE province_territory_id = v_province_id
        AND is_active = TRUE
        AND CURRENT_DATE BETWEEN effective_from AND COALESCE(effective_to, CURRENT_DATE + INTERVAL '1 day')
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF NOT FOUND THEN
        -- Default tax rates if not configured
        v_federal_tax := p_subtotal * 0.05; -- 5% GST
        v_provincial_tax := p_subtotal * 0.08; -- 8% PST (example)
        v_excise_duty := p_subtotal * 0.10; -- 10% excise (example)
    ELSE
        v_federal_tax := p_subtotal * v_tax_rate.federal_tax_rate;
        v_provincial_tax := p_subtotal * v_tax_rate.provincial_tax_rate;
        
        IF v_tax_rate.excise_calculation_method = 'percentage' THEN
            v_excise_duty := p_subtotal * (v_tax_rate.cannabis_excise_duty / 100);
        ELSE
            -- Would need to calculate based on weight
            v_excise_duty := v_tax_rate.cannabis_excise_duty;
        END IF;
    END IF;
    
    v_total_tax := v_federal_tax + v_provincial_tax + v_excise_duty;
    
    RETURN jsonb_build_object(
        'federal_tax', ROUND(v_federal_tax, 2),
        'provincial_tax', ROUND(v_provincial_tax, 2),
        'excise_duty', ROUND(v_excise_duty, 2),
        'total_tax', ROUND(v_total_tax, 2)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check and apply discount code
CREATE OR REPLACE FUNCTION apply_discount_code(
    p_code VARCHAR,
    p_user_id UUID,
    p_subtotal DECIMAL,
    p_tenant_id UUID
) RETURNS JSONB AS $$
DECLARE
    v_discount RECORD;
    v_usage_count INTEGER;
    v_discount_amount DECIMAL;
BEGIN
    -- Find valid discount code
    SELECT * INTO v_discount
    FROM discount_codes
    WHERE UPPER(code) = UPPER(p_code)
        AND is_active = TRUE
        AND (tenant_id = p_tenant_id OR tenant_id IS NULL)
        AND CURRENT_TIMESTAMP BETWEEN valid_from AND COALESCE(valid_until, CURRENT_TIMESTAMP + INTERVAL '1 day')
        AND p_subtotal >= minimum_purchase;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Invalid or expired discount code'
        );
    END IF;
    
    -- Check usage limits
    IF v_discount.usage_limit IS NOT NULL AND v_discount.usage_count >= v_discount.usage_limit THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Discount code usage limit reached'
        );
    END IF;
    
    -- Check per-customer usage limit
    IF p_user_id IS NOT NULL AND v_discount.usage_limit_per_customer IS NOT NULL THEN
        SELECT COUNT(*) INTO v_usage_count
        FROM discount_usage
        WHERE discount_id = v_discount.id AND user_id = p_user_id;
        
        IF v_usage_count >= v_discount.usage_limit_per_customer THEN
            RETURN jsonb_build_object(
                'success', FALSE,
                'message', 'You have already used this discount code'
            );
        END IF;
    END IF;
    
    -- Calculate discount amount
    IF v_discount.discount_type = 'percentage' THEN
        v_discount_amount := p_subtotal * (v_discount.discount_value / 100);
        IF v_discount.maximum_discount IS NOT NULL THEN
            v_discount_amount := LEAST(v_discount_amount, v_discount.maximum_discount);
        END IF;
    ELSIF v_discount.discount_type = 'fixed' THEN
        v_discount_amount := LEAST(v_discount.discount_value, p_subtotal);
    ELSE
        v_discount_amount := 0; -- Handle other types separately
    END IF;
    
    RETURN jsonb_build_object(
        'success', TRUE,
        'discount_id', v_discount.id,
        'discount_amount', ROUND(v_discount_amount, 2),
        'discount_type', v_discount.discount_type,
        'message', v_discount.description
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger to update checkout session timestamp
CREATE OR REPLACE FUNCTION update_checkout_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_checkout_sessions_updated_at
    BEFORE UPDATE ON checkout_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_checkout_session_timestamp();

-- Trigger to auto-expire checkout sessions
CREATE OR REPLACE FUNCTION expire_checkout_sessions()
RETURNS void AS $$
BEGIN
    UPDATE checkout_sessions
    SET status = 'expired'
    WHERE status = 'draft'
        AND expires_at < CURRENT_TIMESTAMP;
    
    -- Release inventory reservations for expired sessions
    UPDATE inventory_reservations
    SET released = TRUE
    WHERE checkout_session_id IN (
        SELECT id FROM checkout_sessions
        WHERE status = 'expired'
    ) AND released = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Add constraints
ALTER TABLE user_addresses
    ADD CONSTRAINT unique_default_delivery_per_user 
    EXCLUDE (user_id WITH =) WHERE (is_default = TRUE AND address_type = 'delivery');

ALTER TABLE user_addresses
    ADD CONSTRAINT unique_default_billing_per_user 
    EXCLUDE (user_id WITH =) WHERE (is_default = TRUE AND address_type = 'billing');

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON checkout_sessions TO weedgo;
GRANT SELECT, INSERT, UPDATE ON tax_rates TO weedgo;
GRANT SELECT ON delivery_zones TO weedgo;
GRANT SELECT, UPDATE ON discount_codes TO weedgo;
GRANT SELECT, INSERT ON discount_usage TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_reservations TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_addresses TO weedgo;

-- Comments
COMMENT ON TABLE checkout_sessions IS 'Stores checkout session data including cart, customer info, and pricing';
COMMENT ON TABLE tax_rates IS 'Tax rates by province/territory for cannabis products';
COMMENT ON TABLE delivery_zones IS 'Delivery zones and fees for each store';
COMMENT ON TABLE discount_codes IS 'Promotional discount and coupon codes';
COMMENT ON TABLE inventory_reservations IS 'Temporary inventory reservations during checkout';
COMMENT ON TABLE user_addresses IS 'Saved delivery and billing addresses for users';