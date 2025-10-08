-- Clean up null values in payment_methods JSONB arrays
-- This migration removes any null entries that may have been created by previous queries

-- Update all profiles to filter out null values from payment_methods array
UPDATE profiles
SET payment_methods = (
    SELECT COALESCE(jsonb_agg(method), '[]'::jsonb)
    FROM jsonb_array_elements(payment_methods) AS method
    WHERE method IS NOT NULL
)
WHERE payment_methods IS NOT NULL
  AND payment_methods != '[]'::jsonb;

-- Log the changes
DO $$
DECLARE
    affected_count INTEGER;
BEGIN
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RAISE NOTICE 'Cleaned payment_methods for % profiles', affected_count;
END $$;
