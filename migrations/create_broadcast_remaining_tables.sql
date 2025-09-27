-- Complete the broadcast system tables
-- This migration adds the remaining tables that depend on the customers view

-- =====================================================
-- BROADCAST MESSAGES PER CHANNEL
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcast_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'sms', 'push')),

    -- Message content
    subject VARCHAR(500), -- For email and push
    content TEXT NOT NULL,
    preview_text VARCHAR(160), -- For email preview

    -- Template support
    template_id UUID REFERENCES message_templates(id),
    template_variables JSONB DEFAULT '{}',

    -- Channel-specific settings
    sender_name VARCHAR(100), -- For email
    sender_email VARCHAR(255), -- For email
    sender_phone VARCHAR(20), -- For SMS

    -- Push notification specific
    push_title VARCHAR(100),
    push_image_url VARCHAR(500),
    push_action_url VARCHAR(500),
    push_badge_count INTEGER,

    -- Settings
    is_active BOOLEAN DEFAULT true,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(broadcast_id, channel_type)
);

CREATE INDEX idx_broadcast_messages_broadcast_id ON broadcast_messages(broadcast_id);
CREATE INDEX idx_broadcast_messages_channel_type ON broadcast_messages(channel_type);
CREATE INDEX idx_broadcast_messages_template_id ON broadcast_messages(template_id);

-- =====================================================
-- RECIPIENTS FOR EACH BROADCAST (using customer_id as TEXT)
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcast_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    customer_id TEXT NOT NULL, -- Changed to TEXT to match the customers view

    -- Contact information (denormalized for performance)
    email VARCHAR(255),
    phone_number VARCHAR(20),
    push_token VARCHAR(500),

    -- Channel selection
    channels JSONB DEFAULT '{}', -- {email: true, sms: false, push: true}

    -- Delivery status per channel
    email_status VARCHAR(50) DEFAULT 'pending',
    sms_status VARCHAR(50) DEFAULT 'pending',
    push_status VARCHAR(50) DEFAULT 'pending',

    -- Timestamps per channel
    email_sent_at TIMESTAMP,
    email_delivered_at TIMESTAMP,
    email_opened_at TIMESTAMP,
    email_clicked_at TIMESTAMP,
    email_bounced_at TIMESTAMP,
    email_unsubscribed_at TIMESTAMP,

    sms_sent_at TIMESTAMP,
    sms_delivered_at TIMESTAMP,
    sms_replied_at TIMESTAMP,

    push_sent_at TIMESTAMP,
    push_delivered_at TIMESTAMP,
    push_opened_at TIMESTAMP,

    -- Error tracking
    email_error TEXT,
    sms_error TEXT,
    push_error TEXT,

    -- Retry tracking
    email_retry_count INTEGER DEFAULT 0,
    sms_retry_count INTEGER DEFAULT 0,
    push_retry_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_broadcast_recipients_broadcast_id ON broadcast_recipients(broadcast_id);
CREATE INDEX idx_broadcast_recipients_customer_id ON broadcast_recipients(customer_id);
CREATE INDEX idx_broadcast_recipients_email_status ON broadcast_recipients(email_status);
CREATE INDEX idx_broadcast_recipients_sms_status ON broadcast_recipients(sms_status);
CREATE INDEX idx_broadcast_recipients_push_status ON broadcast_recipients(push_status);

-- =====================================================
-- PUSH NOTIFICATION SUBSCRIPTIONS (using customer_id as TEXT)
-- =====================================================
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id TEXT NOT NULL, -- Changed to TEXT to match the customers view

    -- Device information
    device_token VARCHAR(500) NOT NULL,
    device_type VARCHAR(50) NOT NULL CHECK (device_type IN ('ios', 'android', 'web')),
    device_name VARCHAR(100),
    device_model VARCHAR(100),
    app_version VARCHAR(20),
    os_version VARCHAR(20),

    -- Web Push specific (for PWA)
    endpoint VARCHAR(500),
    auth_key VARCHAR(500),
    p256dh_key VARCHAR(500),

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_sandbox BOOLEAN DEFAULT false, -- For testing

    -- Tracking
    last_active_at TIMESTAMP,
    notification_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(device_token)
);

CREATE INDEX idx_push_subscriptions_customer_id ON push_subscriptions(customer_id);
CREATE INDEX idx_push_subscriptions_device_type ON push_subscriptions(device_type);
CREATE INDEX idx_push_subscriptions_is_active ON push_subscriptions(is_active);

-- =====================================================
-- COMMUNICATION PREFERENCES (using customer_id as TEXT)
-- =====================================================
CREATE TABLE IF NOT EXISTS communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id TEXT NOT NULL, -- Changed to TEXT to match the customers view

    -- Channel preferences
    channel_email BOOLEAN DEFAULT true,
    channel_sms BOOLEAN DEFAULT true,
    channel_push BOOLEAN DEFAULT true,

    -- Message type preferences
    promotional BOOLEAN DEFAULT true,
    transactional BOOLEAN DEFAULT true,
    alerts BOOLEAN DEFAULT true,

    -- Frequency settings
    frequency VARCHAR(50) DEFAULT 'normal' CHECK (frequency IN ('immediate', 'daily', 'weekly', 'monthly', 'normal')),
    max_emails_per_day INTEGER DEFAULT 5,
    max_sms_per_day INTEGER DEFAULT 3,
    max_push_per_day INTEGER DEFAULT 10,

    -- Quiet hours (stored in UTC)
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'America/Toronto',

    -- Language preference
    preferred_language VARCHAR(10) DEFAULT 'en',

    -- Unsubscribe tokens
    email_unsubscribe_token VARCHAR(100) UNIQUE,
    sms_unsubscribe_token VARCHAR(100) UNIQUE,

    -- Tracking
    last_email_at TIMESTAMP,
    last_sms_at TIMESTAMP,
    last_push_at TIMESTAMP,

    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(customer_id)
);

CREATE INDEX idx_communication_preferences_customer_id ON communication_preferences(customer_id);
CREATE INDEX idx_communication_preferences_email_token ON communication_preferences(email_unsubscribe_token);
CREATE INDEX idx_communication_preferences_sms_token ON communication_preferences(sms_unsubscribe_token);

-- =====================================================
-- UNSUBSCRIBE LIST
-- =====================================================
CREATE TABLE IF NOT EXISTS unsubscribe_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id TEXT, -- Changed to TEXT to match the customers view

    -- Contact info (one of these will be populated)
    email VARCHAR(255),
    phone_number VARCHAR(20),

    -- Unsubscribe details
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'sms', 'push', 'all')),
    reason VARCHAR(255),
    additional_comments TEXT,

    -- Source
    unsubscribe_source VARCHAR(50) CHECK (unsubscribe_source IN ('link', 'reply', 'admin', 'api', 'customer_request')),
    broadcast_id UUID REFERENCES broadcasts(id),

    -- Status
    is_permanent BOOLEAN DEFAULT false,
    resubscribe_allowed_after TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_unsubscribe_list_email ON unsubscribe_list(email) WHERE email IS NOT NULL;
CREATE INDEX idx_unsubscribe_list_phone ON unsubscribe_list(phone_number) WHERE phone_number IS NOT NULL;
CREATE INDEX idx_unsubscribe_list_customer_id ON unsubscribe_list(customer_id) WHERE customer_id IS NOT NULL;
CREATE INDEX idx_unsubscribe_list_channel_type ON unsubscribe_list(channel_type);

-- =====================================================
-- Apply triggers to new tables
-- =====================================================

CREATE TRIGGER update_broadcast_messages_updated_at BEFORE UPDATE ON broadcast_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_broadcast_recipients_updated_at BEFORE UPDATE ON broadcast_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_subscriptions_updated_at BEFORE UPDATE ON push_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communication_preferences_updated_at BEFORE UPDATE ON communication_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();