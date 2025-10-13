-- Migration: Create Ontario CRSA Status Table
-- Date: 2025-10-13
-- Description: Creates table for tracking Ontario Cannabis Retail Store Authorization status
--              Used for tenant validation and auto-fill during signup

-- =====================================================
-- Main CRSA Status Table
-- =====================================================
CREATE TABLE IF NOT EXISTS ontario_crsa_status (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- AGCO Data Fields (from CSV)
    license_number VARCHAR(50) UNIQUE NOT NULL,
    municipality VARCHAR(100),
    first_nation VARCHAR(100),
    store_name VARCHAR(200) NOT NULL,
    address TEXT NOT NULL,
    store_application_status VARCHAR(50) NOT NULL,
    website VARCHAR(500),

    -- Enrichment Fields (our additions)
    linked_tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    verification_status VARCHAR(20) DEFAULT 'unverified',
    verification_date TIMESTAMP,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    admin_notes TEXT,

    -- Sync Tracking
    data_source VARCHAR(50) DEFAULT 'agco_csv',
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (store_application_status IN
        ('Authorized', 'Pending', 'Rejected', 'Withdrawn', 'Cancelled', 'Revoked'))
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Primary lookup by license number
CREATE INDEX idx_crsa_license ON ontario_crsa_status(license_number);

-- Search by store name (supports ILIKE queries)
CREATE INDEX idx_crsa_store_name ON ontario_crsa_status(LOWER(store_name));

-- Filter by status
CREATE INDEX idx_crsa_status ON ontario_crsa_status(store_application_status);

-- Lookup stores linked to tenants
CREATE INDEX idx_crsa_tenant ON ontario_crsa_status(linked_tenant_id);

-- Search by municipality
CREATE INDEX idx_crsa_municipality ON ontario_crsa_status(LOWER(municipality));

-- Active stores only (most common query)
CREATE INDEX idx_crsa_active ON ontario_crsa_status(is_active) WHERE is_active = TRUE;

-- Composite index for authorized stores
CREATE INDEX idx_crsa_authorized ON ontario_crsa_status(store_application_status, is_active)
    WHERE store_application_status = 'Authorized' AND is_active = TRUE;

-- Full-text search on store name and address (optional but useful)
CREATE INDEX idx_crsa_search ON ontario_crsa_status
    USING gin(to_tsvector('english', store_name || ' ' || COALESCE(address, '')));

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_crsa_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_crsa_updated_at
    BEFORE UPDATE ON ontario_crsa_status
    FOR EACH ROW
    EXECUTE FUNCTION update_crsa_updated_at();

-- Function to search stores by name with fuzzy matching
CREATE OR REPLACE FUNCTION search_crsa_stores(
    search_term TEXT,
    limit_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    license_number VARCHAR,
    store_name VARCHAR,
    address TEXT,
    municipality VARCHAR,
    store_application_status VARCHAR,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.license_number,
        c.store_name,
        c.address,
        c.municipality,
        c.store_application_status,
        similarity(c.store_name, search_term) as similarity_score
    FROM ontario_crsa_status c
    WHERE
        c.is_active = TRUE
        AND (
            LOWER(c.store_name) LIKE LOWER('%' || search_term || '%')
            OR LOWER(c.address) LIKE LOWER('%' || search_term || '%')
            OR similarity(c.store_name, search_term) > 0.3
        )
    ORDER BY similarity_score DESC, c.store_name
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Enable pg_trgm extension for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- View for authorized stores only
CREATE OR REPLACE VIEW authorized_crsa_stores AS
SELECT
    id,
    license_number,
    store_name,
    address,
    municipality,
    first_nation,
    website,
    linked_tenant_id,
    verification_status,
    last_synced_at
FROM ontario_crsa_status
WHERE store_application_status = 'Authorized'
  AND is_active = TRUE;

-- View for stores pending tenant signup
CREATE OR REPLACE VIEW unlinked_authorized_stores AS
SELECT
    id,
    license_number,
    store_name,
    address,
    municipality,
    store_application_status,
    first_seen_at
FROM ontario_crsa_status
WHERE store_application_status = 'Authorized'
  AND is_active = TRUE
  AND linked_tenant_id IS NULL;

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE ontario_crsa_status IS
'Tracks Ontario Cannabis Retail Store Authorization (CRSA) data from AGCO. Used for tenant validation and auto-fill during signup.';

COMMENT ON COLUMN ontario_crsa_status.license_number IS
'Unique AGCO license number (e.g., LCBO-1234). Primary identifier for validation.';

COMMENT ON COLUMN ontario_crsa_status.store_application_status IS
'Current status from AGCO: Authorized, Pending, Rejected, Withdrawn, Cancelled, or Revoked';

COMMENT ON COLUMN ontario_crsa_status.linked_tenant_id IS
'Foreign key to tenants table. Set when a tenant signs up using this license.';

COMMENT ON COLUMN ontario_crsa_status.verification_status IS
'Internal verification status: unverified, verified, flagged, or rejected';

COMMENT ON COLUMN ontario_crsa_status.last_synced_at IS
'Timestamp of last sync from AGCO CSV. Used to track data freshness.';

-- =====================================================
-- Initial Statistics View
-- =====================================================

CREATE OR REPLACE VIEW crsa_statistics AS
SELECT
    COUNT(*) as total_stores,
    COUNT(*) FILTER (WHERE store_application_status = 'Authorized') as authorized_count,
    COUNT(*) FILTER (WHERE store_application_status = 'Pending') as pending_count,
    COUNT(*) FILTER (WHERE store_application_status = 'Rejected') as rejected_count,
    COUNT(*) FILTER (WHERE linked_tenant_id IS NOT NULL) as signed_up_count,
    COUNT(*) FILTER (WHERE store_application_status = 'Authorized' AND linked_tenant_id IS NULL) as available_for_signup,
    MAX(last_synced_at) as last_sync_time,
    COUNT(DISTINCT municipality) as municipality_count
FROM ontario_crsa_status
WHERE is_active = TRUE;

-- =====================================================
-- Success Message
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration completed: ontario_crsa_status table created';
    RAISE NOTICE '📊 Indexes: 8 indexes created for optimized queries';
    RAISE NOTICE '🔍 Functions: search_crsa_stores() for fuzzy matching';
    RAISE NOTICE '👁️ Views: authorized_crsa_stores, unlinked_authorized_stores, crsa_statistics';
    RAISE NOTICE '🔄 Triggers: Auto-update updated_at timestamp';
    RAISE NOTICE '📝 Next step: Import CSV data using import_crsa_data.py';
END $$;
