-- Create location_access_log table
CREATE TABLE IF NOT EXISTS location_access_log (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    store_id UUID,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    accuracy DECIMAL(10, 2),
    ip_address VARCHAR(45),
    user_agent TEXT,
    access_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_location_access_log_user_id ON location_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_location_access_log_store_id ON location_access_log(store_id);
CREATE INDEX IF NOT EXISTS idx_location_access_log_created_at ON location_access_log(created_at);
CREATE INDEX IF NOT EXISTS idx_location_access_log_access_type ON location_access_log(access_type);