-- ============================================================================
-- Migration: Create Delivery & Pricing Tables
-- Description: Delivery logistics, pricing rules, promotions, and reviews
-- Dependencies: 008_create_payment_tables.sql
-- ============================================================================

-- ===========================
-- DELIVERY & LOGISTICS TABLES
-- ===========================

-- Delivery Zones
CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    zone_name VARCHAR(255) NOT NULL,
    zone_type VARCHAR(50),
    geometry GEOGRAPHY(POLYGON),
    postal_codes TEXT[],
    min_order_amount NUMERIC(10,2) DEFAULT 0.00,
    delivery_fee NUMERIC(10,2) DEFAULT 0.00,
    estimated_delivery_time_minutes INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_zones_store ON delivery_zones(store_id);
CREATE INDEX IF NOT EXISTS idx_delivery_zones_geometry ON delivery_zones USING GIST(geometry);

-- Delivery Geofences
CREATE TABLE IF NOT EXISTS delivery_geofences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES delivery_zones(id) ON DELETE CASCADE,
    fence_name VARCHAR(255),
    fence_type VARCHAR(50),
    geometry GEOGRAPHY(POLYGON),
    action_on_enter VARCHAR(50),
    action_on_exit VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_geofences_zone ON delivery_geofences(zone_id);
CREATE INDEX IF NOT EXISTS idx_delivery_geofences_geometry ON delivery_geofences USING GIST(geometry);

-- Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    delivery_address JSONB NOT NULL,
    delivery_location GEOGRAPHY(POINT),
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_for TIMESTAMP WITHOUT TIME ZONE,
    picked_up_at TIMESTAMP WITHOUT TIME ZONE,
    delivered_at TIMESTAMP WITHOUT TIME ZONE,
    estimated_delivery_time TIMESTAMP WITHOUT TIME ZONE,
    actual_delivery_time TIMESTAMP WITHOUT TIME ZONE,
    delivery_instructions TEXT,
    signature_url VARCHAR(500),
    delivery_photo_url VARCHAR(500),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deliveries_order ON deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_store ON deliveries(store_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_assigned_to ON deliveries(assigned_to);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_location ON deliveries USING GIST(delivery_location);

-- Delivery Batches
CREATE TABLE IF NOT EXISTS delivery_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    batch_number VARCHAR(50) UNIQUE NOT NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    total_deliveries INTEGER,
    completed_deliveries INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_start TIMESTAMP WITHOUT TIME ZONE,
    actual_start TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    route_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_batches_store ON delivery_batches(store_id);
CREATE INDEX IF NOT EXISTS idx_delivery_batches_assigned_to ON delivery_batches(assigned_to);
CREATE INDEX IF NOT EXISTS idx_delivery_batches_status ON delivery_batches(status);

-- Delivery Events
CREATE TABLE IF NOT EXISTS delivery_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_location GEOGRAPHY(POINT),
    event_data JSONB,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_events_delivery ON delivery_events(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_events_type ON delivery_events(event_type);
CREATE INDEX IF NOT EXISTS idx_delivery_events_created ON delivery_events(created_at DESC);

-- Delivery Tracking
CREATE TABLE IF NOT EXISTS delivery_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    location GEOGRAPHY(POINT),
    accuracy_meters NUMERIC(8,2),
    speed_kmh NUMERIC(6,2),
    heading NUMERIC(5,2),
    battery_level INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_tracking_delivery ON delivery_tracking(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_location ON delivery_tracking USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_created ON delivery_tracking(created_at DESC);

-- Staff Delivery Status
CREATE TABLE IF NOT EXISTS staff_delivery_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    current_location GEOGRAPHY(POINT),
    last_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_user ON staff_delivery_status(user_id);
CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_available ON staff_delivery_status(is_available);
CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_location ON staff_delivery_status USING GIST(current_location);

-- Order Status History
CREATE TABLE IF NOT EXISTS order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by UUID REFERENCES users(id),
    change_reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_status_history_order ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_created ON order_status_history(created_at DESC);

-- ===========================
-- PRICING & PROMOTIONS TABLES
-- ===========================

-- Pricing Rules
CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    store_id UUID REFERENCES stores(id),
    ocs_sku VARCHAR(50),
    category VARCHAR(100),
    markup_percentage NUMERIC(5,2),
    markup_amount NUMERIC(10,2),
    min_price NUMERIC(10,2),
    max_price NUMERIC(10,2),
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP WITHOUT TIME ZONE,
    valid_until TIMESTAMP WITHOUT TIME ZONE,
    conditions JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pricing_rules_store ON pricing_rules(store_id);
CREATE INDEX IF NOT EXISTS idx_pricing_rules_sku ON pricing_rules(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_pricing_rules_active ON pricing_rules(is_active);

-- Customer Pricing Rules (VIP/wholesale pricing)
CREATE TABLE IF NOT EXISTS customer_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,
    discount_percentage NUMERIC(5,2),
    discount_amount NUMERIC(10,2),
    applies_to VARCHAR(50),
    ocs_sku VARCHAR(50),
    category VARCHAR(100),
    min_quantity INTEGER,
    max_quantity INTEGER,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP WITHOUT TIME ZONE,
    valid_until TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_pricing_rules_user ON customer_pricing_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_customer_pricing_rules_active ON customer_pricing_rules(is_active);

-- Dynamic Pricing Rules (surge/demand-based pricing)
CREATE TABLE IF NOT EXISTS dynamic_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    rule_name VARCHAR(255) NOT NULL,
    trigger_condition JSONB NOT NULL,
    price_adjustment_type VARCHAR(50) NOT NULL,
    adjustment_value NUMERIC(10,2),
    max_adjustment_percentage NUMERIC(5,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dynamic_pricing_rules_store ON dynamic_pricing_rules(store_id);

-- Price Tiers (volume discounts)
CREATE TABLE IF NOT EXISTS price_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    min_quantity INTEGER NOT NULL,
    max_quantity INTEGER,
    unit_price NUMERIC(10,2) NOT NULL,
    discount_percentage NUMERIC(5,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_price_tiers_store_sku ON price_tiers(store_id, ocs_sku);

-- Price History
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    price_type VARCHAR(50) NOT NULL,
    old_price NUMERIC(10,2),
    new_price NUMERIC(10,2) NOT NULL,
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_price_history_store_sku ON price_history(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_price_history_created ON price_history(created_at DESC);

-- Bundle Deals
CREATE TABLE IF NOT EXISTS bundle_deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    bundle_name VARCHAR(255) NOT NULL,
    bundle_items JSONB NOT NULL,
    bundle_price NUMERIC(10,2) NOT NULL,
    regular_price NUMERIC(10,2),
    savings_amount NUMERIC(10,2),
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP WITHOUT TIME ZONE,
    valid_until TIMESTAMP WITHOUT TIME ZONE,
    max_purchases_per_customer INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bundle_deals_store ON bundle_deals(store_id);
CREATE INDEX IF NOT EXISTS idx_bundle_deals_active ON bundle_deals(is_active);

-- Discount Codes
CREATE TABLE IF NOT EXISTS discount_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    store_id UUID REFERENCES stores(id),
    discount_type VARCHAR(50) NOT NULL,
    discount_value NUMERIC(10,2) NOT NULL,
    min_purchase_amount NUMERIC(10,2),
    max_discount_amount NUMERIC(10,2),
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    usage_limit_per_user INTEGER,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP WITHOUT TIME ZONE,
    valid_until TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes(code);
CREATE INDEX IF NOT EXISTS idx_discount_codes_store ON discount_codes(store_id);
CREATE INDEX IF NOT EXISTS idx_discount_codes_active ON discount_codes(is_active);

-- Discount Usage
CREATE TABLE IF NOT EXISTS discount_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_code_id UUID NOT NULL REFERENCES discount_codes(id),
    user_id UUID REFERENCES users(id),
    order_id UUID REFERENCES orders(id),
    discount_amount NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_discount_usage_code ON discount_usage(discount_code_id);
CREATE INDEX IF NOT EXISTS idx_discount_usage_user ON discount_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_discount_usage_order ON discount_usage(order_id);

-- Promotion Usage
CREATE TABLE IF NOT EXISTS promotion_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID NOT NULL REFERENCES promotions(id),
    user_id UUID REFERENCES users(id),
    order_id UUID,
    discount_amount NUMERIC(10,2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_promotion_usage_promotion ON promotion_usage(promotion_id);
CREATE INDEX IF NOT EXISTS idx_promotion_usage_user ON promotion_usage(user_id);

-- Tax Rates
CREATE TABLE IF NOT EXISTS tax_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province_territory_id UUID REFERENCES provinces_territories(id),
    tax_name VARCHAR(100) NOT NULL,
    tax_type VARCHAR(50) NOT NULL,
    rate NUMERIC(5,2) NOT NULL,
    is_compound BOOLEAN DEFAULT false,
    applies_to TEXT[],
    is_active BOOLEAN DEFAULT true,
    effective_from DATE,
    effective_until DATE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tax_rates_province ON tax_rates(province_territory_id);
CREATE INDEX IF NOT EXISTS idx_tax_rates_active ON tax_rates(is_active);

COMMENT ON TABLE delivery_zones IS 'Geographic delivery zones with polygonal boundaries';
COMMENT ON TABLE deliveries IS 'Delivery order tracking with real-time status updates';
COMMENT ON TABLE delivery_tracking IS 'GPS tracking points for active deliveries';
COMMENT ON TABLE pricing_rules IS 'Dynamic pricing rules and markup strategies';
COMMENT ON TABLE discount_codes IS 'Promotional discount codes';
COMMENT ON TABLE bundle_deals IS 'Product bundle promotions';
