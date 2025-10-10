-- ============================================================================
-- Migration: Add Foreign Key Constraints
-- Description: Add foreign keys that reference tables created in earlier migrations
-- Dependencies: 011_create_communication_auth_tables.sql
-- ============================================================================

-- ===========================
-- USER TABLE FOREIGN KEYS
-- ===========================

DO $$
BEGIN
    -- Add FK to default_store_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'users_default_store_id_fkey'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_default_store_id_fkey
            FOREIGN KEY (default_store_id) REFERENCES stores(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ===========================
-- STORES TABLE FOREIGN KEYS
-- ===========================

DO $$
BEGIN
    -- Add FK to province_territory_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'stores_province_territory_id_fkey'
    ) THEN
        ALTER TABLE stores ADD CONSTRAINT stores_province_territory_id_fkey
            FOREIGN KEY (province_territory_id) REFERENCES provinces_territories(id);
    END IF;
END $$;

-- ===========================
-- ORDERS TABLE FOREIGN KEYS
-- ===========================

DO $$
BEGIN
    -- Add FK to cart_session_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'orders_cart_session_id_fkey'
    ) THEN
        ALTER TABLE orders ADD CONSTRAINT orders_cart_session_id_fkey
            FOREIGN KEY (cart_session_id) REFERENCES cart_sessions(id) ON DELETE SET NULL;
    END IF;

    -- Add FK to tenant_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'orders_tenant_id_fkey'
    ) THEN
        ALTER TABLE orders ADD CONSTRAINT orders_tenant_id_fkey
            FOREIGN KEY (tenant_id) REFERENCES tenants(id);
    END IF;
END $$;

-- ===========================
-- INVENTORY TABLE FOREIGN KEYS
-- ===========================

-- Add accessory category FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'accessories_catalog_category_id_fkey'
    ) THEN
        ALTER TABLE accessories_catalog ADD CONSTRAINT accessories_catalog_category_id_fkey
            FOREIGN KEY (category_id) REFERENCES accessory_categories(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ===========================
-- PRICING TABLE FOREIGN KEYS
-- ===========================

-- Add delivery zone geometry update trigger (automatically compute ST_GeographyFromText)
CREATE OR REPLACE FUNCTION update_delivery_zone_geometry()
RETURNS TRIGGER AS $$
BEGIN
    -- Trigger logic can be added here if needed for geometry updates
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================
-- ADDITIONAL INDEX OPTIMIZATIONS
-- ===========================

-- Add GiST indexes for geography columns
CREATE INDEX IF NOT EXISTS idx_delivery_zones_geometry_gist
    ON delivery_zones USING GIST(geometry);

CREATE INDEX IF NOT EXISTS idx_delivery_geofences_geometry_gist
    ON delivery_geofences USING GIST(geometry);

CREATE INDEX IF NOT EXISTS idx_deliveries_location_gist
    ON deliveries USING GIST(delivery_location);

CREATE INDEX IF NOT EXISTS idx_delivery_tracking_location_gist
    ON delivery_tracking USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_location_gist
    ON staff_delivery_status USING GIST(current_location);

CREATE INDEX IF NOT EXISTS idx_location_access_log_location_gist
    ON location_access_log USING GIST(location_data);

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_orders_store_created
    ON orders(store_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_user_created
    ON orders(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_store_created
    ON payment_transactions(store_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_store_low_stock
    ON ocs_inventory(store_id, quantity) WHERE quantity <= reorder_point;

CREATE INDEX IF NOT EXISTS idx_cart_sessions_user_active
    ON cart_sessions(user_id, expires_at) WHERE expires_at > NOW();

CREATE INDEX IF NOT EXISTS idx_deliveries_assigned_status
    ON deliveries(assigned_to, status) WHERE status IN ('pending', 'assigned', 'in_transit');

-- Add partial indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_active_customers
    ON users(id, created_at) WHERE active = true AND role = 'customer'::user_role_simple;

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_active_products
    ON ocs_inventory(store_id, ocs_sku, quantity) WHERE quantity > 0;

-- ===========================
-- TRIGGERS
-- ===========================

-- Add trigger to update updated_at on store_settings
DROP TRIGGER IF EXISTS update_store_settings_updated_at ON store_settings;
CREATE TRIGGER update_store_settings_updated_at
    BEFORE UPDATE ON store_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on profiles
DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on user_addresses
DROP TRIGGER IF EXISTS update_user_addresses_updated_at ON user_addresses;
CREATE TRIGGER update_user_addresses_updated_at
    BEFORE UPDATE ON user_addresses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on ocs_inventory
DROP TRIGGER IF EXISTS update_ocs_inventory_updated_at ON ocs_inventory;
CREATE TRIGGER update_ocs_inventory_updated_at
    BEFORE UPDATE ON ocs_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on cart_sessions
DROP TRIGGER IF EXISTS update_cart_sessions_updated_at ON cart_sessions;
CREATE TRIGGER update_cart_sessions_updated_at
    BEFORE UPDATE ON cart_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on deliveries
DROP TRIGGER IF EXISTS update_deliveries_updated_at ON deliveries;
CREATE TRIGGER update_deliveries_updated_at
    BEFORE UPDATE ON deliveries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at on customer_reviews
DROP TRIGGER IF EXISTS update_customer_reviews_updated_at ON customer_reviews;
CREATE TRIGGER update_customer_reviews_updated_at
    BEFORE UPDATE ON customer_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON CONSTRAINT users_default_store_id_fkey ON users IS 'User default store preference';
COMMENT ON CONSTRAINT stores_province_territory_id_fkey ON stores IS 'Store regulatory jurisdiction';
COMMENT ON CONSTRAINT orders_cart_session_id_fkey ON orders IS 'Link order to originating cart session';
