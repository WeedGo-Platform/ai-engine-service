-- User Login Tracking Table
-- Tracks user login attempts with IP and location information

CREATE TABLE IF NOT EXISTS user_login_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Login details
    login_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    login_successful BOOLEAN NOT NULL DEFAULT true,
    login_method VARCHAR(50) DEFAULT 'password', -- password, oauth, sso, api_key
    
    -- IP and location tracking
    ip_address INET,
    user_agent TEXT,
    
    -- Location information (from IP geolocation)
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(50),
    isp VARCHAR(200),
    
    -- Security information
    device_fingerprint VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_user_login_logs_user_id ON user_login_logs(user_id);
CREATE INDEX idx_user_login_logs_tenant_id ON user_login_logs(tenant_id);
CREATE INDEX idx_user_login_logs_timestamp ON user_login_logs(login_timestamp DESC);
CREATE INDEX idx_user_login_logs_ip_address ON user_login_logs(ip_address);
CREATE INDEX idx_user_login_logs_session_id ON user_login_logs(session_id);

-- Add last_login_ip and last_login_at to users table if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip INET;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_location JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- Create a function to update user's last login info
CREATE OR REPLACE FUNCTION update_user_last_login()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.login_successful = true THEN
        UPDATE users 
        SET 
            last_login_ip = NEW.ip_address,
            last_login_at = NEW.login_timestamp,
            last_login_location = jsonb_build_object(
                'country', NEW.country,
                'region', NEW.region,
                'city', NEW.city,
                'postal_code', NEW.postal_code,
                'latitude', NEW.latitude,
                'longitude', NEW.longitude,
                'timezone', NEW.timezone,
                'isp', NEW.isp
            ),
            login_count = COALESCE(login_count, 0) + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update user's last login info
DROP TRIGGER IF EXISTS trigger_update_user_last_login ON user_login_logs;
CREATE TRIGGER trigger_update_user_last_login
AFTER INSERT ON user_login_logs
FOR EACH ROW
EXECUTE FUNCTION update_user_last_login();

-- Create view for recent login activity
CREATE OR REPLACE VIEW recent_login_activity AS
SELECT 
    ull.id,
    ull.user_id,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    ull.tenant_id,
    t.name as tenant_name,
    ull.login_timestamp,
    ull.login_successful,
    ull.login_method,
    ull.ip_address,
    ull.country,
    ull.city,
    ull.user_agent
FROM user_login_logs ull
JOIN users u ON ull.user_id = u.id
LEFT JOIN tenants t ON ull.tenant_id = t.id
WHERE ull.login_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY ull.login_timestamp DESC;

-- Function to get user's login statistics
CREATE OR REPLACE FUNCTION get_user_login_stats(p_user_id UUID)
RETURNS TABLE (
    total_logins INTEGER,
    successful_logins INTEGER,
    failed_logins INTEGER,
    unique_ips INTEGER,
    unique_countries INTEGER,
    last_login TIMESTAMP WITH TIME ZONE,
    most_common_ip INET,
    most_common_country VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_logins,
        COUNT(*) FILTER (WHERE login_successful = true)::INTEGER as successful_logins,
        COUNT(*) FILTER (WHERE login_successful = false)::INTEGER as failed_logins,
        COUNT(DISTINCT ip_address)::INTEGER as unique_ips,
        COUNT(DISTINCT country)::INTEGER as unique_countries,
        MAX(login_timestamp) as last_login,
        MODE() WITHIN GROUP (ORDER BY ip_address) as most_common_ip,
        MODE() WITHIN GROUP (ORDER BY country) as most_common_country
    FROM user_login_logs
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Add comment to the table
COMMENT ON TABLE user_login_logs IS 'Tracks all user login attempts with IP address and geolocation information for security and analytics';