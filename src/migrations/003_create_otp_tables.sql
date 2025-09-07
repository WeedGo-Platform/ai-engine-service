-- OTP Authentication Tables
-- Migration: 003_create_otp_tables.sql

-- OTP codes table for storing temporary one-time passcodes
CREATE TABLE IF NOT EXISTS otp_codes (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    identifier VARCHAR(255) NOT NULL, -- email or phone number
    identifier_type VARCHAR(20) NOT NULL, -- 'email' or 'phone'
    code VARCHAR(10) NOT NULL,
    purpose VARCHAR(50) NOT NULL, -- 'login', 'verification', 'password_reset'
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    expires_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for OTP lookups
CREATE INDEX idx_otp_codes_identifier ON otp_codes(identifier);
CREATE INDEX idx_otp_codes_code ON otp_codes(code);
CREATE INDEX idx_otp_codes_expires_at ON otp_codes(expires_at);
CREATE INDEX idx_otp_codes_user_id ON otp_codes(user_id);

-- OTP rate limiting table
CREATE TABLE IF NOT EXISTS otp_rate_limits (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(20) NOT NULL,
    request_count INTEGER DEFAULT 1,
    first_request_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_request_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for rate limiting
CREATE UNIQUE INDEX idx_otp_rate_limits_identifier ON otp_rate_limits(identifier, identifier_type);
CREATE INDEX idx_otp_rate_limits_blocked_until ON otp_rate_limits(blocked_until);

-- Communication logs table for tracking sent OTPs
CREATE TABLE IF NOT EXISTS communication_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    recipient VARCHAR(255) NOT NULL,
    communication_type VARCHAR(20) NOT NULL, -- 'sms' or 'email'
    provider VARCHAR(50), -- 'twilio', 'sendgrid'
    subject VARCHAR(255),
    content TEXT,
    status VARCHAR(50) NOT NULL, -- 'pending', 'sent', 'delivered', 'failed'
    provider_message_id VARCHAR(255),
    provider_response JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Index for communication logs
CREATE INDEX idx_communication_logs_user_id ON communication_logs(user_id);
CREATE INDEX idx_communication_logs_recipient ON communication_logs(recipient);
CREATE INDEX idx_communication_logs_status ON communication_logs(status);
CREATE INDEX idx_communication_logs_created_at ON communication_logs(created_at);

-- Function to clean up expired OTP codes
CREATE OR REPLACE FUNCTION cleanup_expired_otp_codes()
RETURNS void AS $$
BEGIN
    DELETE FROM otp_codes 
    WHERE expires_at < CURRENT_TIMESTAMP 
    AND verified = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to check OTP rate limits
CREATE OR REPLACE FUNCTION check_otp_rate_limit(
    p_identifier VARCHAR(255),
    p_identifier_type VARCHAR(20),
    p_max_requests INTEGER DEFAULT 5,
    p_window_minutes INTEGER DEFAULT 60
)
RETURNS BOOLEAN AS $$
DECLARE
    v_rate_limit RECORD;
    v_window_start TIMESTAMP;
BEGIN
    v_window_start := CURRENT_TIMESTAMP - (p_window_minutes || ' minutes')::INTERVAL;
    
    -- Get or create rate limit record
    SELECT * INTO v_rate_limit
    FROM otp_rate_limits
    WHERE identifier = p_identifier 
    AND identifier_type = p_identifier_type;
    
    -- If blocked, check if block has expired
    IF v_rate_limit.blocked_until IS NOT NULL AND v_rate_limit.blocked_until > CURRENT_TIMESTAMP THEN
        RETURN FALSE;
    END IF;
    
    -- If no record exists, create one
    IF v_rate_limit.id IS NULL THEN
        INSERT INTO otp_rate_limits (identifier, identifier_type)
        VALUES (p_identifier, p_identifier_type);
        RETURN TRUE;
    END IF;
    
    -- Reset counter if outside window
    IF v_rate_limit.first_request_at < v_window_start THEN
        UPDATE otp_rate_limits
        SET request_count = 1,
            first_request_at = CURRENT_TIMESTAMP,
            last_request_at = CURRENT_TIMESTAMP,
            blocked_until = NULL
        WHERE id = v_rate_limit.id;
        RETURN TRUE;
    END IF;
    
    -- Check if limit exceeded
    IF v_rate_limit.request_count >= p_max_requests THEN
        -- Block for progressive duration
        UPDATE otp_rate_limits
        SET blocked_until = CURRENT_TIMESTAMP + (POWER(2, LEAST(v_rate_limit.request_count - p_max_requests + 1, 5)) || ' minutes')::INTERVAL
        WHERE id = v_rate_limit.id;
        RETURN FALSE;
    END IF;
    
    -- Increment counter
    UPDATE otp_rate_limits
    SET request_count = request_count + 1,
        last_request_at = CURRENT_TIMESTAMP
    WHERE id = v_rate_limit.id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;