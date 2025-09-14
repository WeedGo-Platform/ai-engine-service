-- Migration: Fix inventory_products_view to use INNER JOIN
-- Only show products that have actual inventory records
-- Join on ocs_inventory.sku = ocs_product_catalog.ocs_variant_number

BEGIN;

DROP VIEW IF EXISTS inventory_products_view;

CREATE OR REPLACE VIEW inventory_products_view AS
SELECT
    -- Product catalog fields
    p.id as product_id,
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

FROM ocs_inventory i
INNER JOIN ocs_product_catalog p ON i.sku = p.ocs_variant_number
ORDER BY p.product_name, p.ocs_variant_number;

-- Grant permissions on the view
GRANT SELECT ON inventory_products_view TO PUBLIC;

-- Add comments for documentation
COMMENT ON VIEW inventory_products_view IS 'View showing only products with inventory records. Inner join on sku = ocs_variant_number';

COMMIT;