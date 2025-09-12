-- Migration: Clean up product_catalog_ocs to match exact OCS specification
-- Date: 2025-01-11
-- Description: Remove extra columns, keeping only OCS standard columns + slug, sku, rating, review_count

-- Step 1: Save the view definition before dropping it
CREATE OR REPLACE VIEW inventory_products_view_backup AS
SELECT * FROM inventory_products_view;

-- Step 2: Drop the dependent view
DROP VIEW IF EXISTS inventory_products_view CASCADE;

-- Step 3: Drop extra columns that are not in the OCS standard
ALTER TABLE product_catalog_ocs
DROP COLUMN IF EXISTS long_description CASCADE,
DROP COLUMN IF EXISTS pack_size CASCADE,
DROP COLUMN IF EXISTS thc_content_per_unit CASCADE,
DROP COLUMN IF EXISTS cbd_content_per_unit CASCADE,
DROP COLUMN IF EXISTS ocs_variant_number CASCADE,
DROP COLUMN IF EXISTS description CASCADE,
DROP COLUMN IF EXISTS product_type CASCADE,
DROP COLUMN IF EXISTS subcategory CASCADE,
DROP COLUMN IF EXISTS available_sizes CASCADE,
DROP COLUMN IF EXISTS in_stock CASCADE,
DROP COLUMN IF EXISTS size_3_5g CASCADE,
DROP COLUMN IF EXISTS size_7g CASCADE,
DROP COLUMN IF EXISTS size_14g CASCADE,
DROP COLUMN IF EXISTS size_28g CASCADE;

-- Step 4: Recreate the inventory products view with available columns
CREATE OR REPLACE VIEW inventory_products_view AS
SELECT 
    pc.id as product_id,
    pc.sku,
    pc.product_name,
    pc.brand,
    pc.category,
    pc.sub_category,
    pc.sub_sub_category,
    pc.plant_type,
    pc.strain_type,
    pc.size,
    pc.unit_of_measure,
    pc.thc_min_percent,
    pc.thc_max_percent,
    pc.cbd_min_percent,
    pc.cbd_max_percent,
    pc.unit_price,
    pc.short_description,
    pc.terpenes,
    pc.image_url,
    pc.slug,
    pc.rating,
    pc.review_count,
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
) si ON pc.sku = si.sku;

-- Step 5: Grant permissions on the view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Step 6: Drop the backup view
DROP VIEW IF EXISTS inventory_products_view_backup;

-- Step 7: Verify final structure
COMMENT ON TABLE product_catalog_ocs IS 'OCS product catalog with exact columns: id, product_name, brand, supplier_name, category, sub_category, sub_sub_category, plant_type, strain_type, size, unit_of_measure, thc_max_percent, thc_min_percent, cbd_max_percent, cbd_min_percent, unit_price, short_description, terpenes, image_url, created_at, updated_at, slug, sku, rating, review_count';

-- Verification (run manually):
-- \d product_catalog_ocs
-- Should show exactly 24 columns: 
-- Original OCS: id, product_name, brand, supplier_name, category, sub_category, sub_sub_category, 
--               plant_type, strain_type, size, unit_of_measure, thc_max_percent, thc_min_percent, 
--               cbd_max_percent, cbd_min_percent, unit_price, short_description
-- Keep existing: terpenes, image_url, created_at, updated_at
-- Your requested: slug, sku, rating, review_count