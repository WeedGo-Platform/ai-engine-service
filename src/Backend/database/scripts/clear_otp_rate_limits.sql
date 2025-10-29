-- Clear OTP Rate Limits (Development/Testing Only)
-- Use this to reset rate limits during development when testing OTP functionality

-- Option 1: Clear all rate limits
TRUNCATE TABLE otp_rate_limits;

-- Option 2: Clear rate limit for specific identifier (safer for production-like testing)
-- DELETE FROM otp_rate_limits WHERE identifier = 'charrcy@yahoo.co.uk' AND identifier_type = 'email';

-- Option 3: Reset block time for all identifiers (keep request counts)
-- UPDATE otp_rate_limits SET blocked_until = NULL, request_count = 0;

-- View current rate limits
SELECT 
    identifier,
    identifier_type,
    request_count,
    first_request_at,
    last_request_at,
    blocked_until,
    CASE 
        WHEN blocked_until IS NOT NULL AND blocked_until > CURRENT_TIMESTAMP 
        THEN EXTRACT(EPOCH FROM (blocked_until - CURRENT_TIMESTAMP))::INTEGER
        ELSE 0
    END as seconds_until_unblock
FROM otp_rate_limits
ORDER BY last_request_at DESC;
