-- Add terms acceptance tracking columns to tenants table
-- Migration: add_terms_acceptance_columns
-- Date: 2025-10-31

ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS terms_accepted_version VARCHAR(50),
ADD COLUMN IF NOT EXISTS terms_accepted_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS terms_ip_address VARCHAR(45);

-- Add index for querying tenants by acceptance status
CREATE INDEX IF NOT EXISTS idx_tenants_terms_accepted_at ON tenants(terms_accepted_at);

-- Add comment for documentation
COMMENT ON COLUMN tenants.terms_accepted_at IS 'Timestamp when terms of service were accepted';
COMMENT ON COLUMN tenants.terms_accepted_version IS 'Version of terms accepted (e.g., "1.0")';
COMMENT ON COLUMN tenants.terms_accepted_by IS 'Email of person who accepted terms';
COMMENT ON COLUMN tenants.terms_ip_address IS 'IP address from which terms were accepted';
