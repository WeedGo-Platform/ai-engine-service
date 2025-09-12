-- Migration: Inventory Management System
-- Description: Create inventory tracking tables with purchase order management
-- Date: 2025-09-07

-- 1. Rename products table to product_catalog
ALTER TABLE IF EXISTS products RENAME TO product_catalog;

-- Add ocs_variant_number if it doesn't exist
ALTER TABLE product_catalog 
ADD COLUMN IF NOT EXISTS ocs_variant_number VARCHAR(100);

-- Update existing records to have ocs_variant_number (use id as fallback)
UPDATE product_catalog 
SET ocs_variant_number = COALESCE(ocs_variant_number, 'SKU-' || LEFT(id::text, 8))
WHERE ocs_variant_number IS NULL;

-- Make ocs_variant_number NOT NULL and UNIQUE after populating
ALTER TABLE product_catalog 
ALTER COLUMN ocs_variant_number SET NOT NULL;

-- Add unique constraint for foreign key reference
ALTER TABLE product_catalog
ADD CONSTRAINT uk_product_catalog_ocs_variant UNIQUE (ocs_variant_number);

-- 2. Create suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create purchase_orders table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(100) UNIQUE NOT NULL,
    supplier_id UUID REFERENCES suppliers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_date DATE,
    received_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'received', 'cancelled')),
    total_amount DECIMAL(12,2),
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create purchase_order_items table
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    batch_lot VARCHAR(100),
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    quantity_received INTEGER DEFAULT 0 CHECK (quantity_received >= 0),
    unit_cost DECIMAL(10,2) NOT NULL CHECK (unit_cost >= 0),
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (quantity_ordered * unit_cost) STORED,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    quantity_on_hand INTEGER DEFAULT 0 CHECK (quantity_on_hand >= 0),
    quantity_available INTEGER DEFAULT 0 CHECK (quantity_available >= 0),
    quantity_reserved INTEGER DEFAULT 0 CHECK (quantity_reserved >= 0),
    unit_cost DECIMAL(10,2) DEFAULT 0,
    retail_price DECIMAL(10,2) GENERATED ALWAYS AS (unit_cost * 1.25) STORED,
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    location VARCHAR(100),
    last_restock_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_sku FOREIGN KEY (sku) 
        REFERENCES product_catalog(ocs_variant_number) ON UPDATE CASCADE
);

-- 6. Create inventory_transactions table for audit trail
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('purchase', 'sale', 'adjustment', 'return', 'transfer')),
    reference_id UUID,
    reference_type VARCHAR(50),
    batch_lot VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    running_balance INTEGER,
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Create batch_tracking table for lot management
CREATE TABLE IF NOT EXISTS batch_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_lot VARCHAR(100) UNIQUE NOT NULL,
    sku VARCHAR(100) NOT NULL,
    purchase_order_id UUID REFERENCES purchase_orders(id),
    quantity_received INTEGER NOT NULL,
    quantity_remaining INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    received_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Create inventory_view for product search
CREATE OR REPLACE VIEW inventory_products_view AS
SELECT 
    pc.id,
    pc.product_name as name,
    pc.ocs_variant_number as sku,
    pc.category,
    pc.strain_type,
    pc.thc_max_percent as thc_percentage,
    pc.cbd_max_percent as cbd_percentage,
    pc.long_description as description,
    pc.brand,
    pc.image_url,
    pc.street_name as effects,
    pc.colour as flavors,
    pc.terpenes,
    COALESCE(inv.quantity_available, 0) as quantity_available,
    COALESCE(inv.quantity_on_hand, 0) as quantity_on_hand,
    COALESCE(inv.retail_price, pc.unit_price) as price,
    COALESCE(inv.unit_cost, 0) as unit_cost,
    inv.location,
    inv.reorder_point,
    CASE 
        WHEN inv.quantity_available > 0 THEN 'in_stock'
        WHEN inv.quantity_on_hand > 0 THEN 'reserved'
        ELSE 'out_of_stock'
    END as stock_status,
    pc.created_at,
    pc.updated_at
FROM product_catalog pc
LEFT JOIN inventory inv ON pc.ocs_variant_number = inv.sku;

-- 9. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_quantity ON inventory(quantity_available);
CREATE INDEX IF NOT EXISTS idx_po_items_po_id ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_items_sku ON purchase_order_items(sku);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_transactions_sku ON inventory_transactions(sku);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batch_sku ON batch_tracking(sku);
CREATE INDEX IF NOT EXISTS idx_batch_lot ON batch_tracking(batch_lot);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs ON product_catalog(ocs_variant_number);

-- 10. Create trigger for inventory updates
CREATE OR REPLACE FUNCTION update_inventory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_inventory_timestamp_trigger
BEFORE UPDATE ON inventory
FOR EACH ROW
EXECUTE FUNCTION update_inventory_timestamp();

CREATE TRIGGER update_purchase_orders_timestamp_trigger
BEFORE UPDATE ON purchase_orders
FOR EACH ROW
EXECUTE FUNCTION update_inventory_timestamp();

-- 11. Create function to process purchase order receipt
CREATE OR REPLACE FUNCTION process_purchase_order_receipt(
    p_po_id UUID,
    p_items JSONB
) RETURNS JSONB AS $$
DECLARE
    v_item JSONB;
    v_sku VARCHAR(100);
    v_quantity INTEGER;
    v_unit_cost DECIMAL(10,2);
    v_batch_lot VARCHAR(100);
    v_result JSONB = '[]'::JSONB;
BEGIN
    -- Process each item in the purchase order
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_sku := v_item->>'sku';
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_cost := (v_item->>'unit_cost')::DECIMAL;
        v_batch_lot := v_item->>'batch_lot';
        
        -- Update or insert inventory record
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_sku, v_quantity, v_quantity, v_unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_quantity,
            quantity_available = inventory.quantity_available + v_quantity,
            unit_cost = ((inventory.quantity_on_hand * inventory.unit_cost) + (v_quantity * v_unit_cost)) 
                        / (inventory.quantity_on_hand + v_quantity),
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku, transaction_type, reference_id, reference_type, 
            batch_lot, quantity, unit_cost, running_balance
        )
        SELECT 
            v_sku, 'purchase', p_po_id, 'purchase_order',
            v_batch_lot, v_quantity, v_unit_cost, quantity_on_hand
        FROM inventory
        WHERE sku = v_sku;
        
        -- Track batch/lot
        IF v_batch_lot IS NOT NULL THEN
            INSERT INTO batch_tracking (
                batch_lot, sku, purchase_order_id, 
                quantity_received, quantity_remaining, unit_cost
            )
            VALUES (
                v_batch_lot, v_sku, p_po_id,
                v_quantity, v_quantity, v_unit_cost
            );
        END IF;
        
        v_result := v_result || jsonb_build_object('sku', v_sku, 'processed', true);
    END LOOP;
    
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received', received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- 12. Insert default supplier for testing
INSERT INTO suppliers (name, contact_person, email, phone, payment_terms)
VALUES 
    ('WeedGo Wholesale', 'John Supplier', 'wholesale@weedgo.com', '416-555-0001', 'NET30'),
    ('Green Gardens Co', 'Mary Green', 'orders@greengardens.com', '416-555-0002', 'NET15')
ON CONFLICT DO NOTHING;