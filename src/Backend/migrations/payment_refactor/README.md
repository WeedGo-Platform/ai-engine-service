# Payment System Refactor Migrations

## Overview

These migrations refactor the payment system from **16 tables to 6 tables**, changing from **tenant-level to store-level** provider architecture, and removing unnecessary fee structure complexity.

## Migration Files

| File | Purpose | Status |
|------|---------|--------|
| `001_backup_payment_schema.sql` | Backup all 16 existing payment tables | ✅ Safe |
| `002_drop_deprecated_payment_tables.sql` | Drop 10 deprecated tables | ⚠️ Destructive |
| `003_recreate_payment_core_tables.sql` | Create 6 simplified core tables | ✅ Safe |
| `004_seed_payment_providers.sql` | Seed Clover, Moneris, Interac providers | ✅ Safe |
| `999_rollback.sql` | Rollback to original schema | 🔄 Recovery |

## Quick Start

### Option 1: Automated (Recommended)

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/migrations/payment_refactor
./run_migrations.sh
```

### Option 2: Manual

```bash
# 1. Backup
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 001_backup_payment_schema.sql

# 2. Drop deprecated tables
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 002_drop_deprecated_payment_tables.sql

# 3. Recreate core tables
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 003_recreate_payment_core_tables.sql

# 4. Seed providers
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 004_seed_payment_providers.sql
```

## Changes Summary

### Tables Reduced: 16 → 6 (62.5% reduction)

#### ✅ Kept (Simplified)
1. **payment_providers** (19→12 columns) - Global provider registry
2. **store_payment_providers** (NEW) - Store-level configs (replaces tenant_payment_providers)
3. **payment_transactions** (38→17 columns) - 55% reduction!
4. **payment_methods** (22→14 columns) - Tokenized payment methods
5. **payment_refunds** (17→12 columns) - Refund tracking
6. **payment_webhooks** (16→11 columns) - Webhook events

#### ❌ Removed
1. `payment_fee_splits` - Fee structure removed
2. `payment_settlements` - Handled by processors
3. `payment_metrics` - Calculate from transactions
4. `payment_provider_health_metrics` - Over-engineering
5. `payment_subscriptions` - Not needed for retail
6. `payment_disputes` - Use transaction status
7. `payment_webhook_routes` - Store in config
8. `payment_idempotency_keys` - Column in transactions
9. `payment_audit_log` - Use structured logs
10. `payment_credentials` - Merged into store_payment_providers
11. `tenant_payment_providers` - Replaced by store-level

### Architecture Changes

**BEFORE:**
```
Tenant → Payment Provider (tenant_payment_providers)
  └── All stores inherit same config
```

**AFTER:**
```
Store → Payment Provider (store_payment_providers)
  └── Each store has own config, credentials, terminals
```

### Columns Removed from payment_transactions (21 columns)

- `provider_fee` - Not needed for processing
- `platform_fee` - Not needed for processing
- `net_amount` - Not needed for processing
- `tenant_net_amount` - Not needed for processing
- `tax_amount` - Should be in order
- `tenant_id` - Redundant (store → tenant)
- `tenant_provider_id` - Replaced by store_provider_id
- `fraud_status` - Over-engineering
- `risk_score` - Over-engineering
- `risk_factors` - Over-engineering
- `device_fingerprint` - Over-engineering
- `user_agent` - Not essential
- `authentication_status` - Over-engineering
- `authentication_data` - Over-engineering
- `processed_at` - Redundant with completed_at
- `failed_at` - Use status + updated_at
- `type` - Duplicate of transaction_type
- Plus 4 more...

## Safety Features

### Backups
All tables backed up to `payment_backup` schema before any destructive operations.

### Verification Queries
Each migration includes verification queries to confirm success.

### Rollback
If something goes wrong:
```bash
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 999_rollback.sql
```

## Pre-Migration Checklist

- [ ] Database backup completed
- [ ] No active payment transactions (verified: 0 transactions)
- [ ] Backend services stopped (optional, but recommended)
- [ ] Migration files reviewed
- [ ] Rollback script tested (optional)

## Post-Migration Checklist

- [ ] Verify 6 payment tables exist
- [ ] Verify 3 payment providers seeded
- [ ] Check migration_log table for success
- [ ] Review column counts match expectations
- [ ] Test database connections from application

## Expected Results

### Before Migration
```sql
SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'payment%';
-- Result: 16 tables
```

### After Migration
```sql
SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'payment%';
-- Result: 6 tables (plus payment_backup.* for rollback)
```

### Provider Verification
```sql
SELECT provider_name, is_active, is_sandbox FROM payment_providers ORDER BY priority;
-- Expected:
-- Clover    | t | t
-- Moneris   | t | t
-- Interac   | t | t
```

## Next Steps After Migration

1. **Implement DDD Domain Models**
   - PaymentTransaction (Aggregate Root)
   - Money, PaymentStatus (Value Objects)
   - PaymentRepository (Repository Pattern)

2. **Update Provider Integrations**
   - Clover: Update for store_id instead of tenant_id
   - Moneris: Update for store_id instead of tenant_id
   - Interac: Update for store_id instead of tenant_id

3. **Build V2 API Endpoints**
   - POST `/api/v2/payments/stores/{store_id}/transactions`
   - POST `/api/v2/payments/stores/{store_id}/providers/{provider_type}/configure`
   - POST `/api/v2/payments/transactions/{transaction_id}/refund`

4. **Remove V1 Endpoints**
   - Delete `/api/payment_endpoints.py`
   - Delete `/api/payment_provider_endpoints.py`
   - Plus 5 more V1 files

5. **Update Frontend**
   - Change to V2 API endpoints
   - Update to use store-level provider selection

## Troubleshooting

### Migration Fails at Step 2
**Problem:** Foreign key constraints prevent dropping tables
**Solution:** Run with CASCADE (already included in scripts)

### Migration Fails at Step 3
**Problem:** Stores table doesn't exist
**Solution:** Ensure stores table exists before running migrations

### Need to Rollback
**Problem:** Something went wrong
**Solution:**
```bash
psql "postgresql://weedgo:weedgo123@localhost:5434/ai_engine" -f 999_rollback.sql
```

## Support

For issues or questions:
1. Check `migration_log` table for error messages
2. Review PostgreSQL logs
3. Consult PAYMENT_REFACTOR_PLAN.md for full implementation details

---

**Created:** 2025-01-18
**Status:** Ready for execution
**Risk Level:** Low (0 payment transactions in database)
