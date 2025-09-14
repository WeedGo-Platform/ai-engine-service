-- Fix ocs_inventory unique constraint to allow same SKU across different stores
-- The constraint should be on (store_id, sku) not just (sku)

BEGIN;

-- Drop the existing unique constraint on sku only
ALTER TABLE ocs_inventory DROP CONSTRAINT IF EXISTS ocs_inventory_sku_key;

-- Add unique constraint on (store_id, sku) to allow same SKU in different stores
ALTER TABLE ocs_inventory ADD CONSTRAINT ocs_inventory_store_id_sku_key UNIQUE (store_id, sku);

-- Also ensure store_id is not null (if not already)
ALTER TABLE ocs_inventory ALTER COLUMN store_id SET NOT NULL;

COMMIT;