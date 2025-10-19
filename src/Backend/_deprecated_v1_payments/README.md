# Deprecated V1 Payment Endpoints

**Deprecated Date:** 2025-01-18
**Reason:** Migrated to V2 DDD-powered payment implementation
**New Location:** `api/v2/payments/payment_endpoints.py`

---

## Summary

This directory contains the deprecated V1 payment endpoints and services that have been replaced by a simplified DDD (Domain-Driven Design) implementation.

### Migration Overview

**From:** Complex 16-table tenant-level architecture
**To:** Simplified 6-table store-level architecture (62.5% reduction)

---

## Archived Files

### V1 Payment Endpoints (7 files)
1. **`payment_endpoints.py`** (737 lines)
   - General payment transaction endpoints
   - Replaced by: `api/v2/payments/payment_endpoints.py`

2. **`payment_session_endpoints.py`** (278 lines)
   - Clover payment session management
   - Replaced by: Store-level provider integration in V2

3. **`payment_provider_endpoints.py`** (722 lines)
   - Payment provider CRUD operations
   - Replaced by: `store_payment_providers` table + V2 endpoints

4. **`payment_settings_endpoints.py`**
   - Payment configuration settings
   - Replaced by: Store-level provider configuration

5. **`user_payment_endpoints.py`**
   - User-specific payment methods
   - Replaced by: V2 payment method management

6. **`client_payment_endpoints.py`**
   - Client payment processing
   - Replaced by: V2 unified payment processing

7. **`store_payment_endpoints.py`**
   - Store payment terminal endpoints
   - Replaced by: V2 store provider endpoints

### V1 Payment Services (4 files)
1. **`payment_service.py`** (775 lines)
   - Legacy payment service (non-DDD)
   - Replaced by: `ddd_refactored/application/services/payment_service.py`

2. **`payment_service_v2.py`**
   - Intermediate payment service
   - Replaced by: DDD PaymentService

3. **`store_payment_service.py`**
   - Store-specific payment logic
   - Replaced by: Store-level PaymentService

4. **`services/payments/payment_service_v2.py`**
   - Another intermediate version
   - Replaced by: Final DDD implementation

---

## Key Changes in V2

### Architecture
- **Old:** Tenant-level payment providers
- **New:** Store-level payment providers (each store has own config)

### Database
- **Old:** 16 tables, 38 columns in payment_transactions
- **New:** 6 tables, 17 columns in payment_transactions (55% reduction)

### Providers
- **Old:** 7 providers (STRIPE, SQUARE, MONERIS, BAMBORA, PAYPAL, MANUAL, INTERNAL)
- **New:** 3 providers (CLOVER, MONERIS, INTERAC) - Canadian focus

### DDD Implementation
- **Old:** Mixed inheritance-based + non-DDD code
- **New:** Pure DDD with dataclasses, clean layers, events

### Features Removed
- Platform fee calculation (handled by payment processors)
- Split payments (simplified to single provider per transaction)
- Multiple payment methods per transaction

---

## Migration Guide

### For Developers

If you need to reference old V1 endpoints:
1. Check `api/v2/payments/payment_endpoints.py` for V2 equivalents
2. Review `PAYMENT_REFACTOR_SESSION_COMPLETE.md` for migration details
3. See `PAYMENT_DDD_ALIGNMENT_ANALYSIS.md` for architectural differences

### For Frontend Teams

**V1 Endpoints (Deprecated):**
```
POST /api/payments/process
GET  /api/payments/{id}
POST /api/payments/{id}/refund
```

**V2 Endpoints (Active):**
```
POST /api/v2/payments/process
GET  /api/v2/payments/{transaction_id}
POST /api/v2/payments/{transaction_id}/refund
```

**Breaking Changes:**
1. Response structure changed (now returns DTOs, not domain objects)
2. Provider configuration is now store-level, not tenant-level
3. Payment method structure simplified
4. Platform fees removed from response

---

## Files Archived

### Endpoint Files (Total: ~2,500 lines)
```
_deprecated_v1_payments/
├── payment_endpoints.py                (737 lines)
├── payment_session_endpoints.py        (278 lines)
├── payment_provider_endpoints.py       (722 lines)
├── payment_settings_endpoints.py       (~500 lines)
├── user_payment_endpoints.py           (~600 lines)
├── client_payment_endpoints.py         (~700 lines)
└── store_payment_endpoints.py          (~650 lines)
```

### Service Files (Total: ~1,200 lines)
```
_deprecated_v1_payments/
├── payment_service.py                  (775 lines)
├── payment_service_v2.py               (~400 lines)
└── store_payment_service.py            (~700 lines)
```

**Total Deprecated Code:** ~3,700 lines
**New V2 Implementation:** ~6,370 lines (includes domain, infrastructure, application layers)

---

## Rollback Instructions

**⚠️ NOT RECOMMENDED - Use only in emergency**

If you need to rollback to V1 (not recommended):

1. **Restore files:**
   ```bash
   cd /Backend
   mv _deprecated_v1_payments/*.py api/
   ```

2. **Update api_server.py:**
   - Uncomment V1 payment endpoint imports (lines ~54-56)
   - Uncomment V1 router registrations (lines ~518-522)
   - Comment out V2 payment endpoint import (lines ~763-769)

3. **Database rollback:**
   ```bash
   psql -U weedgo -d ai_engine < migrations/payment_refactor/rollback.sql
   ```

---

## Support

For questions about the migration:
- Review `PAYMENT_REFACTOR_SESSION_COMPLETE.md` for complete implementation details
- Check `PAYMENT_REFACTOR_PLAN.md` for original migration strategy
- See `ddd_refactored/domain/payment_processing/` for new domain models

**Status:** Migration complete, V1 endpoints deprecated
**Next Steps:** Frontend migration to V2 endpoints
