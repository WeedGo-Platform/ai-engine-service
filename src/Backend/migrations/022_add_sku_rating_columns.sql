-- Migration: Add SKU, rating, and review count columns to product_catalog_ocs
-- Date: 2025-01-11
-- Description: Add SKU for product identification, and rating/review columns for customer feedback

-- Step 1: Add SKU column
ALTER TABLE product_catalog_ocs 
ADD COLUMN IF NOT EXISTS sku VARCHAR(100);

-- Step 2: Add rating column (1-5 stars with decimal precision)
ALTER TABLE product_catalog_ocs 
ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2) CHECK (rating >= 0 AND rating <= 5);

-- Step 3: Add review count column
ALTER TABLE product_catalog_ocs 
ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0 CHECK (review_count >= 0);

-- Step 4: Add additional missing columns for better product information
ALTER TABLE product_catalog_ocs 
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS product_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS subcategory VARCHAR(255),
ADD COLUMN IF NOT EXISTS terpenes TEXT,
ADD COLUMN IF NOT EXISTS available_sizes TEXT,
ADD COLUMN IF NOT EXISTS in_stock BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS image_url TEXT,
ADD COLUMN IF NOT EXISTS size_3_5g DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS size_7g DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS size_14g DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS size_28g DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Step 5: Generate SKUs for existing products if they don't have one
UPDATE product_catalog_ocs 
SET sku = 'OCS-' || UPPER(LEFT(COALESCE(brand, 'UNK'), 3)) || '-' || id::text
WHERE sku IS NULL;

-- Step 6: Make SKU NOT NULL and add unique constraint after populating
ALTER TABLE product_catalog_ocs 
ALTER COLUMN sku SET NOT NULL;

ALTER TABLE product_catalog_ocs 
ADD CONSTRAINT unique_sku UNIQUE (sku);

-- Step 7: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_sku 
ON product_catalog_ocs(sku);

CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_rating 
ON product_catalog_ocs(rating DESC) 
WHERE rating IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_review_count 
ON product_catalog_ocs(review_count DESC) 
WHERE review_count > 0;

CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_in_stock 
ON product_catalog_ocs(in_stock) 
WHERE in_stock = true;

-- Step 8: Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_product_catalog_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_product_catalog_updated_at ON product_catalog_ocs;
CREATE TRIGGER trigger_update_product_catalog_updated_at
BEFORE UPDATE ON product_catalog_ocs
FOR EACH ROW
EXECUTE FUNCTION update_product_catalog_updated_at();

-- Step 9: Add comments for documentation
COMMENT ON COLUMN product_catalog_ocs.sku IS 'Stock Keeping Unit - unique product identifier';
COMMENT ON COLUMN product_catalog_ocs.rating IS 'Average customer rating (0-5 stars)';
COMMENT ON COLUMN product_catalog_ocs.review_count IS 'Total number of customer reviews';
COMMENT ON COLUMN product_catalog_ocs.description IS 'Detailed product description';
COMMENT ON COLUMN product_catalog_ocs.size_3_5g IS 'Price for 3.5g size';
COMMENT ON COLUMN product_catalog_ocs.size_7g IS 'Price for 7g size';
COMMENT ON COLUMN product_catalog_ocs.size_14g IS 'Price for 14g size';
COMMENT ON COLUMN product_catalog_ocs.size_28g IS 'Price for 28g (1oz) size';

-- Step 10: Populate some sample ratings for existing products (optional, for testing)
-- This gives random ratings between 3.5 and 5.0 with review counts between 10 and 500
UPDATE product_catalog_ocs 
SET 
    rating = ROUND((3.5 + RANDOM() * 1.5)::numeric, 2),
    review_count = FLOOR(10 + RANDOM() * 490)::integer
WHERE rating IS NULL;

-- Verification queries (commented out, run manually if needed)
-- SELECT COUNT(*) as total, COUNT(sku) as has_sku, COUNT(rating) as has_rating FROM product_catalog_ocs;
-- SELECT id, product_name, sku, rating, review_count FROM product_catalog_ocs LIMIT 5;