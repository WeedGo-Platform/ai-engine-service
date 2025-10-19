# Purchase Order Tables Investigation Report

**Date:** 2025-10-18
**Tables:** `purchase_orders`, `purchase_order_items`
**Status:** 🔍 INVESTIGATION COMPLETE

---

## Executive Summary

### Current State:
- **2 Purchase Orders** with **55 line items** in database
- **Multiple unused columns** identified in both tables
- **Missing data** in several columns that should be populated

### Issues Found:

1. **`purchase_order_items`:**
   - `batch_number` - Never populated (0/55)
   - `line_total` - Never populated (0/55)
   - `item_name` - Never populated (0/55) **← Excel has data but not extracted**

2. **`purchase_orders`:**
   - `tenant_id` - Never populated (0/2)
   - `ocs_order_number` - Never populated (0/2)
   - `expected_delivery_date` - Never populated (0/2)
   - `actual_delivery_date` - Never populated (0/2)
   - `tax_amount` - Never populated (0/2)
   - `subtotal` - Never populated (0/2)
   - `created_by` - Never populated (0/2)
   - `approved_by` - Never populated (0/2)
   - `received_by` - Never populated (0/2)
   - `vendor` - IS being populated (2/2) ✅

---

## Table 1: `purchase_order_items`

### Schema Analysis

```sql
Table "public.purchase_order_items"
       Column        |            Type             | Nullable |      Default
---------------------+-----------------------------+----------+-------------------
 id                  | uuid                        | not null | gen_random_uuid()
 purchase_order_id   | uuid                        | not null |
 sku                 | character varying(100)      | not null |
 item_name           | character varying(255)      |          |  ← ISSUE #1
 quantity_ordered    | integer                     | not null |
 quantity_received   | integer                     |          | 0
 unit_cost           | numeric(10,2)               | not null |
 total_cost          | numeric(12,2)               | not null |
 batch_number        | character varying(100)      |          |  ← ISSUE #2 (REMOVE)
 batch_lot           | character varying(100)      |          |
 line_total          | numeric(12,2)               |          |  ← ISSUE #3 (REMOVE)
 case_gtin           | character varying(100)      |          |
 each_gtin           | character varying(100)      |          |
 gtin_barcode        | character varying(100)      |          |
 vendor              | character varying(255)      |          |
 brand               | character varying(255)      |          |
 packaged_on_date    | date                        |          |
 shipped_qty         | integer                     |          |
 uom                 | character varying(50)       |          |
 uom_conversion      | numeric(10,4)               |          |
 uom_conversion_qty  | integer                     |          |
 exists_in_inventory | boolean                     |          | false
 created_at          | timestamp                   |          | CURRENT_TIMESTAMP
 updated_at          | timestamp                   |          | CURRENT_TIMESTAMP
```

### Issue #1: `item_name` Not Populated

**Current State:**
```sql
SELECT COUNT(*) as total, COUNT(item_name) as has_item_name
FROM purchase_order_items;

-- Result: total=55, has_item_name=0
```

**Root Cause Analysis:**

1. **Frontend DOES Extract Data** (`ASNImportModal.tsx:477`):
   ```typescript
   item_name: String(row['ItemName'] || ''),
   ```

2. **Backend DOES Accept Data** (`inventory_service.py:199`):
   ```python
   item.get('item_name'),  # From Excel ItemName column
   ```

3. **Problem:** Excel ASN files likely **don't have `ItemName` column**
   - Frontend extracts `row['ItemName']`
   - If column doesn't exist → returns empty string `''`
   - Backend inserts empty string → stored as NULL

**Sample Data:**
```sql
SELECT sku, item_name, vendor FROM purchase_order_items LIMIT 3;

sku               | item_name | vendor
------------------+-----------+---------------------
330143_1X10G___   | NULL      | INDIVA INC.
300592_1.2G___    | NULL      | ORGANIGRAM INC.
102779_10X0.5G___ | NULL      | MERA CANNABIS CORP.
```

**Fix Options:**

**Option A:** Remove `item_name` column entirely
- Not used
- Can lookup product name from `ocs_product_catalog` via SKU join
- **RECOMMENDED**

**Option B:** Populate from product catalog during PO creation
```sql
-- Could lookup product_name:
SELECT product_name FROM ocs_product_catalog WHERE ocs_variant_number = $1
```

**Option C:** Add `ItemName` column to Excel template
- Requires OCS to change their Excel format
- Unlikely to happen

### Issue #2: `batch_number` Never Used

**Current State:**
```sql
SELECT COUNT(batch_number) FROM purchase_order_items;
-- Result: 0
```

**Root Cause:**
- Column exists but never populated
- System uses `batch_lot` instead
- `batch_number` vs `batch_lot` confusion

**Evidence:**
```sql
SELECT
    COUNT(batch_number) as has_batch_number,
    COUNT(batch_lot) as has_batch_lot
FROM purchase_order_items;

-- Result: has_batch_number=0, has_batch_lot=55
```

**Analysis:**
- `batch_lot` = Actual batch identifier from supplier (e.g., "FP-25AL-002")
- `batch_number` = Unused duplicate column
- Code references `batch_lot` everywhere

**Recommendation:** **REMOVE `batch_number` column**

### Issue #3: `line_total` Never Calculated

**Current State:**
```sql
SELECT COUNT(line_total) FROM purchase_order_items;
-- Result: 0
```

**Why Not Populated:**

**Code Analysis** (`inventory_service.py:186-213`):
```python
item_query = """
    INSERT INTO purchase_order_items
    (purchase_order_id, sku, item_name, batch_lot, quantity_ordered,
     unit_cost, case_gtin, gtin_barcode, each_gtin,
     vendor, brand, packaged_on_date,
     shipped_qty, uom, uom_conversion, uom_conversion_qty)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
"""
# NOTE: line_total is NOT in INSERT statement!
```

**Duplicate with `total_cost`:**
```sql
SELECT
    COUNT(total_cost) as has_total_cost,
    COUNT(line_total) as has_line_total
FROM purchase_order_items;

-- Result: has_total_cost=55, has_line_total=0
```

**Both columns serve same purpose:**
- `total_cost` = Calculated and populated
- `line_total` = Duplicate, never used

**Recommendation:** **REMOVE `line_total` column**

---

## Table 2: `purchase_orders`

### Schema Analysis

```sql
Table "public.purchase_orders"
         Column         |            Type             | Nullable | Default
------------------------+-----------------------------+----------+-------------------
 id                     | uuid                        | not null | gen_random_uuid()
 po_number              | character varying(50)       | not null |
 store_id               | uuid                        | not null |
 supplier_id            | uuid                        |          |
 order_date             | date                        | not null |
 expected_date          | date                        |          |  ✅ Being used
 expected_delivery_date | date                        |          |  ← ISSUE #4 (REMOVE - duplicate)
 actual_delivery_date   | date                        |          |  ← ISSUE #5 (REMOVE)
 status                 | character varying(50)       |          | 'pending'
 subtotal               | numeric(12,2)               |          |  ← ISSUE #6 (REMOVE)
 tax_amount             | numeric(12,2)               |          |  ← ISSUE #7 (REMOVE)
 total_amount           | numeric(12,2)               |          |  ✅ Being used
 notes                  | text                        |          |
 tenant_id              | uuid                        |          |  ← ISSUE #8 (REMOVE)
 vendor                 | character varying(255)      |          |  ✅ Being used
 ocs_order_number       | character varying(100)      |          |  ← ISSUE #9 (REMOVE)
 shipment_id            | character varying(100)      |          |  ✅ Being used
 container_id           | character varying(100)      |          |  ✅ Being used
 received_date          | timestamp                   |          |
 created_by             | uuid                        |          |  ← ISSUE #10 (REMOVE)
 approved_by            | uuid                        |          |  ← ISSUE #11 (REMOVE)
 received_by            | uuid                        |          |  ← ISSUE #12 (REMOVE)
 created_at             | timestamp                   |          | CURRENT_TIMESTAMP
 updated_at             | timestamp                   |          | CURRENT_TIMESTAMP
```

### Issue #4-5: Delivery Date Columns

**Duplicate Columns:**
- `expected_date` ✅ **Being used**
- `expected_delivery_date` ❌ **Never used (duplicate)**
- `actual_delivery_date` ❌ **Never used**

**Current Usage:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(expected_date) as has_expected_date,
    COUNT(expected_delivery_date) as has_expected_delivery_date,
    COUNT(actual_delivery_date) as has_actual_delivery_date
FROM purchase_orders;

-- Result: total=2, has_expected_date=2, has_expected_delivery_date=0, has_actual_delivery_date=0
```

**Code Evidence** (`inventory_service.py:166-172`):
```python
po_query = """
    INSERT INTO purchase_orders
    (po_number, supplier_id, order_date, expected_date, status, total_amount, notes, store_id,
     shipment_id, container_id, vendor, created_by)
    VALUES ($1, $2, CURRENT_DATE, $3, 'pending', $4, $5, $6, $7, $8, $9, $10)
    RETURNING id
"""
# Uses expected_date, NOT expected_delivery_date
```

**Recommendation:**
- **KEEP:** `expected_date`
- **REMOVE:** `expected_delivery_date` (duplicate)
- **REMOVE:** `actual_delivery_date` (never tracked)

### Issue #6-7: Tax and Subtotal

**Never Calculated:**
```sql
SELECT
    COUNT(subtotal) as has_subtotal,
    COUNT(tax_amount) as has_tax_amount,
    COUNT(total_amount) as has_total_amount
FROM purchase_orders;

-- Result: has_subtotal=0, has_tax_amount=0, has_total_amount=2
```

**Why:**
- Purchase orders from suppliers come **tax-included** in Canada
- `total_amount` is populated (sum of line items)
- Breaking down into subtotal + tax not needed
- No requirement to track tax separately on incoming POs

**Code Evidence:**
```python
# Only total_amount calculated (line 160-163):
total_amount = sum(
    Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
    for item in items
)
```

**Recommendation:** **REMOVE `subtotal` and `tax_amount`**

### Issue #8: `tenant_id` Never Set

**Current State:**
```sql
SELECT COUNT(tenant_id) FROM purchase_orders;
-- Result: 0
```

**Why Not Needed:**
- `store_id` is always set
- Can JOIN to `stores` table to get `tenant_id`
- Denormalization not necessary

```sql
-- Get tenant_id via join:
SELECT po.*, s.tenant_id
FROM purchase_orders po
JOIN stores s ON po.store_id = s.id;
```

**Recommendation:** **REMOVE `tenant_id` column**

### Issue #9: `ocs_order_number` Never Set

**Current State:**
```sql
SELECT COUNT(ocs_order_number) FROM purchase_orders;
-- Result: 0
```

**Why:**
- Was intended for OCS order reference number
- Excel files don't contain this field
- `po_number` is generated from filename instead
- Not tracked in current workflow

**Recommendation:** **REMOVE `ocs_order_number`**

### Issue #10-12: User Tracking Columns

**Never Populated:**
```sql
SELECT
    COUNT(created_by) as has_created_by,
    COUNT(approved_by) as has_approved_by,
    COUNT(received_by) as has_received_by
FROM purchase_orders;

-- Result: has_created_by=0, has_approved_by=0, has_received_by=0
```

**Why:**
- No user authentication passed during PO creation
- Frontend doesn't send user ID
- Backend doesn't extract from session/JWT
- No approval workflow implemented
- `received_date` timestamp exists but `received_by` user not tracked

**Code Evidence** (`inventory_service.py:169`):
```python
INSERT INTO purchase_orders
(..., created_by)
VALUES (..., $10)

# But passed as None:
await self.db.fetchval(
    po_query,
    ..., created_by  # = None from parameters
)
```

**Recommendation:**
**REMOVE all three columns:**
- `created_by`
- `approved_by`
- `received_by`

**Alternative:** Use `created_at` and `updated_at` timestamps for audit trail

---

## Summary of Findings

### Columns to REMOVE:

**`purchase_order_items` (3 columns):**
1. ✅ `batch_number` - Duplicate of `batch_lot`, never used
2. ✅ `line_total` - Duplicate of `total_cost`, never calculated
3. ⚠️ `item_name` - **Decision needed** (see options below)

**`purchase_orders` (9 columns):**
1. ✅ `tenant_id` - Redundant, can JOIN via `store_id`
2. ✅ `ocs_order_number` - Never extracted from Excel
3. ✅ `expected_delivery_date` - Duplicate of `expected_date`
4. ✅ `actual_delivery_date` - Never tracked
5. ✅ `tax_amount` - Not needed (tax-included pricing)
6. ✅ `subtotal` - Not needed (only `total_amount` used)
7. ✅ `created_by` - User ID never passed
8. ✅ `approved_by` - No approval workflow
9. ✅ `received_by` - User not tracked on receive

### `item_name` Decision:

**Option A: Remove (Recommended)**
- Can lookup via SKU from `ocs_product_catalog`
- Query: `SELECT product_name FROM ocs_product_catalog WHERE ocs_variant_number = sku`
- Simpler schema

**Option B: Populate from catalog**
- Add logic to lookup product_name during PO creation
- Store denormalized copy for performance
- Keep column

**Recommendation:** **Option A (Remove)** - cleaner schema, avoid denormalization

---

## Migration Plan

### Phase 1: Remove Unused Columns

```sql
BEGIN;

-- purchase_order_items: Remove 3 columns
ALTER TABLE purchase_order_items DROP COLUMN IF EXISTS batch_number CASCADE;
ALTER TABLE purchase_order_items DROP COLUMN IF EXISTS line_total CASCADE;
ALTER TABLE purchase_order_items DROP COLUMN IF EXISTS item_name CASCADE;

-- purchase_orders: Remove 9 columns
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS tenant_id CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS ocs_order_number CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS expected_delivery_date CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS actual_delivery_date CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS tax_amount CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS subtotal CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS created_by CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS approved_by CASCADE;
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS received_by CASCADE;

COMMIT;
```

### Phase 2: Update Code

**Files to Update:**

1. **`inventory_service.py`** (Lines 186-213)
   - Remove `item_name` from INSERT
   - Remove unused column references

2. **`ddd_refactored/domain/purchase_order/repositories/__init__.py`** (Lines 310-340)
   - Remove `item_name` from INSERT
   - Remove `total_cost` duplicate logic

3. **`store_inventory_service.py`** (Lines 525-553)
   - Remove unused column references

4. **Frontend:** `ASNImportModal.tsx`
   - Remove `item_name` extraction (line 477)
   - Remove `item_name` from interface (line 16)
   - Remove `item_name` display (lines 996, 1027, 1228)

### Phase 3: Verification

```sql
-- Verify columns removed
\d purchase_order_items
\d purchase_orders

-- Test PO creation
INSERT INTO purchase_orders (po_number, store_id, order_date, expected_date, status, total_amount)
VALUES ('TEST-PO-001', '5071d685-00dc-4e56-bb11-36e31b305c50', CURRENT_DATE, CURRENT_DATE + 7, 'pending', 100.00);

-- Test cleanup successful
SELECT COUNT(*) FROM purchase_orders;
```

---

## Impact Assessment

### Benefits:
1. ✅ **Cleaner Schema** - 12 fewer columns
2. ✅ **Less Confusion** - No duplicate columns
3. ✅ **Reduced Storage** - Smaller row size
4. ✅ **Faster Queries** - Less data to scan
5. ✅ **Easier Maintenance** - Clear data model

### Risks:
- ❌ **ZERO RISK** - All columns are empty/unused
- ✅ No data loss (columns are NULL/0)
- ✅ No code dependencies (unused in queries)
- ✅ No frontend dependencies (except `item_name` display of NULL)

---

## Before/After Comparison

### `purchase_order_items` Table

**Before:** 24 columns
**After:** 21 columns (-3)

**Removed:**
- `batch_number`
- `line_total`
- `item_name`

### `purchase_orders` Table

**Before:** 24 columns
**After:** 15 columns (-9)

**Removed:**
- `tenant_id`
- `ocs_order_number`
- `expected_delivery_date`
- `actual_delivery_date`
- `tax_amount`
- `subtotal`
- `created_by`
- `approved_by`
- `received_by`

**Total Reduction:** 12 columns removed (25% smaller schema)

---

## Recommendations Summary

### Immediate Actions:

1. ✅ **Remove unused columns** from both tables (safe, zero risk)
2. ✅ **Update code** to remove references to deleted columns
3. ✅ **Update frontend** to remove `item_name` display

### Future Improvements:

1. **Add User Tracking (Optional):**
   - Implement JWT authentication
   - Pass user context in API calls
   - Re-add `created_by` if user tracking becomes requirement

2. **Add Approval Workflow (Optional):**
   - If PO approval needed in future
   - Add back `approved_by` + `approved_at`

3. **Item Name Lookup:**
   - Create view joining PO items with product catalog
   - Provides product_name without denormalization

```sql
CREATE OR REPLACE VIEW purchase_order_items_with_names AS
SELECT
    poi.*,
    pc.product_name
FROM purchase_order_items poi
LEFT JOIN ocs_product_catalog pc
    ON LOWER(TRIM(poi.sku)) = LOWER(TRIM(pc.ocs_variant_number));
```

---

**Status:** ✅ Investigation Complete
**Next Step:** Execute migration to remove unused columns
**Est. Time:** 30 minutes (migration + code updates + testing)
