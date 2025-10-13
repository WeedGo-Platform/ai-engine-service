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
SELECT 'Stage 8: Constraints added' AS status;
