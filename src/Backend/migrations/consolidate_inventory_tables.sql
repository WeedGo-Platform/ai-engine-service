-- Migration: Consolidate store_inventory into ocs_inventory
-- Date: 2025-01-13
-- Description: 
--   1. Add store-specific columns from store_inventory to ocs_inventory
--   2. Drop the empty store_inventory table
--   3. Update inventory_products_view to include store columns
--   Note: store_inventory is empty, so no data migration needed

BEGIN;

-- 1. Add store-specific columns to ocs_inventory if they don't exist
ALTER TABLE ocs_inventory 
    ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS min_stock_level INTEGER DEFAULT 10,
    ADD COLUMN IF NOT EXISTS max_stock_level INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS override_price NUMERIC(10,2);

-- 2. Create indexes for store-specific queries
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_store ON ocs_inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_available ON ocs_inventory(is_available);

-- 3. Add unique constraint for store + sku combination if it doesn't exist
-- Note: This allows same SKU across different stores
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'ocs_inventory_store_sku_unique'
    ) THEN
        ALTER TABLE ocs_inventory 
            ADD CONSTRAINT ocs_inventory_store_sku_unique 
            UNIQUE(store_id, sku);
    END IF;
END $$;

-- 4. Drop the store_inventory table and its dependencies
DROP TABLE IF EXISTS store_inventory CASCADE;

-- 5. Recreate inventory_products_view to include store columns
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
    
    -- Inventory fields
    i.id as inventory_id,
    i.sku,
    i.store_id,  -- NEW: Store association
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.override_price,  -- NEW: Store-specific price override
    COALESCE(i.override_price, i.retail_price) as effective_price,  -- NEW: Calculated field
    i.reorder_point,
    i.reorder_quantity,
    i.min_stock_level,  -- NEW: Store-specific min stock
    i.max_stock_level,  -- NEW: Store-specific max stock
    i.location,
    i.is_available,  -- NEW: Store-specific availability
    i.last_restock_date,
    i.created_at as inventory_created_at,
    i.updated_at as inventory_updated_at,
    
    -- Store information (if associated)
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
COMMENT ON VIEW inventory_products_view IS 'Unified view joining OCS product catalog with inventory data, now including store-specific inventory tracking';
COMMENT ON COLUMN inventory_products_view.store_id IS 'Store ID for store-specific inventory (NULL for provincial/warehouse inventory)';
COMMENT ON COLUMN inventory_products_view.override_price IS 'Store-specific price override';
COMMENT ON COLUMN inventory_products_view.effective_price IS 'Calculated price: override_price if set, otherwise retail_price';
COMMENT ON COLUMN inventory_products_view.is_available IS 'Store-specific availability flag';

-- Add comments to ocs_inventory columns
COMMENT ON COLUMN ocs_inventory.store_id IS 'Optional store ID for store-specific inventory. NULL indicates provincial/warehouse inventory';
COMMENT ON COLUMN ocs_inventory.override_price IS 'Store-specific price override. NULL uses default retail_price';
COMMENT ON COLUMN ocs_inventory.is_available IS 'Availability flag. Can be false even if quantity > 0';
COMMENT ON COLUMN ocs_inventory.min_stock_level IS 'Minimum stock level for reordering alerts';
COMMENT ON COLUMN ocs_inventory.max_stock_level IS 'Maximum stock level for inventory planning';

COMMIT;

-- Verification queries (uncomment to test after migration)
-- SELECT COUNT(*) FROM ocs_inventory WHERE store_id IS NOT NULL;
-- SELECT * FROM inventory_products_view WHERE store_id IS NOT NULL LIMIT 5;
-- \d ocs_inventory
-- \dv inventory_products_view