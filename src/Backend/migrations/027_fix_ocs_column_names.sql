-- Migration: Remove SKU column that was not requested
-- Date: 2025-01-11
-- Description: Remove SKU column, keep other column names as they are

-- Step 1: Drop the dependent view
DROP VIEW IF EXISTS inventory_products_view CASCADE;

-- Step 2: Drop the SKU column that was not requested
ALTER TABLE product_catalog_ocs DROP COLUMN IF EXISTS sku CASCADE;

-- Step 3: Recreate the inventory products view without SKU
CREATE OR REPLACE VIEW inventory_products_view AS
SELECT 
    pc.id as product_id,
    pc.product_name,
    pc.brand,
    pc.category,
    pc.sub_category,
    pc.sub_sub_category,
    pc.plant_type,
    pc.strain_type,
    pc.size,
    pc.unit_of_measure,
    pc.minimum_thc_content_percent,
    pc.maximum_thc_content_percent,
    pc.minimum_cbd_content_percent,
    pc.maximum_cbd_content_percent,
    pc.unit_price,
    pc.product_short_description,
    pc.product_long_description,
    pc.terpenes,
    pc.image_url,
    pc.slug,
    pc.rating,
    pc.rating_count,
    pc.supplier_name,
    pc.created_at,
    pc.updated_at,
    COALESCE(si.total_quantity, 0) as total_inventory,
    COALESCE(si.available_quantity, 0) as available_quantity
FROM product_catalog_ocs pc
LEFT JOIN (
    SELECT 
        sku,
        SUM(quantity_on_hand) as total_quantity,
        SUM(quantity_available) as available_quantity
    FROM store_inventory
    GROUP BY sku
) si ON pc.slug = si.sku;

-- Step 4: Grant permissions on the view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Step 5: Update table comment
COMMENT ON TABLE product_catalog_ocs IS 'Ontario Cannabis Store product catalog with 68 OCS columns plus slug, rating, and rating_count (70 total columns)';

-- Verification query
-- SELECT COUNT(*) as total_columns FROM information_schema.columns WHERE table_name = 'product_catalog_ocs';
-- Should return 70 columns (68 OCS + slug, rating, rating_count - no SKU)