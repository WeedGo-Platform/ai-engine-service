-- Migration: Enhanced Promotions System
-- Version: 032
-- Created: 2025-01-04
-- Description: Add store/tenant scoping, continuous promotions, and recurring time windows
--
-- FEATURES ADDED:
-- 1. Store-level and Tenant-level promotion scoping
-- 2. Continuous promotions (no end date)
-- 3. Recurring time-based schedules (e.g., daily 9AM-5PM, weekly Sun-Tue)
-- 4. Timezone support for multi-store operations
-- 5. Audit trail (created_by_user_id)

-- ============================================================================
-- STEP 1: Add new columns to promotions table
-- ============================================================================

-- Store and Tenant Scoping
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- Continuous Promotion Flag
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS is_continuous BOOLEAN DEFAULT false;

-- Recurrence System
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS recurrence_type VARCHAR(20) DEFAULT 'none';
    -- Values: 'none', 'daily', 'weekly'

-- Time Window Fields
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS time_start TIME,  -- Daily start time (e.g., 09:00:00)
    ADD COLUMN IF NOT EXISTS time_end TIME;    -- Daily end time (e.g., 17:00:00)

-- Timezone Support
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/Toronto';

-- Add comments for documentation
COMMENT ON COLUMN promotions.store_id IS 'Optional: Limits promotion to specific store. NULL = all stores';
COMMENT ON COLUMN promotions.tenant_id IS 'Optional: Limits promotion to specific tenant. NULL = all tenants';
COMMENT ON COLUMN promotions.is_continuous IS 'If true, promotion runs indefinitely (end_date must be NULL)';
COMMENT ON COLUMN promotions.recurrence_type IS 'Schedule pattern: none (one-time), daily (every day), weekly (specific days)';
COMMENT ON COLUMN promotions.time_start IS 'Daily start time for recurring promotions (in timezone specified)';
COMMENT ON COLUMN promotions.time_end IS 'Daily end time for recurring promotions (in timezone specified)';
COMMENT ON COLUMN promotions.timezone IS 'IANA timezone for time window validation';
COMMENT ON COLUMN promotions.created_by_user_id IS 'User who created this promotion (audit trail)';

-- ============================================================================
-- STEP 2: Add indexes for query performance
-- ============================================================================

-- Index for filtering by store
CREATE INDEX IF NOT EXISTS idx_promotions_store
    ON promotions(store_id)
    WHERE store_id IS NOT NULL;

-- Index for filtering by tenant
CREATE INDEX IF NOT EXISTS idx_promotions_tenant
    ON promotions(tenant_id)
    WHERE tenant_id IS NOT NULL;

-- Composite index for active promotions by date range
CREATE INDEX IF NOT EXISTS idx_promotions_active_dates
    ON promotions(active, start_date, end_date)
    WHERE active = true;

-- Index for continuous promotions
CREATE INDEX IF NOT EXISTS idx_promotions_continuous
    ON promotions(is_continuous, active)
    WHERE is_continuous = true AND active = true;

-- Index for recurring promotions
CREATE INDEX IF NOT EXISTS idx_promotions_recurring
    ON promotions(recurrence_type, active)
    WHERE recurrence_type != 'none' AND active = true;

-- ============================================================================
-- STEP 3: Add constraints for data integrity
-- ============================================================================

-- Constraint: Continuous promotions cannot have end_date
ALTER TABLE promotions
    ADD CONSTRAINT check_continuous_end_date
    CHECK (
        (is_continuous = true AND end_date IS NULL) OR
        (is_continuous = false)
    );

-- Constraint: If time_start is set, time_end must also be set
ALTER TABLE promotions
    ADD CONSTRAINT check_time_window_complete
    CHECK (
        (time_start IS NULL AND time_end IS NULL) OR
        (time_start IS NOT NULL AND time_end IS NOT NULL)
    );

-- Constraint: time_start must be before time_end
ALTER TABLE promotions
    ADD CONSTRAINT check_time_window_valid
    CHECK (
        time_start IS NULL OR
        time_end IS NULL OR
        time_start < time_end
    );

-- Constraint: Recurring promotions should have day_of_week or daily type
ALTER TABLE promotions
    ADD CONSTRAINT check_recurrence_logic
    CHECK (
        (recurrence_type = 'none') OR
        (recurrence_type = 'daily') OR
        (recurrence_type = 'weekly' AND day_of_week IS NOT NULL AND array_length(day_of_week, 1) > 0)
    );

-- ============================================================================
-- STEP 4: Update existing data (if any)
-- ============================================================================

-- Set recurrence_type based on existing day_of_week/hour_of_day
UPDATE promotions
SET recurrence_type = CASE
    WHEN day_of_week IS NOT NULL AND array_length(day_of_week, 1) > 0 THEN 'weekly'
    WHEN hour_of_day IS NOT NULL AND array_length(hour_of_day, 1) > 0 THEN 'daily'
    ELSE 'none'
END
WHERE recurrence_type = 'none';

-- Mark promotions without end_date as continuous
UPDATE promotions
SET is_continuous = true
WHERE end_date IS NULL AND is_continuous = false;

-- ============================================================================
-- STEP 5: Create helper function for promotion validation
-- ============================================================================

CREATE OR REPLACE FUNCTION is_promotion_active_now(
    p_id UUID,
    p_current_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) RETURNS BOOLEAN AS $$
DECLARE
    promo RECORD;
    current_day INTEGER;
    current_time_only TIME;
    is_active BOOLEAN := false;
BEGIN
    -- Get promotion details
    SELECT * INTO promo FROM promotions WHERE id = p_id;

    IF NOT FOUND OR NOT promo.active THEN
        RETURN false;
    END IF;

    -- Convert timestamp to timezone-aware time
    current_day := EXTRACT(DOW FROM p_current_time AT TIME ZONE promo.timezone);
    current_time_only := (p_current_time AT TIME ZONE promo.timezone)::TIME;

    -- Check 1: Date range
    IF promo.start_date > p_current_time THEN
        RETURN false;
    END IF;

    IF NOT promo.is_continuous AND promo.end_date IS NOT NULL AND promo.end_date < p_current_time THEN
        RETURN false;
    END IF;

    -- Check 2: Day of week (if specified)
    IF promo.day_of_week IS NOT NULL AND array_length(promo.day_of_week, 1) > 0 THEN
        IF NOT (current_day = ANY(promo.day_of_week)) THEN
            RETURN false;
        END IF;
    END IF;

    -- Check 3: Time window (if specified)
    IF promo.time_start IS NOT NULL AND promo.time_end IS NOT NULL THEN
        IF NOT (current_time_only >= promo.time_start AND current_time_only <= promo.time_end) THEN
            RETURN false;
        END IF;
    END IF;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_promotion_active_now IS 'Check if a promotion is currently active based on date, time, and recurrence rules';

-- ============================================================================
-- STEP 6: Create view for currently active promotions
-- ============================================================================

CREATE OR REPLACE VIEW active_promotions AS
SELECT
    p.*,
    s.name AS store_name,
    s.store_code,
    t.name AS tenant_name,
    u.email AS created_by_email,
    CASE
        WHEN p.store_id IS NOT NULL AND p.tenant_id IS NOT NULL THEN 'tenant_store'
        WHEN p.store_id IS NOT NULL THEN 'store'
        WHEN p.tenant_id IS NOT NULL THEN 'tenant'
        ELSE 'global'
    END AS scope_type,
    CASE
        WHEN p.is_continuous THEN 'Continuous'
        WHEN p.end_date IS NOT NULL THEN 'Until ' || p.end_date::TEXT
        ELSE 'No end date'
    END AS duration_display,
    CASE
        WHEN p.time_start IS NOT NULL AND p.time_end IS NOT NULL THEN
            p.time_start::TEXT || ' - ' || p.time_end::TEXT
        ELSE 'All day'
    END AS time_window_display
FROM promotions p
LEFT JOIN stores s ON p.store_id = s.id
LEFT JOIN tenants t ON p.tenant_id = t.id
LEFT JOIN users u ON p.created_by_user_id = u.id
WHERE p.active = true
  AND p.start_date <= CURRENT_TIMESTAMP
  AND (p.is_continuous = true OR p.end_date IS NULL OR p.end_date >= CURRENT_TIMESTAMP);

COMMENT ON VIEW active_promotions IS 'Currently active promotions with human-readable scope and duration info';

-- ============================================================================
-- STEP 7: Grant permissions
-- ============================================================================

-- Grant execute permission on helper function
GRANT EXECUTE ON FUNCTION is_promotion_active_now(UUID, TIMESTAMP) TO PUBLIC;

-- ============================================================================
-- STEP 8: Migration verification
-- ============================================================================

-- Verify all columns were added
DO $$
DECLARE
    missing_columns TEXT[] := ARRAY[]::TEXT[];
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'store_id'
    ) THEN
        missing_columns := array_append(missing_columns, 'store_id');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'tenant_id'
    ) THEN
        missing_columns := array_append(missing_columns, 'tenant_id');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'is_continuous'
    ) THEN
        missing_columns := array_append(missing_columns, 'is_continuous');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'recurrence_type'
    ) THEN
        missing_columns := array_append(missing_columns, 'recurrence_type');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'time_start'
    ) THEN
        missing_columns := array_append(missing_columns, 'time_start');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'promotions' AND column_name = 'time_end'
    ) THEN
        missing_columns := array_append(missing_columns, 'time_end');
    END IF;

    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Migration failed: Missing columns: %', array_to_string(missing_columns, ', ');
    END IF;

    RAISE NOTICE '✅ Migration 032_enhance_promotions_system completed successfully';
    RAISE NOTICE '   - Added store/tenant scoping';
    RAISE NOTICE '   - Added continuous promotion support';
    RAISE NOTICE '   - Added recurrence system (daily/weekly)';
    RAISE NOTICE '   - Added time window controls';
    RAISE NOTICE '   - Added timezone support';
    RAISE NOTICE '   - Created indexes for performance';
    RAISE NOTICE '   - Created helper function: is_promotion_active_now()';
    RAISE NOTICE '   - Created view: active_promotions';
END;
$$;
