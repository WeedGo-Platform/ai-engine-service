-- ============================================================================
-- Complete Migration: inventory_products_view and Dependencies
-- Source: ai-engine-db (legacy) -> ai-engine-db-postgis (current)
-- ============================================================================

-- Step 1: Create trigger functions
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_inventory_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.update_product_catalog_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$;

-- Step 2: Drop existing triggers if they exist (to avoid conflicts)
-- ============================================================================

DROP TRIGGER IF EXISTS update_ocs_inventory_timestamp_trigger ON ocs_inventory;
DROP TRIGGER IF EXISTS trigger_update_ocs_product_catalog_updated_at ON ocs_product_catalog;

-- Step 3: Create triggers
-- ============================================================================

CREATE TRIGGER update_ocs_inventory_timestamp_trigger
    BEFORE UPDATE ON public.ocs_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_timestamp();

CREATE TRIGGER trigger_update_ocs_product_catalog_updated_at
    BEFORE UPDATE ON public.ocs_product_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_product_catalog_updated_at();

-- Step 4: Create missing indexes (only create if they don't exist)
-- ============================================================================

-- ocs_product_catalog indexes
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_rating_count 
    ON public.ocs_product_catalog USING btree (rating_count DESC) 
    WHERE (rating_count > 0);

CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_slug 
    ON public.ocs_product_catalog USING btree (slug);

CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_strain_type 
    ON public.ocs_product_catalog USING btree (strain_type);

CREATE INDEX IF NOT EXISTS idx_products_name 
    ON public.ocs_product_catalog USING btree (product_name);

CREATE INDEX IF NOT EXISTS idx_products_plant_type 
    ON public.ocs_product_catalog USING btree (plant_type);

CREATE INDEX IF NOT EXISTS idx_products_price 
    ON public.ocs_product_catalog USING btree (unit_price);

CREATE INDEX IF NOT EXISTS idx_products_subcategory 
    ON public.ocs_product_catalog USING btree (sub_category);

-- ocs_inventory indexes
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_each_gtin 
    ON public.ocs_inventory USING btree (each_gtin);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_quantity 
    ON public.ocs_inventory USING btree (quantity_available);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_store 
    ON public.ocs_inventory USING btree (store_id);

CREATE INDEX IF NOT EXISTS idx_ocs_inventory_supplier 
    ON public.ocs_inventory USING btree (supplier);

-- Step 5: Create the inventory_products_view
-- ============================================================================

CREATE OR REPLACE VIEW inventory_products_view AS
SELECT
    p.id AS product_id,
    p.product_name,
    p.brand,
    p.supplier_name,
    p.category,
    p.sub_category,
    p.sub_sub_category,
    p.plant_type,
    p.strain_type,
    p.size,
    p.unit_of_measure,
    p.unit_price,
    p.image_url,
    p.street_name,
    p.terpenes,
    p.ocs_item_number,
    p.ocs_variant_number,
    p.gtin,
    p.colour,
    p.pack_size,
    p.thc_content_per_unit,
    p.cbd_content_per_unit,
    p.stock_status AS catalog_stock_status,
    p.inventory_status,
    p.ingredients,
    p.grow_method,
    p.grow_region,
    p.drying_method,
    p.trimming_method,
    p.extraction_process,
    p.ontario_grown,
    p.craft,
    p.created_at AS product_created_at,
    p.updated_at AS product_updated_at,
    p.rating,
    p.rating_count,
    p.product_long_description,
    p.product_short_description,
    p.physical_dimension_width,
    p.physical_dimension_height,
    p.physical_dimension_depth,
    p.physical_dimension_volume,
    p.physical_dimension_weight,
    p.thc_content_per_volume,
    p.cbd_content_per_volume,
    p.dried_flower_cannabis_equivalency,
    p.growing_method,
    p.number_of_items_in_retail_pack,
    p.eaches_per_inner_pack,
    p.eaches_per_master_case,
    p.storage_criteria,
    p.food_allergens,
    p.grow_medium,
    p.carrier_oil,
    p.heating_element_type,
    p.battery_type,
    p.rechargeable_battery,
    p.removable_battery,
    p.replacement_parts_available,
    p.temperature_control,
    p.temperature_display,
    p.compatibility,
    p.minimum_thc_content_percent,
    p.maximum_thc_content_percent,
    p.minimum_cbd_content_percent,
    p.maximum_cbd_content_percent,
    p.net_weight,
    p.fulfilment_method,
    p.delivery_tier,
    p.slug,
    i.id AS inventory_id,
    i.sku,
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.reorder_point,
    i.reorder_quantity,
    i.last_restock_date,
    i.created_at AS inventory_created_at,
    i.updated_at AS inventory_updated_at,
    i.store_id,
    i.min_stock_level,
    i.max_stock_level,
    i.is_available,
    i.override_price,
    CASE
        WHEN i.quantity_available > 0 THEN true
        ELSE false
    END AS in_stock,
    CASE
        WHEN i.quantity_available > 10 THEN 'in_stock'::text
        WHEN i.quantity_available > 0 THEN 'low_stock'::text
        ELSE 'out_of_stock'::text
    END AS stock_status,
    COALESCE(i.retail_price, p.unit_price) AS effective_price,
    p.minimum_thc_content_percent AS thc_range_min,
    p.maximum_thc_content_percent AS thc_range_max,
    p.minimum_cbd_content_percent AS cbd_range_min,
    p.maximum_cbd_content_percent AS cbd_range_max,
    p.pack_size AS package_size,
    p.created_at AS product_created_date,
    p.updated_at AS product_modified_date
FROM ocs_product_catalog p
LEFT JOIN ocs_inventory i ON lower(TRIM(BOTH FROM i.sku)) = lower(TRIM(BOTH FROM p.ocs_variant_number));

-- Step 6: Grant permissions
-- ============================================================================

GRANT SELECT ON inventory_products_view TO weedgo;

-- Step 7: Verify the view was created successfully
-- ============================================================================

SELECT 
    'inventory_products_view migration completed successfully' AS status,
    COUNT(*) as total_products
FROM inventory_products_view;
