-- Migration to update provincial_suppliers table to use provinces_territories_id instead of province_code
-- Date: 2025-01-19

-- Step 1: Add provinces_territories_id column to provincial_suppliers
ALTER TABLE provincial_suppliers
ADD COLUMN provinces_territories_id UUID;

-- Step 2: Add foreign key constraint to the new column
ALTER TABLE provincial_suppliers
ADD CONSTRAINT fk_provincial_supplier_province_territory
FOREIGN KEY (provinces_territories_id)
REFERENCES provinces_territories(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- Step 3: Update provinces_territories_id based on existing province_code values
UPDATE provincial_suppliers ps
SET provinces_territories_id = pt.id
FROM provinces_territories pt
WHERE ps.province_code = pt.code
AND ps.province_code IS NOT NULL;

-- Step 4: Drop the unique constraint that depends on province_code
ALTER TABLE provincial_suppliers
DROP CONSTRAINT IF EXISTS unique_province_supplier;

-- Step 5: Create a new unique partial index for provincial suppliers
CREATE UNIQUE INDEX unique_province_territory_supplier
ON provincial_suppliers(provinces_territories_id)
WHERE provinces_territories_id IS NOT NULL AND is_provincial_supplier = true;

-- Step 6: Create index on the new column
CREATE INDEX idx_provincial_suppliers_province_territory
ON provincial_suppliers(provinces_territories_id);

-- Step 7: Drop the foreign key constraint on province_code
ALTER TABLE provincial_suppliers
DROP CONSTRAINT IF EXISTS fk_provincial_supplier_province;

-- Step 8: Drop the old index on province_code
DROP INDEX IF EXISTS idx_provincial_suppliers_province;

-- Step 9: Drop the province_code column
ALTER TABLE provincial_suppliers
DROP COLUMN province_code;

-- Step 10: Add comment to the table
COMMENT ON COLUMN provincial_suppliers.provinces_territories_id IS 'Reference to the province or territory this supplier serves';