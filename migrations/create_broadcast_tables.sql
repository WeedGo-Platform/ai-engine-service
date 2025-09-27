-- Message Broadcast System Database Schema
-- Created: 2024
-- Purpose: Support multi-channel broadcast messaging (Email, SMS, Push)

-- =====================================================
-- BROADCAST CAMPAIGNS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'sending', 'sent', 'paused', 'cancelled', 'failed')),
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Statistics
    total_recipients INTEGER DEFAULT 0,
    successful_sends INTEGER DEFAULT 0,
    failed_sends INTEGER DEFAULT 0,

    -- Configuration
    send_immediately BOOLEAN DEFAULT false,
    respect_quiet_hours BOOLEAN DEFAULT true,
    retry_failed BOOLEAN DEFAULT true,
    max_retries INTEGER DEFAULT 3,

    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_broadcasts_store_id ON broadcasts(store_id);
CREATE INDEX idx_broadcasts_tenant_id ON broadcasts(tenant_id);
CREATE INDEX idx_broadcasts_status ON broadcasts(status);
CREATE INDEX idx_broadcasts_scheduled_at ON broadcasts(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX idx_broadcasts_created_by ON broadcasts(created_by);

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
-- RECIPIENTS FOR EACH BROADCAST
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcast_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id),

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
-- MESSAGE TEMPLATES
-- =====================================================
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'sms', 'push')),
    category VARCHAR(100) DEFAULT 'general' CHECK (category IN ('promotional', 'transactional', 'alert', 'general')),

    -- Template content
    subject VARCHAR(500),
    content TEXT NOT NULL,
    preview_text VARCHAR(160),

    -- Variables that can be used in the template
    variables JSONB DEFAULT '{}', -- {customer_name: "string", points: "number", etc}

    -- Ownership
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    is_global BOOLEAN DEFAULT false, -- System-wide templates

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT true,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,

    -- Metadata
    tags TEXT[],
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_message_templates_channel_type ON message_templates(channel_type);
CREATE INDEX idx_message_templates_category ON message_templates(category);
CREATE INDEX idx_message_templates_store_id ON message_templates(store_id);
CREATE INDEX idx_message_templates_tenant_id ON message_templates(tenant_id);
CREATE INDEX idx_message_templates_is_active ON message_templates(is_active);

-- =====================================================
-- PUSH NOTIFICATION SUBSCRIPTIONS
-- =====================================================
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

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
-- COMMUNICATION PREFERENCES
-- =====================================================
CREATE TABLE IF NOT EXISTS communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

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
-- BROADCAST SEGMENTS (For recipient filtering)
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcast_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,

    -- Segment criteria (stored as JSON for flexibility)
    criteria JSONB NOT NULL, -- Complex filtering rules

    -- Cached results
    recipient_count INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_broadcast_segments_broadcast_id ON broadcast_segments(broadcast_id);

-- =====================================================
-- BROADCAST AUDIT LOGS
-- =====================================================
CREATE TABLE IF NOT EXISTS broadcast_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID REFERENCES broadcasts(id) ON DELETE CASCADE,

    -- Action details
    action VARCHAR(100) NOT NULL,
    action_category VARCHAR(50) CHECK (action_category IN ('create', 'update', 'send', 'cancel', 'pause', 'resume', 'delete', 'approve')),

    -- User information
    performed_by UUID REFERENCES users(id),
    user_role VARCHAR(50),

    -- Change tracking
    old_values JSONB,
    new_values JSONB,

    -- Context
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_broadcast_audit_logs_broadcast_id ON broadcast_audit_logs(broadcast_id);
CREATE INDEX idx_broadcast_audit_logs_performed_by ON broadcast_audit_logs(performed_by);
CREATE INDEX idx_broadcast_audit_logs_action ON broadcast_audit_logs(action);
CREATE INDEX idx_broadcast_audit_logs_created_at ON broadcast_audit_logs(created_at);

-- =====================================================
-- COMMUNICATION ANALYTICS
-- =====================================================
CREATE TABLE IF NOT EXISTS communication_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID REFERENCES broadcasts(id) ON DELETE CASCADE,

    -- Metrics per channel
    email_sent INTEGER DEFAULT 0,
    email_delivered INTEGER DEFAULT 0,
    email_opened INTEGER DEFAULT 0,
    email_clicked INTEGER DEFAULT 0,
    email_bounced INTEGER DEFAULT 0,
    email_unsubscribed INTEGER DEFAULT 0,

    sms_sent INTEGER DEFAULT 0,
    sms_delivered INTEGER DEFAULT 0,
    sms_failed INTEGER DEFAULT 0,
    sms_replied INTEGER DEFAULT 0,

    push_sent INTEGER DEFAULT 0,
    push_delivered INTEGER DEFAULT 0,
    push_opened INTEGER DEFAULT 0,
    push_failed INTEGER DEFAULT 0,

    -- Engagement rates (calculated)
    email_open_rate DECIMAL(5,2),
    email_click_rate DECIMAL(5,2),
    push_open_rate DECIMAL(5,2),

    -- Cost tracking
    email_cost DECIMAL(10,2) DEFAULT 0,
    sms_cost DECIMAL(10,2) DEFAULT 0,
    push_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,

    -- Performance
    avg_delivery_time_seconds INTEGER,

    calculated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(broadcast_id)
);

CREATE INDEX idx_communication_analytics_broadcast_id ON communication_analytics(broadcast_id);

-- =====================================================
-- UNSUBSCRIBE LIST
-- =====================================================
CREATE TABLE IF NOT EXISTS unsubscribe_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),

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
-- FUNCTIONS FOR AUTOMATED UPDATES
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_broadcasts_updated_at BEFORE UPDATE ON broadcasts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_broadcast_messages_updated_at BEFORE UPDATE ON broadcast_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_broadcast_recipients_updated_at BEFORE UPDATE ON broadcast_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_message_templates_updated_at BEFORE UPDATE ON message_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_subscriptions_updated_at BEFORE UPDATE ON push_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communication_preferences_updated_at BEFORE UPDATE ON communication_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default message templates
INSERT INTO message_templates (name, channel_type, category, subject, content, variables, is_global, is_active)
VALUES
    ('Welcome Email', 'email', 'transactional', 'Welcome to {{store_name}}!',
     'Hi {{customer_name}},\n\nWelcome to {{store_name}}! We''re excited to have you as our customer.\n\nBest regards,\n{{store_name}} Team',
     '{"customer_name": "string", "store_name": "string"}', true, true),

    ('Order Confirmation SMS', 'sms', 'transactional', NULL,
     'Hi {{customer_name}}, your order #{{order_number}} has been confirmed. Track it at {{tracking_url}}',
     '{"customer_name": "string", "order_number": "string", "tracking_url": "string"}', true, true),

    ('Promotion Push', 'push', 'promotional', '{{promotion_title}}',
     '{{promotion_message}}. Valid until {{expiry_date}}.',
     '{"promotion_title": "string", "promotion_message": "string", "expiry_date": "string"}', true, true)
ON CONFLICT DO NOTHING;