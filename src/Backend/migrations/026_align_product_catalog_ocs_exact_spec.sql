-- Migration: Align product_catalog_ocs with exact OCS specification
-- Date: 2025-01-11
-- Description: Restructure table to match exact OCS columns plus slug, rating, rating_count

-- Step 1: Save the view definition before dropping it
CREATE OR REPLACE VIEW inventory_products_view_backup AS
SELECT * FROM inventory_products_view;

-- Step 2: Drop the dependent view
DROP VIEW IF EXISTS inventory_products_view CASCADE;

-- Step 3: Add missing OCS standard columns
ALTER TABLE product_catalog_ocs
ADD COLUMN IF NOT EXISTS product_long_description VARCHAR(1000),
ADD COLUMN IF NOT EXISTS product_short_description VARCHAR(255),
ADD COLUMN IF NOT EXISTS physical_dimension_width DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS physical_dimension_height DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS physical_dimension_depth DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS physical_dimension_volume DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS physical_dimension_weight DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS thc_content_per_volume DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS cbd_content_per_volume DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS dried_flower_cannabis_equivalency DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS growing_method VARCHAR(255),
ADD COLUMN IF NOT EXISTS number_of_items_in_retail_pack INTEGER,
ADD COLUMN IF NOT EXISTS eaches_per_inner_pack INTEGER,
ADD COLUMN IF NOT EXISTS eaches_per_master_case INTEGER,
ADD COLUMN IF NOT EXISTS storage_criteria VARCHAR(500),
ADD COLUMN IF NOT EXISTS food_allergens VARCHAR(500),
ADD COLUMN IF NOT EXISTS grow_medium VARCHAR(255),
ADD COLUMN IF NOT EXISTS carrier_oil VARCHAR(255),
ADD COLUMN IF NOT EXISTS heating_element_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS battery_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS rechargeable_battery BOOLEAN,
ADD COLUMN IF NOT EXISTS removable_battery BOOLEAN,
ADD COLUMN IF NOT EXISTS replacement_parts_available BOOLEAN,
ADD COLUMN IF NOT EXISTS temperature_control BOOLEAN,
ADD COLUMN IF NOT EXISTS temperature_display BOOLEAN,
ADD COLUMN IF NOT EXISTS compatibility VARCHAR(500),
ADD COLUMN IF NOT EXISTS thc_min DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS thc_max DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS cbd_min DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS cbd_max DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS net_weight DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS fulfilment_method VARCHAR(255),
ADD COLUMN IF NOT EXISTS delivery_tier VARCHAR(255);

-- Step 4: Copy data from existing columns with different names (if they exist)
UPDATE product_catalog_ocs
SET growing_method = COALESCE(growing_method, grow_method)
WHERE grow_method IS NOT NULL;

-- Step 5: Drop the trigger that depends on product_name column
DROP TRIGGER IF EXISTS trigger_update_product_slug ON product_catalog_ocs;

-- Step 6: Ensure all column types match specification
ALTER TABLE product_catalog_ocs
ALTER COLUMN category TYPE VARCHAR(255),
ALTER COLUMN sub_category TYPE VARCHAR(255),
ALTER COLUMN sub_sub_category TYPE VARCHAR(255),
ALTER COLUMN product_name TYPE VARCHAR(500),
ALTER COLUMN brand TYPE VARCHAR(255),
ALTER COLUMN supplier_name TYPE VARCHAR(255),
ALTER COLUMN product_short_description TYPE VARCHAR(500),
ALTER COLUMN product_long_description TYPE TEXT,
ALTER COLUMN size TYPE VARCHAR(255),
ALTER COLUMN colour TYPE VARCHAR(255),
ALTER COLUMN image_url TYPE VARCHAR(500),
ALTER COLUMN unit_of_measure TYPE VARCHAR(255),
ALTER COLUMN stock_status TYPE VARCHAR(255),
ALTER COLUMN unit_price TYPE DECIMAL(10,2),
ALTER COLUMN pack_size TYPE INTEGER,
ALTER COLUMN thc_content_per_unit TYPE DECIMAL(10,2),
ALTER COLUMN thc_content_per_volume TYPE DECIMAL(10,2),
ALTER COLUMN cbd_content_per_unit TYPE DECIMAL(10,2),
ALTER COLUMN cbd_content_per_volume TYPE DECIMAL(10,2),
ALTER COLUMN dried_flower_cannabis_equivalency TYPE DECIMAL(10,2),
ALTER COLUMN plant_type TYPE VARCHAR(255),
ALTER COLUMN terpenes TYPE TEXT,
ALTER COLUMN growing_method TYPE VARCHAR(255),
ALTER COLUMN number_of_items_in_retail_pack TYPE INTEGER,
ALTER COLUMN gtin TYPE BIGINT,
ALTER COLUMN ocs_item_number TYPE VARCHAR(255),
ALTER COLUMN ocs_variant_number TYPE VARCHAR(255),
ALTER COLUMN inventory_status TYPE VARCHAR(255),
ALTER COLUMN storage_criteria TYPE TEXT,
ALTER COLUMN food_allergens TYPE TEXT,
ALTER COLUMN ingredients TYPE TEXT,
ALTER COLUMN street_name TYPE VARCHAR(255),
ALTER COLUMN grow_medium TYPE VARCHAR(255),
ALTER COLUMN grow_method TYPE VARCHAR(255),
ALTER COLUMN grow_region TYPE VARCHAR(255),
ALTER COLUMN drying_method TYPE VARCHAR(255),
ALTER COLUMN trimming_method TYPE VARCHAR(255),
ALTER COLUMN extraction_process TYPE VARCHAR(255),
ALTER COLUMN carrier_oil TYPE VARCHAR(255),
ALTER COLUMN heating_element_type TYPE VARCHAR(255),
ALTER COLUMN battery_type TYPE VARCHAR(255),
ALTER COLUMN compatibility TYPE TEXT,
ALTER COLUMN net_weight TYPE DECIMAL(10,2),
ALTER COLUMN ontario_grown TYPE VARCHAR(255),
ALTER COLUMN craft TYPE VARCHAR(255),
ALTER COLUMN fulfilment_method TYPE VARCHAR(255),
ALTER COLUMN delivery_tier TYPE VARCHAR(255);

-- Step 7: Recreate the trigger for slug generation
CREATE OR REPLACE FUNCTION update_product_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := lower(regexp_replace(NEW.product_name, '[^a-zA-Z0-9]+', '-', 'g'));
        NEW.slug := trim(both '-' from NEW.slug);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_slug
BEFORE INSERT OR UPDATE ON product_catalog_ocs
FOR EACH ROW
EXECUTE FUNCTION update_product_slug();

-- Step 8: Recreate the inventory products view with all columns
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
    pc.thc_min,
    pc.thc_max,
    pc.cbd_min,
    pc.cbd_max,
    pc.unit_price,
    pc.product_short_description,
    pc.product_long_description,
    pc.terpenes,
    pc.image_url,
    pc.slug,
    pc.rating,
    pc.rating_count,
    pc.supplier_name,
    pc.colour,
    pc.stock_status,
    pc.pack_size,
    pc.thc_content_per_unit,
    pc.thc_content_per_volume,
    pc.cbd_content_per_unit,
    pc.cbd_content_per_volume,
    pc.dried_flower_cannabis_equivalency,
    pc.growing_method,
    pc.number_of_items_in_retail_pack,
    pc.gtin,
    pc.ocs_item_number,
    pc.ocs_variant_number,
    pc.physical_dimension_width,
    pc.physical_dimension_height,
    pc.physical_dimension_depth,
    pc.physical_dimension_volume,
    pc.physical_dimension_weight,
    pc.eaches_per_inner_pack,
    pc.eaches_per_master_case,
    pc.inventory_status,
    pc.storage_criteria,
    pc.food_allergens,
    pc.ingredients,
    pc.street_name,
    pc.grow_medium,
    pc.grow_method,
    pc.grow_region,
    pc.drying_method,
    pc.trimming_method,
    pc.extraction_process,
    pc.carrier_oil,
    pc.heating_element_type,
    pc.battery_type,
    pc.rechargeable_battery,
    pc.removable_battery,
    pc.replacement_parts_available,
    pc.temperature_control,
    pc.temperature_display,
    pc.compatibility,
    pc.net_weight,
    pc.ontario_grown,
    pc.craft,
    pc.fulfilment_method,
    pc.delivery_tier,
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

-- Step 9: Grant permissions on the view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Step 10: Drop the backup view
DROP VIEW IF EXISTS inventory_products_view_backup;

-- Step 11: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_category ON product_catalog_ocs(category);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_brand ON product_catalog_ocs(brand);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_strain_type ON product_catalog_ocs(strain_type);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_slug ON product_catalog_ocs(slug);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_sku ON product_catalog_ocs(sku);
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_rating ON product_catalog_ocs(rating DESC) WHERE rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_rating_count ON product_catalog_ocs(rating_count DESC) WHERE rating_count > 0;

-- Step 12: Update table comment
COMMENT ON TABLE product_catalog_ocs IS 'Ontario Cannabis Store product catalog with exact OCS specification columns plus slug, rating, and rating_count';

-- Column comments for documentation
COMMENT ON COLUMN product_catalog_ocs.slug IS 'URL-friendly identifier auto-generated from product name';
COMMENT ON COLUMN product_catalog_ocs.rating IS 'Average customer rating (0-5 stars)';
COMMENT ON COLUMN product_catalog_ocs.rating_count IS 'Total number of customer ratings (rating-only model, no text reviews)';
COMMENT ON COLUMN product_catalog_ocs.sku IS 'Stock Keeping Unit - unique product identifier';

-- Verification query
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'product_catalog_ocs' 
-- ORDER BY ordinal_position;