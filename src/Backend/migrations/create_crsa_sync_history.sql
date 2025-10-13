-- Migration: Create CRSA Sync History Table
-- Date: 2025-10-13
-- Description: Tracks synchronization history for Ontario CRSA data

-- =====================================================
-- CRSA Sync History Table
-- =====================================================
CREATE TABLE IF NOT EXISTS crsa_sync_history (
    id SERIAL PRIMARY KEY,
    sync_date TIMESTAMP NOT NULL,
    success BOOLEAN NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    error_message TEXT,
    csv_source VARCHAR(500),
    duration_seconds DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for querying recent syncs
CREATE INDEX idx_crsa_sync_date ON crsa_sync_history(sync_date DESC);

-- Index for filtering by success/failure
CREATE INDEX idx_crsa_sync_success ON crsa_sync_history(success);

-- =====================================================
-- Sync Statistics View
-- =====================================================
CREATE OR REPLACE VIEW crsa_sync_statistics AS
SELECT
    COUNT(*) as total_syncs,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_syncs,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_syncs,
    MAX(sync_date) FILTER (WHERE success = TRUE) as last_successful_sync,
    MAX(sync_date) as last_sync_attempt,
    SUM(records_processed) as total_records_processed,
    AVG(duration_seconds) FILTER (WHERE success = TRUE) as avg_sync_duration_seconds
FROM crsa_sync_history
WHERE sync_date > NOW() - INTERVAL '30 days';

-- =====================================================
-- Comments
-- =====================================================
COMMENT ON TABLE crsa_sync_history IS
'Tracks synchronization history for Ontario CRSA data imports';

COMMENT ON COLUMN crsa_sync_history.sync_date IS
'Date and time when sync was performed';

COMMENT ON COLUMN crsa_sync_history.success IS
'Whether the sync completed successfully';

COMMENT ON COLUMN crsa_sync_history.records_processed IS
'Total number of records processed during sync';

-- =====================================================
-- Success Message
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ CRSA sync history table created successfully';
    RAISE NOTICE '📊 View: crsa_sync_statistics for 30-day metrics';
END $$;
