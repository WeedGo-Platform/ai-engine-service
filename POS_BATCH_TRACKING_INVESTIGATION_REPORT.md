# POS Batch Tracking Investigation Report - Critical Issues Found

**Date:** 2025-10-18
**Status:** 🔴 TWO CRITICAL ISSUES IDENTIFIED
**Test Case:** SKU 310102_2G___ - POS sale after ASN/PO import

---

## Executive Summary

After implementing the POS inventory fix and testing with sanitized database + 2 ASN/PO imports, **batch tracking is still not working**. Investigation reveals **TWO separate root causes**:

1. **Frontend Issue**: POS UI not sending batch data in transaction payload
2. **Backend Issue**: ASN/PO receiving logic aggregating batches into single unbatched inventory record

---

## Test Scenario

### User Actions:
1. ✅ Sanitized database
2. ✅ Imported 2 ASN/PO documents
3. ✅ Used POS to make sale for SKU `310102_2G___`
4. ❌ Inventory/batch tracking NOT updated

### Expected Result:
- Batch-specific inventory record should be created during PO import
- POS sale should send batch information
- Backend should deduct from specific batch
- Transaction log should record batch_lot

### Actual Result:
- ❌ No batch-specific inventory records created
- ❌ POS transaction missing batch field
- ❌ No inventory deduction occurred
- ❌ No sale transaction logged

---

## Issue #1: Frontend Not Sending Batch Data

### Evidence

**Order Created Successfully:**
```sql
SELECT id, order_number, items::text
FROM orders
WHERE order_source = 'pos'
ORDER BY created_at DESC
LIMIT 1;
```

**Result:**
```
id: 233c2bde-5cae-4bb9-a969-6bed1b93d549
order_number: R1760820127011
items: [
  {
    "product": {
      "id": "310102_2g___",
      "sku": "310102_2G___",
      "name": "Hybrid 3.5g",
      "price": 35,
      "category": "Cannabis"
    },
    "quantity": 1,
    "discount": 0
    // ❌ NO "batch" field present!
  }
]
```

### Analysis

**Missing Field:**
```json
{
  "product": {...},
  "quantity": 1,
  "discount": 0
  // ❌ Should have: "batch": { "batch_lot": "FP-25AL-002", ... }
}
```

**Backend Ready to Accept:**
The backend `pos_transaction_endpoints.py` was updated with:
```python
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    batch: Optional[BatchInfo] = None  # ✅ Backend ready
```

**But Frontend Not Sending:**
- Frontend file: `src/Frontend/ai-admin-dashboard/src/pages/POS.tsx`
- API call in: `src/Frontend/ai-admin-dashboard/src/services/posService.ts`
- Currently sends: `{ product, quantity, discount }`
- Missing: `batch` field with batch_lot information

### Root Cause #1

**POS Frontend does not include batch information in transaction payload.**

The POS UI needs to:
1. Capture batch_lot when product is scanned/selected
2. Include batch data in cart item structure
3. Send batch field in API request to `/api/pos/transactions`

---

## Issue #2: ASN/PO Import Not Creating Batch Records

### Evidence

**Purchase Transactions Logged Correctly:**
```sql
SELECT sku, batch_lot, quantity, transaction_type, created_at
FROM ocs_inventory_transactions
WHERE sku = '310102_2G___'
ORDER BY created_at DESC
LIMIT 5;
```

**Result:**
```
sku          | batch_lot    | quantity | type     | created_at
-------------|--------------|----------|----------|-------------------
310102_2G___ | FP-25AL-002  | 12       | purchase | 2025-10-18 ...
310102_2G___ | FP-25JN-001  | 12       | purchase | 2025-10-18 ...
310102_2G___ | FP-24OC-003  | 24       | purchase | 2025-10-18 ...
```

✅ **Transaction log correctly shows 3 separate batches received**

**BUT Inventory Table Shows:**
```sql
SELECT id, sku, batch_lot, quantity_on_hand, quantity_available
FROM ocs_inventory
WHERE sku = '310102_2G___';
```

**Result:**
```
id                                   | sku          | batch_lot | qty_on_hand | qty_available
-------------------------------------|--------------|-----------|-------------|---------------
dbd36ea0-3c37-4b45-a3a3-b4c9d05f926f | 310102_2G___ | NULL      | 24          | 24
```

❌ **Only ONE inventory record exists with batch_lot = NULL**

### Analysis

**Expected Inventory Records:**
```sql
-- Should have 3 separate records:
('310102_2G___', 'FP-25AL-002', 12, 12)
('310102_2G___', 'FP-25JN-001', 12, 12)
('310102_2G___', 'FP-24OC-003', 24, 24)
```

**Actual Inventory Record:**
```sql
-- But only has 1 aggregated record:
('310102_2G___', NULL, 24, 24)  -- Sum of only one batch!
```

**Data Mismatch:**
- Transaction log: 3 batches totaling 48 units (12+12+24)
- Inventory record: 1 unbatched entry with 24 units (only last batch?)

### Root Cause #2

**ASN/PO receiving logic is NOT creating separate inventory records per batch.**

Instead of creating:
```sql
INSERT INTO ocs_inventory (store_id, sku, batch_lot, quantity_on_hand, quantity_available)
VALUES
  ($1, '310102_2G___', 'FP-25AL-002', 12, 12),
  ($1, '310102_2G___', 'FP-25JN-001', 12, 12),
  ($1, '310102_2G___', 'FP-24OC-003', 24, 24);
```

It's doing:
```sql
-- Either aggregating or overwriting:
INSERT INTO ocs_inventory (store_id, sku, batch_lot, quantity_on_hand, quantity_available)
VALUES ($1, '310102_2G___', NULL, 24, 24);
-- batch_lot is NULL and quantity is only 24 (missing 24 units!)
```

---

## Files Requiring Investigation

### Frontend (Issue #1):

1. **`src/Frontend/ai-admin-dashboard/src/pages/POS.tsx`**
   - Product selection/scanning logic
   - Cart state management
   - Need to capture and store batch_lot with each cart item

2. **`src/Frontend/ai-admin-dashboard/src/services/posService.ts`**
   - API call to POST `/api/pos/transactions`
   - Payload structure
   - Need to include `batch` field in items array

### Backend (Issue #2):

1. **`src/Backend/api/inventory_endpoints.py`**
   - ASN/PO receiving endpoints
   - Inventory record creation logic

2. **`src/Backend/services/inventory_service.py`**
   - Business logic for inventory updates
   - Batch record creation

3. **`src/Backend/api/store_endpoints.py`**
   - Store-specific inventory operations

4. **Purchase Order Domain Logic:**
   - `src/Backend/ddd_refactored/application/services/purchase_order_service.py`
   - `src/Backend/ddd_refactored/domain/purchase_order/entities/purchase_order.py`
   - `src/Backend/ddd_refactored/domain/purchase_order/repositories/`

---

## Database Verification Queries

### Check All Inventory Records for SKU:
```sql
SELECT
    id,
    sku,
    batch_lot,
    quantity_on_hand,
    quantity_available,
    quantity_reserved,
    case_gtin,
    each_gtin,
    packaged_on_date,
    location_code,
    created_at,
    updated_at
FROM ocs_inventory
WHERE sku = '310102_2G___'
ORDER BY created_at;
```

**Current Output:**
```
Only 1 record with batch_lot = NULL, quantity = 24
```

**Expected Output:**
```
3 records with distinct batch_lot values and correct quantities
```

### Check All Transaction Logs:
```sql
SELECT
    sku,
    batch_lot,
    transaction_type,
    quantity,
    reference_id,
    reference_type,
    notes,
    created_at
FROM ocs_inventory_transactions
WHERE sku = '310102_2G___'
ORDER BY created_at;
```

**Current Output:**
```
3 purchase transactions with correct batch_lot values
0 sale transactions
```

**Expected After Fix:**
```
3 purchase transactions (existing)
1 sale transaction with batch_lot from POS
```

---

## Impact Analysis

### Current System Behavior:

1. **ASN/PO Import:**
   - ✅ Logs batch data to `ocs_inventory_transactions`
   - ❌ Creates single unbatched inventory record
   - ❌ Loses batch-level tracking
   - ❌ Possible quantity mismatch (only 24 units vs 48 received)

2. **POS Sale:**
   - ✅ Creates order record
   - ✅ Processes payment
   - ❌ No batch data sent from frontend
   - ❌ No inventory deduction occurs (validation fails due to missing batch)
   - ❌ No sale transaction logged

### Business Impact:

- **Inventory Accuracy:** Lost units (48 received but only 24 tracked)
- **Batch Traceability:** Cannot track products by batch/lot
- **Compliance Risk:** Health Canada requires batch-level tracking
- **Recall Capability:** Cannot identify products from specific batches
- **FIFO/FEFO:** Cannot implement proper rotation strategy
- **Expiry Management:** No packaged_on_date tracking per batch

---

## Recommended Investigation Steps

### For Issue #1 (Frontend):

1. **Examine Product Selection Logic:**
   ```bash
   # Search for where products are added to cart
   grep -n "addToCart\|handleScan" src/Frontend/ai-admin-dashboard/src/pages/POS.tsx
   ```

2. **Check Barcode Scanning:**
   - Does GS1-128 barcode parsing extract batch_lot?
   - Is batch data available in product object?

3. **Review Cart State:**
   - What structure is used for cart items?
   - Is there a batch field in cart item state?

4. **Inspect API Payload:**
   - Check `posService.ts` `createTransaction` method
   - Verify payload structure sent to backend

### For Issue #2 (Backend):

1. **Find ASN/PO Receiving Endpoint:**
   ```bash
   grep -rn "def.*receive.*asn\|def.*import.*asn" src/Backend/api/
   ```

2. **Trace Inventory Creation:**
   ```bash
   grep -rn "INSERT INTO ocs_inventory" src/Backend/
   ```

3. **Check Batch Handling:**
   ```bash
   grep -rn "batch_lot" src/Backend/services/inventory_service.py
   ```

4. **Review Purchase Order Processing:**
   - How are ASN line items processed?
   - Where is inventory record created?
   - Why is batch_lot not being set?

---

## Test Data Summary

### Store:
```
store_id: 5071d685-00dc-4e56-bb11-36e31b305c50
```

### Product:
```
sku: 310102_2G___
name: Hybrid 3.5g
price: 35
category: Cannabis
```

### Batches Received:
```
1. FP-25AL-002 - 12 units
2. FP-25JN-001 - 12 units
3. FP-24OC-003 - 24 units
Total: 48 units
```

### Current Inventory:
```
batch_lot: NULL
quantity_on_hand: 24
quantity_available: 24
Missing: 24 units (50% of received inventory!)
```

### POS Order:
```
order_id: 233c2bde-5cae-4bb9-a969-6bed1b93d549
order_number: R1760820127011
items[0].quantity: 1
items[0].batch: undefined (missing)
```

---

## Critical Questions

1. **Why are only 24 units in inventory when 48 were received?**
   - Is the receiving logic overwriting instead of creating new records?
   - Is there a UNIQUE constraint conflict forcing updates instead of inserts?

2. **Where is batch_lot being lost?**
   - Is it present in ASN import data?
   - Is it extracted from purchase order line items?
   - Is it intentionally being set to NULL?

3. **Why did the POS transaction succeed without batch data?**
   - Backend should have failed validation (strict mode)
   - Did validation pass because batch_lot = NULL matched inventory record?

4. **Is the schema constraint correct?**
   ```sql
   UNIQUE (store_id, sku, batch_lot)
   ```
   - Does this allow multiple NULL batch_lot values?
   - PostgreSQL treats NULL values as distinct in UNIQUE constraints

---

## Next Steps (Investigation Only)

### Priority 1: Fix ASN/PO Import (Issue #2)

**Why First:** This is blocking proper inventory records from being created

**Tasks:**
1. Read ASN/PO receiving endpoints
2. Identify where inventory records are created
3. Understand why batch_lot is NULL
4. Determine why only 24 units instead of 48

### Priority 2: Fix POS Frontend (Issue #1)

**Why Second:** Even if batches exist, POS won't use them without this fix

**Tasks:**
1. Read POS.tsx cart logic
2. Check barcode scanning implementation
3. Review posService.ts payload
4. Identify where to add batch field

---

## Status

**Investigation Complete:** ✅
**Root Causes Identified:** 2
**Files to Review:** 7
**Database Evidence:** Documented
**Ready for Fix:** ❌ (Awaiting user decision)

---

## Files Modified (None Yet)

This is a **REPORT ONLY** investigation as requested. No code changes have been made.

---

**End of Report**
