-- Fix malformed image URLs in ocs_product_catalog
-- Issue: URLs contain "_compress_" instead of "_compressed_"
-- This affects 1,222 products across 1,113 tenants

-- Preview affected records before fixing
SELECT
    COUNT(*) as affected_records,
    'Before fix - compress (broken)' as status
FROM ocs_product_catalog
WHERE image_url LIKE '%_compress_%'
  AND image_url NOT LIKE '%compressed%';

-- Update the malformed URLs
-- Replace "_compress_" with "_compressed_"
UPDATE ocs_product_catalog
SET
    image_url = REPLACE(image_url, '_compress_', '_compressed_'),
    updated_at = NOW()
WHERE
    image_url LIKE '%_compress_%'
    AND image_url NOT LIKE '%compressed%';

-- Verify the fix
SELECT
    COUNT(*) as remaining_broken_urls,
    'After fix - compress (should be 0)' as status
FROM ocs_product_catalog
WHERE image_url LIKE '%_compress_%'
  AND image_url NOT LIKE '%compressed%';

-- Show sample of fixed URLs
SELECT
    ocs_variant_number,
    product_name,
    image_url,
    'Fixed URL' as status
FROM ocs_product_catalog
WHERE image_url LIKE '%00843087006929%'
LIMIT 5;
