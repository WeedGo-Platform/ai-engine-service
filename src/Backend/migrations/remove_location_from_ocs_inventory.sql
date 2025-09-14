-- Migration: Remove legacy location field from ocs_inventory
-- Date: 2025-01-13
-- Description: Remove the legacy location field from ocs_inventory table as locations
--              are now tracked via shelf_locations and inventory_locations tables

BEGIN;

-- Drop the inventory_products_view that depends on the location column
DROP VIEW IF EXISTS inventory_products_view;

-- Drop the location column from ocs_inventory
ALTER TABLE ocs_inventory
DROP COLUMN IF EXISTS location;

-- Recreate the inventory_products_view without the location field
CREATE OR REPLACE VIEW inventory_products_view AS
SELECT
    p.id AS product_id,
    p.ocs_variant_number,
    p.ocs_item_number,
    p.product_name,
    p.brand,
    p.category,
    p.sub_category,
    p.sub_sub_category,
    p.plant_type,
    p.strain_type,
    p.gtin,
    p.minimum_thc_content_percent AS thc_range_min,
    p.maximum_thc_content_percent AS thc_range_max,
    p.minimum_cbd_content_percent AS cbd_range_min,
    p.maximum_cbd_content_percent AS cbd_range_max,
    p.terpenes,
    p.unit_of_measure,
    p.size AS package_size,
    p.unit_price,
    p.created_at AS product_created_date,
    p.updated_at AS product_modified_date,
    i.id AS inventory_id,
    i.sku,
    i.store_id,
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.override_price,
    COALESCE(i.override_price, i.retail_price) AS effective_price,
    i.reorder_point,
    i.reorder_quantity,
    i.min_stock_level,
    i.max_stock_level,
    -- Location is now handled via shelf_locations and inventory_locations tables
    -- Removed: i.location,
    i.is_available,
    i.last_restock_date,
    i.created_at AS inventory_created_at,
    i.updated_at AS inventory_updated_at,
    s.name AS store_name,
    s.store_code,
    CASE
        WHEN i.is_available = false THEN false
        WHEN i.quantity_available > 0 THEN true
        ELSE false
    END AS in_stock,
    CASE
        WHEN i.is_available = false THEN 'unavailable'::text
        WHEN i.quantity_available = 0 THEN 'out_of_stock'::text
        WHEN i.quantity_available <= COALESCE(i.reorder_point, 10) THEN 'low_stock'::text
        ELSE 'in_stock'::text
    END AS stock_status
FROM ocs_product_catalog p
LEFT JOIN ocs_inventory i ON p.ocs_variant_number::text = i.sku::text
LEFT JOIN stores s ON i.store_id = s.id
ORDER BY p.product_name, p.ocs_variant_number;

-- Add comment to document the change
COMMENT ON VIEW inventory_products_view IS 'Product catalog joined with inventory - location tracking moved to shelf_locations table';

COMMIT;

-- Verification queries
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'ocs_inventory' AND column_name = 'location';
-- Should return 0 rows after migration