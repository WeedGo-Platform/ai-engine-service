-- Consolidate Store Settings Tables
-- Merge all store_* configuration tables into store_settings with JSONB fields

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Add consolidated settings to store_settings
-- =========================================

-- Since store_settings already exists with the right structure (category, key, value as JSONB),
-- we'll use it to store all settings from other tables

-- Insert placeholder settings for hours configuration (from empty tables)
-- These will be stored as JSONB in the value column

-- Add regular hours settings
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT DISTINCT
    s.id as store_id,
    'hours' as category,
    'regular_hours' as key,
    jsonb_build_object(
        'monday', jsonb_build_object('open', '09:00', 'close', '21:00', 'is_closed', false),
        'tuesday', jsonb_build_object('open', '09:00', 'close', '21:00', 'is_closed', false),
        'wednesday', jsonb_build_object('open', '09:00', 'close', '21:00', 'is_closed', false),
        'thursday', jsonb_build_object('open', '09:00', 'close', '21:00', 'is_closed', false),
        'friday', jsonb_build_object('open', '09:00', 'close', '21:00', 'is_closed', false),
        'saturday', jsonb_build_object('open', '10:00', 'close', '20:00', 'is_closed', false),
        'sunday', jsonb_build_object('open', '11:00', 'close', '19:00', 'is_closed', false)
    ) as value,
    'Regular store operating hours' as description
FROM stores s
WHERE NOT EXISTS (
    SELECT 1 FROM store_settings ss
    WHERE ss.store_id = s.id
    AND ss.category = 'hours'
    AND ss.key = 'regular_hours'
);

-- Add special hours settings (for overrides)
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT DISTINCT
    s.id as store_id,
    'hours' as category,
    'special_hours' as key,
    '[]'::jsonb as value,  -- Empty array for special hours
    'Special hours overrides for specific dates' as description
FROM stores s
WHERE NOT EXISTS (
    SELECT 1 FROM store_settings ss
    WHERE ss.store_id = s.id
    AND ss.category = 'hours'
    AND ss.key = 'special_hours'
);

-- Add holiday hours settings
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT DISTINCT
    s.id as store_id,
    'hours' as category,
    'holiday_hours' as key,
    '[]'::jsonb as value,  -- Empty array for holiday hours
    'Holiday hours configuration' as description
FROM stores s
WHERE NOT EXISTS (
    SELECT 1 FROM store_settings ss
    WHERE ss.store_id = s.id
    AND ss.category = 'hours'
    AND ss.key = 'holiday_hours'
);

-- Add hours settings (general configuration)
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT DISTINCT
    s.id as store_id,
    'hours' as category,
    'settings' as key,
    jsonb_build_object(
        'timezone', 'America/Toronto',
        'auto_close_warning_minutes', 15,
        'allow_orders_when_closed', false,
        'display_next_open_time', true
    ) as value,
    'General hours settings and configuration' as description
FROM stores s
WHERE NOT EXISTS (
    SELECT 1 FROM store_settings ss
    WHERE ss.store_id = s.id
    AND ss.category = 'hours'
    AND ss.key = 'settings'
);

-- Add AI agents configuration
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT DISTINCT
    s.id as store_id,
    'ai' as category,
    'agents' as key,
    jsonb_build_object(
        'chat_agent', jsonb_build_object(
            'enabled', true,
            'model', 'gpt-4',
            'temperature', 0.7,
            'max_tokens', 500
        ),
        'recommendation_agent', jsonb_build_object(
            'enabled', true,
            'model', 'gpt-3.5-turbo',
            'update_frequency', 'daily'
        ),
        'analytics_agent', jsonb_build_object(
            'enabled', false,
            'model', 'gpt-4',
            'report_frequency', 'weekly'
        )
    ) as value,
    'AI agents configuration for the store' as description
FROM stores s
WHERE NOT EXISTS (
    SELECT 1 FROM store_settings ss
    WHERE ss.store_id = s.id
    AND ss.category = 'ai'
    AND ss.key = 'agents'
);

-- =========================================
-- STEP 2: Drop the empty store_* tables
-- =========================================

DROP TABLE IF EXISTS store_regular_hours CASCADE;
DROP TABLE IF EXISTS store_special_hours CASCADE;
DROP TABLE IF EXISTS store_holiday_hours CASCADE;
DROP TABLE IF EXISTS store_hours_settings CASCADE;
DROP TABLE IF EXISTS store_ai_agents CASCADE;

-- =========================================
-- STEP 3: Create helper view for easy access
-- =========================================

CREATE OR REPLACE VIEW store_settings_consolidated AS
SELECT
    s.id as store_id,
    s.name as store_name,
    -- Hours settings
    (SELECT value FROM store_settings WHERE store_id = s.id AND category = 'hours' AND key = 'regular_hours') as regular_hours,
    (SELECT value FROM store_settings WHERE store_id = s.id AND category = 'hours' AND key = 'special_hours') as special_hours,
    (SELECT value FROM store_settings WHERE store_id = s.id AND category = 'hours' AND key = 'holiday_hours') as holiday_hours,
    (SELECT value FROM store_settings WHERE store_id = s.id AND category = 'hours' AND key = 'settings') as hours_settings,
    -- AI settings
    (SELECT value FROM store_settings WHERE store_id = s.id AND category = 'ai' AND key = 'agents') as ai_agents,
    -- Other settings can be added here as needed
    s.created_at,
    s.updated_at
FROM stores s;

-- =========================================
-- VERIFICATION
-- =========================================
DO $$
DECLARE
    settings_count INTEGER;
    store_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO settings_count
    FROM store_settings;

    SELECT COUNT(*) INTO store_table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name LIKE 'store_%';

    RAISE NOTICE 'Consolidation complete!';
    RAISE NOTICE 'Total settings records: %', settings_count;
    RAISE NOTICE 'Remaining store_* tables: %', store_table_count;
END $$;

COMMIT;

-- =========================================
-- Helper functions for accessing settings
-- =========================================

-- Function to get store hours
CREATE OR REPLACE FUNCTION get_store_hours(p_store_id UUID, p_day_of_week TEXT DEFAULT NULL)
RETURNS JSONB AS $$
BEGIN
    IF p_day_of_week IS NOT NULL THEN
        RETURN (
            SELECT value->lower(p_day_of_week)
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get AI agent config
CREATE OR REPLACE FUNCTION get_store_ai_config(p_store_id UUID, p_agent_name TEXT DEFAULT NULL)
RETURNS JSONB AS $$
BEGIN
    IF p_agent_name IS NOT NULL THEN
        RETURN (
            SELECT value->p_agent_name
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    END IF;
END;
$$ LANGUAGE plpgsql;