-- Migration: Add ASN (Advance Shipping Notice) fields to purchase orders
-- Date: 2025-09-07
-- Description: Extends purchase_orders and purchase_order_items tables to support ASN Excel import

BEGIN;

-- 1. Add ASN-specific columns to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS shipment_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS container_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS vendor VARCHAR(255);

-- 2. Add ASN-specific columns to purchase_order_items table  
ALTER TABLE purchase_order_items
ADD COLUMN IF NOT EXISTS item_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS vendor VARCHAR(255),
ADD COLUMN IF NOT EXISTS brand VARCHAR(255),
ADD COLUMN IF NOT EXISTS case_gtin VARCHAR(100),
ADD COLUMN IF NOT EXISTS packaged_on_date DATE,
ADD COLUMN IF NOT EXISTS gtin_barcode VARCHAR(100),
ADD COLUMN IF NOT EXISTS each_gtin VARCHAR(100),
ADD COLUMN IF NOT EXISTS shipped_qty INTEGER,
ADD COLUMN IF NOT EXISTS uom VARCHAR(50),
ADD COLUMN IF NOT EXISTS uom_conversion DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS uom_conversion_qty INTEGER,
ADD COLUMN IF NOT EXISTS exists_in_inventory BOOLEAN DEFAULT FALSE;

-- 3. Add indexes for improved query performance
CREATE INDEX IF NOT EXISTS idx_po_shipment_id ON purchase_orders(shipment_id);
CREATE INDEX IF NOT EXISTS idx_po_container_id ON purchase_orders(container_id);
CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor);
CREATE INDEX IF NOT EXISTS idx_poi_sku_batch ON purchase_order_items(sku, batch_lot);
CREATE INDEX IF NOT EXISTS idx_poi_case_gtin ON purchase_order_items(case_gtin);
CREATE INDEX IF NOT EXISTS idx_poi_gtin_barcode ON purchase_order_items(gtin_barcode);

-- 4. Create ASN import staging table for temporary data during import
CREATE TABLE IF NOT EXISTS asn_import_staging (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) NOT NULL,
    shipment_id VARCHAR(100),
    container_id VARCHAR(100),
    sku VARCHAR(100) NOT NULL,
    item_name VARCHAR(255),
    unit_price DECIMAL(10,2),
    vendor VARCHAR(255),
    brand VARCHAR(255),
    case_gtin VARCHAR(100),
    packaged_on_date DATE,
    batch_lot VARCHAR(100),
    gtin_barcode VARCHAR(100),
    each_gtin VARCHAR(100),
    shipped_qty INTEGER,
    uom VARCHAR(50),
    uom_conversion DECIMAL(10,4),
    uom_conversion_qty INTEGER,
    exists_in_inventory BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create function to check if item exists in inventory (SKU + BatchLot)
CREATE OR REPLACE FUNCTION check_inventory_exists(p_sku VARCHAR, p_batch_lot VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM batch_tracking 
        WHERE sku = p_sku 
        AND batch_lot = p_batch_lot 
        AND quantity_remaining > 0
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$$ LANGUAGE plpgsql;

-- 6. Create function to process ASN import into purchase order
CREATE OR REPLACE FUNCTION process_asn_to_purchase_order(
    p_session_id VARCHAR,
    p_po_number VARCHAR,
    p_supplier_id UUID,
    p_expected_date DATE,
    p_notes TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_po_id UUID;
    v_shipment_id VARCHAR;
    v_container_id VARCHAR;
    v_vendor VARCHAR;
    v_total_amount DECIMAL(12,2);
    v_item RECORD;
BEGIN
    -- Get common values from staging
    SELECT DISTINCT 
        shipment_id, 
        container_id, 
        vendor 
    INTO v_shipment_id, v_container_id, v_vendor
    FROM asn_import_staging
    WHERE session_id = p_session_id
    LIMIT 1;
    
    -- Calculate total amount
    SELECT SUM(unit_price * shipped_qty) INTO v_total_amount
    FROM asn_import_staging
    WHERE session_id = p_session_id;
    
    -- Create purchase order
    INSERT INTO purchase_orders (
        po_number,
        supplier_id,
        expected_date,
        status,
        total_amount,
        notes,
        shipment_id,
        container_id,
        vendor
    ) VALUES (
        p_po_number,
        p_supplier_id,
        p_expected_date,
        'pending',
        v_total_amount,
        p_notes,
        v_shipment_id,
        v_container_id,
        v_vendor
    ) RETURNING id INTO v_po_id;
    
    -- Insert purchase order items from staging
    FOR v_item IN 
        SELECT * FROM asn_import_staging 
        WHERE session_id = p_session_id
    LOOP
        -- Check if item exists in inventory
        v_item.exists_in_inventory := check_inventory_exists(v_item.sku, v_item.batch_lot);
        
        -- Insert into purchase_order_items
        INSERT INTO purchase_order_items (
            purchase_order_id,
            sku,
            batch_lot,
            quantity_ordered,
            unit_cost,
            item_name,
            vendor,
            brand,
            case_gtin,
            packaged_on_date,
            gtin_barcode,
            each_gtin,
            shipped_qty,
            uom,
            uom_conversion,
            uom_conversion_qty,
            exists_in_inventory,
            expiry_date
        ) VALUES (
            v_po_id,
            v_item.sku,
            v_item.batch_lot,
            v_item.shipped_qty,
            v_item.unit_price,
            v_item.item_name,
            v_item.vendor,
            v_item.brand,
            v_item.case_gtin,
            v_item.packaged_on_date,
            v_item.gtin_barcode,
            v_item.each_gtin,
            v_item.shipped_qty,
            v_item.uom,
            v_item.uom_conversion,
            v_item.uom_conversion_qty,
            v_item.exists_in_inventory,
            v_item.packaged_on_date + INTERVAL '1 year' -- Default expiry 1 year from packaged date
        );
    END LOOP;
    
    -- Clean up staging data
    DELETE FROM asn_import_staging WHERE session_id = p_session_id;
    
    RETURN v_po_id;
END;
$$ LANGUAGE plpgsql;

-- 7. Update the receive purchase order function to handle ASN fields
CREATE OR REPLACE FUNCTION receive_purchase_order(p_po_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_item RECORD;
    v_result JSONB = '{"status": "success", "items_processed": []}'::JSONB;
    v_items_array JSONB = '[]'::JSONB;
BEGIN
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received',
        received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    -- Process each item
    FOR v_item IN 
        SELECT * FROM purchase_order_items 
        WHERE purchase_order_id = p_po_id
    LOOP
        -- Update inventory
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_item.sku, v_item.shipped_qty, v_item.shipped_qty, v_item.unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_item.shipped_qty,
            quantity_available = inventory.quantity_available + v_item.shipped_qty,
            unit_cost = v_item.unit_cost,
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Update batch tracking
        INSERT INTO batch_tracking (
            sku,
            batch_lot,
            purchase_order_id,
            quantity_received,
            quantity_remaining,
            unit_cost,
            expiry_date
        ) VALUES (
            v_item.sku,
            v_item.batch_lot,
            p_po_id,
            v_item.shipped_qty,
            v_item.shipped_qty,
            v_item.unit_cost,
            v_item.expiry_date
        );
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku,
            transaction_type,
            quantity,
            reference_type,
            reference_id,
            notes
        ) VALUES (
            v_item.sku,
            'purchase_receipt',
            v_item.shipped_qty,
            'purchase_order',
            p_po_id::TEXT,
            CONCAT('Received from PO: ', (SELECT po_number FROM purchase_orders WHERE id = p_po_id))
        );
        
        -- Update quantity_received in purchase_order_items
        UPDATE purchase_order_items
        SET quantity_received = shipped_qty
        WHERE id = v_item.id;
        
        -- Add to result
        v_items_array = v_items_array || jsonb_build_object(
            'sku', v_item.sku,
            'batch_lot', v_item.batch_lot,
            'quantity_received', v_item.shipped_qty
        );
    END LOOP;
    
    v_result = jsonb_set(v_result, '{items_processed}', v_items_array);
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- 8. Add comments for documentation
COMMENT ON COLUMN purchase_orders.shipment_id IS 'ASN Shipment ID from Excel import';
COMMENT ON COLUMN purchase_orders.container_id IS 'ASN Container ID from Excel import';
COMMENT ON COLUMN purchase_order_items.case_gtin IS 'Global Trade Item Number for case';
COMMENT ON COLUMN purchase_order_items.gtin_barcode IS 'GTIN Barcode from ASN';
COMMENT ON COLUMN purchase_order_items.each_gtin IS 'GTIN for individual item';
COMMENT ON COLUMN purchase_order_items.uom IS 'Unit of Measure from ASN';
COMMENT ON COLUMN purchase_order_items.uom_conversion IS 'UOM conversion factor';
COMMENT ON COLUMN purchase_order_items.exists_in_inventory IS 'Flag indicating if SKU+BatchLot exists in inventory';
COMMENT ON TABLE asn_import_staging IS 'Temporary staging table for ASN Excel imports';
COMMENT ON FUNCTION check_inventory_exists IS 'Checks if SKU+BatchLot combination exists in inventory';
COMMENT ON FUNCTION process_asn_to_purchase_order IS 'Processes staged ASN data into purchase order';

COMMIT;