-- ============================================================================
-- Migration: Create Inventory & Product Tables
-- Description: Create OCS product catalog, inventory, and tracking tables
-- Dependencies: 006_create_foundation_tables.sql
-- ============================================================================

-- OCS Product Catalog (Ontario Cannabis Store master catalog)
CREATE TABLE IF NOT EXISTS ocs_product_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ocs_sku VARCHAR(50) UNIQUE NOT NULL,
    item_number VARCHAR(50),
    category VARCHAR(100),
    brand VARCHAR(255),
    product_name VARCHAR(500) NOT NULL,
    thc_min NUMERIC(5,2),
    thc_max NUMERIC(5,2),
    cbd_min NUMERIC(5,2),
    cbd_max NUMERIC(5,2),
    product_type VARCHAR(100),
    weight NUMERIC(10,2),
    weight_unit VARCHAR(20),
    wholesale_price NUMERIC(10,2),
    suggested_retail_price NUMERIC(10,2),
    description TEXT,
    ingredients TEXT,
    producer VARCHAR(255),
    country_of_origin VARCHAR(2) DEFAULT 'CA',
    image_url VARCHAR(500),
    lab_results_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_sku ON ocs_product_catalog(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_category ON ocs_product_catalog(category);
CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_brand ON ocs_product_catalog(brand);
CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_active ON ocs_product_catalog(is_active);
CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_name_trgm ON ocs_product_catalog USING gin(product_name gin_trgm_ops);

-- OCS Inventory (per-store inventory levels)
CREATE TABLE IF NOT EXISTS ocs_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    reorder_point INTEGER DEFAULT 5,
    reorder_quantity INTEGER DEFAULT 20,
    location_code VARCHAR(50),
    last_received TIMESTAMP WITHOUT TIME ZONE,
    last_sold TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, ocs_sku)
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_store_sku ON ocs_inventory(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_sku ON ocs_inventory(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_low_stock ON ocs_inventory(store_id) WHERE quantity <= reorder_point;

-- OCS Inventory Transactions (audit trail for all inventory movements)
CREATE TABLE IF NOT EXISTS ocs_inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    quantity_change INTEGER NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    reference_id UUID,
    reference_type VARCHAR(50),
    notes TEXT,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_transactions_store ON ocs_inventory_transactions(store_id);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_transactions_sku ON ocs_inventory_transactions(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_transactions_type ON ocs_inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_transactions_created ON ocs_inventory_transactions(created_at DESC);

-- OCS Inventory Movements
CREATE TABLE IF NOT EXISTS ocs_inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_store_id UUID REFERENCES stores(id),
    to_store_id UUID REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    requested_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_movements_from_store ON ocs_inventory_movements(from_store_id);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_movements_to_store ON ocs_inventory_movements(to_store_id);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_movements_status ON ocs_inventory_movements(status);

-- OCS Inventory Reservations
CREATE TABLE IF NOT EXISTS ocs_inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    reserved_for VARCHAR(50),
    reference_id UUID,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_reservations_store_sku ON ocs_inventory_reservations(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_reservations_expires ON ocs_inventory_reservations(expires_at);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_reservations_reference ON ocs_inventory_reservations(reference_id);

-- OCS Inventory Snapshots (daily inventory snapshots for reporting)
CREATE TABLE IF NOT EXISTS ocs_inventory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    snapshot_date DATE NOT NULL,
    inventory_data JSONB NOT NULL,
    total_skus INTEGER,
    total_quantity INTEGER,
    total_value NUMERIC(12,2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_snapshots_store_date ON ocs_inventory_snapshots(store_id, snapshot_date DESC);

-- OCS Inventory Logs (change history)
CREATE TABLE IF NOT EXISTS ocs_inventory_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES users(id),
    change_reason TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_logs_store_sku ON ocs_inventory_logs(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_logs_created ON ocs_inventory_logs(created_at DESC);

-- Batch Tracking (lot/batch tracking for product recalls)
CREATE TABLE IF NOT EXISTS batch_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    ocs_sku VARCHAR(50) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    lot_number VARCHAR(100),
    production_date DATE,
    expiry_date DATE,
    received_date DATE NOT NULL,
    quantity_received INTEGER NOT NULL,
    quantity_remaining INTEGER NOT NULL,
    supplier_id UUID REFERENCES provincial_suppliers(id),
    test_results JSONB,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, batch_number, ocs_sku)
);

CREATE INDEX IF NOT EXISTS idx_batch_tracking_store_sku ON batch_tracking(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_batch_tracking_batch ON batch_tracking(batch_number);
CREATE INDEX IF NOT EXISTS idx_batch_tracking_expiry ON batch_tracking(expiry_date);
CREATE INDEX IF NOT EXISTS idx_batch_tracking_status ON batch_tracking(status);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) UNIQUE NOT NULL,
    store_id UUID NOT NULL REFERENCES stores(id),
    supplier_id UUID REFERENCES provincial_suppliers(id),
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    subtotal NUMERIC(12,2),
    tax_amount NUMERIC(12,2),
    total_amount NUMERIC(12,2),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    received_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_store ON purchase_orders(store_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_po_number ON purchase_orders(po_number);

-- Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    unit_cost NUMERIC(10,2) NOT NULL,
    total_cost NUMERIC(12,2) NOT NULL,
    batch_number VARCHAR(100),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_order_items_po ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_sku ON purchase_order_items(ocs_sku);

-- Inventory Locations (warehouse locations, bins, shelves)
CREATE TABLE IF NOT EXISTS inventory_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    location_code VARCHAR(50) NOT NULL,
    location_name VARCHAR(255),
    location_type VARCHAR(50),
    parent_location_id UUID REFERENCES inventory_locations(id),
    aisle VARCHAR(20),
    bay VARCHAR(20),
    shelf VARCHAR(20),
    bin VARCHAR(20),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, location_code)
);

CREATE INDEX IF NOT EXISTS idx_inventory_locations_store ON inventory_locations(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_locations_parent ON inventory_locations(parent_location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_locations_type ON inventory_locations(location_type);

-- Shelf Locations
CREATE TABLE IF NOT EXISTS shelf_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    location_id UUID REFERENCES inventory_locations(id),
    quantity INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shelf_locations_store_sku ON shelf_locations(store_id, ocs_sku);
CREATE INDEX IF NOT EXISTS idx_shelf_locations_location ON shelf_locations(location_id);

-- Cart Sessions (shopping cart persistence)
CREATE TABLE IF NOT EXISTS cart_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id UUID NOT NULL REFERENCES stores(id),
    session_id VARCHAR(255) NOT NULL,
    items JSONB DEFAULT '[]'::jsonb,
    subtotal NUMERIC(10,2) DEFAULT 0.00,
    tax_amount NUMERIC(10,2) DEFAULT 0.00,
    total_amount NUMERIC(10,2) DEFAULT 0.00,
    promo_code VARCHAR(50),
    discount_amount NUMERIC(10,2) DEFAULT 0.00,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    converted_to_order_id UUID,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cart_sessions_user_id ON cart_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_sessions_store_id ON cart_sessions(store_id);
CREATE INDEX IF NOT EXISTS idx_cart_sessions_session_id ON cart_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_cart_sessions_expires ON cart_sessions(expires_at);

-- Accessories Catalog
CREATE TABLE IF NOT EXISTS accessories_catalog (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category_id INTEGER,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    brand VARCHAR(255),
    wholesale_price NUMERIC(10,2),
    retail_price NUMERIC(10,2),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_accessories_catalog_sku ON accessories_catalog(sku);
CREATE INDEX IF NOT EXISTS idx_accessories_catalog_category ON accessories_catalog(category_id);

-- Accessory Categories
CREATE TABLE IF NOT EXISTS accessory_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES accessory_categories(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Accessories Inventory
CREATE TABLE IF NOT EXISTS accessories_inventory (
    id SERIAL PRIMARY KEY,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    accessory_id INTEGER NOT NULL REFERENCES accessories_catalog(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 5,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, accessory_id)
);

CREATE INDEX IF NOT EXISTS idx_accessories_inventory_store ON accessories_inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_accessories_inventory_accessory ON accessories_inventory(accessory_id);

COMMENT ON TABLE ocs_product_catalog IS 'OCS (Ontario Cannabis Store) master product catalog';
COMMENT ON TABLE ocs_inventory IS 'Store-level inventory for OCS products';
COMMENT ON TABLE ocs_inventory_transactions IS 'Complete audit trail of all inventory changes';
COMMENT ON TABLE batch_tracking IS 'Lot/batch tracking for product recalls and compliance';
COMMENT ON TABLE purchase_orders IS 'Purchase orders from provincial suppliers';
COMMENT ON TABLE cart_sessions IS 'Persistent shopping cart sessions';
