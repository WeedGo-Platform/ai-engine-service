-- =====================================================
-- Migration: Enhanced Store Hours and Holiday Management
-- Version: 009
-- Description: Add comprehensive store hours, holiday schedules, and special hours
-- Author: WeedGo Platform Team
-- Date: 2025-01-08
-- =====================================================

-- =====================================================
-- 1. HOLIDAY DEFINITIONS TABLE
-- =====================================================
-- Stores federal and provincial holidays
CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    holiday_type VARCHAR(20) NOT NULL CHECK (holiday_type IN ('federal', 'provincial', 'municipal', 'custom')),
    province_territory_id UUID REFERENCES provinces_territories(id),
    date_type VARCHAR(20) NOT NULL CHECK (date_type IN ('fixed', 'floating', 'calculated')),
    
    -- For fixed dates (e.g., Christmas - Dec 25)
    fixed_month INTEGER CHECK (fixed_month BETWEEN 1 AND 12),
    fixed_day INTEGER CHECK (fixed_day BETWEEN 1 AND 31),
    
    -- For floating dates (e.g., Labour Day - first Monday of September)
    floating_rule JSONB, -- {"month": 9, "weekday": "monday", "occurrence": "first"}
    
    -- For calculated dates (e.g., Easter)
    calculation_rule VARCHAR(100),
    
    -- Holiday metadata
    is_statutory BOOLEAN DEFAULT true,
    is_bank_holiday BOOLEAN DEFAULT true,
    typical_business_impact VARCHAR(20) CHECK (typical_business_impact IN ('closed', 'reduced_hours', 'normal', 'extended_hours')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT holiday_date_check CHECK (
        (date_type = 'fixed' AND fixed_month IS NOT NULL AND fixed_day IS NOT NULL) OR
        (date_type = 'floating' AND floating_rule IS NOT NULL) OR
        (date_type = 'calculated' AND calculation_rule IS NOT NULL)
    )
);

CREATE INDEX idx_holidays_type ON holidays(holiday_type);
CREATE INDEX idx_holidays_province ON holidays(province_territory_id);

-- =====================================================
-- 2. STORE REGULAR HOURS TABLE
-- =====================================================
-- Detailed regular hours for each day of the week
CREATE TABLE IF NOT EXISTS store_regular_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday
    
    -- Multiple time slots per day (for lunch breaks, etc.)
    time_slots JSONB NOT NULL DEFAULT '[]', -- Array of {"open": "09:00", "close": "17:00"}
    
    is_closed BOOLEAN DEFAULT false,
    
    -- Service-specific hours
    delivery_hours JSONB, -- {"start": "10:00", "end": "20:00"}
    pickup_hours JSONB,   -- {"start": "09:00", "end": "21:00"}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, day_of_week)
);

CREATE INDEX idx_store_regular_hours_store ON store_regular_hours(store_id);

-- =====================================================
-- 3. STORE HOLIDAY HOURS TABLE
-- =====================================================
-- Store-specific holiday hours and observances
CREATE TABLE IF NOT EXISTS store_holiday_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    holiday_id UUID REFERENCES holidays(id),
    
    -- For custom store holidays
    custom_holiday_name VARCHAR(100),
    custom_holiday_date DATE,
    
    year INTEGER, -- Specific year override
    
    -- Holiday schedule
    is_closed BOOLEAN DEFAULT true,
    open_time TIME,
    close_time TIME,
    
    -- Special hours for holiday eve
    eve_hours JSONB, -- {"open": "09:00", "close": "18:00"}
    
    -- Service availability
    delivery_available BOOLEAN DEFAULT false,
    pickup_available BOOLEAN DEFAULT false,
    
    -- Holiday message
    customer_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT store_holiday_check CHECK (
        (holiday_id IS NOT NULL) OR 
        (custom_holiday_name IS NOT NULL AND custom_holiday_date IS NOT NULL)
    )
);

CREATE INDEX idx_store_holiday_hours_store ON store_holiday_hours(store_id);
CREATE INDEX idx_store_holiday_hours_holiday ON store_holiday_hours(holiday_id);
CREATE INDEX idx_store_holiday_hours_date ON store_holiday_hours(custom_holiday_date);

-- =====================================================
-- 4. STORE SPECIAL HOURS TABLE
-- =====================================================
-- Temporary hour changes for specific dates
CREATE TABLE IF NOT EXISTS store_special_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    date DATE NOT NULL,
    reason VARCHAR(100), -- "Staff Training", "Inventory", "Special Event", etc.
    
    is_closed BOOLEAN DEFAULT false,
    open_time TIME,
    close_time TIME,
    
    -- Service availability
    delivery_available BOOLEAN DEFAULT true,
    pickup_available BOOLEAN DEFAULT true,
    
    customer_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, date)
);

CREATE INDEX idx_store_special_hours_store_date ON store_special_hours(store_id, date);

-- =====================================================
-- 5. STORE HOURS SETTINGS TABLE
-- =====================================================
-- Store-level settings for hours management
CREATE TABLE IF NOT EXISTS store_hours_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Holiday observance settings
    observe_federal_holidays BOOLEAN DEFAULT true,
    observe_provincial_holidays BOOLEAN DEFAULT true,
    observe_municipal_holidays BOOLEAN DEFAULT false,
    
    -- Auto-scheduling
    auto_close_on_stat_holidays BOOLEAN DEFAULT true,
    
    -- Default holiday hours (if not closed)
    default_holiday_hours JSONB, -- {"open": "10:00", "close": "18:00"}
    
    -- Notification settings
    notify_customers_of_changes BOOLEAN DEFAULT true,
    advance_notice_days INTEGER DEFAULT 7,
    
    -- Time zone handling
    display_timezone VARCHAR(50) DEFAULT 'America/Toronto',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id)
);

-- =====================================================
-- 6. POPULATE DEFAULT CANADIAN HOLIDAYS
-- =====================================================
INSERT INTO holidays (name, holiday_type, date_type, fixed_month, fixed_day, is_statutory, typical_business_impact) VALUES
    ('New Year''s Day', 'federal', 'fixed', 1, 1, true, 'closed'),
    ('Good Friday', 'federal', 'calculated', NULL, NULL, true, 'closed'),
    ('Canada Day', 'federal', 'fixed', 7, 1, true, 'closed'),
    ('Labour Day', 'federal', 'floating', NULL, NULL, true, 'closed'),
    ('Thanksgiving', 'federal', 'floating', NULL, NULL, true, 'closed'),
    ('Remembrance Day', 'federal', 'fixed', 11, 11, true, 'reduced_hours'),
    ('Christmas Day', 'federal', 'fixed', 12, 25, true, 'closed'),
    ('Boxing Day', 'federal', 'fixed', 12, 26, true, 'reduced_hours');

-- Update floating holiday rules
UPDATE holidays SET floating_rule = '{"month": 9, "weekday": "monday", "occurrence": "first"}' 
WHERE name = 'Labour Day';

UPDATE holidays SET floating_rule = '{"month": 10, "weekday": "monday", "occurrence": "second"}' 
WHERE name = 'Thanksgiving';

UPDATE holidays SET calculation_rule = 'easter_sunday-2' 
WHERE name = 'Good Friday';

-- Add Victoria Day (floating)
INSERT INTO holidays (name, holiday_type, date_type, floating_rule, is_statutory, typical_business_impact)
VALUES ('Victoria Day', 'federal', 'floating', 
        '{"month": 5, "weekday": "monday", "on_or_before": 24}', 
        true, 'closed');

-- =====================================================
-- 7. PROVINCIAL HOLIDAYS (Examples for Ontario and BC)
-- =====================================================
-- Ontario specific holidays
INSERT INTO holidays (name, holiday_type, province_territory_id, date_type, floating_rule, is_statutory, typical_business_impact)
SELECT 
    'Family Day', 
    'provincial', 
    id, 
    'floating',
    '{"month": 2, "weekday": "monday", "occurrence": "third"}',
    true,
    'closed'
FROM provinces_territories WHERE code = 'ON';

INSERT INTO holidays (name, holiday_type, province_territory_id, date_type, floating_rule, is_statutory, typical_business_impact)
SELECT 
    'Civic Holiday', 
    'provincial', 
    id, 
    'floating',
    '{"month": 8, "weekday": "monday", "occurrence": "first"}',
    false,
    'normal'
FROM provinces_territories WHERE code = 'ON';

-- British Columbia specific holidays
INSERT INTO holidays (name, holiday_type, province_territory_id, date_type, floating_rule, is_statutory, typical_business_impact)
SELECT 
    'Family Day', 
    'provincial', 
    id, 
    'floating',
    '{"month": 2, "weekday": "monday", "occurrence": "second"}',
    true,
    'closed'
FROM provinces_territories WHERE code = 'BC';

INSERT INTO holidays (name, holiday_type, province_territory_id, date_type, floating_rule, is_statutory, typical_business_impact)
SELECT 
    'BC Day', 
    'provincial', 
    id, 
    'floating',
    '{"month": 8, "weekday": "monday", "occurrence": "first"}',
    true,
    'closed'
FROM provinces_territories WHERE code = 'BC';

-- =====================================================
-- 8. MIGRATION OF EXISTING HOURS DATA
-- =====================================================
-- Migrate existing hours from stores table to store_regular_hours
INSERT INTO store_regular_hours (store_id, day_of_week, time_slots)
SELECT 
    s.id,
    day_num,
    CASE 
        WHEN s.hours->day_name IS NOT NULL THEN
            jsonb_build_array(
                jsonb_build_object(
                    'open', s.hours->day_name->>'open',
                    'close', s.hours->day_name->>'close'
                )
            )
        ELSE '[]'::jsonb
    END
FROM stores s
CROSS JOIN (
    VALUES 
        (0, 'sunday'),
        (1, 'monday'),
        (2, 'tuesday'),
        (3, 'wednesday'),
        (4, 'thursday'),
        (5, 'friday'),
        (6, 'saturday')
) AS days(day_num, day_name)
WHERE s.hours IS NOT NULL
ON CONFLICT (store_id, day_of_week) DO NOTHING;

-- =====================================================
-- 9. HELPER FUNCTIONS
-- =====================================================

-- Function to calculate next occurrence of a holiday
CREATE OR REPLACE FUNCTION calculate_holiday_date(
    p_year INTEGER,
    p_holiday_id UUID
) RETURNS DATE AS $$
DECLARE
    v_holiday holidays%ROWTYPE;
    v_date DATE;
BEGIN
    SELECT * INTO v_holiday FROM holidays WHERE id = p_holiday_id;
    
    IF v_holiday.date_type = 'fixed' THEN
        v_date := make_date(p_year, v_holiday.fixed_month, v_holiday.fixed_day);
    ELSIF v_holiday.date_type = 'floating' THEN
        -- This would need more complex logic for floating dates
        -- Simplified example
        v_date := make_date(p_year, (v_holiday.floating_rule->>'month')::int, 1);
    ELSIF v_holiday.date_type = 'calculated' THEN
        -- Handle calculated dates like Easter
        -- This would require complex calculation
        v_date := make_date(p_year, 4, 1); -- Placeholder
    END IF;
    
    RETURN v_date;
END;
$$ LANGUAGE plpgsql;

-- Function to check if store is open at specific datetime
CREATE OR REPLACE FUNCTION is_store_open(
    p_store_id UUID,
    p_datetime TIMESTAMP
) RETURNS BOOLEAN AS $$
DECLARE
    v_date DATE;
    v_time TIME;
    v_day_of_week INTEGER;
    v_is_holiday BOOLEAN;
    v_special_hours store_special_hours%ROWTYPE;
    v_regular_hours store_regular_hours%ROWTYPE;
BEGIN
    v_date := p_datetime::DATE;
    v_time := p_datetime::TIME;
    v_day_of_week := EXTRACT(DOW FROM v_date);
    
    -- Check special hours first
    SELECT * INTO v_special_hours 
    FROM store_special_hours 
    WHERE store_id = p_store_id AND date = v_date;
    
    IF FOUND THEN
        IF v_special_hours.is_closed THEN
            RETURN FALSE;
        END IF;
        RETURN v_time >= v_special_hours.open_time AND v_time <= v_special_hours.close_time;
    END IF;
    
    -- Check holidays
    -- (Simplified - would need more complex logic)
    
    -- Check regular hours
    SELECT * INTO v_regular_hours
    FROM store_regular_hours
    WHERE store_id = p_store_id AND day_of_week = v_day_of_week;
    
    IF v_regular_hours.is_closed THEN
        RETURN FALSE;
    END IF;
    
    -- Check against time slots
    -- (Would need to check JSON array of time slots)
    
    RETURN TRUE; -- Simplified
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 10. VIEWS FOR EASIER QUERYING
-- =====================================================

-- View for current week's store hours
CREATE OR REPLACE VIEW store_week_schedule AS
SELECT 
    s.id as store_id,
    s.name as store_name,
    srh.day_of_week,
    CASE srh.day_of_week
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_name,
    srh.is_closed,
    srh.time_slots,
    srh.delivery_hours,
    srh.pickup_hours
FROM stores s
LEFT JOIN store_regular_hours srh ON s.id = srh.store_id
ORDER BY s.id, srh.day_of_week;

-- View for upcoming holidays affecting stores
CREATE OR REPLACE VIEW upcoming_store_holidays AS
SELECT 
    s.id as store_id,
    s.name as store_name,
    h.name as holiday_name,
    h.holiday_type,
    COALESCE(shh.is_closed, h.typical_business_impact = 'closed') as will_be_closed,
    shh.open_time,
    shh.close_time,
    shh.customer_message
FROM stores s
CROSS JOIN holidays h
LEFT JOIN store_holiday_hours shh ON s.id = shh.store_id AND h.id = shh.holiday_id
WHERE h.is_statutory = true
ORDER BY s.id;

-- =====================================================
-- 11. INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX idx_store_regular_hours_lookup ON store_regular_hours(store_id, day_of_week, is_closed);
CREATE INDEX idx_store_special_hours_lookup ON store_special_hours(store_id, date, is_closed);
CREATE INDEX idx_holidays_lookup ON holidays(holiday_type, province_territory_id, is_statutory);

-- =====================================================
-- END OF MIGRATION
-- =====================================================