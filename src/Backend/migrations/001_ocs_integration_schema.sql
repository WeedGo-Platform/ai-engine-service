-- OCS Integration Database Schema Migration
-- Migration: 001_ocs_integration_schema.sql
-- Date: 2025-10-22
-- Purpose: Add tables for Ontario Cannabis Store regulatory compliance integration

-- ============================================================================
-- 1. OCS OAuth Tokens Table
-- ============================================================================
-- Stores encrypted OAuth 2.0 credentials and tokens for OCS API authentication
CREATE TABLE IF NOT EXISTS ocs_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Encrypted credentials (using bcrypt pattern)
    client_id_encrypted TEXT NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    
    -- OAuth tokens
    access_token_encrypted TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    refresh_token_encrypted TEXT,
    
    -- Metadata
    scope TEXT,
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one credential set per store
    UNIQUE(store_id)
);

CREATE INDEX idx_ocs_oauth_tokens_tenant ON ocs_oauth_tokens(tenant_id);
CREATE INDEX idx_ocs_oauth_tokens_store ON ocs_oauth_tokens(store_id);
CREATE INDEX idx_ocs_oauth_tokens_expires_at ON ocs_oauth_tokens(expires_at);

-- ============================================================================
-- 2. OCS Inventory Position Log Table
-- ============================================================================
-- Tracks daily inventory position snapshots submitted to OCS
CREATE TABLE IF NOT EXISTS ocs_inventory_position_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Snapshot details
    snapshot_date DATE NOT NULL,
    total_items INTEGER NOT NULL DEFAULT 0,
    
    -- Submission tracking
    submitted_at TIMESTAMPTZ,
    ocs_response_code VARCHAR(10),
    ocs_transaction_id VARCHAR(255),
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status values: pending, submitted, accepted, failed, retrying
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- One snapshot per store per date
    UNIQUE(store_id, snapshot_date)
);

CREATE INDEX idx_ocs_position_log_tenant ON ocs_inventory_position_log(tenant_id);
CREATE INDEX idx_ocs_position_log_store ON ocs_inventory_position_log(store_id);
CREATE INDEX idx_ocs_position_log_date ON ocs_inventory_position_log(snapshot_date);
CREATE INDEX idx_ocs_position_log_status ON ocs_inventory_position_log(status);
CREATE INDEX idx_ocs_position_log_submitted ON ocs_inventory_position_log(submitted_at);

-- ============================================================================
-- 3. OCS Inventory Event Log Table
-- ============================================================================
-- Tracks real-time inventory transactions submitted to OCS
CREATE TABLE IF NOT EXISTS ocs_inventory_event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Transaction reference
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    internal_transaction_type VARCHAR(50) NOT NULL,
    -- Internal types: sale, purchase, adjustment, transfer, return, damage
    
    -- OCS mapping
    ocs_event_type VARCHAR(50) NOT NULL,
    -- OCS types: PURCHASE, RECEIVING, ADJUSTMENT, TRANSFER_OUT, RETURN, DESTRUCTION
    ocs_sku VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    
    -- Event details
    event_date TIMESTAMPTZ NOT NULL,
    
    -- Submission tracking
    submitted_at TIMESTAMPTZ,
    ocs_response_code VARCHAR(10),
    ocs_event_id VARCHAR(255),
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status values: pending, submitted, accepted, failed, retrying
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ocs_event_log_tenant ON ocs_inventory_event_log(tenant_id);
CREATE INDEX idx_ocs_event_log_store ON ocs_inventory_event_log(store_id);
CREATE INDEX idx_ocs_event_log_transaction ON ocs_inventory_event_log(transaction_id);
CREATE INDEX idx_ocs_event_log_status ON ocs_inventory_event_log(status);
CREATE INDEX idx_ocs_event_log_event_date ON ocs_inventory_event_log(event_date);
CREATE INDEX idx_ocs_event_log_submitted ON ocs_inventory_event_log(submitted_at);
CREATE INDEX idx_ocs_event_log_ocs_sku ON ocs_inventory_event_log(ocs_sku);

-- ============================================================================
-- 4. OCS ASN (Advanced Shipping Notice) Log Table
-- ============================================================================
-- Stores shipping notices received from OCS
CREATE TABLE IF NOT EXISTS ocs_asn_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- ASN details from OCS
    ocs_asn_id VARCHAR(255) NOT NULL,
    ocs_po_number VARCHAR(255),
    expected_delivery_date DATE,
    
    -- Shipping details
    carrier VARCHAR(255),
    tracking_number VARCHAR(255),
    
    -- Items (stored as JSONB for flexibility)
    items JSONB NOT NULL DEFAULT '[]',
    -- Structure: [{"ocs_sku": "...", "quantity": 10, "lot_number": "..."}]
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status values: pending, received, partially_received, cancelled
    received_at TIMESTAMPTZ,
    
    -- Audit
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate ASNs
    UNIQUE(ocs_asn_id, store_id)
);

CREATE INDEX idx_ocs_asn_log_tenant ON ocs_asn_log(tenant_id);
CREATE INDEX idx_ocs_asn_log_store ON ocs_asn_log(store_id);
CREATE INDEX idx_ocs_asn_log_ocs_asn_id ON ocs_asn_log(ocs_asn_id);
CREATE INDEX idx_ocs_asn_log_status ON ocs_asn_log(status);
CREATE INDEX idx_ocs_asn_log_expected_date ON ocs_asn_log(expected_delivery_date);
CREATE INDEX idx_ocs_asn_log_items_gin ON ocs_asn_log USING gin(items);

-- ============================================================================
-- 5. OCS Audit Log Table
-- ============================================================================
-- Comprehensive audit trail of all OCS API interactions
CREATE TABLE IF NOT EXISTS ocs_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    
    -- API interaction details
    api_endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    
    -- Request/Response
    request_payload JSONB,
    response_payload JSONB,
    response_code INTEGER,
    
    -- Status
    status VARCHAR(50) NOT NULL,
    -- Status values: success, error, timeout, retry
    error_message TEXT,
    
    -- Performance
    duration_ms INTEGER,
    
    -- Context
    initiated_by VARCHAR(100),
    -- Values: system, user:{user_id}, worker:{worker_name}
    correlation_id UUID,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ocs_audit_log_tenant ON ocs_audit_log(tenant_id);
CREATE INDEX idx_ocs_audit_log_store ON ocs_audit_log(store_id);
CREATE INDEX idx_ocs_audit_log_endpoint ON ocs_audit_log(api_endpoint);
CREATE INDEX idx_ocs_audit_log_status ON ocs_audit_log(status);
CREATE INDEX idx_ocs_audit_log_created_at ON ocs_audit_log(created_at DESC);
CREATE INDEX idx_ocs_audit_log_correlation_id ON ocs_audit_log(correlation_id);

-- ============================================================================
-- 6. OCS Catalog Sync Log Table
-- ============================================================================
-- Tracks synchronization of OCS product catalog
CREATE TABLE IF NOT EXISTS ocs_catalog_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Sync details
    sync_type VARCHAR(50) NOT NULL,
    -- Sync types: full, incremental, manual
    
    -- Results
    total_items_fetched INTEGER DEFAULT 0,
    items_created INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    -- Status values: in_progress, completed, failed, partial
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Audit
    initiated_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ocs_catalog_sync_tenant ON ocs_catalog_sync_log(tenant_id);
CREATE INDEX idx_ocs_catalog_sync_status ON ocs_catalog_sync_log(status);
CREATE INDEX idx_ocs_catalog_sync_started ON ocs_catalog_sync_log(started_at DESC);
CREATE INDEX idx_ocs_catalog_sync_type ON ocs_catalog_sync_log(sync_type);

-- ============================================================================
-- Verify Existing Columns in Stores and Tenants Tables
-- ============================================================================
-- Note: These columns should already exist. This migration does NOT create them.
-- stores.ocs_key VARCHAR(255) - Store's OCS hash key
-- stores.license_number VARCHAR(100) - Store's CRSA license number
-- tenants.crol_number VARCHAR(100) - Tenant's CROL number

-- ============================================================================
-- Update Triggers for updated_at Columns
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_ocs_oauth_tokens_updated_at
    BEFORE UPDATE ON ocs_oauth_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ocs_inventory_position_log_updated_at
    BEFORE UPDATE ON ocs_inventory_position_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ocs_inventory_event_log_updated_at
    BEFORE UPDATE ON ocs_inventory_event_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ocs_asn_log_updated_at
    BEFORE UPDATE ON ocs_asn_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE ocs_oauth_tokens IS 'OAuth 2.0 credentials and tokens for OCS API authentication';
COMMENT ON TABLE ocs_inventory_position_log IS 'Daily inventory position snapshots submitted to OCS';
COMMENT ON TABLE ocs_inventory_event_log IS 'Real-time inventory transaction events submitted to OCS';
COMMENT ON TABLE ocs_asn_log IS 'Advanced Shipping Notices received from OCS';
COMMENT ON TABLE ocs_audit_log IS 'Comprehensive audit trail of all OCS API interactions';
COMMENT ON TABLE ocs_catalog_sync_log IS 'Product catalog synchronization tracking';

-- ============================================================================
-- Migration Complete
-- ============================================================================
