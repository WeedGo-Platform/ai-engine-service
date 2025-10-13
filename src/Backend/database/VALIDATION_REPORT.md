# Migration Validation Report
**Generated:** 2025-10-12 22:27:22

## Summary
- ✅ Passed: 22
- ⚠️  Warnings: 2
- ❌ Failed: 0
- **Success Rate:** 91.7%

## Passed Tests
- ✅ Table agi_audit_aggregates: Accessible, can insert
- ✅ Table agi_audit_alerts: Accessible, can insert
- ✅ Table agi_audit_logs: Accessible, can insert
- ✅ Table agi_rate_limit_buckets: Accessible, can insert
- ✅ Table agi_rate_limit_rules: Accessible, can insert
- ✅ Table agi_rate_limit_violations: Accessible, can insert
- ✅ Column ai_conversations.tenant_id: uuid
- ✅ Column ai_conversations.personality_id: uuid
- ✅ Column profiles.customer_type: character varying
- ✅ Column ocs_inventory.quantity_available: integer
- ✅ Column deliveries.customer_id: uuid
- ✅ Column payment_transactions.tenant_id: uuid
- ✅ Column promotions.tenant_id: uuid
- ✅ Column broadcasts.tenant_id: uuid
- ✅ Index idx_ocs_inventory_sku_lower: Exists
- ✅ Index idx_profiles_customer_type: Exists
- ✅ Index idx_transactions_tenant: Exists
- ✅ Index idx_deliveries_customer_id: Exists
- ✅ Function update_updated_at_column: Exists
- ✅ Function calculate_final_price: Exists
- ✅ Function is_promotion_active_now: Exists
- ✅ Function get_store_ai_config: Exists

## Warnings
- ⚠️  No test data for trigger validation
- ⚠️  No user_role constraints found
