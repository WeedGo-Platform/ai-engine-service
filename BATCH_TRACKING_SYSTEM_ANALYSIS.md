# Batch Tracking System - Complete Analysis

**Date:** 2025-10-18
**Status:** ✅ COMPREHENSIVE INVESTIGATION COMPLETE

---

## Executive Summary

The `batch_tracking` table is a **critical component** of the inventory management system, serving as the bridge between:
- Purchase Order receiving
- Inventory stock levels
- POS sales (FIFO consumption)
- Shelf location management

**Primary Purpose:** Track individual product batches with unique identifiers (`batch_lot`) from supplier receipt through to sale, maintaining quantity remaining and GTIN barcodes for regulatory compliance.

---

## Table Schema (After Cleanup)

```sql
Table "public.batch_tracking"
       Column       |            Type             |   Purpose
--------------------+-----------------------------+------------------------------------------
 id                 | uuid                        | Primary key
 store_id           | uuid                        | Which store owns this batch
 received_date      | date                        | When batch was received
 quantity_received  | integer                     | Original quantity received
 quantity_remaining | integer                     | Current quantity available (decremented on sales)
 status             | varchar(50)                 | Batch status (default: 'active')
 notes              | text                        | Optional notes
 created_at         | timestamp                   | Record creation time
 updated_at         | timestamp                   | Last modification time
 is_active          | boolean                     | Active status (false when depleted)
 purchase_order_id  | uuid                        | Link to PO that received this batch
 gtin_barcode       | varchar(100)                | GTIN barcode for scanning
 batch_lot          | varchar(100)                | Unique batch identifier (PRIMARY BUSINESS KEY)
 unit_cost          | numeric(10,2)               | Unit cost (weighted average on merge)
 each_gtin          | varchar(100)                | GTIN for individual units
 location_id        | uuid                        | Shelf location where batch is stored
 sku                | varchar(100)                | Product SKU
 case_gtin          | varchar(100)                | GTIN for case-level barcode
 packaged_on_date   | date                        | When product was packaged by supplier
```

**Unique Constraint:** `batch_lot` must be unique across the system
**Unique Constraint:** `(store_id, batch_lot, sku)` combination must be unique (REMOVED during cleanup)

**Key Indexes:**
- `batch_tracking_batch_lot_key` - UNIQUE index on batch_lot
- `idx_batch_lot` - Performance index for batch_lot lookups
- `idx_batch_sku` - Index for SKU searches
- `idx_batch_tracking_gtin_barcode` - GTIN barcode scanning
- `idx_batch_tracking_location` - Location-based queries
- `idx_batch_tracking_store_sku_new` - Store+SKU composite index

---

## Complete Data Flow

### 1️⃣ **ASN Import & Purchase Order Creation**

**Frontend:** `ASNImportModal.tsx`

```typescript
// Extract batch_lot from Excel (Line 483)
batch_lot: batchLot  // Format: "Batch1", "Batch2", etc.

// Map to PO items (Line 580)
{
  sku: item.sku,
  batch_lot: item.batch_lot,
  quantity_ordered: item.shipped_qty,
  unit_cost: item.unit_price,
  case_gtin: item.case_gtin,
  packaged_on_date: item.packaged_on_date,
  gtin_barcode: item.gtin_barcode,
  each_gtin: item.each_gtin
}
```

**Backend:** `purchase_order_service.py`

- Creates PurchaseOrder aggregate
- Saves line items to `purchase_order_items` table with `batch_lot`
- **Does NOT create batch_tracking records yet** (happens during receiving)

**Files Involved:**
- `src/Frontend/ai-admin-dashboard/src/components/ASNImportModal.tsx:480-485`
- `src/Backend/ddd_refactored/application/services/purchase_order_service.py:35-147`
- `src/Backend/ddd_refactored/domain/purchase_order/repositories/__init__.py:299-358`

---

### 2️⃣ **Purchase Order Receiving (Batch Creation)**

**Endpoint:** `POST /api/inventory/purchase-orders/{po_id}/receive`

**File:** `inventory_endpoints.py:228-253`

```python
async def receive_purchase_order(
    po_id: UUID,
    request: ReceivePurchaseOrderRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    success = await service.receive_purchase_order(
        po_id,
        [item.dict() for item in request.items],
        received_by=user_id
    )
```

**Service:** `inventory_service.py:273-488`

```python
async def receive_purchase_order(self, po_id: UUID,
                                 received_items: List[Dict[str, Any]],
                                 received_by: Optional[UUID] = None) -> bool:
    # For each received item:

    # 1. Update ocs_inventory quantity
    UPDATE ocs_inventory
    SET quantity_on_hand = quantity_on_hand + $quantity_received

    # 2. Log transaction
    INSERT INTO ocs_inventory_transactions (...)

    # 3. CREATE OR UPDATE batch_tracking record
    INSERT INTO batch_tracking
    (store_id, batch_number, batch_lot, sku, purchase_order_id,
     quantity_received, quantity_remaining, unit_cost, received_date,
     case_gtin, packaged_on_date, gtin_barcode, each_gtin)
    VALUES ($1, $2, $3, $4, $5, $6, $6, $7, CURRENT_DATE, $8, $9, $10, $11)
    ON CONFLICT (batch_lot) DO UPDATE
    SET quantity_received = batch_tracking.quantity_received + $6,
        quantity_remaining = batch_tracking.quantity_remaining + $6,
        unit_cost = ((batch_tracking.quantity_remaining * batch_tracking.unit_cost) +
                    ($6 * $7)) / (batch_tracking.quantity_remaining + $6),
        case_gtin = COALESCE(NULLIF($8, ''), batch_tracking.case_gtin),
        packaged_on_date = COALESCE($9, batch_tracking.packaged_on_date),
        gtin_barcode = COALESCE(NULLIF($10, ''), batch_tracking.gtin_barcode),
        each_gtin = COALESCE(NULLIF($11, ''), batch_tracking.each_gtin)
```

**Key Behavior:**
- ✅ **UPSERT logic**: If batch_lot already exists, adds quantities together
- ✅ **Weighted average cost**: Recalculates unit_cost when merging batches
- ✅ **GTIN preservation**: Only overwrites NULL/empty GTINs with new values
- ✅ **Initial values**: `quantity_received = quantity_remaining` on first insert

**Files:** `src/Backend/services/inventory_service.py:454-486`

---

### 3️⃣ **POS Sales (FIFO Batch Consumption)**

**Service:** `store_inventory_service.py:update_store_inventory()`

**File:** `src/Backend/services/store_inventory_service.py:423-453`

```python
# When transaction_type == SALE:
# Get active batches ordered by created_at (FIFO)
active_batches = await conn.fetch("""
    SELECT id, batch_lot, quantity_remaining
    FROM batch_tracking
    WHERE store_id = $1 AND sku = $2 AND is_active = true
          AND quantity_remaining > 0
    ORDER BY created_at ASC  -- OLDEST FIRST
""", store_id, sku)

# Consume batches in FIFO order
for batch in active_batches:
    if quantity_to_reduce <= 0:
        break

    batch_reduction = min(batch['quantity_remaining'], quantity_to_reduce)
    new_remaining = batch['quantity_remaining'] - batch_reduction

    # Update batch quantity
    UPDATE batch_tracking
    SET quantity_remaining = $3,
        is_active = CASE WHEN $3 = 0 THEN false ELSE true END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = $1 AND store_id = $2

    quantity_to_reduce -= batch_reduction
```

**Behavior:**
- ✅ **FIFO (First In, First Out)**: Oldest batches sold first
- ✅ **Auto-deactivation**: Sets `is_active = false` when `quantity_remaining = 0`
- ✅ **Partial consumption**: Can consume across multiple batches in one sale
- ✅ **No negative quantities**: WHERE clause ensures quantity_remaining >= 0

**Critical for:**
- Regulatory compliance (oldest product sold first)
- Expiry management (although `expiry_date` column was removed)
- Accurate COGS calculation (using unit_cost from specific batches)

---

### 4️⃣ **Shelf Location Management**

**Service:** `shelf_location_service.py`

**File:** `src/Backend/services/shelf_location_service.py:222-230, 294-300`

```python
# When assigning product to shelf location
async def assign_product_to_location(...):
    # Update batch_tracking with location
    UPDATE batch_tracking
    SET location_id = $2
    WHERE batch_lot = $1

# When transferring between locations
async def transfer_product_between_locations(...):
    # Update batch_tracking to new location
    UPDATE batch_tracking
    SET location_id = $2
    WHERE batch_lot = $1
```

**Purpose:**
- Track physical location of each batch in warehouse
- Enable efficient picking/fulfillment
- Support inventory audits

**Files:**
- `src/Backend/services/shelf_location_service.py:217-232` (assign)
- `src/Backend/services/shelf_location_service.py:288-303` (transfer)

---

### 5️⃣ **Inventory Display & Search**

**Endpoint:** `GET /api/inventory/batch/{batch_lot}`

**File:** `inventory_endpoints.py:362-391`

```python
@router.get("/batch/{batch_lot}")
async def get_batch_details(batch_lot: str, ...):
    SELECT
        bt.*,
        pc.product_name,
        s.name as supplier_name
    FROM batch_tracking bt
    LEFT JOIN product_catalog pc ON bt.sku = pc.sku
    LEFT JOIN provincial_suppliers s ON bt.supplier_id = s.id  -- PROBLEM: supplier_id removed!
    WHERE bt.batch_lot = $1
```

**⚠️ ISSUE DETECTED:** This query references `bt.supplier_id` which was **just removed** in cleanup!

**Inventory Search:** `inventory_service.py:591-600`

```python
SELECT
    ipv.*,
    bt.batch_lot,
    bt.case_gtin,
    bt.gtin_barcode,
    bt.each_gtin,
    bt.quantity_remaining as batch_quantity,
    s.name as supplier_name
FROM inventory_products_view ipv
LEFT JOIN batch_tracking bt ON ipv.sku = bt.sku AND bt.quantity_remaining > 0
LEFT JOIN purchase_orders po ON bt.purchase_order_id = po.id
LEFT JOIN suppliers s ON po.supplier_id = s.id  -- Supplier from PO, not batch
WHERE 1=1
```

**Frontend Display:** `Inventory.tsx:440-503`

- Displays `batch_lot` in expandable rows
- Shows batch details (quantity_remaining, unit_cost, GTINs)
- Allows clicking to expand and see all batches for a SKU

---

### 6️⃣ **Batch Adjustment (Manual Stock Correction)**

**Service:** `store_inventory_service.py:adjust_batch_quantity()`

**File:** `src/Backend/services/store_inventory_service.py:678-686`

```python
async def adjust_batch_quantity(self, batch_lot: str, sku: str,
                                store_id: UUID, adjustment: int):
    UPDATE batch_tracking
    SET quantity_remaining = quantity_remaining + $1,
        updated_at = CURRENT_TIMESTAMP
    WHERE batch_lot = $2 AND sku = $3 AND store_id = $4
          AND quantity_remaining + $1 >= 0  -- Prevent negative
```

**Use Cases:**
- Stock count corrections
- Damaged goods write-offs
- Shrinkage adjustments

---

## 🔗 System Integration Points

### **Purchase Orders → Batch Tracking**
- **Trigger:** Receiving PO items
- **Action:** INSERT batch_tracking records with batch_lot from ASN
- **Link:** `batch_tracking.purchase_order_id` → `purchase_orders.id`

### **Batch Tracking → Inventory Levels**
- **Relationship:** `SUM(quantity_remaining)` should equal `ocs_inventory.quantity_on_hand` for each SKU
- **Maintained By:**
  - `receive_purchase_order()` - increases both
  - SALE transactions - decreases both via FIFO

### **Batch Tracking → Shelf Locations**
- **Link:** `batch_tracking.location_id` → `shelf_locations.id`
- **Updated By:** `assign_product_to_location()`, `transfer_product_between_locations()`

### **Batch Tracking → POS Sales**
- **Consumed By:** FIFO logic in `update_store_inventory()` when `transaction_type = SALE`
- **Effect:** Decrements `quantity_remaining`, sets `is_active = false` when depleted

---

## 📊 Usage Summary by Component

| Component | Usage Type | Files |
|-----------|-----------|-------|
| **ASN Import** | Provides batch_lot | `ASNImportModal.tsx:483` |
| **PO Creation** | Stores batch_lot in line items | `purchase_order_service.py`, `repositories/__init__.py:299-358` |
| **PO Receiving** | **CREATES batch_tracking records** | `inventory_service.py:454-486` |
| **POS Sales** | **CONSUMES batches (FIFO)** | `store_inventory_service.py:423-453` |
| **Shelf Locations** | Updates location_id | `shelf_location_service.py:222-230, 294-300` |
| **Inventory Display** | Shows batch details | `Inventory.tsx:440-503`, `inventory_endpoints.py:362-391` |
| **Stock Adjustments** | Manual quantity changes | `store_inventory_service.py:678-686` |
| **GTIN Population** | Backfill GTIN values | `populate_missing_gtin_values.py:47-102` |

---

## ⚠️ Critical Issues Found

### ✅ Issue #1: FIXED - Removed Supplier Join from Batch Endpoint

**File:** `src/Backend/api/inventory_endpoints.py:377`

**Problem:** Query joined to `provincial_suppliers` using removed `supplier_id` column

**Fix Applied:** Removed supplier join entirely - batch endpoint now only returns batch tracking data

```python
# BEFORE:
SELECT bt.*, pc.product_name, s.name as supplier_name
FROM batch_tracking bt
LEFT JOIN product_catalog pc ON bt.sku = pc.sku
LEFT JOIN provincial_suppliers s ON bt.supplier_id = s.id

# AFTER:
SELECT bt.*, pc.product_name
FROM batch_tracking bt
LEFT JOIN product_catalog pc ON bt.sku = pc.sku
```

**Rationale:** Batch detail endpoint should focus on batch tracking fields only. Supplier information belongs in purchase order queries, not batch queries.

---

### 🚨 Issue #2: Duplicate batch_number Column Reference

**File:** `src/Backend/services/inventory_service.py:457`

```python
INSERT INTO batch_tracking
(store_id, batch_number, batch_lot, sku, ...)
VALUES ($1, $2, $3, $4, ...)
```

**Problem:** Query still inserts into `batch_number` column which was **removed during cleanup**!

**Impact:**
- **PO receiving will FAIL completely**
- Cannot receive any new inventory
- Critical production-breaking bug

**Fix Required:**
```python
# BEFORE:
INSERT INTO batch_tracking
(store_id, batch_number, batch_lot, sku, purchase_order_id, ...)

# AFTER:
INSERT INTO batch_tracking
(store_id, batch_lot, sku, purchase_order_id, ...)
```

Remove `batch_number` from INSERT columns and remove `$2` parameter.

---

## 🎯 Business Logic Patterns

### **FIFO Consumption**
```
Batch 1 (oldest) → Batch 2 → Batch 3 (newest)
Sale of 100 units consumes from Batch 1 first
```

### **Weighted Average Cost**
```
Batch 1: 50 units @ $10 = $500
Batch 2: 50 units @ $12 = $600
Merged: 100 units @ $11 = $1,100
```

### **Batch Lifecycle**
```
1. Created     → quantity_received = 100, quantity_remaining = 100, is_active = true
2. Partial Sale → quantity_received = 100, quantity_remaining = 30,  is_active = true
3. Depleted     → quantity_received = 100, quantity_remaining = 0,   is_active = false
```

---

## 📝 Recommendations

### ✅ **Keep Current Columns:**
- `batch_lot` - Primary business identifier
- `quantity_received` - Audit trail of original quantity
- `quantity_remaining` - Current available stock
- `unit_cost` - COGS calculation
- `packaged_on_date` - Supplier packaging date
- `gtin_barcode`, `case_gtin`, `each_gtin` - Regulatory compliance
- `location_id` - Warehouse management
- `purchase_order_id` - Traceability to source

### 🔧 **Immediate Fixes Needed:**

1. **Fix inventory_endpoints.py:377** - Update supplier join
2. **Fix inventory_service.py:457** - Remove batch_number from INSERT

### 📊 **Future Enhancements:**

1. Add `expiry_date` back if needed for compliance
2. Add `received_by` user tracking for batch receiving
3. Consider `lot_number` for sub-batch tracking if required by suppliers
4. Add batch history/audit log for quantity changes

---

## 🔍 Testing Checklist

After cleanup, verify:

- [ ] ASN import creates PO with batch_lot ✅
- [ ] PO receiving creates batch_tracking records ⚠️ **Will FAIL - needs fix**
- [ ] Batch detail endpoint returns data ⚠️ **Will FAIL - needs fix**
- [ ] POS sale decrements batch quantities via FIFO ✅
- [ ] Inventory page displays batch_lot ✅
- [ ] Shelf location assignment updates batch_tracking ✅
- [ ] Stock adjustments modify quantity_remaining ✅

---

**Status:** Investigation complete. **Critical bugs found** in recently removed columns.
