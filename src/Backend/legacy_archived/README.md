# Legacy Code Archive

**Date Archived:** 2025-10-18
**Git Tag:** `legacy-snapshot-before-ddd-migration`
**Migration Project:** DDD Migration for Inventory Management Domain

---

## Purpose

This directory contains archived legacy service implementations that have been replaced by Domain-Driven Design (DDD) architecture. These files are preserved for:

1. **Historical Reference:** Understanding legacy business logic
2. **Rollback Safety:** Quick restoration if critical issues arise
3. **Migration Verification:** Comparing legacy vs DDD behavior during testing
4. **Documentation:** Preserving institutional knowledge

---

## Archived Services

### 1. `inventory_service.py` (1,247 lines)

**Original Location:** `src/Backend/services/inventory_service.py`

**Responsibilities:**
- Purchase order creation from ASN imports
- Purchase order receiving workflow
- Inventory receiving with batch creation
- Direct SQL queries for batch_tracking and ocs_inventory tables
- Weighted average cost calculations
- Product catalog integration

**Replaced By:**
- `PurchaseOrderApplicationService` (DDD) - PO creation and receiving
- `InventoryManagementService` (DDD) - Inventory and batch operations
- `BatchTrackingRepository` (DDD) - Batch data access
- `InventoryRepository` (DDD) - Inventory data access

**Key Issues in Legacy Code:**
- Business logic scattered across SQL queries
- No domain model - uses raw dictionaries
- FIFO logic embedded in SQL ORDER BY clauses
- Difficult to test (tightly coupled to database)
- No validation in domain layer

---

### 2. `store_inventory_service.py` (782 lines)

**Original Location:** `src/Backend/services/store_inventory_service.py`

**Responsibilities:**
- POS inventory updates (SALE, RETURN, ADJUSTMENT, DAMAGE, SPOILAGE)
- FIFO consumption logic for sales
- Batch quantity adjustments
- Transaction logging to inventory_transactions table
- Inventory balance calculations

**Replaced By:**
- `InventoryManagementService.consume_inventory_fifo()` (DDD) - FIFO consumption
- `InventoryManagementService.adjust_inventory()` (DDD) - Manual adjustments
- `BatchTrackingService.adjust_batch_quantity()` (DDD) - Batch adjustments
- `BatchTracking.consume()` (Domain method) - Consumption logic
- `Inventory.reduce()` (Domain method) - Balance reduction

**Key Issues in Legacy Code:**
- Transaction logic mixed with infrastructure code
- FIFO algorithm duplicated in multiple places
- No domain events for audit trail
- Hard to extend for new transaction types

---

### 3. `shelf_location_service.py` (486 lines)

**Original Location:** `src/Backend/services/shelf_location_service.py`

**Responsibilities:**
- Shelf location management (CRUD)
- Product-to-location assignment
- Product transfer between locations
- Location capacity validation
- Batch-to-location mapping

**Replaced By:**
- `BatchTrackingService.move_batch_to_location()` (DDD)
- `BatchTracking.move_to_location()` (Domain method)
- Future: `LocationManagementService` (DDD) - for location CRUD

**Key Issues in Legacy Code:**
- Batch location updates scattered across multiple methods
- No domain validation for location capacity
- Weak enforcement of business rules

---

## Migration Timeline

| Phase | Status | Date |
|-------|--------|------|
| Phase 1: DDD Infrastructure | ✅ Complete | 2025-10-18 |
| Phase 2: Archive Legacy | ✅ Complete | 2025-10-18 |
| Phase 3: Feature Flags | ⏳ In Progress | TBD |
| Phase 4: DDD Endpoints | ⏳ Pending | TBD |
| Phase 5: Dependency Wiring | ⏳ Pending | TBD |
| Phase 6: Testing & Rollout | ⏳ Pending | TBD |

---

## How to Restore Legacy Code (Rollback Procedure)

**⚠️ ONLY use this if DDD implementation has critical bugs**

```bash
# 1. Checkout git tag
git checkout legacy-snapshot-before-ddd-migration

# 2. Restore specific legacy service
cp src/Backend/legacy_archived/services/inventory_service.py src/Backend/services/inventory_service.py

# 3. Turn off DDD feature flags
export USE_DDD_INVENTORY=false
export USE_DDD_BATCH_TRACKING=false
export USE_DDD_PO_RECEIVING=false

# 4. Restart API server
# (Your restart command)

# 5. Verify legacy endpoints work
curl http://localhost:8000/api/inventory/...
```

**Estimated Rollback Time:** 5 minutes

---

## Code Metrics Comparison

| Metric | Legacy (3 Services) | DDD (Phase 1) |
|--------|---------------------|---------------|
| Total Lines of Code | ~2,515 | ~1,258 |
| Business Logic in SQL | 85% | 0% |
| Test Coverage | 12% | 0% (TBD in Phase 6) |
| Domain Model | None | Rich Aggregates/Entities |
| Separation of Concerns | Poor | Excellent |
| FIFO Implementation | 5 places | 1 place |
| Weighted Avg Cost | SQL function | Python method |

---

## Key Business Logic Preserved

✅ **FIFO Consumption:** Legacy: SQL ORDER BY created_at → DDD: `find_active_for_sku(order_by="created_at")`
✅ **Weighted Average Cost:** Legacy: SQL calculation → DDD: Python calculation in `receive_inventory()`
✅ **Auto-Approve on Receive:** Legacy: Manual SQL UPDATE → DDD: `PurchaseOrder.receive(auto_approve=True)`
✅ **Batch UPSERT:** Legacy: SQL ON CONFLICT → DDD: Repository `save()` with find_by_lot check
✅ **Inventory Balance:** Legacy: `quantity_on_hand` → DDD: `Inventory.running_balance`
✅ **Transaction Logging:** Legacy: INSERT to inventory_transactions → DDD: Domain events (future)

---

## Removal Plan

**When to remove:** After 4 weeks of production stability with DDD implementation (Phase 6 complete)

**Procedure:**
1. Confirm zero usage of legacy services in logs
2. Confirm all feature flags permanently set to DDD mode
3. Delete `legacy_archived/` directory
4. Delete legacy service files from `services/` directory
5. Update git tag to `legacy-fully-removed`

---

## Contact

For questions about legacy code behavior or migration status, see:
- `DDD_MIGRATION_PROGRESS.md` - Migration status tracker
- `DDD_MIGRATION_STRATEGY.md` - Complete migration plan
- `BATCH_TRACKING_SYSTEM_ANALYSIS.md` - Legacy system analysis

---

**Status:** Legacy code safely archived ✅
**Next Step:** Implement feature flags (Phase 3)
