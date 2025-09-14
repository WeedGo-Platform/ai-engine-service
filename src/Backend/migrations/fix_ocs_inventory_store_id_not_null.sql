-- Migration: Fix ocs_inventory store_id to be NOT NULL
-- Date: 2025-01-13
-- Description: 
--   Make store_id NOT NULL since all inventory must be associated with a store
--   Remove the concept of provincial/warehouse inventory (store_id = NULL)

BEGIN;

-- 1. First drop the unique constraint that allows NULL store_id
ALTER TABLE ocs_inventory 
    DROP CONSTRAINT IF EXISTS ocs_inventory_store_sku_unique;

-- 2. Make store_id NOT NULL
ALTER TABLE ocs_inventory 
    ALTER COLUMN store_id SET NOT NULL;

-- 3. Re-add the unique constraint with NOT NULL store_id
ALTER TABLE ocs_inventory 
    ADD CONSTRAINT ocs_inventory_store_sku_unique 
    UNIQUE(store_id, sku);

-- 4. Update the view to reflect that store_id is always present
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

-- Update comments to reflect that store_id is always required
COMMENT ON VIEW inventory_products_view IS 'Unified view joining OCS product catalog with store-specific inventory data';
COMMENT ON COLUMN ocs_inventory.store_id IS 'Required store ID for store-specific inventory. Every inventory record must belong to a store';
COMMENT ON COLUMN inventory_products_view.store_id IS 'Store ID for inventory (always present, NOT NULL)';

COMMIT;

-- Verification queries (uncomment to test after migration)
-- \d ocs_inventory
-- SELECT * FROM inventory_products_view LIMIT 5;