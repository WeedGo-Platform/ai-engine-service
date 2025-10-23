-- ============================================================================
-- OCS Integration Schema Migration
-- Description: Create tables for Ontario Cannabis Store regulatory reporting
-- Date: 2025-10-22
-- Requirements: AGCO/OCS compliance for cannabis retailers in Ontario
-- ============================================================================

BEGIN;

-- ============================================================================
-- Table 1: OCS OAuth Token Management
-- Purpose: Store OAuth access tokens with automatic refresh capability
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- OAuth Token Data (bcrypt encrypted)
    access_token_encrypted TEXT NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ NOT NULL,
    scope TEXT,
    
    -- OAuth Credentials (bcrypt encrypted)
    client_id_encrypted TEXT NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    token_url TEXT NOT NULL,
    
    -- API Configuration
    api_base_url TEXT NOT NULL,  -- UAT or PROD endpoint
    pos_vendor VARCHAR(100) DEFAULT 'WeedGo',
    pos_vendor_version VARCHAR(50) DEFAULT '1.0.0',
    
    -- Status & Metadata
    last_refreshed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    refresh_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_store_oauth UNIQUE (store_id)
);

CREATE INDEX idx_ocs_oauth_store ON ocs_oauth_tokens(store_id);
CREATE INDEX idx_ocs_oauth_expires ON ocs_oauth_tokens(expires_at) WHERE is_active = true;
CREATE INDEX idx_ocs_oauth_active ON ocs_oauth_tokens(is_active) WHERE is_active = true;

COMMENT ON TABLE ocs_oauth_tokens IS 'OAuth 2.0 access tokens for OCS API authentication per store';
COMMENT ON COLUMN ocs_oauth_tokens.access_token_encrypted IS 'bcrypt encrypted OAuth access token';
COMMENT ON COLUMN ocs_oauth_tokens.expires_at IS 'Token expiry timestamp for automatic refresh';

-- ============================================================================
-- Table 2: OCS Inventory Position Submission Log
-- Purpose: Track daily inventory snapshot submissions to OCS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_inventory_position_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Submission Details
    position_date DATE NOT NULL,
    position_timestamp TIMESTAMPTZ NOT NULL,
    submission_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- OCS Response
    ocs_reference_id VARCHAR(255),
    submission_status VARCHAR(50) DEFAULT 'pending',
    http_status_code INT,
    
    -- Payload Tracking
    total_items_count INT NOT NULL,
    payload_size_bytes INT,
    
    -- Error Handling
    error_message TEXT,
    error_code VARCHAR(100),
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    
    -- Performance Metrics
    processing_duration_ms INT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_store_position_date UNIQUE (store_id, position_date)
);

CREATE INDEX idx_ocs_pos_store ON ocs_inventory_position_log(store_id);
CREATE INDEX idx_ocs_pos_date ON ocs_inventory_position_log(position_date);
CREATE INDEX idx_ocs_pos_status ON ocs_inventory_position_log(submission_status);
CREATE INDEX idx_ocs_pos_retry ON ocs_inventory_position_log(next_retry_at) 
    WHERE submission_status = 'retrying';
CREATE INDEX idx_ocs_pos_failed ON ocs_inventory_position_log(store_id, submission_status) 
    WHERE submission_status IN ('failed', 'retrying');

COMMENT ON TABLE ocs_inventory_position_log IS 'Daily inventory position snapshot submissions to OCS';
COMMENT ON COLUMN ocs_inventory_position_log.submission_status IS 'Status: pending, success, failed, retrying';
COMMENT ON COLUMN ocs_inventory_position_log.ocs_reference_id IS 'OCS-provided reference ID for tracking';

-- ============================================================================
-- Table 3: OCS Inventory Event Submission Log
-- Purpose: Track individual inventory transaction submissions to OCS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_inventory_event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Link to Internal Transaction
    inventory_transaction_id UUID NOT NULL,
    
    -- Event Details
    ocs_sku VARCHAR(50) NOT NULL,
    upc_barcode VARCHAR(50),
    event_type VARCHAR(50) NOT NULL,
    quantity_change DECIMAL(10,2) NOT NULL,
    value_change DECIMAL(10,2),
    sold_at_price DECIMAL(10,2),
    counter_party_crsa VARCHAR(20),
    reason_category VARCHAR(255),
    
    -- Transaction IDs for OCS
    pos_transaction_id VARCHAR(255) NOT NULL,
    pos_transaction_line_id VARCHAR(255) NOT NULL,
    
    -- Timing
    event_timestamp TIMESTAMPTZ NOT NULL,
    submission_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- OCS Response
    ocs_reference_id VARCHAR(255),
    submission_status VARCHAR(50) DEFAULT 'pending',
    http_status_code INT,
    
    -- Error Handling
    error_message TEXT,
    error_code VARCHAR(100),
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    
    -- Performance Metrics
    processing_duration_ms INT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_event_store ON ocs_inventory_event_log(store_id);
CREATE INDEX idx_ocs_event_txn ON ocs_inventory_event_log(inventory_transaction_id);
CREATE INDEX idx_ocs_event_status ON ocs_inventory_event_log(submission_status);
CREATE INDEX idx_ocs_event_timestamp ON ocs_inventory_event_log(event_timestamp);
CREATE INDEX idx_ocs_event_retry ON ocs_inventory_event_log(next_retry_at) 
    WHERE submission_status = 'retrying';
CREATE INDEX idx_ocs_event_failed ON ocs_inventory_event_log(store_id, submission_status) 
    WHERE submission_status IN ('failed', 'retrying');

COMMENT ON TABLE ocs_inventory_event_log IS 'Real-time inventory transaction event submissions to OCS';
COMMENT ON COLUMN ocs_inventory_event_log.event_type IS 'OCS event types: PURCHASE, RECEIVING, ADJUSTMENT, TRANSFER_OUT, RETURN, DESTRUCTION';
COMMENT ON COLUMN ocs_inventory_event_log.inventory_transaction_id IS 'References inventory_transactions.id';

-- ============================================================================
-- Table 4: OCS Advanced Shipping Notice (ASN) Log
-- Purpose: Store incoming shipment notifications from OCS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_asn_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- ASN Details from OCS
    asn_number VARCHAR(100) NOT NULL,
    shipment_date DATE,
    expected_delivery_date DATE,
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    
    -- Line Items (JSONB array)
    line_items JSONB NOT NULL,
    
    -- Processing Status
    fetch_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'received',
    processed_at TIMESTAMPTZ,
    
    -- Integration with Purchase Orders
    purchase_order_id UUID,
    
    -- Summary
    total_items_count INT,
    total_value DECIMAL(10,2),
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_store_asn UNIQUE (store_id, asn_number)
);

CREATE INDEX idx_ocs_asn_store ON ocs_asn_log(store_id);
CREATE INDEX idx_ocs_asn_status ON ocs_asn_log(processing_status);
CREATE INDEX idx_ocs_asn_delivery ON ocs_asn_log(expected_delivery_date);
CREATE INDEX idx_ocs_asn_number ON ocs_asn_log(asn_number);
CREATE INDEX idx_ocs_asn_fetch ON ocs_asn_log(fetch_timestamp);

COMMENT ON TABLE ocs_asn_log IS 'Advanced Shipping Notices (ASN) from OCS for incoming inventory';
COMMENT ON COLUMN ocs_asn_log.line_items IS 'JSONB array of products: [{ocs_sku, quantity, unit_price, product_name}]';
COMMENT ON COLUMN ocs_asn_log.processing_status IS 'Status: received, processing, completed, error';

-- ============================================================================
-- Table 5: OCS Audit Log
-- Purpose: Comprehensive audit trail for all OCS API interactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Event Classification
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    
    -- Request Details
    request_method VARCHAR(10),
    request_url TEXT,
    request_payload_summary JSONB,
    
    -- Response Details
    response_status INT,
    response_reference_id VARCHAR(255),
    response_message TEXT,
    
    -- Timing & Performance
    request_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMPTZ,
    duration_ms INT,
    
    -- Result
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_code VARCHAR(100),
    
    -- User Context (for configuration changes)
    user_id UUID,
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    ip_address INET,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_audit_store ON ocs_audit_log(store_id);
CREATE INDEX idx_ocs_audit_tenant ON ocs_audit_log(tenant_id);
CREATE INDEX idx_ocs_audit_type ON ocs_audit_log(event_type);
CREATE INDEX idx_ocs_audit_category ON ocs_audit_log(event_category);
CREATE INDEX idx_ocs_audit_timestamp ON ocs_audit_log(request_timestamp);
CREATE INDEX idx_ocs_audit_success ON ocs_audit_log(success);
CREATE INDEX idx_ocs_audit_user ON ocs_audit_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_ocs_audit_failed ON ocs_audit_log(event_category, success) WHERE success = false;

COMMENT ON TABLE ocs_audit_log IS 'Complete audit trail for all OCS API interactions and configuration changes';
COMMENT ON COLUMN ocs_audit_log.event_category IS 'Categories: authentication, inventory, asn, configuration, error';
COMMENT ON COLUMN ocs_audit_log.event_type IS 'Types: oauth_refresh, position_submit, event_submit, asn_fetch, config_change';

-- ============================================================================
-- Table 6: OCS Catalog Sync Log
-- Purpose: Track OCS product catalog synchronization (GET Item Master API)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ocs_catalog_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Sync Details
    sync_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sync_type VARCHAR(50) DEFAULT 'full',
    
    -- Results
    total_products_fetched INT,
    new_products_added INT,
    products_updated INT,
    products_deactivated INT,
    
    -- Status
    sync_status VARCHAR(50) DEFAULT 'in_progress',
    start_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ,
    duration_seconds INT,
    
    -- Error Tracking
    error_message TEXT,
    failed_products JSONB,
    
    -- Metadata
    triggered_by VARCHAR(50),
    triggered_by_user_id UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_catalog_sync_timestamp ON ocs_catalog_sync_log(sync_timestamp);
CREATE INDEX idx_ocs_catalog_sync_status ON ocs_catalog_sync_log(sync_status);
CREATE INDEX idx_ocs_catalog_sync_type ON ocs_catalog_sync_log(sync_type);

COMMENT ON TABLE ocs_catalog_sync_log IS 'Track OCS product catalog synchronization via GET Item Master API';
COMMENT ON COLUMN ocs_catalog_sync_log.sync_type IS 'Types: full, incremental';
COMMENT ON COLUMN ocs_catalog_sync_log.triggered_by IS 'Source: cron, manual, api';

-- ============================================================================
-- Ensure Required Columns Exist in Existing Tables
-- ============================================================================

-- Add ocs_key to stores table if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stores' AND column_name = 'ocs_key'
    ) THEN
        ALTER TABLE stores ADD COLUMN ocs_key VARCHAR(255);
        CREATE INDEX idx_stores_ocs_key ON stores(ocs_key) WHERE ocs_key IS NOT NULL;
        COMMENT ON COLUMN stores.ocs_key IS 'OCS retailer hash key for API authentication';
    END IF;
END $$;

-- Add crol_number to tenants table if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tenants' AND column_name = 'crol_number'
    ) THEN
        ALTER TABLE tenants ADD COLUMN crol_number VARCHAR(50);
        CREATE INDEX idx_tenants_crol ON tenants(crol_number) WHERE crol_number IS NOT NULL;
        COMMENT ON COLUMN tenants.crol_number IS 'OCS CROL (Cannabis Retail Operating License) number';
    END IF;
END $$;

-- ============================================================================
-- Create Enum Type for OCS Event Types (for reference)
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ocs_event_type') THEN
        CREATE TYPE ocs_event_type AS ENUM (
            'PURCHASE',      -- Customer purchase (sale)
            'RECEIVING',     -- Receiving from supplier (purchase)
            'ADJUSTMENT',    -- Inventory count adjustment
            'TRANSFER_OUT',  -- Transfer to another store
            'RETURN',        -- Customer return
            'DESTRUCTION'    -- Damaged/destroyed product
        );
    END IF;
END $$;

COMMENT ON TYPE ocs_event_type IS 'OCS inventory event types as per AGCO regulatory requirements';

-- ============================================================================
-- Create Updated At Triggers
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all OCS tables
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
-- Grant Permissions
-- ============================================================================

-- Grant access to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON 
    ocs_oauth_tokens,
    ocs_inventory_position_log,
    ocs_inventory_event_log,
    ocs_asn_log,
    ocs_audit_log,
    ocs_catalog_sync_log
TO weedgo;

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables created
SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE 'ocs_%' 
ORDER BY tablename;

-- Verify indexes created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename LIKE 'ocs_%' 
ORDER BY tablename, indexname;
