-- ============================================================================
-- Schema Migration: Legacy → Current Database
-- Generated: 2025-10-12 22:05:46
-- Description: Copy all missing schema objects from legacy to current
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- STEP 1: Create 6 Missing Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS agi_audit_aggregates (
    id integer NOT NULL DEFAULT nextval('agi_audit_aggregates_id_seq'::regclass),
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    event_type text NOT NULL,
    severity text,
    count bigint NOT NULL DEFAULT 0,
    unique_users integer DEFAULT 0,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_audit_alerts (
    id integer NOT NULL DEFAULT nextval('agi_audit_alerts_id_seq'::regclass),
    alert_type text NOT NULL,
    severity text NOT NULL,
    event_count integer NOT NULL,
    time_window_minutes integer NOT NULL,
    triggered_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    alert_data jsonb DEFAULT '{}'::jsonb,
    acknowledged boolean DEFAULT false,
    acknowledged_by text,
    acknowledged_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS agi_audit_logs (
    id bigint NOT NULL DEFAULT nextval('agi_audit_logs_id_seq'::regclass),
    event_type text NOT NULL,
    severity text NOT NULL,
    user_id text,
    session_id text,
    resource_type text,
    resource_id text,
    action text,
    result text,
    ip_address text,
    user_agent text,
    error_message text,
    stack_trace text,
    metadata jsonb DEFAULT '{}'::jsonb,
    event_hash text NOT NULL,
    timestamp timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_buckets (
    key text NOT NULL,
    tokens double precision NOT NULL,
    last_update timestamp with time zone NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_rules (
    name text NOT NULL,
    scope text NOT NULL,
    strategy text NOT NULL,
    limit_value integer NOT NULL,
    window_seconds integer NOT NULL,
    burst_size integer,
    priority integer DEFAULT 0,
    enabled boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_violations (
    id integer NOT NULL DEFAULT nextval('agi_rate_limit_violations_id_seq'::regclass),
    rule_name text NOT NULL,
    identifier text NOT NULL,
    resource text,
    attempts integer NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STEP 2: Add Missing Columns to Existing Tables
-- ============================================================================

-- Table: age_verification_logs
ALTER TABLE age_verification_logs
ADD COLUMN IF NOT EXISTS session_id character varying(255),
ADD COLUMN IF NOT EXISTS verified boolean NOT NULL,
ADD COLUMN IF NOT EXISTS timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS age_info jsonb NOT NULL
;

-- Table: ai_conversations
ALTER TABLE ai_conversations
ADD COLUMN IF NOT EXISTS personality_id uuid,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS messages jsonb,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS customer_id character varying(255),
ADD COLUMN IF NOT EXISTS context jsonb,
ADD COLUMN IF NOT EXISTS agent_id uuid,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS conversation_id uuid DEFAULT gen_random_uuid() NOT NULL
;

-- Table: ai_personalities
ALTER TABLE ai_personalities
ADD COLUMN IF NOT EXISTS voice_config jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS avatar_url character varying(500),
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS name character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS is_default boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS traits jsonb DEFAULT '{}'::jsonb
;

-- Table: ai_training_data
ALTER TABLE ai_training_data
ADD COLUMN IF NOT EXISTS feedback_score double precision,
ADD COLUMN IF NOT EXISTS customer_message text NOT NULL,
ADD COLUMN IF NOT EXISTS model_confidence double precision,
ADD COLUMN IF NOT EXISTS search_results jsonb,
ADD COLUMN IF NOT EXISTS correction jsonb,
ADD COLUMN IF NOT EXISTS inferred_params jsonb NOT NULL,
ADD COLUMN IF NOT EXISTS customer_action character varying(50),
ADD COLUMN IF NOT EXISTS response_time_ms integer
;

-- Table: api_keys
ALTER TABLE api_keys
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS name character varying(255),
ADD COLUMN IF NOT EXISTS allowed_stores text[],
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS last_used timestamp without time zone
;

-- Table: audit_log
ALTER TABLE audit_log
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS success boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS store_id uuid,
ADD COLUMN IF NOT EXISTS resource_id character varying(255)
;

-- Table: auth_tokens
ALTER TABLE auth_tokens
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS is_used boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS used_at timestamp without time zone
;

-- Table: batch_tracking
ALTER TABLE batch_tracking
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS purchase_order_id uuid,
ADD COLUMN IF NOT EXISTS gtin_barcode character varying(100),
ADD COLUMN IF NOT EXISTS batch_lot character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS unit_cost numeric(10,2),
ADD COLUMN IF NOT EXISTS each_gtin character varying(100),
ADD COLUMN IF NOT EXISTS location_id uuid,
ADD COLUMN IF NOT EXISTS sku character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS case_gtin character varying(100),
ADD COLUMN IF NOT EXISTS packaged_on_date date
;

-- Table: broadcast_audit_logs
ALTER TABLE broadcast_audit_logs
ADD COLUMN IF NOT EXISTS user_role character varying(50),
ADD COLUMN IF NOT EXISTS new_values jsonb,
ADD COLUMN IF NOT EXISTS details jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS user_agent text,
ADD COLUMN IF NOT EXISTS old_values jsonb,
ADD COLUMN IF NOT EXISTS action_category character varying(50)
;

-- Table: broadcast_messages
ALTER TABLE broadcast_messages
ADD COLUMN IF NOT EXISTS priority character varying(20) DEFAULT 'normal'::character varying,
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS preview_text character varying(160),
ADD COLUMN IF NOT EXISTS push_title character varying(100),
ADD COLUMN IF NOT EXISTS template_variables jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS channel_type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS content text NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS sender_phone character varying(20),
ADD COLUMN IF NOT EXISTS sender_name character varying(100),
ADD COLUMN IF NOT EXISTS push_image_url character varying(500),
ADD COLUMN IF NOT EXISTS push_action_url character varying(500),
ADD COLUMN IF NOT EXISTS push_badge_count integer,
ADD COLUMN IF NOT EXISTS template_id uuid,
ADD COLUMN IF NOT EXISTS sender_email character varying(255)
;

-- Table: broadcast_recipients
ALTER TABLE broadcast_recipients
ADD COLUMN IF NOT EXISTS sms_retry_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_retry_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_clicked_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS sms_error text,
ADD COLUMN IF NOT EXISTS email_error text,
ADD COLUMN IF NOT EXISTS email_opened_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_status character varying(50) DEFAULT 'pending'::character varying,
ADD COLUMN IF NOT EXISTS email_unsubscribed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_retry_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS customer_id text NOT NULL,
ADD COLUMN IF NOT EXISTS sms_delivered_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS sms_replied_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_delivered_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS sms_status character varying(50) DEFAULT 'pending'::character varying,
ADD COLUMN IF NOT EXISTS phone_number character varying(20),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS channels jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS email_status character varying(50) DEFAULT 'pending'::character varying,
ADD COLUMN IF NOT EXISTS email character varying(255),
ADD COLUMN IF NOT EXISTS email_sent_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_error text,
ADD COLUMN IF NOT EXISTS push_opened_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS sms_sent_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_sent_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS email_bounced_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS email_delivered_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS push_token character varying(500)
;

-- Table: broadcast_segments
ALTER TABLE broadcast_segments
ADD COLUMN IF NOT EXISTS criteria jsonb NOT NULL,
ADD COLUMN IF NOT EXISTS broadcast_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS recipient_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_calculated_at timestamp without time zone
;

-- Table: broadcasts
ALTER TABLE broadcasts
ADD COLUMN IF NOT EXISTS max_retries integer DEFAULT 3,
ADD COLUMN IF NOT EXISTS successful_sends integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS cancelled_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS completed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS send_immediately boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS started_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS retry_failed boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS name character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS failed_sends integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS tags text[],
ADD COLUMN IF NOT EXISTS respect_quiet_hours boolean DEFAULT true
;

-- Table: bundle_deals
ALTER TABLE bundle_deals
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS bundle_type character varying(50),
ADD COLUMN IF NOT EXISTS min_quantity integer DEFAULT 1,
ADD COLUMN IF NOT EXISTS discount_percentage numeric(5,2),
ADD COLUMN IF NOT EXISTS require_all_items boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS max_quantity integer,
ADD COLUMN IF NOT EXISTS start_date timestamp without time zone,
ADD COLUMN IF NOT EXISTS allow_substitutions boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS optional_products jsonb,
ADD COLUMN IF NOT EXISTS name character varying(200) NOT NULL,
ADD COLUMN IF NOT EXISTS end_date timestamp without time zone,
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS required_products jsonb
;

-- Table: cart_sessions
ALTER TABLE cart_sessions
ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'active'::character varying,
ADD COLUMN IF NOT EXISTS discount_codes jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS user_profile_id uuid,
ADD COLUMN IF NOT EXISTS ai_personality_id uuid,
ADD COLUMN IF NOT EXISTS tax_calculation jsonb,
ADD COLUMN IF NOT EXISTS delivery_fee numeric(10,2) DEFAULT 0.00
;

-- Table: chat_interactions
ALTER TABLE chat_interactions
ADD COLUMN IF NOT EXISTS session_id character varying(255),
ADD COLUMN IF NOT EXISTS response_time double precision,
ADD COLUMN IF NOT EXISTS ai_response text,
ADD COLUMN IF NOT EXISTS customer_id character varying(255),
ADD COLUMN IF NOT EXISTS metadata jsonb,
ADD COLUMN IF NOT EXISTS user_message text
;

-- Table: communication_analytics
ALTER TABLE communication_analytics
ADD COLUMN IF NOT EXISTS sms_sent integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_open_rate numeric(5,2),
ADD COLUMN IF NOT EXISTS email_cost numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS push_cost numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_clicked integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_delivered integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sms_delivered integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sms_cost numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS calculated_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS push_open_rate numeric(5,2),
ADD COLUMN IF NOT EXISTS total_cost numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS push_failed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS push_delivered integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS push_sent integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS broadcast_id uuid,
ADD COLUMN IF NOT EXISTS email_click_rate numeric(5,2),
ADD COLUMN IF NOT EXISTS email_opened integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sms_failed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sms_replied integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS push_opened integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_sent integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_unsubscribed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_bounced integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS avg_delivery_time_seconds integer
;

-- Table: communication_logs
ALTER TABLE communication_logs
ADD COLUMN IF NOT EXISTS retry_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS content text,
ADD COLUMN IF NOT EXISTS provider_response jsonb,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS delivered_at timestamp without time zone
;

-- Table: communication_preferences
ALTER TABLE communication_preferences
ADD COLUMN IF NOT EXISTS channel_push boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS transactional boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS quiet_hours_end time without time zone,
ADD COLUMN IF NOT EXISTS email_unsubscribe_token character varying(100),
ADD COLUMN IF NOT EXISTS last_sms_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS max_push_per_day integer DEFAULT 10,
ADD COLUMN IF NOT EXISTS preferred_language character varying(10) DEFAULT 'en'::character varying,
ADD COLUMN IF NOT EXISTS last_email_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS alerts boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS max_emails_per_day integer DEFAULT 5,
ADD COLUMN IF NOT EXISTS quiet_hours_start time without time zone,
ADD COLUMN IF NOT EXISTS promotional boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS customer_id text NOT NULL,
ADD COLUMN IF NOT EXISTS last_push_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS quiet_hours_enabled boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS sms_unsubscribe_token character varying(100),
ADD COLUMN IF NOT EXISTS channel_sms boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS channel_email boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS timezone character varying(50) DEFAULT 'America/Toronto'::character varying,
ADD COLUMN IF NOT EXISTS max_sms_per_day integer DEFAULT 3,
ADD COLUMN IF NOT EXISTS frequency character varying(50) DEFAULT 'normal'::character varying
;

-- Table: conversation_states
ALTER TABLE conversation_states
ADD COLUMN IF NOT EXISTS session_id character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS intent_history jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS previous_stage character varying(50),
ADD COLUMN IF NOT EXISTS engagement_score double precision DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS total_duration_seconds integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS stage_start_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS resistance_level double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS current_stage character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS stage_history jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS message_count integer DEFAULT 0
;

-- Table: conversion_metrics
ALTER TABLE conversion_metrics
ADD COLUMN IF NOT EXISTS cart_removals integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS converted boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS conversion_score double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS engagement_score double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS stage_transitions jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS abandonment_stage character varying(50),
ADD COLUMN IF NOT EXISTS total_session_duration_seconds integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS products_viewed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS conversion_events jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS cart_additions integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS abandonment_reason text
;

-- Table: customer_pricing_rules
ALTER TABLE customer_pricing_rules
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS volume_discounts jsonb,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS negotiated_products jsonb,
ADD COLUMN IF NOT EXISTS custom_markup_percentage numeric(5,2),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS early_payment_discount numeric(5,2),
ADD COLUMN IF NOT EXISTS price_tier_id uuid,
ADD COLUMN IF NOT EXISTS payment_terms character varying(50),
ADD COLUMN IF NOT EXISTS category_discounts jsonb
;

-- Table: customer_reviews
ALTER TABLE customer_reviews
ADD COLUMN IF NOT EXISTS status character varying(20) DEFAULT 'pending'::character varying,
ADD COLUMN IF NOT EXISTS is_recommended boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS sku character varying(255) NOT NULL
;

-- Table: deliveries
ALTER TABLE deliveries
ADD COLUMN IF NOT EXISTS id_verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS batch_id uuid,
ADD COLUMN IF NOT EXISTS feedback text,
ADD COLUMN IF NOT EXISTS issues_reported jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS scheduled_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS signature_captured_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS delivery_notes text,
ADD COLUMN IF NOT EXISTS age_verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS delivery_longitude numeric(11,8),
ADD COLUMN IF NOT EXISTS customer_name character varying(200) NOT NULL,
ADD COLUMN IF NOT EXISTS completed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS customer_id uuid,
ADD COLUMN IF NOT EXISTS assigned_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS customer_email character varying(255),
ADD COLUMN IF NOT EXISTS id_verification_type character varying(50),
ADD COLUMN IF NOT EXISTS delivery_fee numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS accepted_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS photo_proof_urls text[],
ADD COLUMN IF NOT EXISTS batch_sequence integer,
ADD COLUMN IF NOT EXISTS cancelled_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS rating integer,
ADD COLUMN IF NOT EXISTS delivery_latitude numeric(10,8),
ADD COLUMN IF NOT EXISTS arrived_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS customer_phone character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS signature_data text,
ADD COLUMN IF NOT EXISTS departed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS id_verification_data jsonb,
ADD COLUMN IF NOT EXISTS distance_km numeric(10,2),
ADD COLUMN IF NOT EXISTS tip_amount numeric(10,2) DEFAULT 0
;

-- Table: delivery_batches
ALTER TABLE delivery_batches
ADD COLUMN IF NOT EXISTS optimized_route jsonb,
ADD COLUMN IF NOT EXISTS total_distance_km numeric(10,2),
ADD COLUMN IF NOT EXISTS estimated_duration_minutes integer
;

-- Table: delivery_geofences
ALTER TABLE delivery_geofences
ADD COLUMN IF NOT EXISTS delivery_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS exited_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS center_latitude numeric(10,8) NOT NULL,
ADD COLUMN IF NOT EXISTS dwell_time_seconds integer,
ADD COLUMN IF NOT EXISTS center_longitude numeric(11,8) NOT NULL,
ADD COLUMN IF NOT EXISTS auto_complete_on_enter boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS notify_on_enter boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS radius_meters integer DEFAULT 100 NOT NULL,
ADD COLUMN IF NOT EXISTS entered_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS notify_on_exit boolean DEFAULT false
;

-- Table: delivery_tracking
ALTER TABLE delivery_tracking
ADD COLUMN IF NOT EXISTS altitude_meters numeric(10,2),
ADD COLUMN IF NOT EXISTS activity_type character varying(50),
ADD COLUMN IF NOT EXISTS provider character varying(50),
ADD COLUMN IF NOT EXISTS is_mock_location boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS recorded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS received_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: delivery_zones
ALTER TABLE delivery_zones
ADD COLUMN IF NOT EXISTS free_delivery_minimum numeric(10,2),
ADD COLUMN IF NOT EXISTS base_delivery_fee numeric(10,2) DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS delivery_time_minutes integer DEFAULT 60,
ADD COLUMN IF NOT EXISTS radius_km numeric(5,2),
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS available_days text[] DEFAULT ARRAY[0, 1, 2, 3, 4, 5, 6],
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS polygon_coordinates jsonb,
ADD COLUMN IF NOT EXISTS delivery_hours jsonb
;

-- Table: discount_codes
ALTER TABLE discount_codes
ADD COLUMN IF NOT EXISTS minimum_purchase numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS promotion_id uuid,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS customer_id uuid,
ADD COLUMN IF NOT EXISTS used_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS order_id uuid,
ADD COLUMN IF NOT EXISTS used boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS description text
;

-- Table: discount_usage
ALTER TABLE discount_usage
ADD COLUMN IF NOT EXISTS used_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: dynamic_pricing_rules
ALTER TABLE dynamic_pricing_rules
ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS trigger_type character varying(50),
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS action_value numeric(10,2),
ADD COLUMN IF NOT EXISTS action_type character varying(50),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS category_ids text[],
ADD COLUMN IF NOT EXISTS name character varying(200) NOT NULL,
ADD COLUMN IF NOT EXISTS product_ids text[],
ADD COLUMN IF NOT EXISTS description text
;

-- Table: holidays
ALTER TABLE holidays
ADD COLUMN IF NOT EXISTS holiday_type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS fixed_day integer,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS floating_rule jsonb,
ADD COLUMN IF NOT EXISTS date_type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS typical_business_impact character varying(20),
ADD COLUMN IF NOT EXISTS is_bank_holiday boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS fixed_month integer,
ADD COLUMN IF NOT EXISTS calculation_rule character varying(100)
;

-- Table: inventory_locations
ALTER TABLE inventory_locations
ADD COLUMN IF NOT EXISTS code character varying(50),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS name character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS type character varying(50),
ADD COLUMN IF NOT EXISTS zone character varying(50)
;

-- Table: location_access_log
ALTER TABLE location_access_log
ADD COLUMN IF NOT EXISTS latitude numeric(10,8),
ADD COLUMN IF NOT EXISTS accuracy numeric(10,2),
ADD COLUMN IF NOT EXISTS store_id uuid,
ADD COLUMN IF NOT EXISTS longitude numeric(11,8),
ADD COLUMN IF NOT EXISTS user_agent text,
ADD COLUMN IF NOT EXISTS metadata jsonb
;

-- Table: location_assignments_log
ALTER TABLE location_assignments_log
ADD COLUMN IF NOT EXISTS inventory_id uuid,
ADD COLUMN IF NOT EXISTS quantity integer NOT NULL,
ADD COLUMN IF NOT EXISTS notes text,
ADD COLUMN IF NOT EXISTS location_id uuid
;

-- Table: message_templates
ALTER TABLE message_templates
ADD COLUMN IF NOT EXISTS preview_text character varying(160),
ADD COLUMN IF NOT EXISTS is_global boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_approved boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS channel_type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS content text NOT NULL,
ADD COLUMN IF NOT EXISTS last_used_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS usage_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS name character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS approved_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS category character varying(100) DEFAULT 'general'::character varying,
ADD COLUMN IF NOT EXISTS tags text[]
;

-- Table: model_deployments
ALTER TABLE model_deployments
ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'inactive'::character varying,
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS stopped_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS traffic_percentage double precision DEFAULT 100.0,
ADD COLUMN IF NOT EXISTS deployment_name character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS started_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS endpoint character varying(255) NOT NULL
;

-- Table: model_metrics
ALTER TABLE model_metrics
ADD COLUMN IF NOT EXISTS notes text,
ADD COLUMN IF NOT EXISTS evaluation_date date DEFAULT CURRENT_DATE,
ADD COLUMN IF NOT EXISTS model_name character varying(100),
ADD COLUMN IF NOT EXISTS training_samples integer,
ADD COLUMN IF NOT EXISTS accuracy_score double precision,
ADD COLUMN IF NOT EXISTS f1_score double precision,
ADD COLUMN IF NOT EXISTS precision_score double precision,
ADD COLUMN IF NOT EXISTS recall_score double precision
;

-- Table: model_versions
ALTER TABLE model_versions
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS config jsonb DEFAULT '{}'::jsonb
;

-- Table: ocs_inventory
ALTER TABLE ocs_inventory
ADD COLUMN IF NOT EXISTS quantity_reserved integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS image_url text,
ADD COLUMN IF NOT EXISTS vendor character varying(100),
ADD COLUMN IF NOT EXISTS subcategory character varying(100),
ADD COLUMN IF NOT EXISTS case_gtin character varying(50),
ADD COLUMN IF NOT EXISTS is_available boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS thc_content numeric(5,2),
ADD COLUMN IF NOT EXISTS brand character varying(100),
ADD COLUMN IF NOT EXISTS each_gtin character varying(50),
ADD COLUMN IF NOT EXISTS batch_lot character varying(100),
ADD COLUMN IF NOT EXISTS retail_price numeric(10,2),
ADD COLUMN IF NOT EXISTS min_stock_level integer DEFAULT 10,
ADD COLUMN IF NOT EXISTS cbd_content numeric(5,2),
ADD COLUMN IF NOT EXISTS last_restock_date timestamp without time zone,
ADD COLUMN IF NOT EXISTS plant_type character varying(50),
ADD COLUMN IF NOT EXISTS quantity_available integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sku character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS quantity_on_hand integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS supplier character varying(100),
ADD COLUMN IF NOT EXISTS container_id character varying(50),
ADD COLUMN IF NOT EXISTS max_stock_level integer DEFAULT 100,
ADD COLUMN IF NOT EXISTS override_price numeric(10,2),
ADD COLUMN IF NOT EXISTS gtin_barcode character varying(50),
ADD COLUMN IF NOT EXISTS retail_price_dynamic numeric(10,2),
ADD COLUMN IF NOT EXISTS unit_cost numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS strain_type character varying(50),
ADD COLUMN IF NOT EXISTS product_name character varying(255),
ADD COLUMN IF NOT EXISTS shipment_id character varying(50),
ADD COLUMN IF NOT EXISTS packaged_on_date date,
ADD COLUMN IF NOT EXISTS category character varying(100)
;

-- Table: ocs_inventory_logs
ALTER TABLE ocs_inventory_logs
ADD COLUMN IF NOT EXISTS inventory_id uuid,
ADD COLUMN IF NOT EXISTS reason text,
ADD COLUMN IF NOT EXISTS performed_by uuid,
ADD COLUMN IF NOT EXISTS change_quantity integer,
ADD COLUMN IF NOT EXISTS previous_quantity integer,
ADD COLUMN IF NOT EXISTS order_id uuid,
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS new_quantity integer
;

-- Table: ocs_inventory_movements
ALTER TABLE ocs_inventory_movements
ADD COLUMN IF NOT EXISTS inventory_id uuid,
ADD COLUMN IF NOT EXISTS reference_id character varying(100),
ADD COLUMN IF NOT EXISTS reason text,
ADD COLUMN IF NOT EXISTS performed_by uuid,
ADD COLUMN IF NOT EXISTS reference_type character varying(50)
;

-- Table: ocs_inventory_reservations
ALTER TABLE ocs_inventory_reservations
ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'active'::character varying,
ADD COLUMN IF NOT EXISTS inventory_id uuid,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS order_id uuid,
ADD COLUMN IF NOT EXISTS cart_session_id uuid
;

-- Table: ocs_inventory_snapshots
ALTER TABLE ocs_inventory_snapshots
ADD COLUMN IF NOT EXISTS inventory_id uuid,
ADD COLUMN IF NOT EXISTS last_movement_id uuid,
ADD COLUMN IF NOT EXISTS reserved_quantity integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS quantity_on_hand integer NOT NULL,
ADD COLUMN IF NOT EXISTS available_quantity integer NOT NULL
;

-- Table: ocs_inventory_transactions
ALTER TABLE ocs_inventory_transactions
ADD COLUMN IF NOT EXISTS quantity integer NOT NULL,
ADD COLUMN IF NOT EXISTS batch_lot character varying(100),
ADD COLUMN IF NOT EXISTS unit_cost numeric(10,2),
ADD COLUMN IF NOT EXISTS running_balance integer,
ADD COLUMN IF NOT EXISTS sku character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS created_by uuid
;

-- Table: ocs_product_catalog
ALTER TABLE ocs_product_catalog
ADD COLUMN IF NOT EXISTS minimum_cbd_content_percent numeric(10,2),
ADD COLUMN IF NOT EXISTS slug character varying(500),
ADD COLUMN IF NOT EXISTS temperature_display character varying(100),
ADD COLUMN IF NOT EXISTS fulfilment_method character varying(255),
ADD COLUMN IF NOT EXISTS ontario_grown character varying(255),
ADD COLUMN IF NOT EXISTS rechargeable_battery boolean,
ADD COLUMN IF NOT EXISTS ocs_item_number integer,
ADD COLUMN IF NOT EXISTS thc_content_per_unit numeric(10,2),
ADD COLUMN IF NOT EXISTS cbd_content_per_volume numeric(10,2),
ADD COLUMN IF NOT EXISTS minimum_thc_content_percent numeric(10,2),
ADD COLUMN IF NOT EXISTS terpenes text,
ADD COLUMN IF NOT EXISTS colour character varying(255),
ADD COLUMN IF NOT EXISTS temperature_control character varying(100),
ADD COLUMN IF NOT EXISTS maximum_cbd_content_percent numeric(10,2),
ADD COLUMN IF NOT EXISTS number_of_items_in_retail_pack integer,
ADD COLUMN IF NOT EXISTS rating_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS sub_sub_category character varying(255),
ADD COLUMN IF NOT EXISTS replacement_parts_available boolean,
ADD COLUMN IF NOT EXISTS drying_method character varying(255),
ADD COLUMN IF NOT EXISTS gtin bigint,
ADD COLUMN IF NOT EXISTS grow_method character varying(255),
ADD COLUMN IF NOT EXISTS maximum_thc_content_percent numeric(10,2),
ADD COLUMN IF NOT EXISTS heating_element_type character varying(255),
ADD COLUMN IF NOT EXISTS sub_category character varying(255),
ADD COLUMN IF NOT EXISTS inventory_status character varying(255),
ADD COLUMN IF NOT EXISTS physical_dimension_depth numeric(10,2),
ADD COLUMN IF NOT EXISTS craft character varying(255),
ADD COLUMN IF NOT EXISTS growing_method character varying(255),
ADD COLUMN IF NOT EXISTS product_short_description character varying(500),
ADD COLUMN IF NOT EXISTS physical_dimension_volume numeric(10,2),
ADD COLUMN IF NOT EXISTS unit_price numeric(10,2),
ADD COLUMN IF NOT EXISTS ocs_variant_number character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS extraction_process character varying(255),
ADD COLUMN IF NOT EXISTS physical_dimension_height numeric(10,2),
ADD COLUMN IF NOT EXISTS delivery_tier character varying(255),
ADD COLUMN IF NOT EXISTS carrier_oil character varying(255),
ADD COLUMN IF NOT EXISTS plant_type character varying(255),
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS rating numeric(3,2),
ADD COLUMN IF NOT EXISTS eaches_per_inner_pack integer,
ADD COLUMN IF NOT EXISTS eaches_per_master_case integer,
ADD COLUMN IF NOT EXISTS product_long_description text,
ADD COLUMN IF NOT EXISTS food_allergens text,
ADD COLUMN IF NOT EXISTS grow_medium character varying(255),
ADD COLUMN IF NOT EXISTS cbd_content_per_unit numeric(10,2),
ADD COLUMN IF NOT EXISTS battery_type character varying(255),
ADD COLUMN IF NOT EXISTS storage_criteria text,
ADD COLUMN IF NOT EXISTS size character varying(255),
ADD COLUMN IF NOT EXISTS removable_battery boolean,
ADD COLUMN IF NOT EXISTS supplier_name character varying(255),
ADD COLUMN IF NOT EXISTS compatibility text,
ADD COLUMN IF NOT EXISTS physical_dimension_weight numeric(10,2),
ADD COLUMN IF NOT EXISTS dried_flower_cannabis_equivalency numeric(10,2),
ADD COLUMN IF NOT EXISTS street_name character varying(255),
ADD COLUMN IF NOT EXISTS trimming_method character varying(255),
ADD COLUMN IF NOT EXISTS pack_size integer,
ADD COLUMN IF NOT EXISTS physical_dimension_width numeric(10,2),
ADD COLUMN IF NOT EXISTS thc_content_per_volume numeric(10,2),
ADD COLUMN IF NOT EXISTS strain_type character varying(255),
ADD COLUMN IF NOT EXISTS unit_of_measure character varying(255),
ADD COLUMN IF NOT EXISTS grow_region character varying(255),
ADD COLUMN IF NOT EXISTS net_weight numeric(10,2),
ADD COLUMN IF NOT EXISTS stock_status character varying(255)
;

-- Table: order_status_history
ALTER TABLE order_status_history
ADD COLUMN IF NOT EXISTS status character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS notes text
;

-- Table: otp_codes
ALTER TABLE otp_codes
ADD COLUMN IF NOT EXISTS identifier character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS identifier_type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS purpose character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS code character varying(10) NOT NULL,
ADD COLUMN IF NOT EXISTS verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS user_agent text,
ADD COLUMN IF NOT EXISTS ip_address character varying(45)
;

-- Table: otp_rate_limits
ALTER TABLE otp_rate_limits
ADD COLUMN IF NOT EXISTS blocked_until timestamp without time zone,
ADD COLUMN IF NOT EXISTS identifier character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS identifier_type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS last_request_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS first_request_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: parameter_accuracy
ALTER TABLE parameter_accuracy
ADD COLUMN IF NOT EXISTS is_correct boolean,
ADD COLUMN IF NOT EXISTS parameter_type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS inferred_value text,
ADD COLUMN IF NOT EXISTS confidence_score double precision,
ADD COLUMN IF NOT EXISTS correct_value text
;

-- Table: payment_audit_log
ALTER TABLE payment_audit_log
ADD COLUMN IF NOT EXISTS entity_type character varying(50),
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS entity_id character varying(255),
ADD COLUMN IF NOT EXISTS details jsonb DEFAULT '{}'::jsonb
;

-- Table: payment_credentials
ALTER TABLE payment_credentials
ADD COLUMN IF NOT EXISTS encryption_metadata jsonb NOT NULL,
ADD COLUMN IF NOT EXISTS encrypted_data text NOT NULL,
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS provider character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS description text,
ADD COLUMN IF NOT EXISTS revoked_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS updated_by uuid
;

-- Table: payment_disputes
ALTER TABLE payment_disputes
ADD COLUMN IF NOT EXISTS provider_id uuid,
ADD COLUMN IF NOT EXISTS amount numeric(10,2) NOT NULL,
ADD COLUMN IF NOT EXISTS reason_code character varying(50),
ADD COLUMN IF NOT EXISTS reason character varying(255),
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS provider_response jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS evidence_due_date date,
ADD COLUMN IF NOT EXISTS evidence_submitted jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'CAD'::character varying,
ADD COLUMN IF NOT EXISTS merchant_response text,
ADD COLUMN IF NOT EXISTS dispute_id character varying(255)
;

-- Table: payment_fee_splits
ALTER TABLE payment_fee_splits
ADD COLUMN IF NOT EXISTS platform_percentage_fee numeric(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS provider_fee numeric(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS platform_fee_collected_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS tenant_net_amount numeric(10,2) NOT NULL,
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS gross_amount numeric(10,2) NOT NULL,
ADD COLUMN IF NOT EXISTS platform_fee numeric(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS platform_fixed_fee numeric(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS tenant_settled boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS platform_fee_collected boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS tenant_settled_at timestamp with time zone
;

-- Table: payment_idempotency_keys
ALTER TABLE payment_idempotency_keys
ADD COLUMN IF NOT EXISTS status character varying(20) DEFAULT 'processing'::character varying,
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS response jsonb
;

-- Table: payment_methods
ALTER TABLE payment_methods
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS display_name character varying(100),
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS payment_token text,
ADD COLUMN IF NOT EXISTS last_used_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS card_last_four character varying(4)
;

-- Table: payment_metrics
ALTER TABLE payment_metrics
ADD COLUMN IF NOT EXISTS net_amount numeric(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS metrics_by_type jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS success_rate numeric(5,2),
ADD COLUMN IF NOT EXISTS avg_transaction_time_ms integer,
ADD COLUMN IF NOT EXISTS date date NOT NULL,
ADD COLUMN IF NOT EXISTS total_refunds numeric(10,2) DEFAULT 0
;

-- Table: payment_provider_health_metrics
ALTER TABLE payment_provider_health_metrics
ADD COLUMN IF NOT EXISTS error_type character varying(100),
ADD COLUMN IF NOT EXISTS is_successful boolean,
ADD COLUMN IF NOT EXISTS endpoint character varying(255),
ADD COLUMN IF NOT EXISTS checked_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS method character varying(10),
ADD COLUMN IF NOT EXISTS tenant_provider_id uuid,
ADD COLUMN IF NOT EXISTS status_code integer
;

-- Table: payment_providers
ALTER TABLE payment_providers
ADD COLUMN IF NOT EXISTS name character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS fee_structure jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS supported_card_types text[] DEFAULT ARRAY['visa'::text, 'mastercard'::text, 'amex'::text],
ADD COLUMN IF NOT EXISTS capabilities jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS is_default boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS webhook_url text,
ADD COLUMN IF NOT EXISTS settlement_schedule character varying(50) DEFAULT 'daily'::character varying
;

-- Table: payment_refunds
ALTER TABLE payment_refunds
ADD COLUMN IF NOT EXISTS notes text,
ADD COLUMN IF NOT EXISTS initiated_by uuid,
ADD COLUMN IF NOT EXISTS refund_transaction_id uuid,
ADD COLUMN IF NOT EXISTS amount numeric(10,2) NOT NULL,
ADD COLUMN IF NOT EXISTS reason character varying(255),
ADD COLUMN IF NOT EXISTS completed_at timestamp with time zone
;

-- Table: payment_settlements
ALTER TABLE payment_settlements
ADD COLUMN IF NOT EXISTS settlement_id character varying(255),
ADD COLUMN IF NOT EXISTS refund_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS reconciled_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS chargeback_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS bank_account_last_four character varying(4),
ADD COLUMN IF NOT EXISTS gross_amount numeric(12,2) NOT NULL,
ADD COLUMN IF NOT EXISTS adjustment_amount numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS settlement_report_url text,
ADD COLUMN IF NOT EXISTS refund_amount numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'CAD'::character varying,
ADD COLUMN IF NOT EXISTS chargeback_amount numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS deposit_date date
;

-- Table: payment_subscriptions
ALTER TABLE payment_subscriptions
ADD COLUMN IF NOT EXISTS next_billing_date date,
ADD COLUMN IF NOT EXISTS provider_id uuid,
ADD COLUMN IF NOT EXISTS interval character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS trial_end_date date,
ADD COLUMN IF NOT EXISTS cancelled_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS subscription_id character varying(255),
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS interval_count integer DEFAULT 1,
ADD COLUMN IF NOT EXISTS billing_cycles_completed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_payment_count integer DEFAULT 0
;

-- Table: payment_transactions
ALTER TABLE payment_transactions
ADD COLUMN IF NOT EXISTS net_amount numeric(10,2),
ADD COLUMN IF NOT EXISTS idempotency_key character varying(255),
ADD COLUMN IF NOT EXISTS provider_fee numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS fraud_status character varying(50),
ADD COLUMN IF NOT EXISTS risk_factors jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS tenant_provider_id uuid,
ADD COLUMN IF NOT EXISTS processed_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS tenant_net_amount numeric(10,2),
ADD COLUMN IF NOT EXISTS authentication_status character varying(50),
ADD COLUMN IF NOT EXISTS transaction_reference character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS user_agent text,
ADD COLUMN IF NOT EXISTS ip_address inet,
ADD COLUMN IF NOT EXISTS risk_score integer,
ADD COLUMN IF NOT EXISTS device_fingerprint text,
ADD COLUMN IF NOT EXISTS failed_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS tax_amount numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS platform_fee numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS authentication_data jsonb DEFAULT '{}'::jsonb
;

-- Table: payment_webhook_routes
ALTER TABLE payment_webhook_routes
ADD COLUMN IF NOT EXISTS tenant_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS provider character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS webhook_url_path character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS tenant_provider_id uuid
;

-- Table: payment_webhooks
ALTER TABLE payment_webhooks
ADD COLUMN IF NOT EXISTS signature_verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS processing_error text,
ADD COLUMN IF NOT EXISTS webhook_id character varying(255),
ADD COLUMN IF NOT EXISTS processed boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS received_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: price_history
ALTER TABLE price_history
ADD COLUMN IF NOT EXISTS changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS product_id character varying(100) NOT NULL
;

-- Table: price_tiers
ALTER TABLE price_tiers
ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS customer_type character varying(50),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS name character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS min_monthly_volume numeric(10,2),
ADD COLUMN IF NOT EXISTS min_order_value numeric(10,2),
ADD COLUMN IF NOT EXISTS description text
;

-- Table: pricing_rules
ALTER TABLE pricing_rules
ADD COLUMN IF NOT EXISTS sub_category character varying(100),
ADD COLUMN IF NOT EXISTS sub_sub_category character varying(100),
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: product_ratings
ALTER TABLE product_ratings
ADD COLUMN IF NOT EXISTS verified_purchase_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_reviews integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS rating_distribution jsonb DEFAULT '{"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}'::jsonb,
ADD COLUMN IF NOT EXISTS recommended_percentage numeric(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS sku character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: product_recommendations
ALTER TABLE product_recommendations
ADD COLUMN IF NOT EXISTS based_on character varying(50),
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS conversion_rate numeric(5,4) DEFAULT 0,
ADD COLUMN IF NOT EXISTS recommended_product_id character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS revenue_impact numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS product_id character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS click_through_rate numeric(5,4) DEFAULT 0
;

-- Table: profiles
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS total_spent numeric(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS phone character varying(50),
ADD COLUMN IF NOT EXISTS customer_type character varying(50) DEFAULT 'regular'::character varying,
ADD COLUMN IF NOT EXISTS last_interaction timestamp without time zone,
ADD COLUMN IF NOT EXISTS first_name character varying(100),
ADD COLUMN IF NOT EXISTS last_name character varying(100),
ADD COLUMN IF NOT EXISTS preferred_effects jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS medical_conditions jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS order_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS experience_level character varying(50),
ADD COLUMN IF NOT EXISTS purchase_history jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS preferred_categories jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS price_range jsonb,
ADD COLUMN IF NOT EXISTS language character varying(10) DEFAULT 'en'::character varying,
ADD COLUMN IF NOT EXISTS address text,
ADD COLUMN IF NOT EXISTS preferred_payment_method character varying(50),
ADD COLUMN IF NOT EXISTS needs jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS interaction_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS payment_methods jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS city character varying(100),
ADD COLUMN IF NOT EXISTS is_verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS postal_code character varying(20),
ADD COLUMN IF NOT EXISTS tags jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS marketing_consent boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS timezone character varying(50),
ADD COLUMN IF NOT EXISTS last_order_date timestamp without time zone,
ADD COLUMN IF NOT EXISTS notes text,
ADD COLUMN IF NOT EXISTS state character varying(50),
ADD COLUMN IF NOT EXISTS sms_consent boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS date_of_birth date,
ADD COLUMN IF NOT EXISTS country character varying(100) DEFAULT 'USA'::character varying
;

-- Table: promotion_usage
ALTER TABLE promotion_usage
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS customer_id uuid
;

-- Table: promotions
ALTER TABLE promotions
ADD COLUMN IF NOT EXISTS recurrence_type character varying(20) DEFAULT 'none'::character varying,
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS discount_value numeric(10,2) NOT NULL,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS total_usage_limit integer,
ADD COLUMN IF NOT EXISTS time_end time without time zone,
ADD COLUMN IF NOT EXISTS discount_type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS max_discount_amount numeric(10,2),
ADD COLUMN IF NOT EXISTS created_by_user_id uuid,
ADD COLUMN IF NOT EXISTS brand_ids text[],
ADD COLUMN IF NOT EXISTS is_continuous boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS customer_tier_ids text[],
ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS stackable boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS applies_to character varying(50) DEFAULT 'all'::character varying,
ADD COLUMN IF NOT EXISTS hour_of_day text[],
ADD COLUMN IF NOT EXISTS usage_limit_per_customer integer,
ADD COLUMN IF NOT EXISTS time_start time without time zone,
ADD COLUMN IF NOT EXISTS timezone character varying(50) DEFAULT 'America/Toronto'::character varying,
ADD COLUMN IF NOT EXISTS day_of_week text[],
ADD COLUMN IF NOT EXISTS min_purchase_amount numeric(10,2),
ADD COLUMN IF NOT EXISTS category_ids text[],
ADD COLUMN IF NOT EXISTS product_ids text[],
ADD COLUMN IF NOT EXISTS first_time_customer_only boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS exclude_product_ids text[]
;

-- Table: provinces_territories
ALTER TABLE provinces_territories
ADD COLUMN IF NOT EXISTS pickup_allowed boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS license_prefix character varying(10),
ADD COLUMN IF NOT EXISTS min_age integer DEFAULT 19,
ADD COLUMN IF NOT EXISTS delivery_allowed boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS type character varying(20) NOT NULL,
ADD COLUMN IF NOT EXISTS settings jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS regulatory_body character varying(255)
;

-- Table: provincial_suppliers
ALTER TABLE provincial_suppliers
ADD COLUMN IF NOT EXISTS address text,
ADD COLUMN IF NOT EXISTS phone character varying(50),
ADD COLUMN IF NOT EXISTS contact_person character varying(255),
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS provinces_territories_id uuid,
ADD COLUMN IF NOT EXISTS is_provincial_supplier boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS payment_terms character varying(100),
ADD COLUMN IF NOT EXISTS email character varying(255)
;

-- Table: purchase_order_items
ALTER TABLE purchase_order_items
ADD COLUMN IF NOT EXISTS uom_conversion numeric(10,4),
ADD COLUMN IF NOT EXISTS uom character varying(50),
ADD COLUMN IF NOT EXISTS packaged_on_date date,
ADD COLUMN IF NOT EXISTS shipped_qty integer,
ADD COLUMN IF NOT EXISTS brand character varying(255),
ADD COLUMN IF NOT EXISTS gtin_barcode character varying(100),
ADD COLUMN IF NOT EXISTS exists_in_inventory boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS uom_conversion_qty integer,
ADD COLUMN IF NOT EXISTS batch_lot character varying(100),
ADD COLUMN IF NOT EXISTS each_gtin character varying(100),
ADD COLUMN IF NOT EXISTS line_total numeric(12,2),
ADD COLUMN IF NOT EXISTS sku character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS vendor character varying(255),
ADD COLUMN IF NOT EXISTS case_gtin character varying(100),
ADD COLUMN IF NOT EXISTS item_name character varying(255)
;

-- Table: purchase_orders
ALTER TABLE purchase_orders
ADD COLUMN IF NOT EXISTS expected_date date,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS vendor character varying(255),
ADD COLUMN IF NOT EXISTS ocs_order_number character varying(100),
ADD COLUMN IF NOT EXISTS shipment_id character varying(100),
ADD COLUMN IF NOT EXISTS received_date timestamp without time zone,
ADD COLUMN IF NOT EXISTS container_id character varying(100)
;

-- Table: push_subscriptions
ALTER TABLE push_subscriptions
ADD COLUMN IF NOT EXISTS is_sandbox boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS notification_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS app_version character varying(20),
ADD COLUMN IF NOT EXISTS device_token character varying(500) NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS failed_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_active_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS device_name character varying(100),
ADD COLUMN IF NOT EXISTS customer_id text NOT NULL,
ADD COLUMN IF NOT EXISTS device_model character varying(100),
ADD COLUMN IF NOT EXISTS os_version character varying(20)
;

-- Table: recommendation_metrics
ALTER TABLE recommendation_metrics
ADD COLUMN IF NOT EXISTS customer_id uuid,
ADD COLUMN IF NOT EXISTS session_id character varying(100),
ADD COLUMN IF NOT EXISTS event_type character varying(50),
ADD COLUMN IF NOT EXISTS event_value numeric(10,2)
;

-- Table: review_attributes
ALTER TABLE review_attributes
ADD COLUMN IF NOT EXISTS attribute_value character varying(100),
ADD COLUMN IF NOT EXISTS rating integer
;

-- Table: review_media
ALTER TABLE review_media
ADD COLUMN IF NOT EXISTS caption character varying(500)
;

-- Table: role_permissions
ALTER TABLE role_permissions
ADD COLUMN IF NOT EXISTS granted boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS resource_type character varying(50) NOT NULL
;

-- Table: shelf_locations
ALTER TABLE shelf_locations
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS location_type character varying(50) DEFAULT 'standard'::character varying,
ADD COLUMN IF NOT EXISTS notes text,
ADD COLUMN IF NOT EXISTS shelf character varying(50),
ADD COLUMN IF NOT EXISTS bin character varying(50),
ADD COLUMN IF NOT EXISTS location_code character varying(200),
ADD COLUMN IF NOT EXISTS zone character varying(50),
ADD COLUMN IF NOT EXISTS max_volume_m3 numeric(10,4),
ADD COLUMN IF NOT EXISTS max_weight_kg numeric(10,2),
ADD COLUMN IF NOT EXISTS is_available boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS aisle character varying(50),
ADD COLUMN IF NOT EXISTS temperature_range character varying(100)
;

-- Table: skip_words
ALTER TABLE skip_words
ADD COLUMN IF NOT EXISTS active boolean DEFAULT true
;

-- Table: staff_delivery_status
ALTER TABLE staff_delivery_status
ADD COLUMN IF NOT EXISTS available_from timestamp without time zone,
ADD COLUMN IF NOT EXISTS current_longitude numeric(11,8),
ADD COLUMN IF NOT EXISTS current_status character varying(50) DEFAULT 'offline'::character varying,
ADD COLUMN IF NOT EXISTS deliveries_today integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS deliveries_completed integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS current_deliveries integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS current_latitude numeric(10,8),
ADD COLUMN IF NOT EXISTS max_deliveries integer DEFAULT 5,
ADD COLUMN IF NOT EXISTS last_location_update timestamp without time zone,
ADD COLUMN IF NOT EXISTS average_delivery_time_minutes integer,
ADD COLUMN IF NOT EXISTS available_until timestamp without time zone
;

-- Table: store_settings
ALTER TABLE store_settings
ADD COLUMN IF NOT EXISTS category character varying(100) NOT NULL
;

-- Table: supported_languages
ALTER TABLE supported_languages
ADD COLUMN IF NOT EXISTS coverage_percentage numeric(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS is_rtl boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS name character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS code character varying(10) NOT NULL
;

-- Table: tax_rates
ALTER TABLE tax_rates
ADD COLUMN IF NOT EXISTS effective_to date,
ADD COLUMN IF NOT EXISTS provincial_tax_rate numeric(5,4) DEFAULT 0,
ADD COLUMN IF NOT EXISTS tenant_id uuid,
ADD COLUMN IF NOT EXISTS federal_tax_rate numeric(5,4) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cannabis_excise_duty numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS environmental_fee numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS recycling_fee numeric(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS excise_calculation_method character varying(50) DEFAULT 'percentage'::character varying
;

-- Table: token_blacklist
ALTER TABLE token_blacklist
ADD COLUMN IF NOT EXISTS user_id uuid,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS token_id character varying(255) NOT NULL
;

-- Table: training_examples
ALTER TABLE training_examples
ADD COLUMN IF NOT EXISTS added_by character varying(100) DEFAULT 'admin'::character varying,
ADD COLUMN IF NOT EXISTS feedback_score double precision DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS entities jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS dataset_name character varying(255),
ADD COLUMN IF NOT EXISTS query text NOT NULL,
ADD COLUMN IF NOT EXISTS dataset_id character varying(255),
ADD COLUMN IF NOT EXISTS expected_intent character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS expected_response_qualities jsonb DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS context jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS expected_response text,
ADD COLUMN IF NOT EXISTS expected_products jsonb DEFAULT '[]'::jsonb
;

-- Table: training_sessions
ALTER TABLE training_sessions
ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'in_progress'::character varying,
ADD COLUMN IF NOT EXISTS session_id character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS examples_trained integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS accuracy_before double precision DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_message text,
ADD COLUMN IF NOT EXISTS accuracy_after double precision DEFAULT 0,
ADD COLUMN IF NOT EXISTS dataset_id character varying(255),
ADD COLUMN IF NOT EXISTS completed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS improvements jsonb DEFAULT '{}'::jsonb
;

-- Table: translation_batch_items
ALTER TABLE translation_batch_items
ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'pending'::character varying,
ADD COLUMN IF NOT EXISTS error_message text,
ADD COLUMN IF NOT EXISTS processing_time_ms integer,
ADD COLUMN IF NOT EXISTS completed_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS context character varying(255)
;

-- Table: translation_batches
ALTER TABLE translation_batches
ADD COLUMN IF NOT EXISTS target_language character varying(10) NOT NULL,
ADD COLUMN IF NOT EXISTS namespace character varying(100),
ADD COLUMN IF NOT EXISTS batch_key character varying(255) NOT NULL,
ADD COLUMN IF NOT EXISTS started_at timestamp without time zone,
ADD COLUMN IF NOT EXISTS completed_items integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_items integer NOT NULL,
ADD COLUMN IF NOT EXISTS metadata jsonb
;

-- Table: translation_overrides
ALTER TABLE translation_overrides
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS reason text,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS override_text text NOT NULL,
ADD COLUMN IF NOT EXISTS translation_id uuid,
ADD COLUMN IF NOT EXISTS created_by character varying(255)
;

-- Table: translations
ALTER TABLE translations
ADD COLUMN IF NOT EXISTS is_cached boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS target_language character varying(10) NOT NULL,
ADD COLUMN IF NOT EXISTS model_version character varying(50),
ADD COLUMN IF NOT EXISTS source_text text NOT NULL,
ADD COLUMN IF NOT EXISTS namespace character varying(100),
ADD COLUMN IF NOT EXISTS last_used_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS confidence_score numeric(3,2),
ADD COLUMN IF NOT EXISTS translated_text text NOT NULL,
ADD COLUMN IF NOT EXISTS source_language character varying(10) DEFAULT 'en'::character varying,
ADD COLUMN IF NOT EXISTS is_verified boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS usage_count integer DEFAULT 1
;

-- Table: unsubscribe_list
ALTER TABLE unsubscribe_list
ADD COLUMN IF NOT EXISTS resubscribe_allowed_after timestamp without time zone,
ADD COLUMN IF NOT EXISTS phone_number character varying(20),
ADD COLUMN IF NOT EXISTS additional_comments text,
ADD COLUMN IF NOT EXISTS channel_type character varying(50) NOT NULL,
ADD COLUMN IF NOT EXISTS unsubscribe_source character varying(50),
ADD COLUMN IF NOT EXISTS customer_id text,
ADD COLUMN IF NOT EXISTS is_permanent boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT now(),
ADD COLUMN IF NOT EXISTS broadcast_id uuid
;

-- Table: user_addresses
ALTER TABLE user_addresses
ADD COLUMN IF NOT EXISTS validation_data jsonb,
ADD COLUMN IF NOT EXISTS phone_number character varying(50),
ADD COLUMN IF NOT EXISTS is_validated boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS address_type character varying(50) DEFAULT 'delivery'::character varying,
ADD COLUMN IF NOT EXISTS province_state character varying(100) NOT NULL,
ADD COLUMN IF NOT EXISTS unit_number character varying(50)
;

-- Table: user_login_logs
ALTER TABLE user_login_logs
ADD COLUMN IF NOT EXISTS region character varying(100),
ADD COLUMN IF NOT EXISTS session_id character varying(255),
ADD COLUMN IF NOT EXISTS latitude numeric(10,8),
ADD COLUMN IF NOT EXISTS timezone character varying(50),
ADD COLUMN IF NOT EXISTS country character varying(100),
ADD COLUMN IF NOT EXISTS city character varying(100),
ADD COLUMN IF NOT EXISTS longitude numeric(11,8),
ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS postal_code character varying(20),
ADD COLUMN IF NOT EXISTS isp character varying(200),
ADD COLUMN IF NOT EXISTS device_fingerprint character varying(255)
;

-- Table: user_sessions
ALTER TABLE user_sessions
ADD COLUMN IF NOT EXISTS last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP
;

-- Table: voice_auth_logs
ALTER TABLE voice_auth_logs
ADD COLUMN IF NOT EXISTS user_agent text,
ADD COLUMN IF NOT EXISTS timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS age_info jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS success boolean NOT NULL
;

-- Table: voice_profiles
ALTER TABLE voice_profiles
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS age_verification jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS voice_embedding text NOT NULL
;

-- Table: wishlist
ALTER TABLE wishlist
ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS product_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS customer_id uuid NOT NULL,
ADD COLUMN IF NOT EXISTS store_id uuid NOT NULL
;

-- ============================================================================
-- STEP 3: Create 1 Missing Views
-- ============================================================================

CREATE OR REPLACE VIEW recent_login_activity AS
 SELECT ull.id,
    ull.user_id,
    u.email,
    (((u.first_name)::text || ' '::text) || (u.last_name)::text) AS full_name,
    ull.tenant_id,
    t.name AS tenant_name,
    ull.login_timestamp,
    ull.login_successful,
    ull.login_method,
    ull.ip_address,
    ull.country,
    ull.city,
    ull.user_agent
   FROM ((user_login_logs ull
     JOIN users u ON ((ull.user_id = u.id)))
     LEFT JOIN tenants t ON ((ull.tenant_id = t.id)))
  WHERE (ull.login_timestamp > (CURRENT_TIMESTAMP - '30 days'::interval))
  ORDER BY ull.login_timestamp DESC;
;

-- ============================================================================
-- STEP 4: Create 89 Missing Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION public.apply_discount_code(p_code character varying, p_user_id uuid, p_subtotal numeric, p_tenant_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_discount RECORD;
    v_usage_count INTEGER;
    v_discount_amount DECIMAL;
BEGIN
    -- Find valid discount code
    SELECT * INTO v_discount
    FROM discount_codes
    WHERE UPPER(code) = UPPER(p_code)
        AND is_active = TRUE
        AND (tenant_id = p_tenant_id OR tenant_id IS NULL)
        AND CURRENT_TIMESTAMP BETWEEN valid_from AND COALESCE(valid_until, CURRENT_TIMESTAMP + INTERVAL '1 day')
        AND p_subtotal >= minimum_purchase;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Invalid or expired discount code'
        );
    END IF;
    
    -- Check usage limits
    IF v_discount.usage_limit IS NOT NULL AND v_discount.usage_count >= v_discount.usage_limit THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Discount code usage limit reached'
        );
    END IF;
    
    -- Check per-customer usage limit
    IF p_user_id IS NOT NULL AND v_discount.usage_limit_per_customer IS NOT NULL THEN
        SELECT COUNT(*) INTO v_usage_count
        FROM discount_usage
        WHERE discount_id = v_discount.id AND user_id = p_user_id;
        
        IF v_usage_count >= v_discount.usage_limit_per_customer THEN
            RETURN jsonb_build_object(
                'success', FALSE,
                'message', 'You have already used this discount code'
            );
        END IF;
    END IF;
    
    -- Calculate discount amount
    IF v_discount.discount_type = 'percentage' THEN
        v_discount_amount := p_subtotal * (v_discount.discount_value / 100);
        IF v_discount.maximum_discount IS NOT NULL THEN
            v_discount_amount := LEAST(v_discount_amount, v_discount.maximum_discount);
        END IF;
    ELSIF v_discount.discount_type = 'fixed' THEN
        v_discount_amount := LEAST(v_discount.discount_value, p_subtotal);
    ELSE
        v_discount_amount := 0; -- Handle other types separately
    END IF;
    
    RETURN jsonb_build_object(
        'success', TRUE,
        'discount_id', v_discount.id,
        'discount_amount', ROUND(v_discount_amount, 2),
        'discount_type', v_discount.discount_type,
        'message', v_discount.description
    );
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_checkout_taxes(p_checkout_id uuid, p_subtotal numeric)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_tax_rate RECORD;
    v_province_id UUID;
    v_federal_tax DECIMAL;
    v_provincial_tax DECIMAL;
    v_excise_duty DECIMAL;
    v_total_tax DECIMAL;
BEGIN
    -- Get province from checkout session
    SELECT 
        COALESCE(
            s.province_territory_id,
            (checkout_sessions.delivery_address->>'province_id')::UUID
        ) INTO v_province_id
    FROM checkout_sessions
    LEFT JOIN stores s ON checkout_sessions.pickup_store_id = s.id
    WHERE checkout_sessions.id = p_checkout_id;
    
    -- Get applicable tax rates
    SELECT * INTO v_tax_rate
    FROM tax_rates
    WHERE province_territory_id = v_province_id
        AND is_active = TRUE
        AND CURRENT_DATE BETWEEN effective_from AND COALESCE(effective_to, CURRENT_DATE + INTERVAL '1 day')
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF NOT FOUND THEN
        -- Default tax rates if not configured
        v_federal_tax := p_subtotal * 0.05; -- 5% GST
        v_provincial_tax := p_subtotal * 0.08; -- 8% PST (example)
        v_excise_duty := p_subtotal * 0.10; -- 10% excise (example)
    ELSE
        v_federal_tax := p_subtotal * v_tax_rate.federal_tax_rate;
        v_provincial_tax := p_subtotal * v_tax_rate.provincial_tax_rate;
        
        IF v_tax_rate.excise_calculation_method = 'percentage' THEN
            v_excise_duty := p_subtotal * (v_tax_rate.cannabis_excise_duty / 100);
        ELSE
            -- Would need to calculate based on weight
            v_excise_duty := v_tax_rate.cannabis_excise_duty;
        END IF;
    END IF;
    
    v_total_tax := v_federal_tax + v_provincial_tax + v_excise_duty;
    
    RETURN jsonb_build_object(
        'federal_tax', ROUND(v_federal_tax, 2),
        'provincial_tax', ROUND(v_provincial_tax, 2),
        'excise_duty', ROUND(v_excise_duty, 2),
        'total_tax', ROUND(v_total_tax, 2)
    );
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_distance(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
 RETURNS numeric
 LANGUAGE plpgsql
AS $function$
DECLARE
    R CONSTANT DECIMAL := 6371; -- Earth radius in kilometers
    dlat DECIMAL;
    dlon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlon := radians(lon2 - lon1);
    a := sin(dlat/2) * sin(dlat/2) +
         cos(radians(lat1)) * cos(radians(lat2)) *
         sin(dlon/2) * sin(dlon/2);
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    RETURN R * c;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_final_price(p_product_id character varying, p_quantity integer, p_customer_id uuid, p_tenant_id uuid)
 RETURNS TABLE(base_price numeric, tier_discount numeric, promo_discount numeric, volume_discount numeric, final_price numeric)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_base_price DECIMAL(10,2);
    v_tier_discount DECIMAL(10,2) := 0;
    v_promo_discount DECIMAL(10,2) := 0;
    v_volume_discount DECIMAL(10,2) := 0;
BEGIN
    -- Get base price from product catalog
    SELECT unit_price * p_quantity INTO v_base_price
    FROM product_catalog
    WHERE ocs_variant_number = p_product_id;
    
    -- Calculate tier discount
    SELECT COALESCE(MAX(pt.discount_percentage), 0) INTO v_tier_discount
    FROM customer_pricing_rules cpr
    JOIN price_tiers pt ON cpr.price_tier_id = pt.id
    WHERE cpr.tenant_id = p_tenant_id
    AND cpr.active = true;
    
    -- Calculate applicable promotions (simplified)
    SELECT COALESCE(MAX(discount_value), 0) INTO v_promo_discount
    FROM promotions
    WHERE active = true
    AND CURRENT_TIMESTAMP BETWEEN start_date AND COALESCE(end_date, CURRENT_TIMESTAMP + INTERVAL '1 day')
    AND (applies_to = 'all' OR p_product_id = ANY(product_ids));
    
    -- Calculate volume discount
    IF p_quantity >= 100 THEN
        v_volume_discount := 10;
    ELSIF p_quantity >= 50 THEN
        v_volume_discount := 7;
    ELSIF p_quantity >= 20 THEN
        v_volume_discount := 5;
    ELSIF p_quantity >= 10 THEN
        v_volume_discount := 3;
    END IF;
    
    RETURN QUERY
    SELECT 
        v_base_price,
        v_base_price * v_tier_discount / 100,
        v_base_price * v_promo_discount / 100,
        v_base_price * v_volume_discount / 100,
        v_base_price * (1 - (v_tier_discount + v_promo_discount + v_volume_discount) / 100);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_holiday_date(p_year integer, p_holiday_id uuid)
 RETURNS date
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_holiday holidays%ROWTYPE;
    v_date DATE;
BEGIN
    SELECT * INTO v_holiday FROM holidays WHERE id = p_holiday_id;
    
    IF v_holiday.date_type = 'fixed' THEN
        v_date := make_date(p_year, v_holiday.fixed_month, v_holiday.fixed_day);
    ELSIF v_holiday.date_type = 'floating' THEN
        -- This would need more complex logic for floating dates
        -- Simplified example
        v_date := make_date(p_year, (v_holiday.floating_rule->>'month')::int, 1);
    ELSIF v_holiday.date_type = 'calculated' THEN
        -- Handle calculated dates like Easter
        -- This would require complex calculation
        v_date := make_date(p_year, 4, 1); -- Placeholder
    END IF;
    
    RETURN v_date;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_platform_fee(p_amount numeric, p_percentage_fee numeric, p_fixed_fee numeric)
 RETURNS TABLE(platform_fee numeric, tenant_net numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    platform_fee := ROUND((p_amount * p_percentage_fee) + p_fixed_fee, 2);
    tenant_net := p_amount - platform_fee;
    RETURN NEXT;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_geofence_entry(point_lat numeric, point_lon numeric, fence_lat numeric, fence_lon numeric, fence_radius_meters integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    distance_km DECIMAL;
BEGIN
    distance_km := calculate_distance(point_lat, point_lon, fence_lat, fence_lon);
    RETURN (distance_km * 1000) <= fence_radius_meters;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_idempotency_key(p_key character varying, p_tenant_id uuid, p_request_hash character varying)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_result RECORD;
BEGIN
    -- Check for existing key
    SELECT status, response, request_hash
    INTO v_result
    FROM payment_idempotency_keys
    WHERE idempotency_key = p_key
    AND tenant_id = p_tenant_id
    AND expires_at > CURRENT_TIMESTAMP;
    
    IF v_result.status IS NOT NULL THEN
        -- Key exists, check if same request
        IF v_result.request_hash = p_request_hash THEN
            -- Same request, return cached response
            RETURN v_result.response;
        ELSE
            -- Different request with same key
            RAISE EXCEPTION 'Idempotency key already used for different request';
        END IF;
    END IF;
    
    -- Key doesn't exist, insert it
    INSERT INTO payment_idempotency_keys (
        idempotency_key, tenant_id, request_hash, status
    ) VALUES (
        p_key, p_tenant_id, p_request_hash, 'processing'
    );
    
    RETURN NULL;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_inventory_exists(p_sku character varying, p_batch_lot character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM batch_tracking 
        WHERE sku = p_sku 
        AND batch_lot = p_batch_lot 
        AND quantity_remaining > 0
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_otp_rate_limit(p_identifier character varying, p_identifier_type character varying, p_max_requests integer DEFAULT 5, p_window_minutes integer DEFAULT 60)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
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
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_idempotency_keys()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_idempotency_keys
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_otp_codes()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    DELETE FROM otp_codes 
    WHERE expires_at < CURRENT_TIMESTAMP 
    AND verified = FALSE;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_tokens()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM auth_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
    OR (is_used = true AND used_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_old_audit_logs()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_audit_log
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.create_auth_token(p_user_id uuid, p_token_type character varying, p_token_hash character varying, p_expires_in_hours integer DEFAULT 24, p_metadata jsonb DEFAULT '{}'::jsonb)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
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
$function$

;

CREATE OR REPLACE FUNCTION public.expire_checkout_sessions()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE checkout_sessions
    SET status = 'expired'
    WHERE status = 'draft'
        AND expires_at < CURRENT_TIMESTAMP;
    
    -- Release inventory reservations for expired sessions
    UPDATE inventory_reservations
    SET released = TRUE
    WHERE checkout_session_id IN (
        SELECT id FROM checkout_sessions
        WHERE status = 'expired'
    ) AND released = FALSE;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.generate_product_slug(p_brand text, p_product_name text, p_sub_category text, p_size text, p_colour text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    slug_parts TEXT[];
    result_slug TEXT;
BEGIN
    -- Initialize array
    slug_parts := ARRAY[]::TEXT[];
    
    -- Add brand if not null
    IF p_brand IS NOT NULL AND p_brand != '' THEN
        slug_parts := array_append(slug_parts, p_brand);
    END IF;
    
    -- Add product name if not null
    IF p_product_name IS NOT NULL AND p_product_name != '' THEN
        slug_parts := array_append(slug_parts, p_product_name);
    END IF;
    
    -- Add sub-category if not null
    IF p_sub_category IS NOT NULL AND p_sub_category != '' THEN
        slug_parts := array_append(slug_parts, p_sub_category);
    END IF;
    
    -- Add size if not null
    IF p_size IS NOT NULL AND p_size != '' THEN
        slug_parts := array_append(slug_parts, p_size);
    END IF;
    
    -- Add colour if not null (optional field)
    IF p_colour IS NOT NULL AND p_colour != '' THEN
        slug_parts := array_append(slug_parts, p_colour);
    END IF;
    
    -- Join parts with hyphen
    result_slug := array_to_string(slug_parts, '-');
    
    -- Clean up the slug
    -- Convert to lowercase
    result_slug := lower(result_slug);
    -- Replace spaces and special characters with hyphens
    result_slug := regexp_replace(result_slug, '[^a-z0-9-]+', '-', 'g');
    -- Remove multiple consecutive hyphens
    result_slug := regexp_replace(result_slug, '-+', '-', 'g');
    -- Remove leading and trailing hyphens
    result_slug := trim(BOTH '-' FROM result_slug);
    
    RETURN result_slug;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_staff_active_deliveries(staff_id uuid)
 RETURNS TABLE(delivery_id uuid, order_id uuid, customer_name character varying, delivery_address jsonb, status delivery_status, estimated_time timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.order_id,
        d.customer_name,
        d.delivery_address,
        d.status,
        d.estimated_delivery_time
    FROM deliveries d
    WHERE d.assigned_to = staff_id
    AND d.status NOT IN ('completed', 'failed', 'cancelled')
    ORDER BY d.scheduled_at, d.created_at;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_store_ai_config(p_store_id uuid, p_agent_name text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF p_agent_name IS NOT NULL THEN
        RETURN (
            SELECT value->p_agent_name
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    END IF;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_store_hours(p_store_id uuid, p_day_of_week text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF p_day_of_week IS NOT NULL THEN
        RETURN (
            SELECT value->lower(p_day_of_week)
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    END IF;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_tenant_primary_provider(p_tenant_id uuid, p_provider_type character varying DEFAULT NULL::character varying)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_provider_id UUID;
BEGIN
    SELECT tpp.id INTO v_provider_id
    FROM tenant_payment_providers tpp
    JOIN payment_providers pp ON tpp.provider_id = pp.id
    WHERE tpp.tenant_id = p_tenant_id
    AND tpp.is_active = true
    AND tpp.is_primary = true
    AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
    LIMIT 1;
    
    -- If no primary, get first active
    IF v_provider_id IS NULL THEN
        SELECT tpp.id INTO v_provider_id
        FROM tenant_payment_providers tpp
        JOIN payment_providers pp ON tpp.provider_id = pp.id
        WHERE tpp.tenant_id = p_tenant_id
        AND tpp.is_active = true
        AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
        ORDER BY tpp.created_at
        LIMIT 1;
    END IF;
    
    RETURN v_provider_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_user_context(user_id_param uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'user', jsonb_build_object(
            'id', u.id,
            'email', u.email,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'role', u.role,
            'tenant_id', u.tenant_id,
            'store_id', u.store_id,
            'active', u.active
        ),
        'tenant', CASE 
            WHEN u.tenant_id IS NOT NULL THEN jsonb_build_object(
                'id', t.id,
                'name', t.name
            )
            ELSE NULL
        END,
        'store', CASE 
            WHEN u.store_id IS NOT NULL THEN jsonb_build_object(
                'id', s.id,
                'name', s.name,
                'store_code', s.store_code
            )
            ELSE NULL
        END,
        'permissions', (
            SELECT jsonb_agg(resource_type || ':' || action)
            FROM role_permissions 
            WHERE role = u.role AND granted = true
        )
    ) INTO result
    FROM users u
    LEFT JOIN tenants t ON u.tenant_id = t.id
    LEFT JOIN stores s ON u.store_id = s.id
    WHERE u.id = user_id_param;
    
    RETURN result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_user_login_stats(p_user_id uuid)
 RETURNS TABLE(total_logins integer, successful_logins integer, failed_logins integer, unique_ips integer, unique_countries integer, last_login timestamp with time zone, most_common_ip inet, most_common_country character varying)
 LANGUAGE plpgsql
AS $function$
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
$function$

;

CREATE OR REPLACE FUNCTION public.get_wishlist_stats(p_customer_id uuid)
 RETURNS TABLE(total_items integer, high_priority_items integer, on_sale_items integer, out_of_stock_items integer, total_value numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_items,
        COUNT(CASE WHEN w.priority = 1 THEN 1 END)::INTEGER as high_priority_items,
        0::INTEGER as on_sale_items, -- Sales tracking would need separate table
        COUNT(CASE WHEN p.quantity_available = 0 OR p.is_available = false THEN 1 END)::INTEGER as out_of_stock_items,
        COALESCE(SUM(COALESCE(p.retail_price, p.unit_price)), 0)::DECIMAL as total_value
    FROM wishlist w
    LEFT JOIN comprehensive_product_inventory_view p
        ON w.product_id = p.product_id
        AND w.store_id = p.store_id
    WHERE w.customer_id = p_customer_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_extract_query_trgm$function$

;

CREATE OR REPLACE FUNCTION public.gin_extract_value_trgm(text, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_extract_value_trgm$function$

;

CREATE OR REPLACE FUNCTION public.gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal)
 RETURNS boolean
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_trgm_consistent$function$

;

CREATE OR REPLACE FUNCTION public.gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal)
 RETURNS "char"
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_trgm_triconsistent$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_compress(internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_compress$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_consistent(internal, text, smallint, oid, internal)
 RETURNS boolean
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_consistent$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_decompress(internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_decompress$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_distance(internal, text, smallint, oid, internal)
 RETURNS double precision
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_distance$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_in(cstring)
 RETURNS gtrgm
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_in$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_options(internal)
 RETURNS void
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE
AS '$libdir/pg_trgm', $function$gtrgm_options$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_out(gtrgm)
 RETURNS cstring
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_out$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_penalty(internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_penalty$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_picksplit(internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_picksplit$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_same(gtrgm, gtrgm, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_same$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_union(internal, internal)
 RETURNS gtrgm
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_union$function$

;

CREATE OR REPLACE FUNCTION public.is_promotion_active_now(p_id uuid, p_current_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    promo RECORD;
    current_day INTEGER;
    current_time_only TIME;
    is_active BOOLEAN := false;
BEGIN
    -- Get promotion details
    SELECT * INTO promo FROM promotions WHERE id = p_id;

    IF NOT FOUND OR NOT promo.active THEN
        RETURN false;
    END IF;

    -- Convert timestamp to timezone-aware time
    current_day := EXTRACT(DOW FROM p_current_time AT TIME ZONE promo.timezone);
    current_time_only := (p_current_time AT TIME ZONE promo.timezone)::TIME;

    -- Check 1: Date range
    IF promo.start_date > p_current_time THEN
        RETURN false;
    END IF;

    IF NOT promo.is_continuous AND promo.end_date IS NOT NULL AND promo.end_date < p_current_time THEN
        RETURN false;
    END IF;

    -- Check 2: Day of week (if specified)
    IF promo.day_of_week IS NOT NULL AND array_length(promo.day_of_week, 1) > 0 THEN
        IF NOT (current_day = ANY(promo.day_of_week)) THEN
            RETURN false;
        END IF;
    END IF;

    -- Check 3: Time window (if specified)
    IF promo.time_start IS NOT NULL AND promo.time_end IS NOT NULL THEN
        IF NOT (current_time_only >= promo.time_start AND current_time_only <= promo.time_end) THEN
            RETURN false;
        END IF;
    END IF;

    RETURN true;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.is_store_open(p_store_id uuid, p_datetime timestamp without time zone)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_date DATE;
    v_time TIME;
    v_day_of_week INTEGER;
    v_is_holiday BOOLEAN;
    v_special_hours store_special_hours%ROWTYPE;
    v_regular_hours store_regular_hours%ROWTYPE;
BEGIN
    v_date := p_datetime::DATE;
    v_time := p_datetime::TIME;
    v_day_of_week := EXTRACT(DOW FROM v_date);
    
    -- Check special hours first
    SELECT * INTO v_special_hours 
    FROM store_special_hours 
    WHERE store_id = p_store_id AND date = v_date;
    
    IF FOUND THEN
        IF v_special_hours.is_closed THEN
            RETURN FALSE;
        END IF;
        RETURN v_time >= v_special_hours.open_time AND v_time <= v_special_hours.close_time;
    END IF;
    
    -- Check holidays
    -- (Simplified - would need more complex logic)
    
    -- Check regular hours
    SELECT * INTO v_regular_hours
    FROM store_regular_hours
    WHERE store_id = p_store_id AND day_of_week = v_day_of_week;
    
    IF v_regular_hours.is_closed THEN
        RETURN FALSE;
    END IF;
    
    -- Check against time slots
    -- (Would need to check JSON array of time slots)
    
    RETURN TRUE; -- Simplified
END;
$function$

;

CREATE OR REPLACE FUNCTION public.log_delivery_event(p_delivery_id uuid, p_event_type character varying, p_event_data jsonb DEFAULT '{}'::jsonb, p_user_id uuid DEFAULT NULL::uuid)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO delivery_events (delivery_id, event_type, event_data, performed_by)
    VALUES (p_delivery_id, p_event_type, p_event_data, p_user_id)
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.process_asn_to_purchase_order(p_session_id character varying, p_po_number character varying, p_supplier_id uuid, p_expected_date date, p_notes text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_po_id UUID;
    v_shipment_id VARCHAR;
    v_container_id VARCHAR;
    v_vendor VARCHAR;
    v_total_amount DECIMAL(12,2);
    v_item RECORD;
BEGIN
    -- Get common values from staging
    SELECT DISTINCT 
        shipment_id, 
        container_id, 
        vendor 
    INTO v_shipment_id, v_container_id, v_vendor
    FROM asn_import_staging
    WHERE session_id = p_session_id
    LIMIT 1;
    
    -- Calculate total amount
    SELECT SUM(unit_price * shipped_qty) INTO v_total_amount
    FROM asn_import_staging
    WHERE session_id = p_session_id;
    
    -- Create purchase order
    INSERT INTO purchase_orders (
        po_number,
        supplier_id,
        total_amount,
        status,
        expected_date,
        notes,
        shipment_id,
        container_id,
        vendor
    ) VALUES (
        p_po_number,
        p_supplier_id,
        COALESCE(v_total_amount, 0),
        'pending',
        p_expected_date,
        p_notes,
        v_shipment_id,
        v_container_id,
        v_vendor
    ) RETURNING id INTO v_po_id;
    
    -- Create purchase order items
    FOR v_item IN 
        SELECT * FROM asn_import_staging 
        WHERE session_id = p_session_id
    LOOP
        INSERT INTO purchase_order_items (
            purchase_order_id,
            sku,
            item_name,
            quantity,
            unit_cost,
            total,
            batch_lot,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin,
            shipped_qty,
            uom,
            uom_conversion,
            exists_in_inventory
        ) VALUES (
            v_po_id,
            v_item.sku,
            v_item.item_name,
            v_item.shipped_qty,
            v_item.unit_price,
            v_item.unit_price * v_item.shipped_qty,
            v_item.batch_lot,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin,
            v_item.shipped_qty,
            v_item.uom,
            v_item.uom_conversion,
            v_item.exists_in_inventory
        );
    END LOOP;
    
    -- Clear staging data
    DELETE FROM asn_import_staging WHERE session_id = p_session_id;
    
    RETURN v_po_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.process_purchase_order_receipt(p_po_id uuid, p_items jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_item JSONB;
    v_sku VARCHAR(100);
    v_quantity INTEGER;
    v_unit_cost DECIMAL(10,2);
    v_batch_lot VARCHAR(100);
    v_result JSONB = '[]'::JSONB;
BEGIN
    -- Process each item in the purchase order
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_sku := v_item->>'sku';
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_cost := (v_item->>'unit_cost')::DECIMAL;
        v_batch_lot := v_item->>'batch_lot';
        
        -- Update or insert inventory record
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_sku, v_quantity, v_quantity, v_unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_quantity,
            quantity_available = inventory.quantity_available + v_quantity,
            unit_cost = ((inventory.quantity_on_hand * inventory.unit_cost) + (v_quantity * v_unit_cost)) 
                        / (inventory.quantity_on_hand + v_quantity),
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku, transaction_type, reference_id, reference_type, 
            batch_lot, quantity, unit_cost, running_balance
        )
        SELECT 
            v_sku, 'purchase', p_po_id, 'purchase_order',
            v_batch_lot, v_quantity, v_unit_cost, quantity_on_hand
        FROM inventory
        WHERE sku = v_sku;
        
        -- Track batch/lot
        IF v_batch_lot IS NOT NULL THEN
            INSERT INTO batch_tracking (
                batch_lot, sku, purchase_order_id, 
                quantity_received, quantity_remaining, unit_cost
            )
            VALUES (
                v_batch_lot, v_sku, p_po_id,
                v_quantity, v_quantity, v_unit_cost
            );
        END IF;
        
        v_result := v_result || jsonb_build_object('sku', v_sku, 'processed', true);
    END LOOP;
    
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received', received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    RETURN v_result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.receive_purchase_order(p_po_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_item RECORD;
    v_result JSONB = '{"status": "success", "items_processed": []}'::JSONB;
    v_items_array JSONB = '[]'::JSONB;
BEGIN
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received',
        received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    -- Process each item
    FOR v_item IN 
        SELECT * FROM purchase_order_items 
        WHERE purchase_order_id = p_po_id
    LOOP
        -- Update inventory
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_item.sku, v_item.shipped_qty, v_item.shipped_qty, v_item.unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_item.shipped_qty,
            quantity_available = inventory.quantity_available + v_item.shipped_qty,
            unit_cost = v_item.unit_cost,
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Update batch tracking WITH GTIN columns
        INSERT INTO batch_tracking (
            sku,
            batch_lot,
            purchase_order_id,
            quantity_received,
            quantity_remaining,
            unit_cost,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin
        ) VALUES (
            v_item.sku,
            v_item.batch_lot,
            p_po_id,
            v_item.shipped_qty,
            v_item.shipped_qty,
            v_item.unit_cost,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin
        );
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku,
            transaction_type,
            quantity,
            reference_type,
            reference_id,
            notes
        ) VALUES (
            v_item.sku,
            'purchase',
            v_item.shipped_qty,
            'purchase_order',
            p_po_id,
            'Received from PO'
        );
        
        -- Add item to result
        v_items_array = v_items_array || jsonb_build_object(
            'sku', v_item.sku,
            'quantity', v_item.shipped_qty,
            'status', 'received'
        );
    END LOOP;
    
    v_result = v_result || jsonb_build_object('items_processed', v_items_array);
    
    RETURN v_result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.refresh_review_summary()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY review_summary_view;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.set_limit(real)
 RETURNS real
 LANGUAGE c
 STRICT
AS '$libdir/pg_trgm', $function$set_limit$function$

;

CREATE OR REPLACE FUNCTION public.show_limit()
 RETURNS real
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$show_limit$function$

;

CREATE OR REPLACE FUNCTION public.show_trgm(text)
 RETURNS text[]
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$show_trgm$function$

;

CREATE OR REPLACE FUNCTION public.similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity$function$

;

CREATE OR REPLACE FUNCTION public.similarity_dist(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity_dist$function$

;

CREATE OR REPLACE FUNCTION public.similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_commutator_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_dist_commutator_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_dist_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_dist_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_dist_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_op$function$

;

CREATE OR REPLACE FUNCTION public.unaccent(regdictionary, text)
 RETURNS text
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/unaccent', $function$unaccent_dict$function$

;

CREATE OR REPLACE FUNCTION public.unaccent_init(internal)
 RETURNS internal
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/unaccent', $function$unaccent_init$function$

;

CREATE OR REPLACE FUNCTION public.unaccent_lexize(internal, internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/unaccent', $function$unaccent_lexize$function$

;

CREATE OR REPLACE FUNCTION public.update_checkout_session_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_inventory_movements_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_inventory_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_pricing_rules_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_product_catalog_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_product_rating()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_avg_rating DECIMAL(2,1);
    v_total_reviews INTEGER;
    v_rating_dist JSONB;
    v_verified_count INTEGER;
    v_recommended_pct DECIMAL(5,2);
BEGIN
    -- Calculate aggregated values for the product
    WITH review_stats AS (
        SELECT
            AVG(rating)::DECIMAL(2,1) as avg_rating,
            COUNT(*) as total_reviews,
            COUNT(*) FILTER (WHERE is_verified_purchase = true) as verified_count,
            (COUNT(*) FILTER (WHERE is_recommended = true) * 100.0 / NULLIF(COUNT(*), 0))::DECIMAL(5,2) as recommended_pct,
            jsonb_build_object(
                '5', COUNT(*) FILTER (WHERE rating = 5),
                '4', COUNT(*) FILTER (WHERE rating = 4),
                '3', COUNT(*) FILTER (WHERE rating = 3),
                '2', COUNT(*) FILTER (WHERE rating = 2),
                '1', COUNT(*) FILTER (WHERE rating = 1)
            ) as rating_distribution
        FROM customer_reviews
        WHERE sku = COALESCE(NEW.sku, OLD.sku)
            AND status = 'approved'
    )
    SELECT
        COALESCE(avg_rating, 0),
        COALESCE(total_reviews, 0),
        rating_distribution,
        COALESCE(verified_count, 0),
        COALESCE(recommended_pct, 0)
    INTO
        v_avg_rating,
        v_total_reviews,
        v_rating_dist,
        v_verified_count,
        v_recommended_pct
    FROM review_stats;

    -- Update or insert product rating
    INSERT INTO product_ratings (
        sku,
        average_rating,
        total_reviews,
        rating_distribution,
        verified_purchase_count,
        recommended_percentage,
        last_updated
    ) VALUES (
        COALESCE(NEW.sku, OLD.sku),
        v_avg_rating,
        v_total_reviews,
        v_rating_dist,
        v_verified_count,
        v_recommended_pct,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (sku) DO UPDATE SET
        average_rating = EXCLUDED.average_rating,
        total_reviews = EXCLUDED.total_reviews,
        rating_distribution = EXCLUDED.rating_distribution,
        verified_purchase_count = EXCLUDED.verified_purchase_count,
        recommended_percentage = EXCLUDED.recommended_percentage,
        last_updated = EXCLUDED.last_updated;

    RETURN COALESCE(NEW, OLD);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_review_vote_counts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Update helpful and not_helpful counts
    UPDATE customer_reviews
    SET
        helpful_count = (
            SELECT COUNT(*)
            FROM review_votes
            WHERE review_id = COALESCE(NEW.review_id, OLD.review_id)
                AND vote_type = 'helpful'
        ),
        not_helpful_count = (
            SELECT COUNT(*)
            FROM review_votes
            WHERE review_id = COALESCE(NEW.review_id, OLD.review_id)
                AND vote_type = 'not_helpful'
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.review_id, OLD.review_id);

    RETURN COALESCE(NEW, OLD);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_system_settings_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_translation_usage()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE translations 
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_user_last_login()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$

;

CREATE OR REPLACE FUNCTION public.update_user_payment_methods_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.user_has_permission(user_id_param uuid, resource_type_param character varying, action_param character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    user_rec record;
    has_perm boolean := false;
BEGIN
    -- Get user info
    SELECT role, tenant_id, store_id, permissions_override
    INTO user_rec
    FROM users 
    WHERE id = user_id_param AND active = true;
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check override permissions first
    IF user_rec.permissions_override ? (resource_type_param || ':' || action_param) THEN
        RETURN (user_rec.permissions_override->>(resource_type_param || ':' || action_param))::boolean;
    END IF;
    
    -- Check role-based permissions
    SELECT granted INTO has_perm
    FROM role_permissions 
    WHERE role = user_rec.role 
      AND (resource_type = resource_type_param OR resource_type = '*')
      AND (action = action_param OR action = '*')
    ORDER BY 
        CASE WHEN resource_type = '*' THEN 1 ELSE 0 END,
        CASE WHEN action = '*' THEN 1 ELSE 0 END
    LIMIT 1;
    
    RETURN COALESCE(has_perm, false);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1mc()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1mc$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v3(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v3$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v4()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v4$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v5(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v5$function$

;

CREATE OR REPLACE FUNCTION public.uuid_nil()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_nil$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_dns()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_dns$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_oid()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_oid$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_url()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_url$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_x500()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_x500$function$

;

CREATE OR REPLACE FUNCTION public.validate_auth_token(p_token_hash character varying, p_token_type character varying, p_mark_as_used boolean DEFAULT false)
 RETURNS TABLE(is_valid boolean, user_id uuid, metadata jsonb)
 LANGUAGE plpgsql
AS $function$
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
$function$

;

CREATE OR REPLACE FUNCTION public.validate_verified_purchase()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_has_purchase BOOLEAN;
BEGIN
    -- Check if the user has purchased this product
    IF NEW.order_id IS NOT NULL THEN
        SELECT EXISTS (
            SELECT 1
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.id = NEW.order_id
                AND o.user_id = NEW.user_id
                AND oi.sku = NEW.sku
                AND o.status IN ('completed', 'delivered')
        ) INTO v_has_purchase;

        NEW.is_verified_purchase := v_has_purchase;
    ELSE
        -- Check for any completed order with this product
        SELECT EXISTS (
            SELECT 1
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.user_id = NEW.user_id
                AND oi.sku = NEW.sku
                AND o.status IN ('completed', 'delivered')
        ) INTO v_has_purchase;

        NEW.is_verified_purchase := v_has_purchase;
    END IF;

    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_commutator_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_dist_commutator_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_dist_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_dist_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_dist_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_op$function$

;

-- ============================================================================
-- STEP 5: Create 312 Missing Indexes
-- ============================================================================

CREATE INDEX idx_age_verification_logs_timestamp ON public.age_verification_logs USING btree ("timestamp")
;

CREATE UNIQUE INDEX agi_audit_aggregates_period_start_period_end_event_type_sev_key ON public.agi_audit_aggregates USING btree (period_start, period_end, event_type, severity)
;

CREATE INDEX idx_audit_aggregates_period ON public.agi_audit_aggregates USING btree (period_start, period_end)
;

CREATE INDEX idx_audit_alerts_triggered ON public.agi_audit_alerts USING btree (triggered_at DESC)
;

CREATE INDEX idx_audit_logs_event_type ON public.agi_audit_logs USING btree (event_type)
;

CREATE INDEX idx_audit_logs_resource ON public.agi_audit_logs USING btree (resource_type, resource_id)
;

CREATE INDEX idx_audit_logs_severity ON public.agi_audit_logs USING btree (severity)
;

CREATE INDEX idx_audit_logs_timestamp ON public.agi_audit_logs USING btree ("timestamp" DESC)
;

CREATE INDEX idx_audit_logs_user_id ON public.agi_audit_logs USING btree (user_id)
;

CREATE INDEX idx_rate_limit_buckets_last_update ON public.agi_rate_limit_buckets USING btree (last_update)
;

CREATE INDEX idx_rate_limit_rules_scope ON public.agi_rate_limit_rules USING btree (scope)
;

CREATE INDEX idx_rate_limit_violations_identifier ON public.agi_rate_limit_violations USING btree (identifier)
;

CREATE INDEX idx_rate_limit_violations_rule ON public.agi_rate_limit_violations USING btree (rule_name)
;

CREATE INDEX idx_ai_conversations_context_gin ON public.ai_conversations USING gin (context)
;

CREATE INDEX idx_ai_conversations_created_at ON public.ai_conversations USING btree (created_at DESC)
;

CREATE INDEX idx_ai_conversations_customer_id ON public.ai_conversations USING btree (customer_id)
;

CREATE INDEX idx_ai_conversations_messages_gin ON public.ai_conversations USING gin (messages)
;

CREATE INDEX idx_ai_conversations_session_customer ON public.ai_conversations USING btree (session_id, customer_id)
;

CREATE INDEX idx_ai_conversations_session_id ON public.ai_conversations USING btree (session_id)
;

CREATE INDEX idx_ai_personalities_tenant ON public.ai_personalities USING btree (tenant_id)
;

CREATE INDEX idx_training_action ON public.ai_training_data USING btree (customer_action)
;

CREATE INDEX idx_training_created ON public.ai_training_data USING btree (created_at DESC)
;

CREATE INDEX idx_training_score ON public.ai_training_data USING btree (feedback_score)
;

CREATE INDEX idx_api_keys_key_hash ON public.api_keys USING btree (key_hash)
;

CREATE INDEX idx_api_keys_user_id ON public.api_keys USING btree (user_id)
;

CREATE INDEX idx_audit_log_timestamp ON public.audit_log USING btree ("timestamp")
;

CREATE INDEX idx_audit_log_user_id ON public.audit_log USING btree (user_id)
;

CREATE INDEX idx_auth_tokens_expires_at ON public.auth_tokens USING btree (expires_at)
;

CREATE INDEX idx_auth_tokens_token_hash ON public.auth_tokens USING btree (token_hash)
;

CREATE INDEX idx_auth_tokens_token_type ON public.auth_tokens USING btree (token_type)
;

CREATE INDEX idx_auth_tokens_type_user ON public.auth_tokens USING btree (token_type, user_id)
;

CREATE INDEX idx_auth_tokens_user_id ON public.auth_tokens USING btree (user_id)
;

CREATE UNIQUE INDEX batch_tracking_batch_lot_key ON public.batch_tracking USING btree (batch_lot)
;

CREATE INDEX idx_batch_lot ON public.batch_tracking USING btree (batch_lot)
;

CREATE INDEX idx_batch_sku ON public.batch_tracking USING btree (sku)
;

CREATE INDEX idx_batch_tracking_case_gtin ON public.batch_tracking USING btree (case_gtin)
;

CREATE INDEX idx_batch_tracking_each_gtin ON public.batch_tracking USING btree (each_gtin)
;

CREATE INDEX idx_batch_tracking_gtin_barcode ON public.batch_tracking USING btree (gtin_barcode)
;

CREATE INDEX idx_batch_tracking_location ON public.batch_tracking USING btree (location_id)
;

CREATE INDEX idx_broadcast_audit_logs_action ON public.broadcast_audit_logs USING btree (action)
;

CREATE INDEX idx_broadcast_audit_logs_broadcast_id ON public.broadcast_audit_logs USING btree (broadcast_id)
;

CREATE INDEX idx_broadcast_audit_logs_created_at ON public.broadcast_audit_logs USING btree (created_at)
;

CREATE INDEX idx_broadcast_audit_logs_performed_by ON public.broadcast_audit_logs USING btree (performed_by)
;

CREATE UNIQUE INDEX broadcast_messages_broadcast_id_channel_type_key ON public.broadcast_messages USING btree (broadcast_id, channel_type)
;

CREATE INDEX idx_broadcast_messages_broadcast_id ON public.broadcast_messages USING btree (broadcast_id)
;

CREATE INDEX idx_broadcast_messages_channel_type ON public.broadcast_messages USING btree (channel_type)
;

CREATE INDEX idx_broadcast_messages_template_id ON public.broadcast_messages USING btree (template_id)
;

CREATE INDEX idx_broadcast_recipients_broadcast_id ON public.broadcast_recipients USING btree (broadcast_id)
;

CREATE INDEX idx_broadcast_recipients_customer_id ON public.broadcast_recipients USING btree (customer_id)
;

CREATE INDEX idx_broadcast_recipients_email_status ON public.broadcast_recipients USING btree (email_status)
;

CREATE INDEX idx_broadcast_recipients_push_status ON public.broadcast_recipients USING btree (push_status)
;

CREATE INDEX idx_broadcast_recipients_sms_status ON public.broadcast_recipients USING btree (sms_status)
;

CREATE INDEX idx_broadcast_segments_broadcast_id ON public.broadcast_segments USING btree (broadcast_id)
;

CREATE INDEX idx_broadcasts_created_by ON public.broadcasts USING btree (created_by)
;

CREATE INDEX idx_broadcasts_scheduled_at ON public.broadcasts USING btree (scheduled_at) WHERE (scheduled_at IS NOT NULL)
;

CREATE INDEX idx_broadcasts_store_id ON public.broadcasts USING btree (store_id)
;

CREATE INDEX idx_broadcasts_tenant_id ON public.broadcasts USING btree (tenant_id)
;

CREATE INDEX idx_cart_sessions_status ON public.cart_sessions USING btree (status)
;

CREATE INDEX idx_chat_interactions_created_at ON public.chat_interactions USING btree (created_at DESC)
;

CREATE INDEX idx_chat_interactions_customer_id ON public.chat_interactions USING btree (customer_id)
;

CREATE INDEX idx_chat_interactions_intent ON public.chat_interactions USING btree (intent)
;

CREATE INDEX idx_chat_interactions_metadata_gin ON public.chat_interactions USING gin (metadata)
;

CREATE INDEX idx_chat_interactions_session_customer ON public.chat_interactions USING btree (session_id, customer_id)
;

CREATE INDEX idx_chat_interactions_session_id ON public.chat_interactions USING btree (session_id)
;

CREATE UNIQUE INDEX communication_analytics_broadcast_id_key ON public.communication_analytics USING btree (broadcast_id)
;

CREATE INDEX idx_communication_analytics_broadcast_id ON public.communication_analytics USING btree (broadcast_id)
;

CREATE INDEX idx_communication_logs_created_at ON public.communication_logs USING btree (created_at)
;

CREATE INDEX idx_communication_logs_recipient ON public.communication_logs USING btree (recipient)
;

CREATE INDEX idx_communication_logs_status ON public.communication_logs USING btree (status)
;

CREATE INDEX idx_communication_logs_user_id ON public.communication_logs USING btree (user_id)
;

CREATE UNIQUE INDEX communication_preferences_customer_id_key ON public.communication_preferences USING btree (customer_id)
;

CREATE UNIQUE INDEX communication_preferences_email_unsubscribe_token_key ON public.communication_preferences USING btree (email_unsubscribe_token)
;

CREATE UNIQUE INDEX communication_preferences_sms_unsubscribe_token_key ON public.communication_preferences USING btree (sms_unsubscribe_token)
;

CREATE INDEX idx_communication_preferences_customer_id ON public.communication_preferences USING btree (customer_id)
;

CREATE INDEX idx_communication_preferences_email_token ON public.communication_preferences USING btree (email_unsubscribe_token)
;

CREATE INDEX idx_communication_preferences_sms_token ON public.communication_preferences USING btree (sms_unsubscribe_token)
;

CREATE UNIQUE INDEX conversation_states_session_id_key ON public.conversation_states USING btree (session_id)
;

CREATE INDEX idx_conversation_states_current_stage ON public.conversation_states USING btree (current_stage)
;

CREATE INDEX idx_conversation_states_session_id ON public.conversation_states USING btree (session_id)
;

CREATE INDEX idx_conversation_states_user_id ON public.conversation_states USING btree (user_id)
;

CREATE INDEX idx_conversion_metrics_converted ON public.conversion_metrics USING btree (converted)
;

CREATE INDEX idx_conversion_metrics_created_at ON public.conversion_metrics USING btree (created_at)
;

CREATE INDEX idx_conversion_metrics_session_id ON public.conversion_metrics USING btree (session_id)
;

CREATE INDEX idx_conversion_metrics_user_id ON public.conversion_metrics USING btree (user_id)
;

CREATE INDEX idx_reviews_helpful ON public.customer_reviews USING btree (helpful_count DESC)
;

CREATE INDEX idx_reviews_order ON public.customer_reviews USING btree (order_id)
;

CREATE INDEX idx_reviews_status_created ON public.customer_reviews USING btree (status, created_at DESC)
;

CREATE INDEX idx_reviews_user ON public.customer_reviews USING btree (user_id)
;

CREATE INDEX idx_reviews_variant_rating ON public.customer_reviews USING btree (sku, rating)
;

CREATE INDEX idx_deliveries_batch_id ON public.deliveries USING btree (batch_id)
;

CREATE INDEX idx_deliveries_created_at ON public.deliveries USING btree (created_at DESC)
;

CREATE INDEX idx_deliveries_customer_id ON public.deliveries USING btree (customer_id)
;

CREATE INDEX idx_deliveries_order_id ON public.deliveries USING btree (order_id)
;

CREATE INDEX idx_deliveries_scheduled_at ON public.deliveries USING btree (scheduled_at)
;

CREATE INDEX idx_deliveries_store_id ON public.deliveries USING btree (store_id)
;

CREATE INDEX idx_delivery_events_created_at ON public.delivery_events USING btree (created_at DESC)
;

CREATE INDEX idx_delivery_events_delivery_id ON public.delivery_events USING btree (delivery_id)
;

CREATE INDEX idx_delivery_events_event_type ON public.delivery_events USING btree (event_type)
;

CREATE INDEX idx_delivery_geofences_delivery_id ON public.delivery_geofences USING btree (delivery_id)
;

CREATE INDEX idx_delivery_geofences_location ON public.delivery_geofences USING btree (center_latitude, center_longitude)
;

CREATE INDEX idx_delivery_tracking_delivery_id ON public.delivery_tracking USING btree (delivery_id)
;

CREATE INDEX idx_delivery_tracking_recorded_at ON public.delivery_tracking USING btree (recorded_at DESC)
;

CREATE INDEX idx_delivery_zones_tenant ON public.delivery_zones USING btree (tenant_id, is_active)
;

CREATE INDEX idx_discount_codes_unused ON public.discount_codes USING btree (used, valid_until) WHERE (used = false)
;

CREATE INDEX idx_discount_codes_validity ON public.discount_codes USING btree (valid_from, valid_until)
;

CREATE INDEX idx_discount_usage_discount ON public.discount_usage USING btree (discount_code_id)
;

CREATE INDEX idx_dynamic_pricing_active ON public.dynamic_pricing_rules USING btree (active)
;

CREATE INDEX idx_holidays_lookup ON public.holidays USING btree (holiday_type, province_territory_id, is_statutory)
;

CREATE INDEX idx_holidays_type ON public.holidays USING btree (holiday_type)
;

CREATE INDEX idx_inventory_locations_store_id ON public.inventory_locations USING btree (store_id)
;

CREATE UNIQUE INDEX inventory_locations_code_key ON public.inventory_locations USING btree (code)
;

CREATE INDEX idx_location_access_log_access_type ON public.location_access_log USING btree (access_type)
;

CREATE INDEX idx_location_access_log_created_at ON public.location_access_log USING btree (created_at)
;

CREATE INDEX idx_location_access_log_store_id ON public.location_access_log USING btree (store_id)
;

CREATE INDEX idx_location_access_log_user_id ON public.location_access_log USING btree (user_id)
;

CREATE INDEX idx_location_assignments_inventory_id ON public.location_assignments_log USING btree (inventory_id)
;

CREATE INDEX idx_message_templates_category ON public.message_templates USING btree (category)
;

CREATE INDEX idx_message_templates_channel_type ON public.message_templates USING btree (channel_type)
;

CREATE INDEX idx_message_templates_is_active ON public.message_templates USING btree (is_active)
;

CREATE INDEX idx_message_templates_store_id ON public.message_templates USING btree (store_id)
;

CREATE INDEX idx_message_templates_tenant_id ON public.message_templates USING btree (tenant_id)
;

CREATE UNIQUE INDEX model_deployments_deployment_name_key ON public.model_deployments USING btree (deployment_name)
;

CREATE INDEX idx_ocs_inventory_available ON public.ocs_inventory USING btree (is_available)
;

CREATE INDEX idx_ocs_inventory_batch_lot ON public.ocs_inventory USING btree (batch_lot)
;

CREATE INDEX idx_ocs_inventory_case_gtin ON public.ocs_inventory USING btree (case_gtin)
;

CREATE INDEX idx_ocs_inventory_each_gtin ON public.ocs_inventory USING btree (each_gtin)
;

CREATE INDEX idx_ocs_inventory_gtin_barcode ON public.ocs_inventory USING btree (gtin_barcode)
;

CREATE INDEX idx_ocs_inventory_quantity ON public.ocs_inventory USING btree (quantity_available)
;

CREATE INDEX idx_ocs_inventory_sku_lower ON public.ocs_inventory USING btree (lower(TRIM(BOTH FROM sku)))
;

CREATE INDEX idx_ocs_inventory_store ON public.ocs_inventory USING btree (store_id)
;

CREATE INDEX idx_ocs_inventory_supplier ON public.ocs_inventory USING btree (supplier)
;

CREATE UNIQUE INDEX ocs_inventory_store_id_sku_key ON public.ocs_inventory USING btree (store_id, sku)
;

CREATE UNIQUE INDEX ocs_inventory_store_sku_unique ON public.ocs_inventory USING btree (store_id, sku)
;

CREATE INDEX idx_inventory_logs_created_at ON public.ocs_inventory_logs USING btree (created_at DESC)
;

CREATE INDEX idx_inventory_logs_inventory_id ON public.ocs_inventory_logs USING btree (inventory_id)
;

CREATE INDEX idx_inventory_movements_created_at ON public.ocs_inventory_movements USING btree (created_at DESC)
;

CREATE INDEX idx_inventory_movements_inventory_id ON public.ocs_inventory_movements USING btree (inventory_id)
;

CREATE INDEX idx_inventory_reservations_inventory_id ON public.ocs_inventory_reservations USING btree (inventory_id)
;

CREATE INDEX idx_inventory_reservations_status ON public.ocs_inventory_reservations USING btree (status)
;

CREATE INDEX idx_inventory_snapshots_date ON public.ocs_inventory_snapshots USING btree (snapshot_date DESC)
;

CREATE INDEX idx_inventory_snapshots_inventory_id ON public.ocs_inventory_snapshots USING btree (inventory_id)
;

CREATE INDEX idx_transactions_date ON public.ocs_inventory_transactions USING btree (created_at DESC)
;

CREATE INDEX idx_transactions_sku ON public.ocs_inventory_transactions USING btree (sku)
;

CREATE INDEX idx_ocs_product_catalog_variant_lower ON public.ocs_product_catalog USING btree (lower(TRIM(BOTH FROM ocs_variant_number)))
;

CREATE INDEX idx_product_catalog_ocs ON public.ocs_product_catalog USING btree (ocs_variant_number)
;

CREATE INDEX idx_product_catalog_ocs_brand ON public.ocs_product_catalog USING btree (brand)
;

CREATE INDEX idx_product_catalog_ocs_category ON public.ocs_product_catalog USING btree (category)
;

CREATE INDEX idx_product_catalog_ocs_rating ON public.ocs_product_catalog USING btree (rating DESC) WHERE (rating IS NOT NULL)
;

CREATE INDEX idx_product_catalog_ocs_rating_count ON public.ocs_product_catalog USING btree (rating_count DESC) WHERE (rating_count > 0)
;

CREATE INDEX idx_product_catalog_ocs_slug ON public.ocs_product_catalog USING btree (slug)
;

CREATE INDEX idx_product_catalog_ocs_strain_type ON public.ocs_product_catalog USING btree (strain_type)
;

CREATE INDEX idx_products_brand ON public.ocs_product_catalog USING btree (brand)
;

CREATE INDEX idx_products_category ON public.ocs_product_catalog USING btree (category)
;

CREATE INDEX idx_products_name ON public.ocs_product_catalog USING btree (product_name)
;

CREATE INDEX idx_products_plant_type ON public.ocs_product_catalog USING btree (plant_type)
;

CREATE INDEX idx_products_price ON public.ocs_product_catalog USING btree (unit_price)
;

CREATE INDEX idx_products_subcategory ON public.ocs_product_catalog USING btree (sub_category)
;

CREATE UNIQUE INDEX uk_product_catalog_ocs_variant ON public.ocs_product_catalog USING btree (ocs_variant_number)
;

CREATE INDEX idx_order_status_history_order_id ON public.order_status_history USING btree (order_id)
;

CREATE INDEX idx_otp_codes_code ON public.otp_codes USING btree (code)
;

CREATE INDEX idx_otp_codes_expires_at ON public.otp_codes USING btree (expires_at)
;

CREATE INDEX idx_otp_codes_identifier ON public.otp_codes USING btree (identifier)
;

CREATE INDEX idx_otp_codes_user_id ON public.otp_codes USING btree (user_id)
;

CREATE INDEX idx_otp_rate_limits_blocked_until ON public.otp_rate_limits USING btree (blocked_until)
;

CREATE UNIQUE INDEX idx_otp_rate_limits_identifier ON public.otp_rate_limits USING btree (identifier, identifier_type)
;

CREATE INDEX idx_param_correct ON public.parameter_accuracy USING btree (is_correct)
;

CREATE INDEX idx_param_type ON public.parameter_accuracy USING btree (parameter_type)
;

CREATE INDEX idx_payment_audit_action ON public.payment_audit_log USING btree (action, created_at DESC)
;

CREATE INDEX idx_payment_audit_created ON public.payment_audit_log USING btree (created_at DESC)
;

CREATE INDEX idx_payment_audit_entity ON public.payment_audit_log USING btree (entity_type, entity_id)
;

CREATE INDEX idx_payment_audit_tenant ON public.payment_audit_log USING btree (tenant_id, created_at DESC)
;

CREATE INDEX idx_payment_credentials_active ON public.payment_credentials USING btree (is_active, tenant_id)
;

CREATE INDEX idx_payment_credentials_expires ON public.payment_credentials USING btree (expires_at) WHERE (expires_at IS NOT NULL)
;

CREATE INDEX idx_payment_credentials_tenant ON public.payment_credentials USING btree (tenant_id, provider, is_active)
;

CREATE INDEX idx_payment_credentials_type ON public.payment_credentials USING btree (credential_type, is_active)
;

CREATE INDEX idx_disputes_status ON public.payment_disputes USING btree (status)
;

CREATE INDEX idx_disputes_transaction ON public.payment_disputes USING btree (transaction_id)
;

CREATE INDEX idx_fee_splits_settlement ON public.payment_fee_splits USING btree (tenant_settled, platform_fee_collected)
;

CREATE INDEX idx_fee_splits_tenant ON public.payment_fee_splits USING btree (tenant_id, created_at DESC)
;

CREATE UNIQUE INDEX payment_fee_splits_transaction_id_key ON public.payment_fee_splits USING btree (transaction_id)
;

CREATE INDEX idx_idempotency_expires ON public.payment_idempotency_keys USING btree (expires_at)
;

CREATE INDEX idx_idempotency_status ON public.payment_idempotency_keys USING btree (status, created_at DESC)
;

CREATE INDEX idx_idempotency_tenant ON public.payment_idempotency_keys USING btree (tenant_id, created_at DESC)
;

CREATE UNIQUE INDEX payment_methods_tenant_id_payment_token_provider_id_key ON public.payment_methods USING btree (tenant_id, payment_token, provider_id)
;

CREATE INDEX idx_metrics_date ON public.payment_metrics USING btree (date DESC)
;

CREATE UNIQUE INDEX payment_metrics_date_provider_id_key ON public.payment_metrics USING btree (date, provider_id)
;

CREATE INDEX idx_health_metrics_provider ON public.payment_provider_health_metrics USING btree (tenant_provider_id, checked_at DESC)
;

CREATE INDEX idx_health_metrics_success ON public.payment_provider_health_metrics USING btree (is_successful, checked_at DESC)
;

CREATE UNIQUE INDEX payment_providers_name_key ON public.payment_providers USING btree (name)
;

CREATE INDEX idx_settlements_date ON public.payment_settlements USING btree (settlement_date DESC)
;

CREATE INDEX idx_settlements_provider ON public.payment_settlements USING btree (provider_id, settlement_date DESC)
;

CREATE INDEX idx_subscriptions_next_billing ON public.payment_subscriptions USING btree (next_billing_date)
;

CREATE INDEX idx_subscriptions_status ON public.payment_subscriptions USING btree (status)
;

CREATE INDEX idx_subscriptions_tenant ON public.payment_subscriptions USING btree (tenant_id)
;

CREATE INDEX idx_payment_transactions_idempotency ON public.payment_transactions USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)
;

CREATE INDEX idx_payment_transactions_tenant_provider ON public.payment_transactions USING btree (tenant_provider_id, created_at DESC)
;

CREATE INDEX idx_transactions_created ON public.payment_transactions USING btree (created_at DESC)
;

CREATE INDEX idx_transactions_order ON public.payment_transactions USING btree (order_id)
;

CREATE INDEX idx_transactions_provider_ref ON public.payment_transactions USING btree (provider_transaction_id, provider_id)
;

CREATE INDEX idx_transactions_status ON public.payment_transactions USING btree (status)
;

CREATE INDEX idx_transactions_tenant ON public.payment_transactions USING btree (tenant_id)
;

CREATE UNIQUE INDEX payment_transactions_transaction_reference_key ON public.payment_transactions USING btree (transaction_reference)
;

CREATE INDEX idx_webhook_routes_path ON public.payment_webhook_routes USING btree (webhook_url_path) WHERE (is_active = true)
;

CREATE INDEX idx_webhook_routes_tenant ON public.payment_webhook_routes USING btree (tenant_id, provider)
;

CREATE UNIQUE INDEX payment_webhook_routes_webhook_url_path_key ON public.payment_webhook_routes USING btree (webhook_url_path)
;

CREATE INDEX idx_webhooks_processed ON public.payment_webhooks USING btree (processed, received_at)
;

CREATE INDEX idx_webhooks_provider ON public.payment_webhooks USING btree (provider_id, received_at DESC)
;

CREATE INDEX idx_price_history_product ON public.price_history USING btree (product_id, changed_at)
;

CREATE UNIQUE INDEX price_tiers_name_key ON public.price_tiers USING btree (name)
;

CREATE INDEX idx_pricing_rules_category ON public.pricing_rules USING btree (store_id, category)
;

CREATE INDEX idx_pricing_rules_subcategory ON public.pricing_rules USING btree (store_id, category, sub_category)
;

CREATE INDEX idx_pricing_rules_subsubcategory ON public.pricing_rules USING btree (store_id, category, sub_category, sub_sub_category)
;

CREATE UNIQUE INDEX unique_store_category_rule ON public.pricing_rules USING btree (store_id, category, sub_category, sub_sub_category)
;

CREATE INDEX idx_product_ratings_avg_rating ON public.product_ratings USING btree (average_rating DESC)
;

CREATE INDEX idx_recommendations_product ON public.product_recommendations USING btree (product_id)
;

CREATE INDEX idx_recommendations_type ON public.product_recommendations USING btree (recommendation_type)
;

CREATE UNIQUE INDEX product_recommendations_product_id_recommended_product_id_r_key ON public.product_recommendations USING btree (product_id, recommended_product_id, recommendation_type)
;

CREATE INDEX idx_profiles_customer_type ON public.profiles USING btree (customer_type)
;

CREATE INDEX idx_profiles_last_order_date ON public.profiles USING btree (last_order_date DESC)
;

CREATE INDEX idx_profiles_loyalty_points ON public.profiles USING btree (loyalty_points)
;

CREATE INDEX idx_profiles_payment_methods_gin ON public.profiles USING gin (payment_methods)
;

CREATE INDEX idx_profiles_preferences_gin ON public.profiles USING gin (preferences)
;

CREATE INDEX idx_profiles_purchase_history_gin ON public.profiles USING gin (purchase_history)
;

CREATE UNIQUE INDEX unique_user_profile ON public.profiles USING btree (user_id)
;

CREATE INDEX idx_promotions_active ON public.promotions USING btree (active, start_date, end_date)
;

CREATE INDEX idx_promotions_active_dates ON public.promotions USING btree (active, start_date, end_date) WHERE (active = true)
;

CREATE INDEX idx_promotions_code ON public.promotions USING btree (code) WHERE (code IS NOT NULL)
;

CREATE INDEX idx_promotions_continuous ON public.promotions USING btree (is_continuous, active) WHERE ((is_continuous = true) AND (active = true))
;

CREATE INDEX idx_promotions_recurring ON public.promotions USING btree (recurrence_type, active) WHERE (((recurrence_type)::text <> 'none'::text) AND (active = true))
;

CREATE INDEX idx_promotions_store ON public.promotions USING btree (store_id) WHERE (store_id IS NOT NULL)
;

CREATE INDEX idx_promotions_tenant ON public.promotions USING btree (tenant_id) WHERE (tenant_id IS NOT NULL)
;

CREATE INDEX idx_promotions_type ON public.promotions USING btree (type)
;

CREATE UNIQUE INDEX promotions_code_key ON public.promotions USING btree (code)
;

CREATE INDEX idx_provincial_suppliers_province_territory ON public.provincial_suppliers USING btree (provinces_territories_id)
;

CREATE INDEX idx_suppliers_active ON public.provincial_suppliers USING btree (is_active)
;

CREATE INDEX idx_suppliers_name ON public.provincial_suppliers USING btree (name)
;

CREATE UNIQUE INDEX unique_province_territory_supplier ON public.provincial_suppliers USING btree (provinces_territories_id) WHERE ((provinces_territories_id IS NOT NULL) AND (is_provincial_supplier = true))
;

CREATE INDEX idx_po_items_po_id ON public.purchase_order_items USING btree (purchase_order_id)
;

CREATE INDEX idx_po_items_sku ON public.purchase_order_items USING btree (sku)
;

CREATE INDEX idx_poi_case_gtin ON public.purchase_order_items USING btree (case_gtin)
;

CREATE INDEX idx_poi_gtin_barcode ON public.purchase_order_items USING btree (gtin_barcode)
;

CREATE INDEX idx_poi_sku_batch ON public.purchase_order_items USING btree (sku, batch_lot)
;

CREATE INDEX idx_po_container_id ON public.purchase_orders USING btree (container_id)
;

CREATE INDEX idx_po_shipment_id ON public.purchase_orders USING btree (shipment_id)
;

CREATE INDEX idx_po_status ON public.purchase_orders USING btree (status)
;

CREATE INDEX idx_po_supplier ON public.purchase_orders USING btree (supplier_id)
;

CREATE INDEX idx_po_vendor ON public.purchase_orders USING btree (vendor)
;

CREATE INDEX idx_push_subscriptions_customer_id ON public.push_subscriptions USING btree (customer_id)
;

CREATE INDEX idx_push_subscriptions_device_type ON public.push_subscriptions USING btree (device_type)
;

CREATE INDEX idx_push_subscriptions_is_active ON public.push_subscriptions USING btree (is_active)
;

CREATE UNIQUE INDEX push_subscriptions_device_token_key ON public.push_subscriptions USING btree (device_token)
;

CREATE INDEX idx_attributes_review ON public.review_attributes USING btree (review_id)
;

CREATE UNIQUE INDEX pk_review_attributes ON public.review_attributes USING btree (review_id, attribute_name)
;

CREATE INDEX idx_media_order ON public.review_media USING btree (review_id, display_order)
;

CREATE INDEX idx_media_review ON public.review_media USING btree (review_id)
;

CREATE INDEX idx_review_summary_rating ON public.review_summary_view USING btree (average_rating DESC)
;

CREATE INDEX idx_review_summary_sku ON public.review_summary_view USING btree (sku)
;

CREATE INDEX idx_votes_review ON public.review_votes USING btree (review_id)
;

CREATE INDEX idx_votes_user ON public.review_votes USING btree (user_id)
;

CREATE UNIQUE INDEX unique_user_review_vote ON public.review_votes USING btree (review_id, user_id)
;

CREATE UNIQUE INDEX role_permissions_role_resource_type_action_key ON public.role_permissions USING btree (role, resource_type, action)
;

CREATE INDEX idx_shelf_locations_active ON public.shelf_locations USING btree (is_active, is_available)
;

CREATE INDEX idx_shelf_locations_code ON public.shelf_locations USING btree (location_code)
;

CREATE INDEX idx_shelf_locations_store ON public.shelf_locations USING btree (store_id)
;

CREATE INDEX idx_shelf_locations_type ON public.shelf_locations USING btree (location_type)
;

CREATE UNIQUE INDEX unique_location_per_store ON public.shelf_locations USING btree (store_id, zone, aisle, shelf, bin)
;

CREATE INDEX idx_staff_delivery_status_user_id ON public.staff_delivery_status USING btree (user_id)
;

CREATE INDEX idx_store_settings_category ON public.store_settings USING btree (category)
;

CREATE INDEX idx_store_settings_store ON public.store_settings USING btree (store_id)
;

CREATE UNIQUE INDEX store_settings_store_id_category_key_key ON public.store_settings USING btree (store_id, category, key)
;

CREATE UNIQUE INDEX system_settings_category_key_key ON public.system_settings USING btree (category, key)
;

CREATE INDEX idx_tax_rates_effective ON public.tax_rates USING btree (effective_from, effective_to)
;

CREATE INDEX idx_tax_rates_tenant ON public.tax_rates USING btree (tenant_id, is_active)
;

CREATE UNIQUE INDEX tenants_name_key ON public.tenants USING btree (name)
;

CREATE INDEX idx_token_blacklist_expires_at ON public.token_blacklist USING btree (expires_at)
;

CREATE INDEX idx_token_blacklist_token_id ON public.token_blacklist USING btree (token_id)
;

CREATE UNIQUE INDEX token_blacklist_token_id_key ON public.token_blacklist USING btree (token_id)
;

CREATE UNIQUE INDEX training_sessions_session_id_key ON public.training_sessions USING btree (session_id)
;

CREATE INDEX idx_batch_items_batch ON public.translation_batch_items USING btree (batch_id)
;

CREATE INDEX idx_batch_items_status ON public.translation_batch_items USING btree (status)
;

CREATE UNIQUE INDEX translation_batches_batch_key_key ON public.translation_batches USING btree (batch_key)
;

CREATE INDEX idx_overrides_active ON public.translation_overrides USING btree (is_active) WHERE (is_active = true)
;

CREATE INDEX idx_overrides_translation ON public.translation_overrides USING btree (translation_id)
;

CREATE INDEX idx_translations_created ON public.translations USING btree (created_at DESC)
;

CREATE INDEX idx_translations_lookup ON public.translations USING btree (source_text, target_language, context, namespace)
;

CREATE INDEX idx_translations_usage ON public.translations USING btree (usage_count DESC, last_used_at DESC)
;

CREATE INDEX idx_translations_verified ON public.translations USING btree (is_verified) WHERE (is_verified = true)
;

CREATE UNIQUE INDEX translations_source_text_source_language_target_language_co_key ON public.translations USING btree (source_text, source_language, target_language, context, namespace)
;

CREATE INDEX idx_unsubscribe_list_channel_type ON public.unsubscribe_list USING btree (channel_type)
;

CREATE INDEX idx_unsubscribe_list_customer_id ON public.unsubscribe_list USING btree (customer_id) WHERE (customer_id IS NOT NULL)
;

CREATE INDEX idx_unsubscribe_list_phone ON public.unsubscribe_list USING btree (phone_number) WHERE (phone_number IS NOT NULL)
;

CREATE INDEX idx_user_addresses_user ON public.user_addresses USING btree (user_id)
;

CREATE INDEX unique_default_billing_per_user ON public.user_addresses USING btree (user_id) WHERE ((is_default = true) AND ((address_type)::text = 'billing'::text))
;

CREATE INDEX unique_default_delivery_per_user ON public.user_addresses USING btree (user_id) WHERE ((is_default = true) AND ((address_type)::text = 'delivery'::text))
;

CREATE INDEX idx_user_login_logs_ip_address ON public.user_login_logs USING btree (ip_address)
;

CREATE INDEX idx_user_login_logs_session_id ON public.user_login_logs USING btree (session_id)
;

CREATE INDEX idx_user_login_logs_tenant_id ON public.user_login_logs USING btree (tenant_id)
;

CREATE INDEX idx_user_login_logs_timestamp ON public.user_login_logs USING btree (login_timestamp DESC)
;

CREATE INDEX idx_user_login_logs_user_id ON public.user_login_logs USING btree (user_id)
;

CREATE INDEX idx_user_sessions_expires_at ON public.user_sessions USING btree (expires_at)
;

CREATE INDEX idx_user_sessions_session_token ON public.user_sessions USING btree (session_token)
;

CREATE INDEX idx_user_sessions_user_id ON public.user_sessions USING btree (user_id)
;

CREATE UNIQUE INDEX user_sessions_session_token_key ON public.user_sessions USING btree (session_token)
;

CREATE INDEX idx_users_role_customer ON public.users USING btree (role) WHERE (role = 'customer'::user_role_simple)
;

CREATE INDEX idx_voice_auth_logs_timestamp ON public.voice_auth_logs USING btree ("timestamp")
;

CREATE INDEX idx_voice_auth_logs_user_id ON public.voice_auth_logs USING btree (user_id)
;

CREATE INDEX idx_voice_profiles_user_id ON public.voice_profiles USING btree (user_id)
;

CREATE INDEX idx_wishlist_added_at ON public.wishlist USING btree (added_at DESC)
;

CREATE INDEX idx_wishlist_customer ON public.wishlist USING btree (customer_id)
;

CREATE INDEX idx_wishlist_priority ON public.wishlist USING btree (priority DESC)
;

CREATE INDEX idx_wishlist_store ON public.wishlist USING btree (store_id)
;

CREATE UNIQUE INDEX unique_wishlist_item ON public.wishlist USING btree (customer_id, product_id, store_id)
;

-- ============================================================================
-- STEP 6: Create 155 Missing Constraints
-- ============================================================================

ALTER TABLE accessories_catalog
ADD CONSTRAINT accessories_catalog_barcode_key
UNIQUE (barcode);

ALTER TABLE accessory_categories
ADD CONSTRAINT accessory_categories_slug_key
UNIQUE (slug);

ALTER TABLE agi_audit_aggregates
ADD CONSTRAINT agi_audit_aggregates_period_start_period_end_event_type_sev_key
UNIQUE (period_start, period_end, event_type, severity);

ALTER TABLE ai_conversations
ADD CONSTRAINT ai_conversations_personality_id_fkey
FOREIGN KEY (personality_id) REFERENCES ai_personalities(id);

ALTER TABLE ai_personalities
ADD CONSTRAINT ai_personalities_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE api_keys
ADD CONSTRAINT api_keys_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE audit_log
ADD CONSTRAINT audit_log_store_id_fkey
FOREIGN KEY (store_id) REFERENCES stores(id);

ALTER TABLE audit_log
ADD CONSTRAINT audit_log_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE auth_tokens
ADD CONSTRAINT auth_tokens_token_type_check
CHECK (((token_type)::text = ANY ((ARRAY['email_verification'::character varying, 'password_reset'::character varying, 'refresh'::character varying, 'api_key'::character varying])::text[])));

ALTER TABLE batch_tracking
ADD CONSTRAINT batch_tracking_batch_lot_key
UNIQUE (batch_lot);

ALTER TABLE batch_tracking
ADD CONSTRAINT batch_tracking_location_id_fkey
FOREIGN KEY (location_id) REFERENCES shelf_locations(id);

ALTER TABLE batch_tracking
ADD CONSTRAINT batch_tracking_purchase_order_id_fkey
FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id);

ALTER TABLE broadcast_audit_logs
ADD CONSTRAINT broadcast_audit_logs_action_category_check
CHECK (((action_category)::text = ANY ((ARRAY['create'::character varying, 'update'::character varying, 'send'::character varying, 'cancel'::character varying, 'pause'::character varying, 'resume'::character varying, 'delete'::character varying, 'approve'::character varying])::text[])));

ALTER TABLE broadcast_messages
ADD CONSTRAINT broadcast_messages_broadcast_id_channel_type_key
UNIQUE (broadcast_id, channel_type);

ALTER TABLE broadcast_messages
ADD CONSTRAINT broadcast_messages_channel_type_check
CHECK (((channel_type)::text = ANY ((ARRAY['email'::character varying, 'sms'::character varying, 'push'::character varying])::text[])));

ALTER TABLE broadcast_messages
ADD CONSTRAINT broadcast_messages_priority_check
CHECK (((priority)::text = ANY ((ARRAY['low'::character varying, 'normal'::character varying, 'high'::character varying, 'urgent'::character varying])::text[])));

ALTER TABLE broadcast_messages
ADD CONSTRAINT broadcast_messages_template_id_fkey
FOREIGN KEY (template_id) REFERENCES message_templates(id);

ALTER TABLE broadcast_segments
ADD CONSTRAINT broadcast_segments_broadcast_id_fkey
FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id) ON DELETE CASCADE;

ALTER TABLE broadcasts
ADD CONSTRAINT broadcasts_status_check
CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'scheduled'::character varying, 'sending'::character varying, 'sent'::character varying, 'paused'::character varying, 'cancelled'::character varying, 'failed'::character varying])::text[])));

ALTER TABLE broadcasts
ADD CONSTRAINT broadcasts_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE cart_sessions
ADD CONSTRAINT cart_sessions_ai_personality_id_fkey
FOREIGN KEY (ai_personality_id) REFERENCES ai_personalities(id);

ALTER TABLE cart_sessions
ADD CONSTRAINT cart_sessions_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE communication_analytics
ADD CONSTRAINT communication_analytics_broadcast_id_fkey
FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id) ON DELETE CASCADE;

ALTER TABLE communication_analytics
ADD CONSTRAINT communication_analytics_broadcast_id_key
UNIQUE (broadcast_id);

ALTER TABLE communication_preferences
ADD CONSTRAINT communication_preferences_customer_id_key
UNIQUE (customer_id);

ALTER TABLE communication_preferences
ADD CONSTRAINT communication_preferences_email_unsubscribe_token_key
UNIQUE (email_unsubscribe_token);

ALTER TABLE communication_preferences
ADD CONSTRAINT communication_preferences_frequency_check
CHECK (((frequency)::text = ANY ((ARRAY['immediate'::character varying, 'daily'::character varying, 'weekly'::character varying, 'monthly'::character varying, 'normal'::character varying])::text[])));

ALTER TABLE communication_preferences
ADD CONSTRAINT communication_preferences_sms_unsubscribe_token_key
UNIQUE (sms_unsubscribe_token);

ALTER TABLE conversation_states
ADD CONSTRAINT conversation_states_session_id_key
UNIQUE (session_id);

ALTER TABLE customer_pricing_rules
ADD CONSTRAINT customer_pricing_rules_price_tier_id_fkey
FOREIGN KEY (price_tier_id) REFERENCES price_tiers(id);

ALTER TABLE customer_pricing_rules
ADD CONSTRAINT customer_pricing_rules_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE customer_reviews
ADD CONSTRAINT customer_reviews_helpful_count_check
CHECK ((helpful_count >= 0));

ALTER TABLE customer_reviews
ADD CONSTRAINT customer_reviews_not_helpful_count_check
CHECK ((not_helpful_count >= 0));

ALTER TABLE customer_reviews
ADD CONSTRAINT customer_reviews_status_check
CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying, 'flagged'::character varying])::text[])));

ALTER TABLE customer_reviews
ADD CONSTRAINT fk_reviews_orders
FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;

ALTER TABLE customer_reviews
ADD CONSTRAINT fk_reviews_product_ratings
FOREIGN KEY (sku) REFERENCES product_ratings(sku) ON DELETE CASCADE;

ALTER TABLE customer_reviews
ADD CONSTRAINT fk_reviews_users
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE deliveries
ADD CONSTRAINT deliveries_customer_id_fkey
FOREIGN KEY (customer_id) REFERENCES profiles(id);

ALTER TABLE deliveries
ADD CONSTRAINT deliveries_delivery_address_check
CHECK (((delivery_address ? 'street'::text) AND (delivery_address ? 'city'::text) AND (delivery_address ? 'postal_code'::text)));

ALTER TABLE deliveries
ADD CONSTRAINT deliveries_rating_check
CHECK (((rating >= 1) AND (rating <= 5)));

ALTER TABLE delivery_geofences
ADD CONSTRAINT delivery_geofences_delivery_id_fkey
FOREIGN KEY (delivery_id) REFERENCES deliveries(id) ON DELETE CASCADE;

ALTER TABLE delivery_tracking
ADD CONSTRAINT delivery_tracking_battery_level_check
CHECK (((battery_level >= 0) AND (battery_level <= 100)));

ALTER TABLE delivery_tracking
ADD CONSTRAINT delivery_tracking_heading_check
CHECK (((heading >= 0) AND (heading <= 360)));

ALTER TABLE delivery_zones
ADD CONSTRAINT delivery_zones_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE delivery_zones
ADD CONSTRAINT delivery_zones_zone_type_check
CHECK (((zone_type)::text = ANY ((ARRAY['radius'::character varying, 'polygon'::character varying, 'postal_codes'::character varying])::text[])));

ALTER TABLE discount_codes
ADD CONSTRAINT discount_codes_discount_type_check
CHECK (((discount_type)::text = ANY ((ARRAY['percentage'::character varying, 'fixed'::character varying, 'bogo'::character varying, 'free_delivery'::character varying])::text[])));

ALTER TABLE discount_codes
ADD CONSTRAINT discount_codes_promotion_id_fkey
FOREIGN KEY (promotion_id) REFERENCES promotions(id);

ALTER TABLE discount_codes
ADD CONSTRAINT discount_codes_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE holidays
ADD CONSTRAINT holiday_date_check
CHECK (((((date_type)::text = 'fixed'::text) AND (fixed_month IS NOT NULL) AND (fixed_day IS NOT NULL)) OR (((date_type)::text = 'floating'::text) AND (floating_rule IS NOT NULL)) OR (((date_type)::text = 'calculated'::text) AND (calculation_rule IS NOT NULL))));

ALTER TABLE holidays
ADD CONSTRAINT holidays_date_type_check
CHECK (((date_type)::text = ANY ((ARRAY['fixed'::character varying, 'floating'::character varying, 'calculated'::character varying])::text[])));

ALTER TABLE holidays
ADD CONSTRAINT holidays_fixed_day_check
CHECK (((fixed_day >= 1) AND (fixed_day <= 31)));

ALTER TABLE holidays
ADD CONSTRAINT holidays_fixed_month_check
CHECK (((fixed_month >= 1) AND (fixed_month <= 12)));

ALTER TABLE holidays
ADD CONSTRAINT holidays_holiday_type_check
CHECK (((holiday_type)::text = ANY ((ARRAY['federal'::character varying, 'provincial'::character varying, 'municipal'::character varying, 'custom'::character varying])::text[])));

ALTER TABLE holidays
ADD CONSTRAINT holidays_typical_business_impact_check
CHECK (((typical_business_impact)::text = ANY ((ARRAY['closed'::character varying, 'reduced_hours'::character varying, 'normal'::character varying, 'extended_hours'::character varying])::text[])));

ALTER TABLE inventory_locations
ADD CONSTRAINT inventory_locations_code_key
UNIQUE (code);

ALTER TABLE location_assignments_log
ADD CONSTRAINT location_assignments_log_inventory_id_fkey
FOREIGN KEY (inventory_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE;

ALTER TABLE location_assignments_log
ADD CONSTRAINT location_assignments_log_location_id_fkey
FOREIGN KEY (location_id) REFERENCES inventory_locations(id) ON DELETE SET NULL;

ALTER TABLE message_templates
ADD CONSTRAINT message_templates_category_check
CHECK (((category)::text = ANY ((ARRAY['promotional'::character varying, 'transactional'::character varying, 'alert'::character varying, 'general'::character varying])::text[])));

ALTER TABLE message_templates
ADD CONSTRAINT message_templates_channel_type_check
CHECK (((channel_type)::text = ANY ((ARRAY['email'::character varying, 'sms'::character varying, 'push'::character varying])::text[])));

ALTER TABLE message_templates
ADD CONSTRAINT message_templates_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE model_deployments
ADD CONSTRAINT model_deployments_deployment_name_key
UNIQUE (deployment_name);

ALTER TABLE ocs_inventory
ADD CONSTRAINT ocs_inventory_quantity_available_check
CHECK ((quantity_available >= 0));

ALTER TABLE ocs_inventory
ADD CONSTRAINT ocs_inventory_quantity_on_hand_check
CHECK ((quantity_on_hand >= 0));

ALTER TABLE ocs_inventory
ADD CONSTRAINT ocs_inventory_quantity_reserved_check
CHECK ((quantity_reserved >= 0));

ALTER TABLE ocs_inventory
ADD CONSTRAINT ocs_inventory_store_id_sku_key
UNIQUE (store_id, sku);

ALTER TABLE ocs_inventory
ADD CONSTRAINT ocs_inventory_store_sku_unique
UNIQUE (store_id, sku);

ALTER TABLE ocs_inventory_logs
ADD CONSTRAINT ocs_inventory_logs_inventory_id_fkey
FOREIGN KEY (inventory_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE;

ALTER TABLE ocs_inventory_movements
ADD CONSTRAINT ocs_inventory_movements_inventory_id_fkey
FOREIGN KEY (inventory_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE;

ALTER TABLE ocs_inventory_reservations
ADD CONSTRAINT ocs_inventory_reservations_inventory_id_fkey
FOREIGN KEY (inventory_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE;

ALTER TABLE ocs_inventory_snapshots
ADD CONSTRAINT ocs_inventory_snapshots_inventory_id_fkey
FOREIGN KEY (inventory_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE;

ALTER TABLE ocs_inventory_transactions
ADD CONSTRAINT inventory_transactions_store_id_fkey
FOREIGN KEY (store_id) REFERENCES stores(id);

ALTER TABLE ocs_inventory_transactions
ADD CONSTRAINT inventory_transactions_transaction_type_check
CHECK (((transaction_type)::text = ANY ((ARRAY['purchase'::character varying, 'sale'::character varying, 'adjustment'::character varying, 'return'::character varying, 'transfer'::character varying])::text[])));

ALTER TABLE ocs_product_catalog
ADD CONSTRAINT product_catalog_ocs_rating_check
CHECK (((rating >= (0)::numeric) AND (rating <= (5)::numeric)));

ALTER TABLE ocs_product_catalog
ADD CONSTRAINT product_catalog_ocs_rating_count_check
CHECK ((rating_count >= 0));

ALTER TABLE ocs_product_catalog
ADD CONSTRAINT uk_product_catalog_ocs_variant
UNIQUE (ocs_variant_number);

ALTER TABLE payment_audit_log
ADD CONSTRAINT payment_audit_log_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL;

ALTER TABLE payment_credentials
ADD CONSTRAINT payment_credentials_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE payment_credentials
ADD CONSTRAINT payment_credentials_updated_by_fkey
FOREIGN KEY (updated_by) REFERENCES users(id);

ALTER TABLE payment_disputes
ADD CONSTRAINT payment_disputes_provider_id_fkey
FOREIGN KEY (provider_id) REFERENCES payment_providers(id);

ALTER TABLE payment_fee_splits
ADD CONSTRAINT payment_fee_splits_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE payment_fee_splits
ADD CONSTRAINT payment_fee_splits_transaction_id_key
UNIQUE (transaction_id);

ALTER TABLE payment_idempotency_keys
ADD CONSTRAINT payment_idempotency_keys_status_check
CHECK (((status)::text = ANY ((ARRAY['processing'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])));

ALTER TABLE payment_idempotency_keys
ADD CONSTRAINT payment_idempotency_keys_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE payment_methods
ADD CONSTRAINT payment_methods_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE payment_methods
ADD CONSTRAINT payment_methods_tenant_id_payment_token_provider_id_key
UNIQUE (tenant_id, payment_token, provider_id);

ALTER TABLE payment_metrics
ADD CONSTRAINT payment_metrics_date_provider_id_key
UNIQUE (date, provider_id);

ALTER TABLE payment_providers
ADD CONSTRAINT payment_providers_name_key
UNIQUE (name);

ALTER TABLE payment_refunds
ADD CONSTRAINT payment_refunds_initiated_by_fkey
FOREIGN KEY (initiated_by) REFERENCES users(id);

ALTER TABLE payment_refunds
ADD CONSTRAINT payment_refunds_refund_transaction_id_fkey
FOREIGN KEY (refund_transaction_id) REFERENCES payment_transactions(id);

ALTER TABLE payment_subscriptions
ADD CONSTRAINT payment_subscriptions_provider_id_fkey
FOREIGN KEY (provider_id) REFERENCES payment_providers(id);

ALTER TABLE payment_subscriptions
ADD CONSTRAINT payment_subscriptions_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE payment_transactions
ADD CONSTRAINT payment_transactions_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE payment_transactions
ADD CONSTRAINT payment_transactions_transaction_reference_key
UNIQUE (transaction_reference);

ALTER TABLE payment_webhook_routes
ADD CONSTRAINT payment_webhook_routes_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE payment_webhook_routes
ADD CONSTRAINT payment_webhook_routes_webhook_url_path_key
UNIQUE (webhook_url_path);

ALTER TABLE price_tiers
ADD CONSTRAINT price_tiers_name_key
UNIQUE (name);

ALTER TABLE pricing_rules
ADD CONSTRAINT unique_store_category_rule
UNIQUE (store_id, category, sub_category, sub_sub_category);

ALTER TABLE product_ratings
ADD CONSTRAINT product_ratings_average_rating_check
CHECK (((average_rating >= (0)::numeric) AND (average_rating <= (5)::numeric)));

ALTER TABLE product_ratings
ADD CONSTRAINT product_ratings_recommended_percentage_check
CHECK (((recommended_percentage >= (0)::numeric) AND (recommended_percentage <= (100)::numeric)));

ALTER TABLE product_ratings
ADD CONSTRAINT product_ratings_total_reviews_check
CHECK ((total_reviews >= 0));

ALTER TABLE product_ratings
ADD CONSTRAINT product_ratings_verified_purchase_count_check
CHECK ((verified_purchase_count >= 0));

ALTER TABLE product_recommendations
ADD CONSTRAINT product_recommendations_product_id_recommended_product_id_r_key
UNIQUE (product_id, recommended_product_id, recommendation_type);

ALTER TABLE profiles
ADD CONSTRAINT unique_user_profile
UNIQUE (user_id);

ALTER TABLE promotion_usage
ADD CONSTRAINT promotion_usage_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE promotions
ADD CONSTRAINT check_continuous_end_date
CHECK ((((is_continuous = true) AND (end_date IS NULL)) OR (is_continuous = false)));

ALTER TABLE promotions
ADD CONSTRAINT check_recurrence_logic
CHECK ((((recurrence_type)::text = 'none'::text) OR ((recurrence_type)::text = 'daily'::text) OR (((recurrence_type)::text = 'weekly'::text) AND (day_of_week IS NOT NULL) AND (array_length(day_of_week, 1) > 0))));

ALTER TABLE promotions
ADD CONSTRAINT check_time_window_complete
CHECK ((((time_start IS NULL) AND (time_end IS NULL)) OR ((time_start IS NOT NULL) AND (time_end IS NOT NULL))));

ALTER TABLE promotions
ADD CONSTRAINT check_time_window_valid
CHECK (((time_start IS NULL) OR (time_end IS NULL) OR (time_start < time_end)));

ALTER TABLE promotions
ADD CONSTRAINT promotions_code_key
UNIQUE (code);

ALTER TABLE promotions
ADD CONSTRAINT promotions_created_by_user_id_fkey
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE promotions
ADD CONSTRAINT promotions_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE provinces_territories
ADD CONSTRAINT provinces_territories_type_check
CHECK (((type)::text = ANY ((ARRAY['province'::character varying, 'territory'::character varying])::text[])));

ALTER TABLE provincial_suppliers
ADD CONSTRAINT fk_provincial_supplier_province_territory
FOREIGN KEY (provinces_territories_id) REFERENCES provinces_territories(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE provincial_suppliers
ADD CONSTRAINT suppliers_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE purchase_order_items
ADD CONSTRAINT purchase_order_items_quantity_ordered_check
CHECK ((quantity_ordered > 0));

ALTER TABLE purchase_order_items
ADD CONSTRAINT purchase_order_items_quantity_received_check
CHECK ((quantity_received >= 0));

ALTER TABLE purchase_order_items
ADD CONSTRAINT purchase_order_items_unit_cost_check
CHECK ((unit_cost >= (0)::numeric));

ALTER TABLE purchase_orders
ADD CONSTRAINT purchase_orders_status_check
CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'partial'::character varying, 'received'::character varying, 'cancelled'::character varying])::text[])));

ALTER TABLE purchase_orders
ADD CONSTRAINT purchase_orders_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE push_subscriptions
ADD CONSTRAINT push_subscriptions_device_token_key
UNIQUE (device_token);

ALTER TABLE push_subscriptions
ADD CONSTRAINT push_subscriptions_device_type_check
CHECK (((device_type)::text = ANY ((ARRAY['ios'::character varying, 'android'::character varying, 'web'::character varying])::text[])));

ALTER TABLE review_attributes
ADD CONSTRAINT chk_attribute_name
CHECK (((attribute_name)::text = ANY ((ARRAY['effects'::character varying, 'flavor'::character varying, 'potency'::character varying, 'aroma'::character varying, 'value'::character varying, 'quality'::character varying])::text[])));

ALTER TABLE review_attributes
ADD CONSTRAINT fk_attributes_reviews
FOREIGN KEY (review_id) REFERENCES customer_reviews(id) ON DELETE CASCADE;

ALTER TABLE review_attributes
ADD CONSTRAINT review_attributes_rating_check
CHECK (((rating >= 1) AND (rating <= 5)));

ALTER TABLE review_media
ADD CONSTRAINT fk_media_reviews
FOREIGN KEY (review_id) REFERENCES customer_reviews(id) ON DELETE CASCADE;

ALTER TABLE review_media
ADD CONSTRAINT review_media_media_type_check
CHECK (((media_type)::text = ANY ((ARRAY['image'::character varying, 'video'::character varying])::text[])));

ALTER TABLE review_votes
ADD CONSTRAINT fk_votes_reviews
FOREIGN KEY (review_id) REFERENCES customer_reviews(id) ON DELETE CASCADE;

ALTER TABLE review_votes
ADD CONSTRAINT fk_votes_users
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE review_votes
ADD CONSTRAINT unique_user_review_vote
UNIQUE (review_id, user_id);

ALTER TABLE role_permissions
ADD CONSTRAINT role_permissions_role_resource_type_action_key
UNIQUE (role, resource_type, action);

ALTER TABLE shelf_locations
ADD CONSTRAINT unique_location_per_store
UNIQUE (store_id, zone, aisle, shelf, bin);

ALTER TABLE store_settings
ADD CONSTRAINT store_settings_store_id_category_key_key
UNIQUE (store_id, category, key);

ALTER TABLE system_settings
ADD CONSTRAINT system_settings_category_key_key
UNIQUE (category, key);

ALTER TABLE tax_rates
ADD CONSTRAINT tax_rates_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE tenants
ADD CONSTRAINT tenants_name_key
UNIQUE (name);

ALTER TABLE tenants
ADD CONSTRAINT tenants_status_check
CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'suspended'::character varying, 'cancelled'::character varying, 'trial'::character varying])::text[])));

ALTER TABLE tenants
ADD CONSTRAINT tenants_subscription_tier_check
CHECK (((subscription_tier)::text = ANY ((ARRAY['community_and_new_business'::character varying, 'small_business'::character varying, 'professional_and_growing_business'::character varying, 'enterprise'::character varying])::text[])));

ALTER TABLE token_blacklist
ADD CONSTRAINT token_blacklist_token_id_key
UNIQUE (token_id);

ALTER TABLE token_blacklist
ADD CONSTRAINT token_blacklist_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE training_sessions
ADD CONSTRAINT training_sessions_session_id_key
UNIQUE (session_id);

ALTER TABLE translation_batches
ADD CONSTRAINT translation_batches_batch_key_key
UNIQUE (batch_key);

ALTER TABLE translation_overrides
ADD CONSTRAINT translation_overrides_translation_id_fkey
FOREIGN KEY (translation_id) REFERENCES translations(id) ON DELETE CASCADE;

ALTER TABLE translations
ADD CONSTRAINT translations_source_text_source_language_target_language_co_key
UNIQUE (source_text, source_language, target_language, context, namespace);

ALTER TABLE unsubscribe_list
ADD CONSTRAINT unsubscribe_list_broadcast_id_fkey
FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id);

ALTER TABLE unsubscribe_list
ADD CONSTRAINT unsubscribe_list_channel_type_check
CHECK (((channel_type)::text = ANY ((ARRAY['email'::character varying, 'sms'::character varying, 'push'::character varying, 'all'::character varying])::text[])));

ALTER TABLE unsubscribe_list
ADD CONSTRAINT unsubscribe_list_unsubscribe_source_check
CHECK (((unsubscribe_source)::text = ANY ((ARRAY['link'::character varying, 'reply'::character varying, 'admin'::character varying, 'api'::character varying, 'customer_request'::character varying])::text[])));

ALTER TABLE user_addresses
ADD CONSTRAINT user_addresses_address_type_check
CHECK (((address_type)::text = ANY ((ARRAY['delivery'::character varying, 'billing'::character varying])::text[])));

ALTER TABLE user_login_logs
ADD CONSTRAINT user_login_logs_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE user_sessions
ADD CONSTRAINT user_sessions_session_token_key
UNIQUE (session_token);

ALTER TABLE users
ADD CONSTRAINT users_store_id_fkey
FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL;

ALTER TABLE users
ADD CONSTRAINT users_tenant_id_fkey
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL;

ALTER TABLE users
ADD CONSTRAINT users_tenant_required
CHECK ((((role = 'super_admin'::user_role_simple) AND (tenant_id IS NULL)) OR (role = 'customer'::user_role_simple) OR ((role = ANY (ARRAY['staff'::user_role_simple, 'store_manager'::user_role_simple, 'tenant_admin'::user_role_simple])) AND (tenant_id IS NOT NULL))));

ALTER TABLE voice_auth_logs
ADD CONSTRAINT fk_voice_auth_logs_user_id
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE voice_profiles
ADD CONSTRAINT fk_voice_profiles_user_id
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE wishlist
ADD CONSTRAINT unique_wishlist_item
UNIQUE (customer_id, product_id, store_id);

-- ============================================================================
-- STEP 7: Create 39 Missing Triggers
-- ============================================================================

-- Trigger: update_ai_personalities_updated_at on ai_personalities
CREATE OR REPLACE TRIGGER update_ai_personalities_updated_at
BEFORE UPDATE ON ai_personalities
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_api_keys_updated_at on api_keys
CREATE OR REPLACE TRIGGER update_api_keys_updated_at
BEFORE UPDATE ON api_keys
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_broadcast_messages_updated_at on broadcast_messages
CREATE OR REPLACE TRIGGER update_broadcast_messages_updated_at
BEFORE UPDATE ON broadcast_messages
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_broadcast_recipients_updated_at on broadcast_recipients
CREATE OR REPLACE TRIGGER update_broadcast_recipients_updated_at
BEFORE UPDATE ON broadcast_recipients
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_broadcasts_updated_at on broadcasts
CREATE OR REPLACE TRIGGER update_broadcasts_updated_at
BEFORE UPDATE ON broadcasts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_bundle_deals_updated_at on bundle_deals
CREATE OR REPLACE TRIGGER update_bundle_deals_updated_at
BEFORE UPDATE ON bundle_deals
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_communication_preferences_updated_at on communication_preferences
CREATE OR REPLACE TRIGGER update_communication_preferences_updated_at
BEFORE UPDATE ON communication_preferences
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_conversation_states_updated_at on conversation_states
CREATE OR REPLACE TRIGGER update_conversation_states_updated_at
BEFORE UPDATE ON conversation_states
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_customer_pricing_rules_updated_at on customer_pricing_rules
CREATE OR REPLACE TRIGGER update_customer_pricing_rules_updated_at
BEFORE UPDATE ON customer_pricing_rules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: trigger_update_product_rating on customer_reviews
CREATE OR REPLACE TRIGGER trigger_update_product_rating
AFTER UPDATE ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION update_product_rating()
;

-- Trigger: trigger_update_product_rating on customer_reviews
CREATE OR REPLACE TRIGGER trigger_update_product_rating
AFTER INSERT ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION update_product_rating()
;

-- Trigger: trigger_update_product_rating on customer_reviews
CREATE OR REPLACE TRIGGER trigger_update_product_rating
AFTER DELETE ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION update_product_rating()
;

-- Trigger: trigger_validate_verified_purchase on customer_reviews
CREATE OR REPLACE TRIGGER trigger_validate_verified_purchase
BEFORE UPDATE ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_verified_purchase()
;

-- Trigger: trigger_validate_verified_purchase on customer_reviews
CREATE OR REPLACE TRIGGER trigger_validate_verified_purchase
BEFORE INSERT ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_verified_purchase()
;

-- Trigger: update_dynamic_pricing_rules_updated_at on dynamic_pricing_rules
CREATE OR REPLACE TRIGGER update_dynamic_pricing_rules_updated_at
BEFORE UPDATE ON dynamic_pricing_rules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_message_templates_updated_at on message_templates
CREATE OR REPLACE TRIGGER update_message_templates_updated_at
BEFORE UPDATE ON message_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_ocs_inventory_timestamp_trigger on ocs_inventory
CREATE OR REPLACE TRIGGER update_ocs_inventory_timestamp_trigger
BEFORE UPDATE ON ocs_inventory
FOR EACH ROW
EXECUTE FUNCTION update_inventory_timestamp()
;

-- Trigger: trigger_update_ocs_product_catalog_updated_at on ocs_product_catalog
CREATE OR REPLACE TRIGGER trigger_update_ocs_product_catalog_updated_at
BEFORE UPDATE ON ocs_product_catalog
FOR EACH ROW
EXECUTE FUNCTION update_product_catalog_updated_at()
;

-- Trigger: update_payment_credentials_updated_at on payment_credentials
CREATE OR REPLACE TRIGGER update_payment_credentials_updated_at
BEFORE UPDATE ON payment_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_payment_disputes_updated_at on payment_disputes
CREATE OR REPLACE TRIGGER update_payment_disputes_updated_at
BEFORE UPDATE ON payment_disputes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_payment_methods_updated_at on payment_methods
CREATE OR REPLACE TRIGGER update_payment_methods_updated_at
BEFORE UPDATE ON payment_methods
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_payment_providers_updated_at on payment_providers
CREATE OR REPLACE TRIGGER update_payment_providers_updated_at
BEFORE UPDATE ON payment_providers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_payment_subscriptions_updated_at on payment_subscriptions
CREATE OR REPLACE TRIGGER update_payment_subscriptions_updated_at
BEFORE UPDATE ON payment_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_payment_webhook_routes_updated_at on payment_webhook_routes
CREATE OR REPLACE TRIGGER update_payment_webhook_routes_updated_at
BEFORE UPDATE ON payment_webhook_routes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_price_tiers_updated_at on price_tiers
CREATE OR REPLACE TRIGGER update_price_tiers_updated_at
BEFORE UPDATE ON price_tiers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_pricing_rules_updated_at on pricing_rules
CREATE OR REPLACE TRIGGER update_pricing_rules_updated_at
BEFORE UPDATE ON pricing_rules
FOR EACH ROW
EXECUTE FUNCTION update_pricing_rules_updated_at()
;

-- Trigger: update_product_recommendations_updated_at on product_recommendations
CREATE OR REPLACE TRIGGER update_product_recommendations_updated_at
BEFORE UPDATE ON product_recommendations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_provincial_suppliers_updated_at on provincial_suppliers
CREATE OR REPLACE TRIGGER update_provincial_suppliers_updated_at
BEFORE UPDATE ON provincial_suppliers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_purchase_orders_timestamp_trigger on purchase_orders
CREATE OR REPLACE TRIGGER update_purchase_orders_timestamp_trigger
BEFORE UPDATE ON purchase_orders
FOR EACH ROW
EXECUTE FUNCTION update_inventory_timestamp()
;

-- Trigger: update_push_subscriptions_updated_at on push_subscriptions
CREATE OR REPLACE TRIGGER update_push_subscriptions_updated_at
BEFORE UPDATE ON push_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: trigger_update_review_vote_counts on review_votes
CREATE OR REPLACE TRIGGER trigger_update_review_vote_counts
AFTER INSERT ON review_votes
FOR EACH ROW
EXECUTE FUNCTION update_review_vote_counts()
;

-- Trigger: trigger_update_review_vote_counts on review_votes
CREATE OR REPLACE TRIGGER trigger_update_review_vote_counts
AFTER DELETE ON review_votes
FOR EACH ROW
EXECUTE FUNCTION update_review_vote_counts()
;

-- Trigger: trigger_update_review_vote_counts on review_votes
CREATE OR REPLACE TRIGGER trigger_update_review_vote_counts
AFTER UPDATE ON review_votes
FOR EACH ROW
EXECUTE FUNCTION update_review_vote_counts()
;

-- Trigger: update_shelf_locations_updated_at on shelf_locations
CREATE OR REPLACE TRIGGER update_shelf_locations_updated_at
BEFORE UPDATE ON shelf_locations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_staff_delivery_status_updated_at on staff_delivery_status
CREATE OR REPLACE TRIGGER update_staff_delivery_status_updated_at
BEFORE UPDATE ON staff_delivery_status
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_system_settings_updated_at on system_settings
CREATE OR REPLACE TRIGGER update_system_settings_updated_at
BEFORE UPDATE ON system_settings
FOR EACH ROW
EXECUTE FUNCTION update_system_settings_updated_at()
;

-- Trigger: update_overrides_updated_at on translation_overrides
CREATE OR REPLACE TRIGGER update_overrides_updated_at
BEFORE UPDATE ON translation_overrides
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: update_translations_updated_at on translations
CREATE OR REPLACE TRIGGER update_translations_updated_at
BEFORE UPDATE ON translations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;

-- Trigger: trigger_update_user_last_login on user_login_logs
CREATE OR REPLACE TRIGGER trigger_update_user_last_login
AFTER INSERT ON user_login_logs
FOR EACH ROW
EXECUTE FUNCTION update_user_last_login()
;

COMMIT;

-- Migration complete!