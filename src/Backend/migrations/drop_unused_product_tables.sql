-- Migration: Drop unused product tables
-- Date: 2025-01-13
-- Description: 
--   Remove products and products_complete tables as they are not being used
--   The actual product catalog is ocs_product_catalog

BEGIN;

-- Drop the foreign key constraint from inventory_reservations first
ALTER TABLE inventory_reservations 
    DROP CONSTRAINT IF EXISTS inventory_reservations_product_id_fkey;

-- Drop the products table (CASCADE will also drop dependent objects if any)
DROP TABLE IF EXISTS products CASCADE;

-- Drop the products_complete table
DROP TABLE IF EXISTS products_complete CASCADE;

-- Clean up: Since inventory_reservations.product_id referenced products table,
-- we should either drop the column or update it to reference ocs_product_catalog
-- Since inventory_reservations is empty, let's update the schema to use SKU instead
ALTER TABLE inventory_reservations 
    DROP COLUMN IF EXISTS product_id,
    ADD COLUMN IF NOT EXISTS sku VARCHAR(100);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_inventory_reservations_sku 
    ON inventory_reservations(sku);

-- Add comment to document the change
COMMENT ON COLUMN inventory_reservations.sku IS 'SKU from ocs_product_catalog.ocs_variant_number';

COMMIT;

-- Verification queries (uncomment to test after migration)
-- \dt products
-- \dt products_complete
-- \d inventory_reservations