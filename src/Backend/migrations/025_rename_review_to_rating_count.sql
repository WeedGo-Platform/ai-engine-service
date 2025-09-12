-- Migration: Rename review_count to rating_count for consistency
-- Date: 2025-01-11
-- Description: Since we're using a rating-only model (no text reviews), 
--              rename review_count to rating_count for clarity and consistency

-- Step 1: Rename the column from review_count to rating_count
ALTER TABLE product_catalog_ocs 
RENAME COLUMN review_count TO rating_count;

-- Step 2: Update the check constraint name for consistency
ALTER TABLE product_catalog_ocs 
DROP CONSTRAINT IF EXISTS product_catalog_ocs_review_count_check;

ALTER TABLE product_catalog_ocs 
ADD CONSTRAINT product_catalog_ocs_rating_count_check 
CHECK (rating_count >= 0);

-- Step 3: Rename the index for consistency
DROP INDEX IF EXISTS idx_product_catalog_ocs_review_count;

CREATE INDEX idx_product_catalog_ocs_rating_count 
ON product_catalog_ocs(rating_count DESC) 
WHERE rating_count > 0;

-- Step 4: Update column comment
COMMENT ON COLUMN product_catalog_ocs.rating_count IS 'Total number of customer ratings (rating-only model, no text reviews)';
COMMENT ON COLUMN product_catalog_ocs.rating IS 'Average customer rating (0-5 stars)';

-- Step 5: Update table comment to reflect rating-only model
COMMENT ON TABLE product_catalog_ocs IS 'Ontario Cannabis Store product catalog with rating-only feedback model (no text reviews)';

-- Verification query
-- SELECT product_name, rating, rating_count FROM product_catalog_ocs LIMIT 5;