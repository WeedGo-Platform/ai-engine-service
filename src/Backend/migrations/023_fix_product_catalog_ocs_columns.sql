-- Migration: Fix product_catalog_ocs table to match exact specification
-- Date: 2025-01-11
-- Description: Align table with OCS data structure plus slug, rating, and review_count

-- Step 1: Drop unnecessary columns that were added
ALTER TABLE product_catalog_ocs 
DROP COLUMN IF EXISTS description,
DROP COLUMN IF EXISTS product_type,
DROP COLUMN IF EXISTS subcategory,
DROP COLUMN IF EXISTS available_sizes,
DROP COLUMN IF EXISTS in_stock,
DROP COLUMN IF EXISTS size_3_5g,
DROP COLUMN IF EXISTS size_7g,
DROP COLUMN IF EXISTS size_14g,
DROP COLUMN IF EXISTS size_28g;

-- Step 2: Ensure all required columns exist with correct names and types
-- Keep existing columns that match the specification
ALTER TABLE product_catalog_ocs 
ALTER COLUMN id TYPE UUID USING id::uuid,
ALTER COLUMN product_name TYPE VARCHAR(255),
ALTER COLUMN brand TYPE VARCHAR(255),
ALTER COLUMN supplier_name TYPE VARCHAR(255),
ALTER COLUMN category TYPE VARCHAR(255),
ALTER COLUMN sub_category TYPE VARCHAR(255),
ALTER COLUMN sub_sub_category TYPE VARCHAR(255),
ALTER COLUMN plant_type TYPE VARCHAR(255),
ALTER COLUMN strain_type TYPE VARCHAR(255),
ALTER COLUMN size TYPE VARCHAR(255),
ALTER COLUMN unit_of_measure TYPE VARCHAR(255),
ALTER COLUMN thc_max_percent TYPE DECIMAL(10,2),
ALTER COLUMN thc_min_percent TYPE DECIMAL(10,2),
ALTER COLUMN cbd_max_percent TYPE DECIMAL(10,2),
ALTER COLUMN cbd_min_percent TYPE DECIMAL(10,2),
ALTER COLUMN unit_price TYPE DECIMAL(10,2),
ALTER COLUMN short_description TYPE VARCHAR(255);

-- Step 3: Ensure the three requested columns exist
-- slug already exists from migration 021
-- sku already exists from migration 022
-- rating already exists from migration 022
-- review_count already exists from migration 022

-- Step 4: Drop any other columns not in the specification
DO $$
DECLARE
    col_name text;
BEGIN
    FOR col_name IN 
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'product_catalog_ocs' 
        AND column_name NOT IN (
            'id', 'product_name', 'brand', 'supplier_name', 'category',
            'sub_category', 'sub_sub_category', 'plant_type', 'strain_type',
            'size', 'unit_of_measure', 'thc_max_percent', 'thc_min_percent',
            'cbd_max_percent', 'cbd_min_percent', 'unit_price', 'short_description',
            'terpenes', 'image_url', 'created_at', 'updated_at',
            'slug', 'sku', 'rating', 'review_count'
        )
    LOOP
        EXECUTE format('ALTER TABLE product_catalog_ocs DROP COLUMN IF EXISTS %I', col_name);
    END LOOP;
END $$;

-- Step 5: Verify indexes exist for performance
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_category ON product_catalog_ocs(category);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_brand ON product_catalog_ocs(brand);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_strain_type ON product_catalog_ocs(strain_type);

-- Step 6: Update table comment
COMMENT ON TABLE product_catalog_ocs IS 'Ontario Cannabis Store product catalog with exact OCS data structure plus slug, rating, and review_count';

-- Verification query (run manually to check structure)
-- \d product_catalog_ocs