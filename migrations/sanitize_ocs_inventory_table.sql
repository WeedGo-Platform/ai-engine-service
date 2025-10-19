-- Migration: Sanitize ocs_inventory table by removing redundant columns
-- Date: 2025-10-18
-- Description: Remove product-related columns that should only exist in products table
-- These columns create data redundancy and synchronization issues

BEGIN;

-- Drop indexes for columns we're about to remove
DROP INDEX IF EXISTS idx_ocs_inventory_batch_lot;
DROP INDEX IF EXISTS idx_ocs_inventory_case_gtin;
DROP INDEX IF EXISTS idx_ocs_inventory_each_gtin;
DROP INDEX IF EXISTS idx_ocs_inventory_gtin_barcode;
DROP INDEX IF EXISTS idx_ocs_inventory_supplier;

-- Remove product-related columns (should be in products table)
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS strain_type;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS product_name;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS shipment_id;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS packaged_on_date;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS category;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS gtin_barcode;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS max_stock_level;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS container_id;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS supplier;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS plant_type;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS cbd_content;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS batch_lot;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS each_gtin;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS brand;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS thc_content;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS case_gtin;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS subcategory;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS vendor;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS image_url;

-- Remove duplicate quantity columns (keeping only quantity_on_hand and quantity_reserved)
-- Note: available_quantity is a generated column, so we need to drop it first
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS available_quantity;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS quantity;
ALTER TABLE ocs_inventory DROP COLUMN IF EXISTS reserved_quantity;

-- Rename quantity_reserved to match our fixed naming convention
ALTER TABLE ocs_inventory RENAME COLUMN quantity_reserved TO quantity_reserved;

-- Add comment to table documenting the cleanup
COMMENT ON TABLE ocs_inventory IS 'Inventory tracking table - cleaned 2025-10-18. Product attributes moved to products table. Only inventory-specific columns remain.';

-- Verify final structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ocs_inventory'
ORDER BY ordinal_position;

COMMIT;

-- Expected remaining columns after cleanup:
-- id, store_id, sku
-- quantity_on_hand, quantity_reserved, quantity_available
-- reorder_point, reorder_quantity
-- location_code, last_received, last_sold
-- created_at, updated_at
-- is_available, retail_price, retail_price_dynamic, override_price, unit_cost
-- min_stock_level, last_restock_date
