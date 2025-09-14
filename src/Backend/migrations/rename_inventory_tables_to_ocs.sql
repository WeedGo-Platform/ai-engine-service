-- Migration: Rename inventory_* tables to ocs_inventory_*
-- Date: 2025-01-13
-- Description: 
--   Rename all inventory_* tables to ocs_inventory_* for consistency
--   with OCS naming convention
--   Tables to rename:
--   - inventory_movements -> ocs_inventory_movements
--   - inventory_reservations -> ocs_inventory_reservations
--   - inventory_snapshots -> ocs_inventory_snapshots
--   - inventory_transactions -> ocs_inventory_transactions
--   Note: NOT renaming accessories_inventory as it's not OCS-specific

BEGIN;

-- 1. Rename inventory_movements to ocs_inventory_movements
ALTER TABLE inventory_movements RENAME TO ocs_inventory_movements;

-- Update indexes
ALTER INDEX IF EXISTS idx_inventory_movements_sku RENAME TO idx_ocs_inventory_movements_sku;
ALTER INDEX IF EXISTS idx_inventory_movements_store RENAME TO idx_ocs_inventory_movements_store;
ALTER INDEX IF EXISTS idx_inventory_movements_timestamp RENAME TO idx_ocs_inventory_movements_timestamp;
ALTER INDEX IF EXISTS idx_inventory_movements_type RENAME TO idx_ocs_inventory_movements_type;

-- Update trigger names
ALTER TRIGGER update_inventory_movements_updated_at_trigger ON ocs_inventory_movements 
    RENAME TO update_ocs_inventory_movements_updated_at_trigger;

-- 2. Rename inventory_reservations to ocs_inventory_reservations
ALTER TABLE inventory_reservations RENAME TO ocs_inventory_reservations;

-- Update indexes
ALTER INDEX IF EXISTS idx_inventory_reservations_sku RENAME TO idx_ocs_inventory_reservations_sku;
ALTER INDEX IF EXISTS idx_inventory_reservations_order RENAME TO idx_ocs_inventory_reservations_order;
ALTER INDEX IF EXISTS idx_inventory_reservations_status RENAME TO idx_ocs_inventory_reservations_status;
ALTER INDEX IF EXISTS idx_inventory_reservations_expires RENAME TO idx_ocs_inventory_reservations_expires;

-- 3. Rename inventory_snapshots to ocs_inventory_snapshots
ALTER TABLE inventory_snapshots RENAME TO ocs_inventory_snapshots;

-- Update indexes
ALTER INDEX IF EXISTS idx_inventory_snapshots_sku RENAME TO idx_ocs_inventory_snapshots_sku;
ALTER INDEX IF EXISTS idx_inventory_snapshots_store RENAME TO idx_ocs_inventory_snapshots_store;
ALTER INDEX IF EXISTS idx_inventory_snapshots_date RENAME TO idx_ocs_inventory_snapshots_date;

-- Update trigger names
ALTER TRIGGER update_inventory_snapshots_updated_at_trigger ON ocs_inventory_snapshots 
    RENAME TO update_ocs_inventory_snapshots_updated_at_trigger;

-- 4. Rename inventory_transactions to ocs_inventory_transactions
ALTER TABLE inventory_transactions RENAME TO ocs_inventory_transactions;

-- Update indexes
ALTER INDEX IF EXISTS idx_inventory_transactions_sku RENAME TO idx_ocs_inventory_transactions_sku;
ALTER INDEX IF EXISTS idx_inventory_transactions_type RENAME TO idx_ocs_inventory_transactions_type;
ALTER INDEX IF EXISTS idx_inventory_transactions_timestamp RENAME TO idx_ocs_inventory_transactions_timestamp;
ALTER INDEX IF EXISTS idx_inventory_transactions_reference RENAME TO idx_ocs_inventory_transactions_reference;

-- 5. Update the view to reflect new table names
DROP VIEW IF EXISTS inventory_products_view;

CREATE OR REPLACE VIEW inventory_products_view AS
SELECT 
    -- Product catalog fields
    p.id as product_id,
    p.ocs_variant_number,
    p.ocs_item_number,  -- This is the variant relationship
    p.product_name,
    p.brand,
    p.category,
    p.sub_category,
    p.sub_sub_category,
    p.plant_type,
    p.strain_type,
    p.gtin,
    p.minimum_thc_content_percent as thc_range_min,
    p.maximum_thc_content_percent as thc_range_max,
    p.minimum_cbd_content_percent as cbd_range_min,
    p.maximum_cbd_content_percent as cbd_range_max,
    p.terpenes,
    p.unit_of_measure,
    p.size as package_size,
    p.unit_price,
    p.created_at as product_created_date,
    p.updated_at as product_modified_date,
    
    -- Inventory fields (always store-specific)
    i.id as inventory_id,
    i.sku,
    i.store_id,  -- Always NOT NULL
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.override_price,
    COALESCE(i.override_price, i.retail_price) as effective_price,
    i.reorder_point,
    i.reorder_quantity,
    i.min_stock_level,
    i.max_stock_level,
    i.location,
    i.is_available,
    i.last_restock_date,
    i.created_at as inventory_created_at,
    i.updated_at as inventory_updated_at,
    
    -- Store information (always present since store_id is NOT NULL)
    s.name as store_name,
    s.store_code as store_code,
    
    -- Calculated fields
    CASE 
        WHEN i.is_available = false THEN false
        WHEN i.quantity_available > 0 THEN true
        ELSE false
    END as in_stock,
    
    -- Stock status
    CASE 
        WHEN i.is_available = false THEN 'unavailable'
        WHEN i.quantity_available = 0 THEN 'out_of_stock'
        WHEN i.quantity_available <= COALESCE(i.reorder_point, 10) THEN 'low_stock'
        ELSE 'in_stock'
    END as stock_status
    
FROM ocs_product_catalog p
LEFT JOIN ocs_inventory i ON p.ocs_variant_number = i.sku
LEFT JOIN stores s ON i.store_id = s.id
ORDER BY p.product_name, p.ocs_variant_number;

-- Grant permissions on the updated view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Add comments for documentation
COMMENT ON TABLE ocs_inventory_movements IS 'OCS inventory movement history tracking';
COMMENT ON TABLE ocs_inventory_reservations IS 'OCS inventory reservations for orders';
COMMENT ON TABLE ocs_inventory_snapshots IS 'OCS inventory historical snapshots';
COMMENT ON TABLE ocs_inventory_transactions IS 'OCS inventory transaction records';

COMMIT;

-- Verification queries (uncomment to test after migration)
-- \dt *inventory*
-- SELECT * FROM inventory_products_view LIMIT 1;