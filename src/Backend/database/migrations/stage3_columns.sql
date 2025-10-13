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

SELECT 'Stage 3: Columns added successfully' AS status;
