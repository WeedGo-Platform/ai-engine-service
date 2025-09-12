-- =====================================================
-- Migration: Migrate inventory data to store_inventory table
-- Purpose: Transform single-tenant inventory to multi-tenant store inventory
-- Author: System
-- Date: 2024
-- =====================================================

BEGIN;

-- =====================================================
-- Step 1: Create store_inventory table if not exists
-- =====================================================

CREATE TABLE IF NOT EXISTS store_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    
    -- Quantity fields
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_in_transit INTEGER NOT NULL DEFAULT 0,
    
    -- Cost and pricing
    unit_cost DECIMAL(10, 2),
    retail_price DECIMAL(10, 2),
    
    -- Reorder management
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 100,
    
    -- Location within store
    location VARCHAR(100),
    zone VARCHAR(50),
    bin_number VARCHAR(50),
    
    -- Tracking dates
    last_restock_date TIMESTAMP WITH TIME ZONE,
    last_count_date TIMESTAMP WITH TIME ZONE,
    last_sale_date TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint per store
    UNIQUE(store_id, sku)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_store_inventory_store_id ON store_inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_store_inventory_sku ON store_inventory(sku);
CREATE INDEX IF NOT EXISTS idx_store_inventory_product_id ON store_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_store_inventory_quantity ON store_inventory(quantity_available);
CREATE INDEX IF NOT EXISTS idx_store_inventory_reorder ON store_inventory(quantity_available, reorder_point);

-- =====================================================
-- Step 2: Create inventory_transactions table
-- =====================================================

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    sku VARCHAR(100) NOT NULL,
    
    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL, -- sale, purchase, adjustment, transfer, return, damage, expire
    quantity INTEGER NOT NULL,
    reference_id UUID, -- Reference to order, transfer, etc.
    batch_lot VARCHAR(100),
    
    -- User tracking
    user_id UUID REFERENCES users(id),
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_inventory_transactions_store_id (store_id),
    INDEX idx_inventory_transactions_sku (sku),
    INDEX idx_inventory_transactions_type (transaction_type),
    INDEX idx_inventory_transactions_date (created_at)
);

-- =====================================================
-- Step 3: Create inventory_transfers table
-- =====================================================

CREATE TABLE IF NOT EXISTS inventory_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_store_id UUID NOT NULL REFERENCES stores(id),
    to_store_id UUID NOT NULL REFERENCES stores(id),
    
    -- Transfer details
    transfer_number VARCHAR(50) UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, in_transit, received, cancelled
    
    -- Tracking
    initiated_by UUID REFERENCES users(id),
    received_by UUID REFERENCES users(id),
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    shipped_at TIMESTAMP WITH TIME ZONE,
    received_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_inventory_transfers_from_store (from_store_id),
    INDEX idx_inventory_transfers_to_store (to_store_id),
    INDEX idx_inventory_transfers_status (status)
);

-- =====================================================
-- Step 4: Create inventory_transfer_items table
-- =====================================================

CREATE TABLE IF NOT EXISTS inventory_transfer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id UUID NOT NULL REFERENCES inventory_transfers(id) ON DELETE CASCADE,
    
    -- Item details
    sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    batch_lot VARCHAR(100),
    
    -- Tracking
    quantity_shipped INTEGER,
    quantity_received INTEGER,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Step 5: Create user_store_permissions table
-- =====================================================

CREATE TABLE IF NOT EXISTS user_store_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Permissions
    role VARCHAR(50) NOT NULL, -- owner, manager, staff, viewer
    permissions JSONB, -- Detailed permissions
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(user_id, store_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_store_permissions_user ON user_store_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_store_permissions_store ON user_store_permissions(store_id);

-- =====================================================
-- Step 6: Migrate existing inventory data
-- =====================================================

-- Get the default store (first active store or create one)
DO $$
DECLARE
    default_store_id UUID;
    default_tenant_id UUID;
BEGIN
    -- Try to get first active store
    SELECT id INTO default_store_id FROM stores WHERE status = 'active' LIMIT 1;
    
    -- If no store exists, create a default one
    IF default_store_id IS NULL THEN
        -- Get or create default tenant
        SELECT id INTO default_tenant_id FROM tenants LIMIT 1;
        
        IF default_tenant_id IS NULL THEN
            INSERT INTO tenants (name, code, status)
            VALUES ('Default Tenant', 'DEFAULT', 'active')
            RETURNING id INTO default_tenant_id;
        END IF;
        
        -- Create default store
        INSERT INTO stores (
            tenant_id, 
            store_code, 
            name, 
            address,
            timezone,
            status,
            delivery_enabled,
            pickup_enabled,
            pos_enabled,
            ecommerce_enabled
        ) VALUES (
            default_tenant_id,
            'MAIN',
            'Main Store',
            '{"street": "123 Main St", "city": "Toronto", "province": "ON", "postal_code": "M5V 3A8", "country": "Canada"}'::jsonb,
            'America/Toronto',
            'active',
            true,
            true,
            true,
            true
        ) RETURNING id INTO default_store_id;
    END IF;
    
    -- Migrate inventory data to store_inventory
    INSERT INTO store_inventory (
        store_id,
        product_id,
        sku,
        quantity_on_hand,
        quantity_available,
        quantity_reserved,
        unit_cost,
        retail_price,
        reorder_point,
        reorder_quantity,
        location,
        last_restock_date,
        created_at,
        updated_at
    )
    SELECT 
        default_store_id,
        p.id,
        i.sku,
        COALESCE(i.quantity_on_hand, 0),
        COALESCE(i.quantity_available, 0),
        COALESCE(i.quantity_reserved, 0),
        i.unit_cost,
        i.retail_price,
        COALESCE(i.reorder_point, 10),
        COALESCE(i.reorder_quantity, 100),
        i.location,
        i.last_restock_date,
        COALESCE(i.created_at, CURRENT_TIMESTAMP),
        COALESCE(i.updated_at, CURRENT_TIMESTAMP)
    FROM inventory i
    LEFT JOIN products p ON i.sku = p.sku
    WHERE NOT EXISTS (
        SELECT 1 FROM store_inventory si 
        WHERE si.store_id = default_store_id AND si.sku = i.sku
    );
    
    -- Update purchase_orders to include store_id
    UPDATE purchase_orders 
    SET store_id = default_store_id 
    WHERE store_id IS NULL;
    
    -- Log migration
    RAISE NOTICE 'Migrated inventory data to store % (%)', default_store_id, (SELECT name FROM stores WHERE id = default_store_id);
END $$;

-- =====================================================
-- Step 7: Add store_id to purchase_orders if not exists
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'purchase_orders' AND column_name = 'store_id'
    ) THEN
        ALTER TABLE purchase_orders 
        ADD COLUMN store_id UUID REFERENCES stores(id);
        
        -- Set default store for existing POs
        UPDATE purchase_orders 
        SET store_id = (SELECT id FROM stores WHERE status = 'active' LIMIT 1)
        WHERE store_id IS NULL;
        
        -- Make store_id NOT NULL for future records
        ALTER TABLE purchase_orders 
        ALTER COLUMN store_id SET NOT NULL;
    END IF;
END $$;

-- Create index on purchase_orders.store_id
CREATE INDEX IF NOT EXISTS idx_purchase_orders_store_id ON purchase_orders(store_id);

-- =====================================================
-- Step 8: Create store inventory views
-- =====================================================

-- View for low stock items per store
CREATE OR REPLACE VIEW store_low_stock_items AS
SELECT 
    si.store_id,
    s.name as store_name,
    si.sku,
    p.name as product_name,
    si.quantity_available,
    si.reorder_point,
    si.reorder_quantity,
    (si.reorder_point - si.quantity_available) as units_below_reorder
FROM store_inventory si
JOIN stores s ON si.store_id = s.id
LEFT JOIN products p ON si.product_id = p.id
WHERE si.quantity_available <= si.reorder_point
AND si.is_active = true
ORDER BY units_below_reorder DESC;

-- View for out of stock items per store
CREATE OR REPLACE VIEW store_out_of_stock_items AS
SELECT 
    si.store_id,
    s.name as store_name,
    si.sku,
    p.name as product_name,
    si.last_restock_date,
    si.reorder_quantity
FROM store_inventory si
JOIN stores s ON si.store_id = s.id
LEFT JOIN products p ON si.product_id = p.id
WHERE si.quantity_available = 0
AND si.is_active = true;

-- View for store inventory value
CREATE OR REPLACE VIEW store_inventory_value AS
SELECT 
    si.store_id,
    s.name as store_name,
    COUNT(DISTINCT si.sku) as total_skus,
    SUM(si.quantity_on_hand) as total_units,
    SUM(si.quantity_available * COALESCE(si.unit_cost, 0)) as total_cost_value,
    SUM(si.quantity_available * COALESCE(si.retail_price, 0)) as total_retail_value
FROM store_inventory si
JOIN stores s ON si.store_id = s.id
WHERE si.is_active = true
GROUP BY si.store_id, s.name;

-- =====================================================
-- Step 9: Create triggers for updated_at
-- =====================================================

-- Trigger for store_inventory
CREATE OR REPLACE FUNCTION update_store_inventory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_store_inventory_updated_at
    BEFORE UPDATE ON store_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_store_inventory_updated_at();

-- Trigger for user_store_permissions
CREATE OR REPLACE FUNCTION update_user_store_permissions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_store_permissions_updated_at
    BEFORE UPDATE ON user_store_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_user_store_permissions_updated_at();

-- =====================================================
-- Step 10: Grant permissions
-- =====================================================

-- Grant permissions to application user (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON store_inventory TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_transactions TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_transfers TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_transfer_items TO weedgo;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_store_permissions TO weedgo;
GRANT SELECT ON store_low_stock_items TO weedgo;
GRANT SELECT ON store_out_of_stock_items TO weedgo;
GRANT SELECT ON store_inventory_value TO weedgo;

-- =====================================================
-- Migration complete
-- =====================================================

COMMIT;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 015_migrate_inventory_to_store completed successfully';
    RAISE NOTICE 'Inventory data has been migrated to multi-tenant store structure';
END $$;