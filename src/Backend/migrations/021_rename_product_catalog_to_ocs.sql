-- Migration: Rename product_catalog to product_catalog_ocs and add slug column
-- Date: 2025-01-11
-- Description: Rename product catalog table to indicate OCS (Ontario Cannabis Store) source
--              and add slug column for URL-friendly product identifiers

-- Step 1: Rename the table from product_catalog to product_catalog_ocs
ALTER TABLE IF EXISTS product_catalog 
RENAME TO product_catalog_ocs;

-- Step 2: Add slug column with unique constraint
ALTER TABLE product_catalog_ocs 
ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;

-- Step 3: Create a function to generate slugs from product names
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    slug TEXT;
BEGIN
    -- Convert to lowercase
    slug := lower(input_text);
    
    -- Replace spaces and special characters with hyphens
    slug := regexp_replace(slug, '[^a-z0-9-]+', '-', 'g');
    
    -- Remove leading/trailing hyphens
    slug := trim(both '-' from slug);
    
    -- Replace multiple hyphens with single hyphen
    slug := regexp_replace(slug, '-+', '-', 'g');
    
    RETURN slug;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Step 4: Generate slugs for existing products
UPDATE product_catalog_ocs 
SET slug = generate_slug(product_name || '-' || COALESCE(brand, '') || '-' || id::text)
WHERE slug IS NULL;

-- Step 5: Make slug column NOT NULL after populating
ALTER TABLE product_catalog_ocs 
ALTER COLUMN slug SET NOT NULL;

-- Step 6: Create index on slug for fast lookups
CREATE INDEX IF NOT EXISTS idx_product_catalog_ocs_slug 
ON product_catalog_ocs(slug);

-- Step 7: Create trigger to auto-generate slug on insert/update
CREATE OR REPLACE FUNCTION auto_generate_product_slug()
RETURNS TRIGGER AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
    counter INT := 0;
BEGIN
    -- Generate base slug from product name and brand
    base_slug := generate_slug(
        NEW.product_name || 
        CASE WHEN NEW.brand IS NOT NULL THEN '-' || NEW.brand ELSE '' END
    );
    
    final_slug := base_slug;
    
    -- Check for uniqueness and append counter if needed
    WHILE EXISTS(
        SELECT 1 FROM product_catalog_ocs 
        WHERE slug = final_slug 
        AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
    ) LOOP
        counter := counter + 1;
        final_slug := base_slug || '-' || counter;
    END LOOP;
    
    NEW.slug := final_slug;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Create trigger for auto-generating slugs
DROP TRIGGER IF EXISTS trigger_auto_generate_product_slug ON product_catalog_ocs;
CREATE TRIGGER trigger_auto_generate_product_slug
BEFORE INSERT OR UPDATE OF product_name, brand ON product_catalog_ocs
FOR EACH ROW
WHEN (NEW.slug IS NULL OR NEW.product_name IS DISTINCT FROM OLD.product_name OR NEW.brand IS DISTINCT FROM OLD.brand)
EXECUTE FUNCTION auto_generate_product_slug();

-- Step 9: Update any foreign key references (if they exist)
-- Note: Update any views, functions, or other objects that reference product_catalog

-- Step 10: Add comment to document the table purpose
COMMENT ON TABLE product_catalog_ocs IS 'Product catalog sourced from Ontario Cannabis Store (OCS) with enhanced slug support for URL-friendly identifiers';
COMMENT ON COLUMN product_catalog_ocs.slug IS 'URL-friendly unique identifier auto-generated from product name and brand';

-- Step 11: Grant appropriate permissions
GRANT SELECT ON product_catalog_ocs TO PUBLIC;
GRANT INSERT, UPDATE, DELETE ON product_catalog_ocs TO weedgo;

-- Verification queries (commented out, run manually if needed)
-- SELECT COUNT(*) as total_products, COUNT(DISTINCT slug) as unique_slugs FROM product_catalog_ocs;
-- SELECT id, product_name, brand, slug FROM product_catalog_ocs LIMIT 10;