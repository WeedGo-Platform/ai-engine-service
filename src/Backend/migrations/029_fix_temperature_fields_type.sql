-- Fix temperature_control and temperature_display field types
-- These are not boolean fields but contain values like 'Variable', 'Fixed', 'LED', etc.

ALTER TABLE product_catalog_ocs 
ALTER COLUMN temperature_control TYPE VARCHAR(100);

ALTER TABLE product_catalog_ocs 
ALTER COLUMN temperature_display TYPE VARCHAR(100);