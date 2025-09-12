-- Fix the receive_purchase_order function to include GTIN columns when inserting batch tracking
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
        
        -- Update batch tracking WITH GTIN columns
        INSERT INTO batch_tracking (
            sku,
            batch_lot,
            purchase_order_id,
            quantity_received,
            quantity_remaining,
            unit_cost,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin
        ) VALUES (
            v_item.sku,
            v_item.batch_lot,
            p_po_id,
            v_item.shipped_qty,
            v_item.shipped_qty,
            v_item.unit_cost,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin
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
            'purchase',
            v_item.shipped_qty,
            'purchase_order',
            p_po_id,
            'Received from PO'
        );
        
        -- Add item to result
        v_items_array = v_items_array || jsonb_build_object(
            'sku', v_item.sku,
            'quantity', v_item.shipped_qty,
            'status', 'received'
        );
    END LOOP;
    
    v_result = v_result || jsonb_build_object('items_processed', v_items_array);
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Also update process_asn_to_purchase_order to ensure GTIN columns are properly transferred
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
        total_amount,
        status,
        expected_date,
        notes,
        shipment_id,
        container_id,
        vendor
    ) VALUES (
        p_po_number,
        p_supplier_id,
        COALESCE(v_total_amount, 0),
        'pending',
        p_expected_date,
        p_notes,
        v_shipment_id,
        v_container_id,
        v_vendor
    ) RETURNING id INTO v_po_id;
    
    -- Create purchase order items
    FOR v_item IN 
        SELECT * FROM asn_import_staging 
        WHERE session_id = p_session_id
    LOOP
        INSERT INTO purchase_order_items (
            purchase_order_id,
            sku,
            item_name,
            quantity,
            unit_cost,
            total,
            batch_lot,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin,
            shipped_qty,
            uom,
            uom_conversion,
            exists_in_inventory
        ) VALUES (
            v_po_id,
            v_item.sku,
            v_item.item_name,
            v_item.shipped_qty,
            v_item.unit_price,
            v_item.unit_price * v_item.shipped_qty,
            v_item.batch_lot,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin,
            v_item.shipped_qty,
            v_item.uom,
            v_item.uom_conversion,
            v_item.exists_in_inventory
        );
    END LOOP;
    
    -- Clear staging data
    DELETE FROM asn_import_staging WHERE session_id = p_session_id;
    
    RETURN v_po_id;
END;
$$ LANGUAGE plpgsql;