-- Create API keys table for authentication
-- This table stores hashed API keys for secure authentication

-- Create API keys table
CREATE TABLE IF NOT EXISTS agi.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA256 hash of the API key
    user_id VARCHAR(255) NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '["read"]'::jsonb,
    rate_limit INTEGER DEFAULT 60, -- requests per minute
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON agi.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON agi.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON agi.api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON agi.api_keys(expires_at);

-- Create API key usage tracking table
CREATE TABLE IF NOT EXISTS agi.api_key_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_id UUID REFERENCES agi.api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create index for usage queries
CREATE INDEX IF NOT EXISTS idx_api_key_usage_key_id ON agi.api_key_usage(key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_request_time ON agi.api_key_usage(request_time);

-- Function to clean up expired keys
CREATE OR REPLACE FUNCTION agi.cleanup_expired_api_keys()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agi.api_keys
    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Insert a default API key for testing (in production, generate these securely)
-- This is the hash of "agi_test_key_123"
INSERT INTO agi.api_keys (
    key_hash,
    user_id,
    key_name,
    description,
    permissions,
    rate_limit
) VALUES (
    SHA256('agi_test_key_123'::bytea)::text,
    'system',
    'test_key',
    'Default test API key',
    '["read", "write", "admin"]'::jsonb,
    1000
) ON CONFLICT (key_hash) DO NOTHING;