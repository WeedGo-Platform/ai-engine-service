-- Migration: Create inventory_movements table
-- Purpose: Track all inventory movements for audit and analytics

-- Create inventory_movements table
CREATE TABLE IF NOT EXISTS inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id VARCHAR(255) NOT NULL,
    sku VARCHAR(255) NOT NULL,
    movement_type VARCHAR(50) NOT NULL CHECK (movement_type IN (
        'purchase', 'sale', 'return', 'adjustment', 
        'transfer_in', 'transfer_out', 'damage', 'theft', 'expiry'
    )),
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10, 2),
    unit_price DECIMAL(10, 2),
    total_value DECIMAL(10, 2),
    reference_type VARCHAR(50), -- 'order', 'transfer', 'adjustment', etc
    reference_id VARCHAR(255), -- order_id, transfer_id, etc
    reason TEXT,
    performed_by UUID REFERENCES users(id),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_inventory_movements_store_id ON inventory_movements(store_id);
CREATE INDEX idx_inventory_movements_product_id ON inventory_movements(product_id);
CREATE INDEX idx_inventory_movements_sku ON inventory_movements(sku);
CREATE INDEX idx_inventory_movements_created_at ON inventory_movements(created_at);
CREATE INDEX idx_inventory_movements_movement_type ON inventory_movements(movement_type);
CREATE INDEX idx_inventory_movements_reference ON inventory_movements(reference_type, reference_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_inventory_movements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_inventory_movements_updated_at_trigger
BEFORE UPDATE ON inventory_movements
FOR EACH ROW
EXECUTE FUNCTION update_inventory_movements_updated_at();

-- Create inventory_snapshots table for point-in-time inventory tracking
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id VARCHAR(255) NOT NULL,
    sku VARCHAR(255) NOT NULL,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    reorder_point INTEGER,
    reorder_quantity INTEGER,
    unit_cost DECIMAL(10, 2),
    last_movement_id UUID REFERENCES inventory_movements(id),
    last_counted_at TIMESTAMP,
    last_sold_at TIMESTAMP,
    last_received_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, sku)
);

-- Create indexes for inventory_snapshots
CREATE INDEX idx_inventory_snapshots_store_id ON inventory_snapshots(store_id);
CREATE INDEX idx_inventory_snapshots_product_id ON inventory_snapshots(product_id);
CREATE INDEX idx_inventory_snapshots_sku ON inventory_snapshots(sku);
CREATE INDEX idx_inventory_snapshots_quantity_available ON inventory_snapshots(quantity_available);

-- Create trigger for inventory_snapshots
CREATE TRIGGER update_inventory_snapshots_updated_at_trigger
BEFORE UPDATE ON inventory_snapshots
FOR EACH ROW
EXECUTE FUNCTION update_inventory_movements_updated_at();

-- Add sample data for testing (optional)
COMMENT ON TABLE inventory_movements IS 'Tracks all inventory movements for audit trail and analytics';
COMMENT ON TABLE inventory_snapshots IS 'Current inventory levels and status for each product in each store';