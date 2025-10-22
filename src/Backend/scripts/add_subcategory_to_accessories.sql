-- Add subcategory field to accessories_catalog table

ALTER TABLE accessories_catalog 
ADD COLUMN IF NOT EXISTS subcategory VARCHAR(100);

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_accessories_subcategory ON accessories_catalog(subcategory);

-- Comment for documentation
COMMENT ON COLUMN accessories_catalog.subcategory IS 'Subcategory for more granular product classification within main category';
