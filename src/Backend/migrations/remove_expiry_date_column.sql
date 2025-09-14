-- Remove expiry_date column from batch_tracking table
-- Products do not expire

BEGIN;

-- Drop the expiry_date column from batch_tracking table
ALTER TABLE batch_tracking DROP COLUMN IF EXISTS expiry_date;

COMMIT;