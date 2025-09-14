-- Migration: Add location tracking to batch_tracking table
-- Date: 2025-01-13
-- Description: 
--   Add location_id field to batch_tracking to track where batches are stored

BEGIN;

-- Add location_id column to batch_tracking
ALTER TABLE batch_tracking 
ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES shelf_locations(id);

-- Add index for location lookups
CREATE INDEX IF NOT EXISTS idx_batch_tracking_location 
ON batch_tracking(location_id);

-- Add comment for documentation
COMMENT ON COLUMN batch_tracking.location_id IS 'Primary shelf location where this batch is stored';

COMMIT;

-- Verification query
-- SELECT batch_lot, sku, location_id FROM batch_tracking LIMIT 5;