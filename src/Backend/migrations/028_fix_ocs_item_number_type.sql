-- Migration to fix ocs_item_number data type
-- ocs_item_number should be INTEGER (as per user requirement)
-- ocs_variant_number remains VARCHAR (string)

-- Change ocs_item_number from VARCHAR to INTEGER
ALTER TABLE product_catalog_ocs 
ALTER COLUMN ocs_item_number TYPE INTEGER USING ocs_item_number::INTEGER;