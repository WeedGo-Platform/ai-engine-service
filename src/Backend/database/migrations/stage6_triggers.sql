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
SELECT 'Stage 6: Triggers created' AS status;
