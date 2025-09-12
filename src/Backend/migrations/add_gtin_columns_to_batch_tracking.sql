-- Migration: Add GTIN columns to batch_tracking table
-- Purpose: Add CaseGTIN, PackagedOnDate, GTINBarCode, and EachGTIN columns for enhanced product tracking

-- Add new columns to batch_tracking table
ALTER TABLE batch_tracking
ADD COLUMN IF NOT EXISTS case_gtin VARCHAR(14),
ADD COLUMN IF NOT EXISTS packaged_on_date DATE,
ADD COLUMN IF NOT EXISTS gtin_barcode VARCHAR(14),
ADD COLUMN IF NOT EXISTS each_gtin VARCHAR(14);

-- Add indexes for GTIN lookups
CREATE INDEX IF NOT EXISTS idx_batch_tracking_case_gtin ON batch_tracking(case_gtin);
CREATE INDEX IF NOT EXISTS idx_batch_tracking_gtin_barcode ON batch_tracking(gtin_barcode);
CREATE INDEX IF NOT EXISTS idx_batch_tracking_each_gtin ON batch_tracking(each_gtin);

-- Add comments for documentation
COMMENT ON COLUMN batch_tracking.case_gtin IS 'Global Trade Item Number for case packaging';
COMMENT ON COLUMN batch_tracking.packaged_on_date IS 'Date when the product was packaged';
COMMENT ON COLUMN batch_tracking.gtin_barcode IS 'GTIN barcode identifier for the batch';
COMMENT ON COLUMN batch_tracking.each_gtin IS 'Individual unit GTIN number';