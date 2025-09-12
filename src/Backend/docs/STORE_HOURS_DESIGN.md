# Store Hours and Holiday Management System Design

## Overview
Comprehensive store hours management system supporting regular hours, holidays (federal/provincial), and special hours with full Canadian compliance.

## Database Tables

### 1. **holidays** - Holiday Definitions
Stores all federal, provincial, and custom holidays.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Holiday name (e.g., "Canada Day") |
| holiday_type | ENUM | Type: 'federal', 'provincial', 'municipal', 'custom' |
| province_territory_id | UUID | FK to provinces_territories (null for federal) |
| date_type | ENUM | 'fixed', 'floating', 'calculated' |
| fixed_month | INTEGER | Month for fixed dates (1-12) |
| fixed_day | INTEGER | Day for fixed dates (1-31) |
| floating_rule | JSONB | Rules for floating dates |
| calculation_rule | VARCHAR | Formula for calculated dates (e.g., Easter) |
| is_statutory | BOOLEAN | Is it a statutory holiday? |
| is_bank_holiday | BOOLEAN | Do banks close? |
| typical_business_impact | ENUM | 'closed', 'reduced_hours', 'normal', 'extended_hours' |

#### Pre-populated Federal Holidays:
- New Year's Day (Jan 1)
- Good Friday (Calculated - Easter minus 2 days)
- Victoria Day (Monday on or before May 24)
- Canada Day (July 1)
- Labour Day (First Monday of September)
- Thanksgiving (Second Monday of October)
- Remembrance Day (Nov 11)
- Christmas Day (Dec 25)
- Boxing Day (Dec 26)

### 2. **store_regular_hours** - Weekly Schedule
Regular operating hours for each day of the week.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| store_id | UUID | FK to stores table |
| day_of_week | INTEGER | 0=Sunday, 6=Saturday |
| time_slots | JSONB | Array of time periods |
| is_closed | BOOLEAN | Store closed this day? |
| delivery_hours | JSONB | Delivery service hours |
| pickup_hours | JSONB | Pickup service hours |

**Example time_slots:**
```json
[
  {"open": "09:00", "close": "12:00"},  // Morning
  {"open": "13:00", "close": "21:00"}   // Afternoon (after lunch break)
]
```

### 3. **store_holiday_hours** - Holiday Schedules
Store-specific holiday hours and observances.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| store_id | UUID | FK to stores |
| holiday_id | UUID | FK to holidays (optional) |
| custom_holiday_name | VARCHAR | For store-specific holidays |
| custom_holiday_date | DATE | Date of custom holiday |
| year | INTEGER | Specific year override |
| is_closed | BOOLEAN | Store closed on this holiday? |
| open_time | TIME | Opening time if not closed |
| close_time | TIME | Closing time if not closed |
| eve_hours | JSONB | Special hours for holiday eve |
| delivery_available | BOOLEAN | Delivery service available? |
| pickup_available | BOOLEAN | Pickup service available? |
| customer_message | TEXT | Message to display to customers |

### 4. **store_special_hours** - Temporary Changes
One-time schedule changes for specific dates.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| store_id | UUID | FK to stores |
| date | DATE | Date of special hours |
| reason | VARCHAR | Reason for change |
| is_closed | BOOLEAN | Store closed? |
| open_time | TIME | Opening time |
| close_time | TIME | Closing time |
| delivery_available | BOOLEAN | Delivery available? |
| pickup_available | BOOLEAN | Pickup available? |
| customer_message | TEXT | Customer notification |

**Common reasons:**
- Staff Training
- Inventory Count
- Renovation
- Special Event
- Emergency Closure
- Extended Holiday Hours

### 5. **store_hours_settings** - Configuration
Store-level settings for hours management.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| store_id | UUID | FK to stores (unique) |
| observe_federal_holidays | BOOLEAN | Auto-observe federal holidays? |
| observe_provincial_holidays | BOOLEAN | Auto-observe provincial holidays? |
| observe_municipal_holidays | BOOLEAN | Auto-observe municipal holidays? |
| auto_close_on_stat_holidays | BOOLEAN | Automatically close on stat holidays? |
| default_holiday_hours | JSONB | Default hours if open on holiday |
| notify_customers_of_changes | BOOLEAN | Send notifications? |
| advance_notice_days | INTEGER | Days advance notice for changes |
| display_timezone | VARCHAR | Timezone for display |

## Usage Examples

### 1. Set Regular Store Hours
```sql
-- Set Monday-Friday 9am-9pm
INSERT INTO store_regular_hours (store_id, day_of_week, time_slots)
VALUES 
  ('store-uuid', 1, '[{"open": "09:00", "close": "21:00"}]'),
  ('store-uuid', 2, '[{"open": "09:00", "close": "21:00"}]'),
  ('store-uuid', 3, '[{"open": "09:00", "close": "21:00"}]'),
  ('store-uuid', 4, '[{"open": "09:00", "close": "21:00"}]'),
  ('store-uuid', 5, '[{"open": "09:00", "close": "21:00"}]');

-- Set Saturday 10am-8pm, Sunday 11am-6pm
INSERT INTO store_regular_hours (store_id, day_of_week, time_slots)
VALUES 
  ('store-uuid', 6, '[{"open": "10:00", "close": "20:00"}]'),
  ('store-uuid', 0, '[{"open": "11:00", "close": "18:00"}]');
```

### 2. Configure Holiday Observance
```sql
-- Configure store to observe holidays
INSERT INTO store_hours_settings (
  store_id, 
  observe_federal_holidays,
  observe_provincial_holidays,
  auto_close_on_stat_holidays,
  default_holiday_hours
) VALUES (
  'store-uuid',
  true,
  true,
  true,
  '{"open": "12:00", "close": "17:00"}'
);
```

### 3. Set Special Holiday Hours
```sql
-- Open with reduced hours on Boxing Day
INSERT INTO store_holiday_hours (
  store_id,
  holiday_id,
  year,
  is_closed,
  open_time,
  close_time,
  customer_message
) VALUES (
  'store-uuid',
  (SELECT id FROM holidays WHERE name = 'Boxing Day'),
  2025,
  false,
  '12:00',
  '18:00',
  'Special Boxing Day hours: 12pm-6pm. Limited stock available.'
);
```

### 4. Schedule Temporary Closure
```sql
-- Close for inventory
INSERT INTO store_special_hours (
  store_id,
  date,
  reason,
  is_closed,
  customer_message
) VALUES (
  'store-uuid',
  '2025-02-15',
  'Annual Inventory',
  true,
  'Closed for inventory. We''ll reopen Feb 16 with fresh stock!'
);
```

## Helper Functions

### is_store_open(store_id, datetime)
Check if a store is open at a specific date/time, considering:
1. Special hours (highest priority)
2. Holiday hours
3. Regular weekly hours

### calculate_holiday_date(year, holiday_id)
Calculate the actual date of a holiday for a given year, handling:
- Fixed dates (e.g., Christmas)
- Floating dates (e.g., Labour Day)
- Calculated dates (e.g., Easter)

## Views

### store_week_schedule
Shows the current week's schedule for all stores.

### upcoming_store_holidays
Lists upcoming holidays and how they affect each store.

## Provincial Holiday Examples

### Ontario
- Family Day (3rd Monday in February)
- Civic Holiday (1st Monday in August) - not statutory

### British Columbia
- Family Day (2nd Monday in February)
- BC Day (1st Monday in August)

### Quebec
- National Holiday (June 24)
- Easter Monday

### Alberta
- Family Day (3rd Monday in February)
- Heritage Day (1st Monday in August)

## Implementation Notes

1. **Priority Order**: Special Hours > Holiday Hours > Regular Hours
2. **Timezone Handling**: All times stored in store's local timezone
3. **Service-Specific Hours**: Delivery and pickup can have different hours than store
4. **Holiday Inheritance**: Stores inherit provincial holidays based on their province_territory_id
5. **Flexibility**: System supports both automatic holiday observance and manual overrides

## API Endpoints to Implement

```
GET  /api/stores/{id}/hours/current     - Current hours status
GET  /api/stores/{id}/hours/week        - This week's schedule
GET  /api/stores/{id}/hours/upcoming    - Next 30 days including holidays
POST /api/stores/{id}/hours/regular     - Set regular hours
POST /api/stores/{id}/hours/special     - Add special hours
POST /api/stores/{id}/hours/holiday     - Configure holiday hours
GET  /api/holidays                      - List all holidays
GET  /api/holidays/provincial/{code}    - Get provincial holidays
```