-- Add response cache table for database-level caching

-- Create response cache table
CREATE TABLE IF NOT EXISTS agi.response_cache (
    key VARCHAR(64) PRIMARY KEY,
    value BYTEA NOT NULL,
    tags TEXT[] DEFAULT '{}',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_response_cache_expires ON agi.response_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_response_cache_tags ON agi.response_cache USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_response_cache_created ON agi.response_cache(created_at);

-- Create cleanup function for expired entries
CREATE OR REPLACE FUNCTION agi.cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agi.response_cache
    WHERE expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic cleanup (requires pg_cron extension)
-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('cleanup-cache', '0 * * * *', 'SELECT agi.cleanup_expired_cache();');