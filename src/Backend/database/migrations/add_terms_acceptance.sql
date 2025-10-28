-- Migration: Add Terms of Service Acceptance Tracking
-- Date: 2025-10-28
-- Description: Add columns to track when and by whom terms were accepted

-- Add terms acceptance tracking columns to tenants table
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS terms_accepted_version VARCHAR(50) DEFAULT '1.0',
ADD COLUMN IF NOT EXISTS terms_accepted_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS terms_ip_address INET;

-- Add comments for documentation
COMMENT ON COLUMN tenants.terms_accepted_at IS 'Timestamp when the terms of service were accepted during signup';
COMMENT ON COLUMN tenants.terms_accepted_version IS 'Version of the terms accepted (e.g., "1.0", "2025-10-28")';
COMMENT ON COLUMN tenants.terms_accepted_by IS 'Email of the authorized person who accepted the terms on behalf of the organization';
COMMENT ON COLUMN tenants.terms_ip_address IS 'IP address from which terms were accepted for audit trail';

-- Create index for querying by acceptance date
CREATE INDEX IF NOT EXISTS idx_tenants_terms_accepted_at ON tenants(terms_accepted_at);

-- Add check constraint to ensure terms_accepted_at is set for new tenants
-- Note: Existing tenants without acceptance timestamp are grandfathered in
ALTER TABLE tenants 
ADD CONSTRAINT chk_terms_acceptance 
CHECK (
    (created_at < '2025-10-28' AND terms_accepted_at IS NULL) OR 
    (created_at >= '2025-10-28' AND terms_accepted_at IS NOT NULL)
);
