-- Pricing and Promotions Schema for Cannabis E-commerce
-- Created: 2025-09-09
-- Description: Comprehensive pricing, promotions, and recommendations system

-- 1. CUSTOMER PRICE TIERS
-- Different pricing levels based on customer type/volume
CREATE TABLE IF NOT EXISTS price_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    discount_percentage DECIMAL(5,2) DEFAULT 0, -- Base discount for this tier
    min_order_value DECIMAL(10,2), -- Minimum order value to qualify
    min_monthly_volume DECIMAL(10,2), -- Minimum monthly purchase volume
    customer_type VARCHAR(50), -- 'retail', 'wholesale', 'medical', 'vip'
    priority INTEGER DEFAULT 0, -- Higher priority tiers override lower ones
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PROMOTIONS TABLE
-- Store-wide and product-specific promotions
CREATE TABLE IF NOT EXISTS promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE, -- Promo code if applicable
    name VARCHAR(200) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL, -- 'percentage', 'fixed_amount', 'bogo', 'bundle', 'tiered'
    discount_type VARCHAR(20) NOT NULL, -- 'percentage' or 'amount'
    discount_value DECIMAL(10,2) NOT NULL,
    
    -- Conditions
    min_purchase_amount DECIMAL(10,2),
    max_discount_amount DECIMAL(10,2), -- Cap on discount amount
    usage_limit_per_customer INTEGER,
    total_usage_limit INTEGER,
    times_used INTEGER DEFAULT 0,
    
    -- Applicability
    applies_to VARCHAR(50) DEFAULT 'all', -- 'all', 'category', 'brand', 'products'
    category_ids TEXT[], -- Array of applicable categories
    brand_ids TEXT[], -- Array of applicable brands
    product_ids TEXT[], -- Array of specific product SKUs
    exclude_product_ids TEXT[], -- Products to exclude
    
    -- Stacking rules
    stackable BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 0,
    
    -- Schedule
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    active BOOLEAN DEFAULT true,
    
    -- Special conditions
    day_of_week INTEGER[], -- 1=Monday, 7=Sunday
    hour_of_day INTEGER[], -- 0-23 for happy hours
    customer_tier_ids UUID[], -- Specific tiers only
    first_time_customer_only BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. BUNDLE DEALS
-- Product bundles with special pricing
CREATE TABLE IF NOT EXISTS bundle_deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    bundle_type VARCHAR(50), -- 'fixed', 'mix_match', 'category_combo'
    
    -- Bundle composition
    required_products JSONB, -- {"sku": "quantity"} pairs
    optional_products JSONB, -- Products that can be substituted
    min_quantity INTEGER DEFAULT 1,
    max_quantity INTEGER,
    
    -- Pricing
    bundle_price DECIMAL(10,2), -- Fixed price for bundle
    discount_percentage DECIMAL(5,2), -- Or percentage off total
    savings_amount DECIMAL(10,2), -- Calculated savings
    
    -- Rules
    allow_substitutions BOOLEAN DEFAULT false,
    require_all_items BOOLEAN DEFAULT true,
    
    active BOOLEAN DEFAULT true,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. CUSTOMER PRICING RULES
-- Customer-specific pricing overrides
CREATE TABLE IF NOT EXISTS customer_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    price_tier_id UUID REFERENCES price_tiers(id),
    
    -- Custom pricing
    custom_markup_percentage DECIMAL(5,2),
    volume_discounts JSONB, -- {"min_qty": discount_percentage}
    category_discounts JSONB, -- {"category": discount_percentage}
    
    -- Negotiated rates
    negotiated_products JSONB, -- {"sku": custom_price}
    
    -- Payment terms
    payment_terms VARCHAR(50), -- 'net30', 'net60', 'cod'
    early_payment_discount DECIMAL(5,2),
    
    active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. PRODUCT RECOMMENDATIONS (Enhanced)
-- Dropping existing table first if it exists
DROP TABLE IF EXISTS product_recommendations;

CREATE TABLE product_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL, -- Source product SKU
    recommended_product_id VARCHAR(100) NOT NULL, -- Recommended product SKU
    recommendation_type VARCHAR(50) NOT NULL, -- 'similar', 'complementary', 'upsell', 'crosssell', 'trending'
    
    -- Scoring and reasoning
    score DECIMAL(3,2) DEFAULT 0.5, -- 0-1 confidence score
    reason TEXT,
    
    -- Recommendation basis
    based_on VARCHAR(50), -- 'purchase_history', 'category', 'effects', 'terpenes', 'price_range'
    
    -- Performance metrics
    click_through_rate DECIMAL(5,4) DEFAULT 0,
    conversion_rate DECIMAL(5,4) DEFAULT 0,
    revenue_impact DECIMAL(10,2) DEFAULT 0,
    
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(product_id, recommended_product_id, recommendation_type)
);

-- 6. DISCOUNT CODES
-- Individual discount codes for customers
CREATE TABLE IF NOT EXISTS discount_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    promotion_id UUID REFERENCES promotions(id),
    
    -- Assignment
    customer_id UUID,
    tenant_id UUID REFERENCES tenants(id),
    
    -- Usage tracking
    used BOOLEAN DEFAULT false,
    used_at TIMESTAMP,
    order_id UUID,
    
    -- Validity
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. PROMOTION USAGE TRACKING
CREATE TABLE IF NOT EXISTS promotion_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID REFERENCES promotions(id),
    customer_id UUID,
    tenant_id UUID REFERENCES tenants(id),
    order_id UUID,
    
    discount_amount DECIMAL(10,2),
    order_total DECIMAL(10,2),
    
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. DYNAMIC PRICING RULES
-- Automated pricing based on conditions
CREATE TABLE IF NOT EXISTS dynamic_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Trigger conditions
    trigger_type VARCHAR(50), -- 'inventory_level', 'expiry_date', 'demand', 'competition'
    trigger_condition JSONB, -- Specific conditions
    
    -- Actions
    action_type VARCHAR(50), -- 'discount', 'markup', 'fixed_price'
    action_value DECIMAL(10,2),
    
    -- Applicability
    category_ids TEXT[],
    product_ids TEXT[],
    
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. PRICE HISTORY
-- Track price changes for analytics
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    change_reason VARCHAR(100),
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. RECOMMENDATION METRICS
-- Track recommendation performance
CREATE TABLE IF NOT EXISTS recommendation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID REFERENCES product_recommendations(id),
    
    -- User interaction
    customer_id UUID,
    session_id VARCHAR(100),
    
    -- Events
    event_type VARCHAR(50), -- 'view', 'click', 'add_to_cart', 'purchase'
    event_value DECIMAL(10,2), -- Revenue if purchase
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX idx_promotions_active ON promotions(active, start_date, end_date);
CREATE INDEX idx_promotions_code ON promotions(code) WHERE code IS NOT NULL;
CREATE INDEX idx_promotions_type ON promotions(type);
CREATE INDEX idx_bundle_deals_active ON bundle_deals(active);
CREATE INDEX idx_recommendations_product ON product_recommendations(product_id);
CREATE INDEX idx_recommendations_type ON product_recommendations(recommendation_type);
CREATE INDEX idx_discount_codes_code ON discount_codes(code);
CREATE INDEX idx_discount_codes_unused ON discount_codes(used, valid_until) WHERE used = false;
CREATE INDEX idx_dynamic_pricing_active ON dynamic_pricing_rules(active);
CREATE INDEX idx_price_history_product ON price_history(product_id, changed_at);

-- SAMPLE DATA FOR PRICE TIERS
INSERT INTO price_tiers (name, description, discount_percentage, min_order_value, customer_type, priority) VALUES
    ('Retail', 'Standard retail pricing', 0, 0, 'retail', 1),
    ('Silver', 'Silver tier - 5% discount', 5, 100, 'retail', 2),
    ('Gold', 'Gold tier - 10% discount', 10, 500, 'retail', 3),
    ('Platinum', 'Platinum tier - 15% discount', 15, 1000, 'retail', 4),
    ('Wholesale', 'Wholesale pricing - 20% discount', 20, 2000, 'wholesale', 5),
    ('Medical', 'Medical patients - 10% discount', 10, 0, 'medical', 3)
ON CONFLICT (name) DO NOTHING;

-- SAMPLE PROMOTIONS
INSERT INTO promotions (
    code, name, description, type, discount_type, discount_value,
    start_date, end_date, applies_to
) VALUES
    ('WELCOME15', 'New Customer Discount', 'Get 15% off your first order', 'percentage', 'percentage', 15,
     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year', 'all'),
    ('420SPECIAL', '4/20 Special', '20% off all flower products', 'percentage', 'percentage', 20,
     '2025-04-20'::timestamp, '2025-04-21'::timestamp, 'category'),
    ('HAPPYHOUR', 'Happy Hour', '10% off 4-6pm daily', 'percentage', 'percentage', 10,
     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year', 'all')
ON CONFLICT (code) DO NOTHING;

-- Update existing promotions to set hour_of_day for happy hour
UPDATE promotions 
SET hour_of_day = ARRAY[16, 17] -- 4-6pm
WHERE code = 'HAPPYHOUR';

-- Function to calculate final price with all applicable discounts
CREATE OR REPLACE FUNCTION calculate_final_price(
    p_product_id VARCHAR(100),
    p_quantity INTEGER,
    p_customer_id UUID,
    p_tenant_id UUID
) RETURNS TABLE (
    base_price DECIMAL(10,2),
    tier_discount DECIMAL(10,2),
    promo_discount DECIMAL(10,2),
    volume_discount DECIMAL(10,2),
    final_price DECIMAL(10,2)
) AS $$
DECLARE
    v_base_price DECIMAL(10,2);
    v_tier_discount DECIMAL(10,2) := 0;
    v_promo_discount DECIMAL(10,2) := 0;
    v_volume_discount DECIMAL(10,2) := 0;
BEGIN
    -- Get base price from product catalog
    SELECT unit_price * p_quantity INTO v_base_price
    FROM product_catalog
    WHERE ocs_variant_number = p_product_id;
    
    -- Calculate tier discount
    SELECT COALESCE(MAX(pt.discount_percentage), 0) INTO v_tier_discount
    FROM customer_pricing_rules cpr
    JOIN price_tiers pt ON cpr.price_tier_id = pt.id
    WHERE cpr.tenant_id = p_tenant_id
    AND cpr.active = true;
    
    -- Calculate applicable promotions (simplified)
    SELECT COALESCE(MAX(discount_value), 0) INTO v_promo_discount
    FROM promotions
    WHERE active = true
    AND CURRENT_TIMESTAMP BETWEEN start_date AND COALESCE(end_date, CURRENT_TIMESTAMP + INTERVAL '1 day')
    AND (applies_to = 'all' OR p_product_id = ANY(product_ids));
    
    -- Calculate volume discount
    IF p_quantity >= 100 THEN
        v_volume_discount := 10;
    ELSIF p_quantity >= 50 THEN
        v_volume_discount := 7;
    ELSIF p_quantity >= 20 THEN
        v_volume_discount := 5;
    ELSIF p_quantity >= 10 THEN
        v_volume_discount := 3;
    END IF;
    
    RETURN QUERY
    SELECT 
        v_base_price,
        v_base_price * v_tier_discount / 100,
        v_base_price * v_promo_discount / 100,
        v_base_price * v_volume_discount / 100,
        v_base_price * (1 - (v_tier_discount + v_promo_discount + v_volume_discount) / 100);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables
CREATE TRIGGER update_price_tiers_updated_at BEFORE UPDATE ON price_tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_promotions_updated_at BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bundle_deals_updated_at BEFORE UPDATE ON bundle_deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_pricing_rules_updated_at BEFORE UPDATE ON customer_pricing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_recommendations_updated_at BEFORE UPDATE ON product_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dynamic_pricing_rules_updated_at BEFORE UPDATE ON dynamic_pricing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();