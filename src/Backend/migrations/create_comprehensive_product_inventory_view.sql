-- Create comprehensive view with ALL columns from both ocs_product_catalog and ocs_inventory
-- This view will be used for detailed product information display in the POS system

DROP VIEW IF EXISTS comprehensive_product_inventory_view CASCADE;

CREATE VIEW comprehensive_product_inventory_view AS
SELECT
    -- Product Catalog fields (all 70 columns)
    p.id as product_id,
    p.product_name,
    p.brand,
    p.supplier_name,
    p.category,
    p.sub_category,
    p.sub_sub_category,
    p.plant_type,
    p.strain_type,
    p.size as product_size,
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
    p.stock_status as catalog_stock_status,
    p.inventory_status,
    p.ingredients,
    p.grow_method,
    p.grow_region,
    p.drying_method,
    p.trimming_method,
    p.extraction_process,
    p.ontario_grown,
    p.craft,
    p.created_at as product_created_at,
    p.updated_at as product_updated_at,
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

    -- Inventory fields (all 17 columns)
    i.id as inventory_id,
    i.sku,
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.unit_cost,
    i.retail_price,
    i.reorder_point,
    i.reorder_quantity,
    i.last_restock_date,
    i.created_at as inventory_created_at,
    i.updated_at as inventory_updated_at,
    i.store_id,
    i.min_stock_level,
    i.max_stock_level,
    i.is_available,
    i.override_price,

    -- Computed fields for convenience
    CASE
        WHEN i.quantity_available > 0 THEN true
        ELSE false
    END as in_stock,

    CASE
        WHEN i.quantity_available > 10 THEN 'in_stock'
        WHEN i.quantity_available > 0 THEN 'low_stock'
        ELSE 'out_of_stock'
    END as stock_status,

    COALESCE(i.retail_price, p.unit_price) as effective_price,

    -- THC/CBD ranges for easier display
    COALESCE(p.minimum_thc_content_percent, 0) as thc_min,
    COALESCE(p.maximum_thc_content_percent, 0) as thc_max,
    COALESCE(p.minimum_cbd_content_percent, 0) as cbd_min,
    COALESCE(p.maximum_cbd_content_percent, 0) as cbd_max

FROM ocs_product_catalog p
LEFT JOIN ocs_inventory i ON LOWER(TRIM(i.sku)) = LOWER(TRIM(p.ocs_variant_number));

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_ocs_inventory_sku_lower ON ocs_inventory(LOWER(TRIM(sku)));
CREATE INDEX IF NOT EXISTS idx_ocs_product_catalog_variant_lower ON ocs_product_catalog(LOWER(TRIM(ocs_variant_number)));

-- Grant permissions
GRANT SELECT ON comprehensive_product_inventory_view TO PUBLIC;

COMMENT ON VIEW comprehensive_product_inventory_view IS 'Comprehensive view containing ALL columns from both ocs_product_catalog and ocs_inventory tables for detailed product information display';