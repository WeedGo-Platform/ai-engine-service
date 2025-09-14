-- Migration: Expand GTIN columns in batch_tracking table
-- Issue: GTINBarCode values from Excel can be longer than 14 characters
-- Solution: Expand columns from VARCHAR(14) to VARCHAR(100) to match purchase_order_items table

ALTER TABLE batch_tracking
    ALTER COLUMN case_gtin TYPE VARCHAR(100),
    ALTER COLUMN gtin_barcode TYPE VARCHAR(100),
    ALTER COLUMN each_gtin TYPE VARCHAR(100);

-- Verify the changes
-- SELECT column_name, data_type, character_maximum_length
-- FROM information_schema.columns
-- WHERE table_name = 'batch_tracking'
-- AND column_name LIKE '%gtin%';