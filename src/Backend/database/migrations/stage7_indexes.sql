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
SELECT 'Stage 7: Indexes created' AS status;
