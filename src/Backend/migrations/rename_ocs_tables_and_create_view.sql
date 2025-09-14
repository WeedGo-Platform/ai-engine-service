-- Migration: Rename tables and create inventory_products_view
-- Date: 2025-01-13
-- Description: 
--   1. Rename product_catalog_ocs to ocs_product_catalog
--   2. Rename inventory to ocs_inventory
--   3. Update all dependencies (foreign keys, triggers, etc.)
--   4. Create inventory_products_view joining the renamed tables
--   Note: ocs_item_number represents the variant relationship

BEGIN;

-- 1. Drop the foreign key constraint that references product_catalog_ocs
ALTER TABLE IF EXISTS store_inventory 
    DROP CONSTRAINT IF EXISTS fk_store_inventory_sku;

-- 2. Rename product_catalog_ocs to ocs_product_catalog
ALTER TABLE IF EXISTS product_catalog_ocs RENAME TO ocs_product_catalog;

-- Update indexes for ocs_product_catalog
ALTER INDEX IF EXISTS product_catalog_ocs_pkey RENAME TO ocs_product_catalog_pkey;
ALTER INDEX IF EXISTS idx_product_catalog_ocs_sku RENAME TO idx_ocs_product_catalog_sku;
ALTER INDEX IF EXISTS idx_product_catalog_ocs_variant RENAME TO idx_ocs_product_catalog_variant;
ALTER INDEX IF EXISTS idx_product_catalog_product_name RENAME TO idx_ocs_product_catalog_product_name;
ALTER INDEX IF EXISTS idx_product_catalog_brand RENAME TO idx_ocs_product_catalog_brand;

-- 3. Rename inventory to ocs_inventory
ALTER TABLE IF EXISTS inventory RENAME TO ocs_inventory;

-- Update indexes for ocs_inventory
ALTER INDEX IF EXISTS inventory_pkey RENAME TO ocs_inventory_pkey;
ALTER INDEX IF EXISTS idx_inventory_quantity RENAME TO idx_ocs_inventory_quantity;
ALTER INDEX IF EXISTS idx_inventory_sku RENAME TO idx_ocs_inventory_sku;
ALTER INDEX IF EXISTS inventory_sku_key RENAME TO ocs_inventory_sku_key;

-- Update constraint names for ocs_inventory
ALTER TABLE ocs_inventory RENAME CONSTRAINT inventory_quantity_available_check TO ocs_inventory_quantity_available_check;
ALTER TABLE ocs_inventory RENAME CONSTRAINT inventory_quantity_on_hand_check TO ocs_inventory_quantity_on_hand_check;
ALTER TABLE ocs_inventory RENAME CONSTRAINT inventory_quantity_reserved_check TO ocs_inventory_quantity_reserved_check;

-- 4. Re-create the foreign key constraint with the new table name
ALTER TABLE store_inventory 
    ADD CONSTRAINT fk_store_inventory_sku 
    FOREIGN KEY (sku) 
    REFERENCES ocs_product_catalog(ocs_variant_number);

-- 5. Update trigger names (triggers automatically follow the renamed tables)
-- But we should update their names for consistency
ALTER TRIGGER update_inventory_timestamp_trigger ON ocs_inventory 
    RENAME TO update_ocs_inventory_timestamp_trigger;

ALTER TRIGGER trigger_update_product_catalog_updated_at ON ocs_product_catalog 
    RENAME TO trigger_update_ocs_product_catalog_updated_at;

-- 6. Create inventory_products_view
-- This view joins ocs_product_catalog and ocs_inventory on ocs_variant_number = sku
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
    
    -- Inventory fields
    i.id as inventory_id,
    i.sku,
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.reorder_point,
    i.reorder_quantity,
    i.location,
    i.last_restock_date,
    i.created_at as inventory_created_at,
    i.updated_at as inventory_updated_at,
    
    -- Calculated fields
    CASE 
        WHEN i.quantity_available > 0 THEN true
        ELSE false
    END as in_stock,
    
    -- Stock status
    CASE 
        WHEN i.quantity_available = 0 THEN 'out_of_stock'
        WHEN i.quantity_available <= i.reorder_point THEN 'low_stock'
        ELSE 'in_stock'
    END as stock_status
    
FROM ocs_product_catalog p
LEFT JOIN ocs_inventory i ON p.ocs_variant_number = i.sku
ORDER BY p.product_name, p.ocs_variant_number;

-- Grant permissions on the view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Add comments for documentation
COMMENT ON VIEW inventory_products_view IS 'Unified view joining OCS product catalog with inventory data. Joins on ocs_variant_number = sku';
COMMENT ON COLUMN inventory_products_view.ocs_item_number IS 'The variant relationship identifier from OCS';
COMMENT ON COLUMN inventory_products_view.stock_status IS 'Current stock status: in_stock, low_stock, or out_of_stock';

COMMIT;

-- Verification queries (uncomment to test after migration)
-- SELECT COUNT(*) FROM ocs_product_catalog;
-- SELECT COUNT(*) FROM ocs_inventory;
-- SELECT COUNT(*) FROM inventory_products_view;
-- SELECT * FROM inventory_products_view LIMIT 5;