-- ============================================================================
-- Migration: Create Communication, Translation, Auth & Audit Tables
-- Description: Final set of tables for communication, i18n, security, audit
-- Dependencies: 010_create_reviews_ai_tables.sql
-- ============================================================================

-- ===========================
-- COMMUNICATION & MARKETING TABLES
-- ===========================

-- Broadcasts
CREATE TABLE IF NOT EXISTS broadcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    campaign_name VARCHAR(255) NOT NULL,
    broadcast_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP WITHOUT TIME ZONE,
    sent_at TIMESTAMP WITHOUT TIME ZONE,
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_broadcasts_store ON broadcasts(store_id);
CREATE INDEX IF NOT EXISTS idx_broadcasts_status ON broadcasts(status);
CREATE INDEX IF NOT EXISTS idx_broadcasts_scheduled ON broadcasts(scheduled_at);

-- Broadcast Messages
CREATE TABLE IF NOT EXISTS broadcast_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    subject VARCHAR(500),
    message_content TEXT NOT NULL,
    html_content TEXT,
    variables JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_broadcast_messages_broadcast ON broadcast_messages(broadcast_id);

-- Broadcast Recipients
CREATE TABLE IF NOT EXISTS broadcast_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(50),
    delivery_status VARCHAR(50) DEFAULT 'pending',
    delivered_at TIMESTAMP WITHOUT TIME ZONE,
    opened_at TIMESTAMP WITHOUT TIME ZONE,
    clicked_at TIMESTAMP WITHOUT TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_broadcast ON broadcast_recipients(broadcast_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_user ON broadcast_recipients(user_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_status ON broadcast_recipients(delivery_status);

-- Broadcast Segments
CREATE TABLE IF NOT EXISTS broadcast_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_name VARCHAR(255) NOT NULL,
    description TEXT,
    filter_criteria JSONB NOT NULL,
    estimated_size INTEGER,
    is_dynamic BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_broadcast_segments_name ON broadcast_segments(segment_name);

-- Broadcast Audit Logs
CREATE TABLE IF NOT EXISTS broadcast_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID REFERENCES broadcasts(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    performed_by UUID REFERENCES users(id),
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_broadcast_audit_logs_broadcast ON broadcast_audit_logs(broadcast_id);

-- Communication Logs
CREATE TABLE IF NOT EXISTS communication_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    communication_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    message_content TEXT,
    status VARCHAR(50) DEFAULT 'sent',
    provider VARCHAR(100),
    provider_message_id VARCHAR(255),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    sent_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_communication_logs_user ON communication_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_communication_logs_type ON communication_logs(communication_type);
CREATE INDEX IF NOT EXISTS idx_communication_logs_sent ON communication_logs(sent_at DESC);

-- Communication Preferences
CREATE TABLE IF NOT EXISTS communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    marketing_emails BOOLEAN DEFAULT true,
    order_updates BOOLEAN DEFAULT true,
    promotions BOOLEAN DEFAULT true,
    newsletter BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_communication_preferences_user ON communication_preferences(user_id);

-- Communication Analytics
CREATE TABLE IF NOT EXISTS communication_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_log_id INTEGER REFERENCES communication_logs(id),
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_communication_analytics_log ON communication_analytics(communication_log_id);
CREATE INDEX IF NOT EXISTS idx_communication_analytics_type ON communication_analytics(event_type);

-- Message Templates
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    message_content TEXT NOT NULL,
    html_content TEXT,
    variables TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_message_templates_store ON message_templates(store_id);
CREATE INDEX IF NOT EXISTS idx_message_templates_type ON message_templates(template_type);

-- Push Subscriptions
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(500) NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_active ON push_subscriptions(is_active);

-- Unsubscribe List
CREATE TABLE IF NOT EXISTS unsubscribe_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(50),
    unsubscribe_type VARCHAR(50) NOT NULL,
    reason VARCHAR(255),
    unsubscribed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unsubscribe_list_user ON unsubscribe_list(user_id);
CREATE INDEX IF NOT EXISTS idx_unsubscribe_list_email ON unsubscribe_list(email);
CREATE INDEX IF NOT EXISTS idx_unsubscribe_list_type ON unsubscribe_list(unsubscribe_type);

-- ===========================
-- TRANSLATION & I18N TABLES
-- ===========================

-- Supported Languages
CREATE TABLE IF NOT EXISTS supported_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language_code VARCHAR(10) UNIQUE NOT NULL,
    language_name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_supported_languages_code ON supported_languages(language_code);
CREATE INDEX IF NOT EXISTS idx_supported_languages_active ON supported_languages(is_active);

-- Translations
CREATE TABLE IF NOT EXISTS translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    translation_key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    translation_value TEXT NOT NULL,
    context VARCHAR(255),
    is_approved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(translation_key, language_code)
);

CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(translation_key);
CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language_code);
CREATE INDEX IF NOT EXISTS idx_translations_approved ON translations(is_approved);

-- Translation Batches
CREATE TABLE IF NOT EXISTS translation_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name VARCHAR(255) NOT NULL,
    source_language VARCHAR(10) NOT NULL,
    target_languages TEXT[] NOT NULL,
    total_keys INTEGER DEFAULT 0,
    translated_keys INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_translation_batches_status ON translation_batches(status);

-- Translation Batch Items
CREATE TABLE IF NOT EXISTS translation_batch_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES translation_batches(id) ON DELETE CASCADE,
    translation_key VARCHAR(255) NOT NULL,
    source_text TEXT NOT NULL,
    target_language VARCHAR(10) NOT NULL,
    translated_text TEXT,
    translation_status VARCHAR(50) DEFAULT 'pending',
    translator_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_translation_batch_items_batch ON translation_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_translation_batch_items_status ON translation_batch_items(translation_status);

-- Translation Overrides
CREATE TABLE IF NOT EXISTS translation_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    translation_key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    override_value TEXT NOT NULL,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(translation_key, language_code, store_id)
);

CREATE INDEX IF NOT EXISTS idx_translation_overrides_key ON translation_overrides(translation_key);
CREATE INDEX IF NOT EXISTS idx_translation_overrides_store ON translation_overrides(store_id);

-- ===========================
-- AUTHENTICATION & SECURITY TABLES
-- ===========================

-- Auth Tokens
CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITHOUT TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);

-- Token Blacklist
CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(50),
    revoked_by UUID REFERENCES users(id),
    revoke_reason VARCHAR(255),
    revoked_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20),
    permissions TEXT[],
    rate_limit INTEGER,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- OTP Codes (One-Time Passwords for 2FA)
CREATE TABLE IF NOT EXISTS otp_codes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp_type VARCHAR(50) NOT NULL,
    code_hash VARCHAR(255) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    delivery_address VARCHAR(255),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    is_verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_otp_codes_user ON otp_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at);

-- OTP Rate Limits
CREATE TABLE IF NOT EXISTS otp_rate_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(50),
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_otp_rate_limits_user ON otp_rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_rate_limits_email ON otp_rate_limits(email);

-- Voice Profiles (voice biometric authentication)
CREATE TABLE IF NOT EXISTS voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    voiceprint_data BYTEA NOT NULL,
    enrollment_status VARCHAR(50) DEFAULT 'pending',
    enrollment_samples_count INTEGER DEFAULT 0,
    required_samples INTEGER DEFAULT 3,
    confidence_threshold NUMERIC(5,4) DEFAULT 0.85,
    last_verified_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_profiles_user ON voice_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_status ON voice_profiles(enrollment_status);

-- Voice Auth Logs
CREATE TABLE IF NOT EXISTS voice_auth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    auth_attempt_id UUID NOT NULL,
    audio_duration_seconds NUMERIC(6,2),
    confidence_score NUMERIC(5,4),
    auth_result VARCHAR(50) NOT NULL,
    failure_reason VARCHAR(255),
    ip_address INET,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_auth_logs_user ON voice_auth_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_auth_logs_created ON voice_auth_logs(created_at DESC);

-- Age Verification Logs
CREATE TABLE IF NOT EXISTS age_verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verification_method VARCHAR(50) NOT NULL,
    document_type VARCHAR(50),
    verification_result VARCHAR(50) NOT NULL,
    verified_age INTEGER,
    verification_data JSONB,
    verified_by UUID REFERENCES users(id),
    ip_address INET,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_age_verification_logs_user ON age_verification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_age_verification_logs_result ON age_verification_logs(verification_result);

-- ===========================
-- AUDIT & COMPLIANCE TABLES
-- ===========================

-- AGI Rate Limit Rules
CREATE TABLE IF NOT EXISTS agi_rate_limit_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL,
    endpoint_pattern VARCHAR(500),
    limit_type VARCHAR(50) NOT NULL,
    max_requests INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL,
    scope VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agi_rate_limit_rules_active ON agi_rate_limit_rules(is_active);

-- AGI Rate Limit Buckets
CREATE TABLE IF NOT EXISTS agi_rate_limit_buckets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES agi_rate_limit_rules(id),
    bucket_key VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE(rule_id, bucket_key)
);

CREATE INDEX IF NOT EXISTS idx_agi_rate_limit_buckets_key ON agi_rate_limit_buckets(bucket_key);
CREATE INDEX IF NOT EXISTS idx_agi_rate_limit_buckets_window ON agi_rate_limit_buckets(window_end);

-- AGI Rate Limit Violations
CREATE TABLE IF NOT EXISTS agi_rate_limit_violations (
    id SERIAL PRIMARY KEY,
    rule_id UUID REFERENCES agi_rate_limit_rules(id),
    bucket_key VARCHAR(255) NOT NULL,
    violation_type VARCHAR(50),
    request_count INTEGER,
    limit_exceeded INTEGER,
    ip_address INET,
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agi_rate_limit_violations_key ON agi_rate_limit_violations(bucket_key);
CREATE INDEX IF NOT EXISTS idx_agi_rate_limit_violations_created ON agi_rate_limit_violations(created_at DESC);

-- Location Access Log
CREATE TABLE IF NOT EXISTS location_access_log (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    access_type VARCHAR(50) NOT NULL,
    location_data GEOGRAPHY(POINT),
    accuracy_meters NUMERIC(8,2),
    permission_granted BOOLEAN NOT NULL,
    access_reason VARCHAR(255),
    ip_address INET,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_location_access_log_user ON location_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_location_access_log_created ON location_access_log(created_at DESC);

-- Location Assignments Log
CREATE TABLE IF NOT EXISTS location_assignments_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    assignment_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    assigned_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_location_assignments_log_user ON location_assignments_log(user_id);
CREATE INDEX IF NOT EXISTS idx_location_assignments_log_store ON location_assignments_log(store_id);

COMMENT ON TABLE broadcasts IS 'Marketing campaign broadcasts';
COMMENT ON TABLE communication_logs IS 'Audit trail of all communications sent';
COMMENT ON TABLE communication_preferences IS 'User notification and communication preferences';
COMMENT ON TABLE unsubscribe_list IS 'Unsubscribe list for CAN-SPAM compliance';
COMMENT ON TABLE translations IS 'Multilingual translations key-value store';
COMMENT ON TABLE auth_tokens IS 'Authentication tokens (refresh, access, etc.)';
COMMENT ON TABLE token_blacklist IS 'Revoked tokens list for security';
COMMENT ON TABLE api_keys IS 'API key management for programmatic access';
COMMENT ON TABLE otp_codes IS 'One-time passwords for 2FA';
COMMENT ON TABLE age_verification_logs IS 'Age verification audit trail (cannabis compliance)';
COMMENT ON TABLE location_access_log IS 'Location permission access audit (privacy compliance)';
