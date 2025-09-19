-- Consolidate Authentication Token Tables
-- Merges email_verification_tokens, password_reset_tokens, and refresh_tokens into unified auth_tokens

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Create unified auth_tokens table
-- =========================================

CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL CHECK (token_type IN ('email_verification', 'password_reset', 'refresh', 'api_key')),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    UNIQUE(token_hash)
);

-- Create indexes for performance
CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_token_type ON auth_tokens(token_type);
CREATE INDEX idx_auth_tokens_expires_at ON auth_tokens(expires_at);
CREATE INDEX idx_auth_tokens_token_hash ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_type_user ON auth_tokens(token_type, user_id);

-- =========================================
-- STEP 2: Migrate data from existing tables
-- =========================================

-- Migrate email verification tokens
INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, is_used, metadata, created_at, used_at)
SELECT
    user_id,
    'email_verification' as token_type,
    token as token_hash,
    expires_at,
    verified as is_used,
    jsonb_build_object(
        'email', email,
        'verified', verified
    ) as metadata,
    created_at,
    CASE WHEN verified = true THEN created_at ELSE NULL END as used_at
FROM email_verification_tokens;

-- Migrate password reset tokens
INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, is_used, metadata, created_at, used_at)
SELECT
    user_id,
    'password_reset' as token_type,
    token as token_hash,
    expires_at,
    used as is_used,
    jsonb_build_object(
        'used', used
    ) as metadata,
    created_at,
    CASE WHEN used = true THEN created_at ELSE NULL END as used_at
FROM password_reset_tokens;

-- Migrate refresh tokens
INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, is_used, metadata, created_at, used_at)
SELECT
    user_id,
    'refresh' as token_type,
    token_hash,
    expires_at,
    false as is_used,
    jsonb_build_object(
        'ip_address', ip_address,
        'user_agent', user_agent,
        'last_used', last_used
    ) as metadata,
    created_at,
    last_used as used_at
FROM refresh_tokens;

-- =========================================
-- STEP 3: Create helper views for backward compatibility
-- =========================================

-- View for email verification tokens
CREATE OR REPLACE VIEW email_verification_tokens_view AS
SELECT
    id,
    user_id,
    metadata->>'email' as email,
    token_hash as token,
    expires_at,
    is_used as verified,
    created_at
FROM auth_tokens
WHERE token_type = 'email_verification';

-- View for password reset tokens
CREATE OR REPLACE VIEW password_reset_tokens_view AS
SELECT
    id,
    user_id,
    token_hash as token,
    expires_at,
    is_used as used,
    created_at
FROM auth_tokens
WHERE token_type = 'password_reset';

-- View for refresh tokens
CREATE OR REPLACE VIEW refresh_tokens_view AS
SELECT
    id,
    user_id,
    token_hash,
    expires_at,
    created_at,
    used_at as last_used,
    metadata->>'ip_address' as ip_address,
    metadata->>'user_agent' as user_agent
FROM auth_tokens
WHERE token_type = 'refresh';

-- =========================================
-- STEP 4: Create helper functions
-- =========================================

-- Function to create auth token
CREATE OR REPLACE FUNCTION create_auth_token(
    p_user_id UUID,
    p_token_type VARCHAR(50),
    p_token_hash VARCHAR(255),
    p_expires_in_hours INTEGER DEFAULT 24,
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    v_token_id UUID;
BEGIN
    INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, metadata)
    VALUES (
        p_user_id,
        p_token_type,
        p_token_hash,
        CURRENT_TIMESTAMP + (p_expires_in_hours || ' hours')::INTERVAL,
        p_metadata
    )
    RETURNING id INTO v_token_id;

    RETURN v_token_id;
END;
$$ LANGUAGE plpgsql;

-- Function to validate and use token
CREATE OR REPLACE FUNCTION validate_auth_token(
    p_token_hash VARCHAR(255),
    p_token_type VARCHAR(50),
    p_mark_as_used BOOLEAN DEFAULT false
) RETURNS TABLE (
    is_valid BOOLEAN,
    user_id UUID,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH token_check AS (
        SELECT
            at.user_id,
            at.metadata,
            at.expires_at > CURRENT_TIMESTAMP AND at.is_used = false as valid
        FROM auth_tokens at
        WHERE at.token_hash = p_token_hash
        AND at.token_type = p_token_type
    )
    SELECT
        COALESCE(tc.valid, false) as is_valid,
        tc.user_id,
        tc.metadata
    FROM token_check tc;

    -- Mark token as used if requested and valid
    IF p_mark_as_used THEN
        UPDATE auth_tokens
        SET is_used = true, used_at = CURRENT_TIMESTAMP
        WHERE token_hash = p_token_hash
        AND token_type = p_token_type
        AND expires_at > CURRENT_TIMESTAMP
        AND is_used = false;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens() RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM auth_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
    OR (is_used = true AND used_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- STEP 5: Drop old tables
-- =========================================

DROP TABLE IF EXISTS email_verification_tokens CASCADE;
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS refresh_tokens CASCADE;

-- =========================================
-- VERIFICATION
-- =========================================
DO $$
DECLARE
    token_count INTEGER;
    email_count INTEGER;
    password_count INTEGER;
    refresh_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO token_count FROM auth_tokens;
    SELECT COUNT(*) INTO email_count FROM auth_tokens WHERE token_type = 'email_verification';
    SELECT COUNT(*) INTO password_count FROM auth_tokens WHERE token_type = 'password_reset';
    SELECT COUNT(*) INTO refresh_count FROM auth_tokens WHERE token_type = 'refresh';

    RAISE NOTICE 'Token consolidation complete!';
    RAISE NOTICE 'Total tokens migrated: %', token_count;
    RAISE NOTICE '  - Email verification: %', email_count;
    RAISE NOTICE '  - Password reset: %', password_count;
    RAISE NOTICE '  - Refresh tokens: %', refresh_count;
END $$;

COMMIT;