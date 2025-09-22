-- Migration: Remove hardcoded 25% markup from retail_price column
-- Date: 2025-01-20
-- Description: Changes retail_price from a generated column with hardcoded 1.25 multiplier
--              to a regular column that can be dynamically calculated based on store settings

BEGIN;

-- Step 1: Drop the generated column
ALTER TABLE ocs_inventory DROP COLUMN retail_price CASCADE;

-- Step 2: Add retail_price as a regular column
ALTER TABLE ocs_inventory ADD COLUMN retail_price NUMERIC(10,2);

-- Step 3: Create a function to calculate retail price based on store settings
CREATE OR REPLACE FUNCTION calculate_retail_price(
    p_unit_cost NUMERIC,
    p_store_id UUID
) RETURNS NUMERIC AS $$
DECLARE
    v_markup_percentage NUMERIC;
    v_settings JSONB;
BEGIN
    -- Get store settings
    SELECT settings INTO v_settings
    FROM stores
    WHERE id = p_store_id;

    -- Extract markup percentage from settings, default to 25 if not set
    IF v_settings IS NOT NULL AND v_settings->'pricing' IS NOT NULL THEN
        v_markup_percentage := COALESCE(
            (v_settings->'pricing'->>'default_markup_percentage')::NUMERIC,
            25.0
        );
    ELSE
        v_markup_percentage := 25.0;
    END IF;

    -- Calculate retail price
    RETURN p_unit_cost * (1 + v_markup_percentage / 100.0);
END;
$$ LANGUAGE plpgsql;

-- Step 4: Update existing retail_price values based on store settings
UPDATE ocs_inventory inv
SET retail_price = calculate_retail_price(inv.unit_cost, inv.store_id)
WHERE retail_price IS NULL AND unit_cost IS NOT NULL AND unit_cost > 0;

-- Step 5: Create a trigger to automatically set retail_price on insert/update if not provided
CREATE OR REPLACE FUNCTION update_retail_price()
RETURNS TRIGGER AS $$
BEGIN
    -- Only calculate if override_price is not set and retail_price is not manually provided
    IF NEW.override_price IS NULL AND
       (NEW.retail_price IS NULL OR NEW.retail_price = OLD.retail_price) AND
       NEW.unit_cost IS NOT NULL AND NEW.unit_cost > 0 THEN
        NEW.retail_price := calculate_retail_price(NEW.unit_cost, NEW.store_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER retail_price_trigger
BEFORE INSERT OR UPDATE ON ocs_inventory
FOR EACH ROW
EXECUTE FUNCTION update_retail_price();

-- Step 6: Add comment to document the change
COMMENT ON COLUMN ocs_inventory.retail_price IS 'Retail price calculated based on store default markup. Can be overridden by override_price.';

COMMIT;

-- Verification query
SELECT
    COUNT(*) as total_products,
    COUNT(CASE WHEN retail_price IS NOT NULL THEN 1 END) as with_retail_price,
    COUNT(CASE WHEN override_price IS NOT NULL THEN 1 END) as with_override
FROM ocs_inventory;