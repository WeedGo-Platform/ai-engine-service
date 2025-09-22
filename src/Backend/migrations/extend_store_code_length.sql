-- Migration to extend store_code column from 20 to 50 characters
-- This allows for auto-generated store codes with longer names

-- Extend the store_code column in stores table
ALTER TABLE stores
ALTER COLUMN store_code TYPE VARCHAR(50);

-- Also update any related constraints if they exist
-- Note: The unique constraint should remain unchanged as it's not dependent on length