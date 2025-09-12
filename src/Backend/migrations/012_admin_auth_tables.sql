-- =====================================================
-- Admin Authentication Support Tables
-- =====================================================

-- 1. Login attempts table for rate limiting
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    success BOOLEAN NOT NULL DEFAULT false,
    ip_address VARCHAR(45),
    user_agent TEXT,
    failure_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for login attempts
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_created ON login_attempts(created_at);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);

-- Cleanup old login attempts (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS void AS $$
BEGIN
    DELETE FROM login_attempts
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 2. Audit log table for admin actions
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit log
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- 3. Add missing columns to user_sessions if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_sessions' 
                   AND column_name = 'refresh_token_hash') THEN
        ALTER TABLE user_sessions ADD COLUMN refresh_token_hash VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_sessions' 
                   AND column_name = 'remember_me') THEN
        ALTER TABLE user_sessions ADD COLUMN remember_me BOOLEAN DEFAULT false;
    END IF;
END $$;

-- 4. Create admin role check function
CREATE OR REPLACE FUNCTION user_has_admin_access(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN;
BEGIN
    -- Check system role
    SELECT EXISTS(
        SELECT 1 FROM users
        WHERE id = p_user_id
        AND role IN ('super_admin', 'admin', 'manager')
        AND active = true
    ) INTO has_access;
    
    IF has_access THEN
        RETURN true;
    END IF;
    
    -- Check tenant roles
    SELECT EXISTS(
        SELECT 1 FROM tenant_users
        WHERE user_id = p_user_id
        AND role IN ('owner', 'admin', 'manager')
        AND is_active = true
    ) INTO has_access;
    
    IF has_access THEN
        RETURN true;
    END IF;
    
    -- Check store roles
    SELECT EXISTS(
        SELECT 1 FROM store_users
        WHERE user_id = p_user_id
        AND role IN ('manager', 'supervisor')
        AND is_active = true
    ) INTO has_access;
    
    RETURN has_access;
END;
$$ LANGUAGE plpgsql;

-- 5. Create function to get user permissions
CREATE OR REPLACE FUNCTION get_user_permissions(p_user_id UUID)
RETURNS TABLE(permission TEXT) AS $$
BEGIN
    -- Get system permissions
    RETURN QUERY
    SELECT 'system:' || role::TEXT as permission
    FROM users
    WHERE id = p_user_id
    AND role IN ('super_admin', 'admin');
    
    -- Get tenant permissions
    RETURN QUERY
    SELECT 'tenant:' || tenant_id::TEXT || ':' || role::TEXT as permission
    FROM tenant_users
    WHERE user_id = p_user_id
    AND is_active = true;
    
    -- Get store permissions
    RETURN QUERY
    SELECT 'store:' || store_id::TEXT || ':' || role::TEXT as permission
    FROM store_users
    WHERE user_id = p_user_id
    AND is_active = true;
END;
$$ LANGUAGE plpgsql;

-- 6. Create default super admin if not exists
DO $$
DECLARE
    admin_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM users WHERE email = 'admin@potpalace.ca'
    ) INTO admin_exists;
    
    IF NOT admin_exists THEN
        INSERT INTO users (
            email,
            password_hash,
            first_name,
            last_name,
            role,
            active,
            email_verified,
            created_at
        ) VALUES (
            'admin@potpalace.ca',
            -- Password: Admin123!
            '$2b$12$KIXxPfL6GrXKxJFY7TOGneY3kH9FvNwxHYXpUqJFcVqNX0bqLZt9e',
            'System',
            'Administrator',
            'super_admin',
            true,
            true,
            CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE 'Default super admin created: admin@potpalace.ca / Admin123!';
    END IF;
END $$;

-- 7. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, active);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE role IN ('super_admin', 'admin', 'manager');

-- 8. Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON login_attempts TO weedgo;
GRANT SELECT, INSERT ON audit_log TO weedgo;
GRANT EXECUTE ON FUNCTION user_has_admin_access TO weedgo;
GRANT EXECUTE ON FUNCTION get_user_permissions TO weedgo;
GRANT EXECUTE ON FUNCTION cleanup_old_login_attempts TO weedgo;