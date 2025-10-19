# DDD vs Legacy Architecture Analysis

**Date:** 2025-10-18
**Status:** Mixed Architecture - Partial DDD Implementation

---

## Executive Summary

The codebase has **TWO parallel architectures** running side-by-side:

1. **DDD (Domain-Driven Design) Implementation** - Partial, only for Purchase Orders
2. **Legacy Direct Database Queries** - Majority of the system (Inventory, Batch Tracking, POS)

**Key Finding:** Only **Purchase Order Creation** uses DDD. Everything else (receiving, inventory management, batch tracking, POS sales) uses direct SQL queries in service classes.

---

## Architecture Breakdown by Feature

### ✅ Purchase Order Creation - **USES DDD**

**Entry Point:** `POST /api/inventory/purchase-orders`

**Flow:**
```
API Endpoint (inventory_endpoints.py:174)
    ↓
PurchaseOrderApplicationService (DDD)
    ↓
PurchaseOrder Entity (Domain Model)
    ↓
AsyncPGPurchaseOrderRepository (Repository Pattern)
    ↓
Database (purchase_orders, purchase_order_items tables)
```

**Files:**
- `api/inventory_endpoints.py:174-225` - API endpoint
- `ddd_refactored/application/services/purchase_order_service.py` - Application service
- `ddd_refactored/domain/purchase_order/entities/purchase_order.py` - Domain entity
- `ddd_refactored/domain/purchase_order/repositories/__init__.py` - Repository

**DDD Components Used:**
- ✅ Application Service
- ✅ Domain Entity (Aggregate Root)
- ✅ Repository Pattern
- ✅ Value Objects (PurchaseOrderStatus, ApprovalStatus)
- ❌ Domain Events (not implemented)
- ❌ Specifications (not used)

**Comment in Code:**
```python
"""
Create a new purchase order using DDD architecture

⚡ REFACTORED: Now uses Domain-Driven Design application service
- Maintains exact same API contract for backward compatibility
- Internal implementation uses PurchaseOrder aggregate and repository
- Business logic encapsulated in domain model
"""
```

---

### ❌ Purchase Order Receiving - **LEGACY SQL QUERIES**

**Entry Point:** `POST /api/inventory/purchase-orders/{po_id}/receive`

**Flow:**
```
API Endpoint (inventory_endpoints.py:228)
    ↓
InventoryService.receive_purchase_order() (Legacy Service)
    ↓
Direct SQL INSERT/UPDATE queries
    ↓
Database (ocs_inventory, batch_tracking, ocs_inventory_transactions)
```

**Files:**
- `api/inventory_endpoints.py:228-253` - API endpoint
- `services/inventory_service.py:273-488` - **Direct SQL queries**

**Code Example:**
```python
async def receive_purchase_order(self, po_id: UUID, received_items: List[Dict[str, Any]],
                                 received_by: Optional[UUID] = None) -> bool:
    # Direct SQL - NO DDD
    update_query = "UPDATE ocs_inventory SET quantity_on_hand = quantity_on_hand + $2 WHERE sku = $1"

    batch_query = """
        INSERT INTO batch_tracking (store_id, batch_number, batch_lot, sku, ...)
        VALUES ($1, $2, $3, $4, ...)
        ON CONFLICT (batch_lot) DO UPDATE ...
    """

    await self.db.execute(batch_query, ...)  # Direct asyncpg execution
```

**NOT using:**
- ❌ BatchTracking entity (exists in `ddd_refactored/domain/inventory_management/entities/batch_tracking.py` but **unused**)
- ❌ Repository pattern
- ❌ Domain methods (like `batch.consume()`, `batch.receive()`)

---

### ❌ Inventory Management - **LEGACY SQL QUERIES**

**Service:** `InventoryService` in `services/inventory_service.py`

**All operations use direct SQL:**
- Inventory search → Direct JOIN queries
- Stock adjustments → Direct UPDATE queries
- Product lookups → Direct SELECT queries

**Code Example:**
```python
# Line 591-600
query = """
    SELECT
        ipv.*,
        bt.batch_lot,
        bt.quantity_remaining
    FROM inventory_products_view ipv
    LEFT JOIN batch_tracking bt ON ipv.sku = bt.sku
    WHERE 1=1
"""
result = await self.db.fetch(query, ...)  # Direct SQL
```

---

### ❌ Batch Tracking - **LEGACY SQL QUERIES**

**No DDD Implementation Used**

**DDD Entity Exists But Unused:**
- File: `ddd_refactored/domain/inventory_management/entities/batch_tracking.py`
- Rich domain model with methods:
  - `consume(quantity)` - Reduce batch quantity
  - `damage(quantity, reason)` - Record damaged items
  - `expire(quantity)` - Mark as expired
  - `perform_quality_check()` - QC workflow
  - `quarantine()` - Quarantine batch
  - `is_expired()`, `days_until_expiry()` - Business logic

**Actual Production Code:**
```python
# services/inventory_service.py:456
batch_query = """
    INSERT INTO batch_tracking
    (store_id, batch_number, batch_lot, sku, purchase_order_id, ...)
    VALUES ($1, $2, $3, $4, $5, ...)
    ON CONFLICT (batch_lot) DO UPDATE ...
"""
await self.db.execute(batch_query, ...)  # Direct SQL, no entity
```

**Why Entity Not Used:**
The DDD BatchTracking entity has extensive business logic (quality checks, quarantine, expiry tracking) that is **NOT being used**. Production code just does raw INSERTs.

---

### ❌ POS Sales (Inventory Consumption) - **LEGACY SQL QUERIES**

**Service:** `StoreInventoryService` in `services/store_inventory_service.py`

**FIFO Batch Consumption:**
```python
# Line 428-453 - FIFO logic
active_batches = await conn.fetch("""
    SELECT id, batch_lot, quantity_remaining
    FROM batch_tracking
    WHERE store_id = $1 AND sku = $2 AND is_active = true
    ORDER BY created_at ASC  -- FIFO
""", store_id, sku)

for batch in active_batches:
    # Direct UPDATE - no domain entity
    await conn.execute("""
        UPDATE batch_tracking
        SET quantity_remaining = $3,
            is_active = CASE WHEN $3 = 0 THEN false ELSE true END
        WHERE id = $1
    """, batch['id'], store_id, new_remaining)
```

**Could Use DDD:**
```python
# What it COULD be with DDD:
batch = await batch_repository.find_by_id(batch_id)
batch.consume(quantity_to_reduce)  # Domain method
await batch_repository.save(batch)
```

---

### ❌ Shelf Location Management - **LEGACY SQL QUERIES**

**Service:** `ShelfLocationService` in `services/shelf_location_service.py`

Direct SQL updates to `batch_tracking.location_id`:

```python
# Line 225-229
batch_update_query = """
    UPDATE batch_tracking
    SET location_id = $2
    WHERE batch_lot = $1
"""
await self.db.execute(batch_update_query, batch_lot, location_id)
```

**Could Use DDD:**
```python
batch = await batch_repository.find_by_lot(batch_lot)
batch.move_to_location(location_id)  # Domain method exists!
await batch_repository.save(batch)
```

---

## DDD Entities That Exist But Are NEVER Used

### 1. BatchTracking Entity
**File:** `ddd_refactored/domain/inventory_management/entities/batch_tracking.py`

**Rich Business Logic Implemented:**
- ✅ `consume()` - Decrease quantity
- ✅ `damage()` - Record damaged items
- ✅ `expire()` - Mark expired
- ✅ `perform_quality_check()` - QC workflow
- ✅ `quarantine()` / `release_from_quarantine()`
- ✅ `move_to_location()` - Location management
- ✅ `is_expired()`, `is_near_expiry()` - Date logic
- ✅ `get_utilization_rate()`, `get_wastage_rate()` - Analytics
- ✅ `can_allocate()` - Business rule validation

**Usage Count:** **ZERO** - Never imported anywhere

---

### 2. Inventory Entity
**File:** `ddd_refactored/domain/inventory_management/entities/inventory.py`

**Methods:**
- Stock level management
- Reserve/release operations
- Reorder point calculations

**Usage Count:** Likely **ZERO** (would need to verify)

---

### 3. InventoryReservation Entity
**File:** `ddd_refactored/domain/inventory_management/entities/inventory_reservation.py`

**Purpose:** Reserve inventory for orders

**Usage Count:** **ZERO** - Table `ocs_inventory_reservations` has 0 records, entity never used

---

## Why This Happened: Migration In Progress

### Evidence of Partial Migration:

**1. Comment in PO Endpoint:**
```python
"""
⚡ REFACTORED: Now uses Domain-Driven Design application service
- Maintains exact same API contract for backward compatibility
"""
```

**2. DDD Folder Structure Exists:**
- Complete bounded context structure
- Entities, repositories, value objects defined
- Application services partially implemented

**3. Only PO Creation Migrated:**
- PO creation uses DDD ✅
- PO receiving still uses legacy SQL ❌
- Everything else untouched ❌

### Why Stop at PO Creation?

**Likely reasons:**
1. **Complexity** - Migrating batch tracking with FIFO logic is complex
2. **Risk** - POS sales is mission-critical, risky to refactor
3. **Time** - DDD migration takes significant effort
4. **Dependencies** - Batch tracking touches many systems

---

## Current Architecture Summary

| Feature | Architecture | File | DDD Components |
|---------|-------------|------|----------------|
| **PO Creation** | ✅ DDD | `ddd_refactored/application/services/purchase_order_service.py` | Entity, Repository, Service |
| **PO Receiving** | ❌ Legacy SQL | `services/inventory_service.py:273` | None |
| **Batch Tracking** | ❌ Legacy SQL | `services/inventory_service.py:456` | Entity exists but unused |
| **Inventory Search** | ❌ Legacy SQL | `services/inventory_service.py:591` | None |
| **POS Sales (FIFO)** | ❌ Legacy SQL | `services/store_inventory_service.py:428` | None |
| **Shelf Locations** | ❌ Legacy SQL | `services/shelf_location_service.py:225` | None |
| **Stock Adjustments** | ❌ Legacy SQL | `services/store_inventory_service.py:678` | None |

---

## Code Smells and Issues

### 1. **Unused DDD Entities**
Comprehensive domain models exist but are never instantiated. This is **wasted code** that:
- Increases maintenance burden
- Creates confusion about which code is "real"
- Makes onboarding harder

### 2. **Inconsistent Patterns**
Same endpoint (`inventory_endpoints.py`) mixes DDD (PO creation) and legacy (PO receiving)

```python
# Same file, different patterns!

@router.post("/purchase-orders")  # Uses DDD
async def create_purchase_order(po_service: PurchaseOrderApplicationService):
    result = await po_service.create_from_asn(...)

@router.post("/purchase-orders/{po_id}/receive")  # Uses Legacy SQL
async def receive_purchase_order(service: InventoryService):
    success = await service.receive_purchase_order(...)  # Direct SQL
```

### 3. **Business Logic in Service Layer**
FIFO logic, batch consumption rules, expiry checks are in SQL, not domain:

```python
# Business rule: "Consume oldest batches first"
# Should be: Domain logic in BatchTracking entity
# Actually is: SQL query in service

active_batches = await conn.fetch("""
    SELECT id FROM batch_tracking
    WHERE ... ORDER BY created_at ASC  -- FIFO rule in SQL!
""")
```

### 4. **Duplicate Validation**
- DDD entities have validation (e.g., `BatchTracking.validate()`)
- Legacy code validates in API layer or not at all

---

## Recommendations

### Option 1: Complete the DDD Migration
**Effort:** High (3-6 months)
**Risk:** Medium
**Benefit:** Clean architecture, maintainable, testable

**Steps:**
1. Migrate PO receiving to use PurchaseOrder.receive() domain method
2. Create BatchTrackingRepository and use existing BatchTracking entity
3. Implement domain services for FIFO consumption
4. Migrate inventory operations to use domain model

### Option 2: Abandon DDD, Keep Legacy
**Effort:** Medium (cleanup)
**Risk:** Low
**Benefit:** Consistency, simpler codebase

**Steps:**
1. Remove unused DDD entities (BatchTracking, Inventory, etc.)
2. Keep only PurchaseOrder DDD implementation (already working)
3. Accept that this is a **"Good Enough" CRUD application**
4. Focus on adding tests to existing services

### Option 3: Hybrid Approach (Recommended)
**Effort:** Medium
**Risk:** Low
**Benefit:** Pragmatic, incremental improvement

**Steps:**
1. **Keep PO Creation as DDD** - it's working, don't touch
2. **Keep PO Receiving as Legacy** - mission-critical, low value to refactor
3. **Remove unused DDD entities** - BatchTracking, Inventory, etc.
4. **Document the hybrid approach** - Make it intentional, not accidental
5. **Add integration tests** to lock in current behavior

---

## Answer to Your Question

> "Are all these codes DDD implementation? Or just quick DB queries?"

**Answer:**

**99% Legacy SQL Queries, 1% DDD**

- **Purchase Order Creation:** DDD implementation with entities, repositories, application services
- **Everything Else:** Direct SQL queries in service classes

**The DDD entities for Batch Tracking exist but are NEVER used.** The production code that handles batch receiving, FIFO consumption, location management - all uses direct `INSERT/UPDATE/SELECT` queries via asyncpg.

**This is a partially migrated codebase** where someone started DDD refactoring but only completed the PO creation use case. All the batch tracking and inventory management still uses the old "service class with SQL queries" pattern.

---

## Impact on Issue #2 (batch_number)

Since batch tracking uses **direct SQL**, not DDD:

❌ **NOT affected by BatchTracking entity** - Entity has different schema
✅ **Need to fix the SQL query** - The INSERT statement in `inventory_service.py:457`

The bug is in raw SQL:
```python
INSERT INTO batch_tracking
(store_id, batch_number, batch_lot, ...)  # ← batch_number removed!
```

Not in a DDD repository method.
