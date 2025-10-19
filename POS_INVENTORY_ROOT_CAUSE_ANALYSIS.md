# POS Inventory Update Root Cause Analysis

**Date:** 2025-10-18
**Investigator:** Claude AI
**Status:** Investigation Complete - Root Causes Identified

---

## Executive Summary

The POS system is **NOT updating inventory or batch tracking** after sales transactions are completed. This root cause analysis has identified **THREE CRITICAL ISSUES** that prevent proper inventory management:

1. **Wrong Table Target**: Backend code attempts to update non-existent `products` table
2. **Missing Batch Deduction Logic**: No code to deduct quantities from specific batches
3. **Batch Information Not Passed**: Frontend passes batch data but backend ignores it

---

## Investigation Flow

### 1. Frontend Payment Flow (POS.tsx)

**File:** `src/Frontend/ai-admin-dashboard/src/pages/POS.tsx`
**Lines:** 1855-1920

#### What Works ✅
- Cart items properly track batch information when scanned
- Batch data is attached to cart items: `item.batch.batch_lot`
- Payment modal collects payment details correctly
- Transaction data is sent to backend via `posService.createTransaction()`

#### Batch Data Structure in Cart:
```typescript
interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  promotion?: string;
  batch?: Batch;  // ✅ Batch info is captured here
}

interface Batch {
  batch_lot: string;           // e.g., "J24042402"
  quantity_remaining: number;
  case_gtin?: string;
  each_gtin?: string;
  packaged_on_date?: string;
  location_code?: string;
}
```

**Transaction Payload Sent to Backend:**
```javascript
{
  store_id: "5071d685-00dc-4e56-bb11-36e31b305c50",
  cashier_id: "cashier_001",
  customer_id: "...",
  items: [
    {
      product: { id: "105000_28g___", sku: "105000_28g___", ... },
      quantity: 2,
      discount: 0,
      promotion: null,
      batch: {                    // ✅ Batch info is included in payload
        batch_lot: "J24042402",
        quantity_remaining: 50,
        case_gtin: "...",
        ...
      }
    }
  ],
  subtotal: 45.99,
  tax: 5.98,
  total: 51.97,
  payment_method: "cash",
  status: "completed"
}
```

---

### 2. Backend Transaction Processing

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Function:** `create_pos_transaction()`
**Lines:** 74-216

#### What the Backend Does:

1. **Creates Order Record** ✅
   - Inserts transaction into `orders` table
   - Stores payment details
   - Records transaction metadata

2. **Attempts Inventory Update** ❌ **FAILS HERE**
   ```python
   # Lines 195-210
   for item in transaction.items:
       product_id = item.product.get('id')
       if product_id:
           try:
               await conn.execute(
                   """
                   UPDATE products                      # ❌ PROBLEM 1: Wrong table!
                   SET available_quantity = GREATEST(0, available_quantity - $1)
                   WHERE id = $2::uuid
                   """,
                   item.quantity,                      # ❌ PROBLEM 2: No batch specified
                   product_id
               )
           except Exception as e:
               logger.warning(f"Failed to update inventory for product {product_id}: {e}")
   ```

---

## Root Causes Identified

### ❌ **ROOT CAUSE #1: Wrong Table - `products` Table Does Not Exist**

**Evidence:**
```bash
$ docker exec ai-engine-db-postgis psql -U weedgo -d ai_engine -c "\d products"
Did not find any relation named "products".
```

**Actual Tables in Database:**
- ✅ `ocs_inventory` - Contains actual inventory with batch tracking
- ✅ `ocs_product_catalog` - Contains product master data
- ✅ `inventory_products_view` - JOIN view used by POS for product search
- ❌ `products` - **DOES NOT EXIST**

**Impact:**
- Every `UPDATE products` query **silently fails** (caught by try/except)
- Logs show warnings but transaction still completes
- No inventory is deducted from any table

---

### ❌ **ROOT CAUSE #2: No Batch-Level Inventory Deduction**

**Current Code Attempts:**
```python
UPDATE products                              # Wrong table
SET available_quantity = available_quantity - 2
WHERE id = '105000_28g___'                   # Wrong identifier (product ID, not inventory ID)
```

**What Should Happen:**
```sql
UPDATE ocs_inventory
SET quantity_available = quantity_available - 2,
    quantity_on_hand = quantity_on_hand - 2,
    updated_at = CURRENT_TIMESTAMP
WHERE store_id = '5071d685-00dc-4e56-bb11-36e31b305c50'
  AND sku = '105000_28g___'
  AND batch_lot = 'J24042402'                # ✅ Deduct from specific batch
  AND quantity_available >= 2;               # ✅ Check sufficient stock
```

**ocs_inventory Table Schema:**
```
Column                | Type      | Key Features
----------------------|-----------|------------------------------------------
id                    | uuid      | Primary Key
store_id              | uuid      | Foreign Key to stores
sku                   | varchar   | Product identifier
batch_lot             | varchar   | ✅ Batch/Lot tracking column (currently NULL for all records)
quantity_on_hand      | integer   | Physical inventory count
quantity_available    | integer   | Available for sale (on_hand - reserved)
quantity_reserved     | integer   | Reserved for orders
case_gtin             | varchar   | Case-level barcode
each_gtin             | varchar   | Unit-level barcode
packaged_on_date      | date      | Batch packaging date
location_code         | varchar   | Warehouse location
```

**Current Database State:**
```sql
SELECT COUNT(*) as total_inventory_records,
       COUNT(DISTINCT batch_lot) as unique_batches,
       COUNT(CASE WHEN batch_lot IS NOT NULL THEN 1 END) as records_with_batches
FROM ocs_inventory;

-- Results:
-- total_inventory_records: 91
-- unique_batches: 0
-- records_with_batches: 0
-- ❌ NO BATCH DATA EXISTS IN INVENTORY TABLE
```

---

### ❌ **ROOT CAUSE #3: Batch Information Ignored by Backend**

**Frontend Sends:**
```javascript
{
  items: [{
    product: { id: "105000_28g___", ... },
    quantity: 2,
    batch: {                           // ✅ Batch info is sent
      batch_lot: "J24042402",
      quantity_remaining: 50,
      ...
    }
  }]
}
```

**Backend Receives and Ignores:**
```python
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    # ❌ NO 'batch' field in model - data is discarded
```

**Backend Only Accesses:**
```python
for item in transaction.items:
    product_id = item.product.get('id')    # ✅ Gets product ID
    quantity = item.quantity                # ✅ Gets quantity
    # ❌ item.batch is never accessed
    # ❌ batch_lot is never used in UPDATE query
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (POS.tsx)                                          │
├─────────────────────────────────────────────────────────────┤
│ 1. User scans barcode with batch info (GS1-128)            │
│    → Batch matched: J24042402                               │
│ 2. Product added to cart WITH batch:                        │
│    cart = [{                                                │
│      product: { id: "105000_28g___", sku: "105000_28g___"},│
│      quantity: 2,                                           │
│      batch: { batch_lot: "J24042402", qty_remaining: 50 }  │
│    }]                                                       │
│ 3. Payment completed → createTransaction() API call         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (pos_transaction_endpoints.py)                      │
├─────────────────────────────────────────────────────────────┤
│ 4. Receives transaction data                                │
│    ✅ Stores order in 'orders' table                        │
│    ✅ Records payment details                               │
│ 5. Attempts inventory update:                               │
│    ❌ UPDATE products                    (table not found)  │
│    ❌ WHERE id = '105000_28g___'         (wrong key)        │
│    ❌ No batch_lot in WHERE clause       (batch ignored)    │
│ 6. Exception caught → logged warning → continues            │
│    ⚠️  "Failed to update inventory for product..."          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ DATABASE (ai_engine)                                         │
├─────────────────────────────────────────────────────────────┤
│ ✅ orders table: Transaction recorded                       │
│ ❌ ocs_inventory table: NO CHANGES                          │
│    - quantity_available: Still 50 (should be 48)            │
│    - quantity_on_hand: Still 50 (should be 48)              │
│    - batch_lot: Still NULL (should be 'J24042402')          │
└─────────────────────────────────────────────────────────────┘
```

---

## Impact Assessment

### Immediate Impacts

1. **Inventory Accuracy**: ❌ Critically Broken
   - Sales do not reduce stock levels
   - Inventory counts remain unchanged
   - Out-of-stock products still show as available

2. **Batch Tracking**: ❌ Completely Non-Functional
   - No batch-level deductions
   - Cannot track which batches are being sold
   - FIFO/FEFO inventory rotation impossible
   - No traceability for recalls

3. **Reordering**: ❌ Broken
   - Reorder points never triggered
   - Automatic restocking alerts do not work
   - Purchase orders based on incorrect data

4. **Compliance**: ❌ Regulatory Risk
   - Canadian cannabis regulations require batch tracking
   - No audit trail for batch sales
   - Cannot comply with Health Canada reporting

### Business Impacts

- **Overselling Risk**: Products can be sold beyond available stock
- **Stockouts**: Real inventory may be depleted while system shows available
- **Financial Loss**: Shrinkage not tracked, discrepancies in accounting
- **Compliance Violations**: Potential fines for missing batch records

---

## Technical Details

### Correct Inventory Table Structure

**Primary Inventory Table: `ocs_inventory`**

Key Columns for Batch Tracking:
```sql
store_id              uuid          -- Which store owns this inventory
sku                   varchar(100)  -- Product SKU
batch_lot             varchar(100)  -- Batch/Lot number (e.g., "J24042402")
quantity_on_hand      integer       -- Physical count
quantity_available    integer       -- Available for sale
quantity_reserved     integer       -- Reserved for pending orders
case_gtin             varchar(50)   -- Case barcode
each_gtin             varchar(50)   -- Unit barcode
packaged_on_date      date          -- Manufacturing date
```

**Composite Unique Key:**
```sql
UNIQUE (store_id, sku)  -- Current constraint
-- ❌ SHOULD BE: UNIQUE (store_id, sku, batch_lot)
```

---

### Inventory Service Method (Exists but Not Used)

**File:** `src/Backend/services/inventory_service.py`
**Method:** `update_inventory()`
**Lines:** 50-119

```python
async def update_inventory(self, sku: str, quantity_change: int,
                         transaction_type: str, reference_id: Optional[UUID] = None,
                         notes: Optional[str] = None) -> bool:
    """Update inventory levels and record transaction"""
    try:
        async with self.db.transaction():
            if transaction_type == 'sale':
                update_query = """
                    UPDATE ocs_inventory                    # ✅ Correct table
                    SET quantity_available = quantity_available - $2,
                        quantity_on_hand = quantity_on_hand - $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sku = $1 AND quantity_available >= $2
                    RETURNING quantity_on_hand
                """
```

**❌ Problem:** This service method exists but is **NEVER CALLED** by POS transaction endpoint.

---

## Recommended Fix Approach

### Fix #1: Update POS Transaction Endpoint (Critical)

**File:** `src/Backend/api/pos_transaction_endpoints.py`

**Current Code (Lines 195-210):**
```python
# ❌ BROKEN
for item in transaction.items:
    product_id = item.product.get('id')
    if product_id:
        await conn.execute(
            """
            UPDATE products
            SET available_quantity = GREATEST(0, available_quantity - $1)
            WHERE id = $2::uuid
            """,
            item.quantity,
            product_id
        )
```

**Recommended Fix:**
```python
# ✅ CORRECT
for item in transaction.items:
    sku = item.product.get('sku') or item.product.get('id')
    batch_lot = None
    if hasattr(item, 'batch') and item.batch:
        batch_lot = item.batch.get('batch_lot')

    if sku:
        # Build WHERE clause dynamically
        where_conditions = ["store_id = $1", "sku = $2", "quantity_available >= $3"]
        params = [store_uuid, sku, item.quantity]

        if batch_lot:
            where_conditions.append("batch_lot = $4")
            params.append(batch_lot)

        where_clause = " AND ".join(where_conditions)

        # Update inventory with batch tracking
        update_query = f"""
            UPDATE ocs_inventory
            SET quantity_available = quantity_available - $3,
                quantity_on_hand = quantity_on_hand - $3,
                last_sold = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE {where_clause}
            RETURNING id, quantity_available, batch_lot
        """

        result = await conn.fetchrow(update_query, *params)

        if not result:
            logger.error(f"Inventory update failed - insufficient stock or SKU not found: {sku}, batch: {batch_lot}")
            # Consider rolling back transaction or alerting
```

### Fix #2: Update Pydantic Model to Accept Batch

**File:** `src/Backend/api/pos_transaction_endpoints.py`

**Current Model:**
```python
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    # ❌ Missing batch field
```

**Fixed Model:**
```python
class BatchInfo(BaseModel):
    batch_lot: str
    quantity_remaining: Optional[int] = None
    case_gtin: Optional[str] = None
    each_gtin: Optional[str] = None
    packaged_on_date: Optional[str] = None
    location_code: Optional[str] = None

class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    batch: Optional[BatchInfo] = None  # ✅ Added batch tracking
```

### Fix #3: Database Schema Enhancement

**Add Inventory Movement Log:**
```sql
CREATE TABLE ocs_inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id),
    transaction_type VARCHAR(50) NOT NULL,  -- 'sale', 'purchase', 'adjustment', 'return'
    quantity_change INTEGER NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    batch_lot VARCHAR(100),
    reference_id UUID,  -- order_id or transaction_id
    reference_type VARCHAR(50),  -- 'pos_sale', 'purchase_order', 'adjustment'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

CREATE INDEX idx_inventory_movements_inventory ON ocs_inventory_movements(inventory_id);
CREATE INDEX idx_inventory_movements_batch ON ocs_inventory_movements(batch_lot);
CREATE INDEX idx_inventory_movements_reference ON ocs_inventory_movements(reference_id);
```

**Enforce Batch Uniqueness:**
```sql
-- Drop existing unique constraint
ALTER TABLE ocs_inventory DROP CONSTRAINT IF EXISTS ocs_inventory_store_id_sku_key;
ALTER TABLE ocs_inventory DROP CONSTRAINT IF EXISTS ocs_inventory_store_sku_unique;

-- Add new constraint with batch_lot
ALTER TABLE ocs_inventory
    ADD CONSTRAINT ocs_inventory_store_sku_batch_unique
    UNIQUE (store_id, sku, batch_lot);
```

---

## Testing Requirements

### Test Case 1: POS Sale with Batch
```
Given: Inventory record exists with batch_lot = "J24042402", quantity = 50
When: POS sale for 2 units of batch "J24042402"
Then:
  - ocs_inventory.quantity_available = 48
  - ocs_inventory.quantity_on_hand = 48
  - ocs_inventory.last_sold = <current_timestamp>
  - ocs_inventory_movements record created
```

### Test Case 2: Insufficient Stock
```
Given: Inventory record with quantity_available = 1
When: POS sale attempts to sell 2 units
Then:
  - Transaction should fail or prompt for override
  - Inventory unchanged
  - Error logged
```

### Test Case 3: Multi-Batch Sale
```
Given:
  - Batch A: quantity = 30
  - Batch B: quantity = 40
When: Sale of 2 units from Batch A, 3 units from Batch B
Then:
  - Batch A: quantity_available = 28
  - Batch B: quantity_available = 37
  - Two inventory movement records created
```

---

## Priority Classification

**CRITICAL - Must Fix Immediately**

This is a **Severity 1** issue affecting core business functionality:
- ❌ Inventory accuracy broken
- ❌ Regulatory compliance at risk
- ❌ Financial reporting impacted
- ❌ Cannot operate POS reliably

---

## Files Requiring Changes

1. **`src/Backend/api/pos_transaction_endpoints.py`** (Lines 40-47, 195-210)
   - Add `BatchInfo` model
   - Update `POSCartItem` model
   - Replace `products` table with `ocs_inventory`
   - Add batch-aware inventory deduction logic

2. **`src/Backend/database/migrations/`** (New migration file)
   - Add `ocs_inventory_movements` table
   - Update unique constraints on `ocs_inventory`
   - Add indexes for batch tracking

3. **`src/Backend/services/inventory_service.py`** (Optional - Use existing method)
   - Expose `update_inventory()` to be called from POS endpoint
   - Add batch parameter support

---

## Dependencies and Risks

### Breaking Changes
- None - This is a bug fix, not a feature change

### Database Migration Risks
- Changing unique constraint from (store, sku) to (store, sku, batch) may fail if duplicate records exist
- **Mitigation:** Check for duplicates before migration, consolidate if needed

### Backward Compatibility
- Existing inventory records have NULL batch_lot
- **Mitigation:** Allow NULL in constraint, treat NULL as "unbatched" inventory

---

## Success Criteria

### Definition of Done
- [ ] POS sales deduct inventory from `ocs_inventory` table
- [ ] Batch-level inventory tracking functional
- [ ] Inventory movements logged in audit table
- [ ] All test cases passing
- [ ] No silent failures in logs
- [ ] Inventory counts accurate after sales

### Verification Commands
```bash
# Before fix - quantity should stay at 50
docker exec ai-engine-db-postgis psql -U weedgo -d ai_engine -c \
  "SELECT sku, batch_lot, quantity_available FROM ocs_inventory WHERE sku = '105000_28g___';"

# Perform POS sale of 2 units

# After fix - quantity should be 48
docker exec ai-engine-db-postgis psql -U weedgo -d ai_engine -c \
  "SELECT sku, batch_lot, quantity_available FROM ocs_inventory WHERE sku = '105000_28g___';"

# Check movement log
docker exec ai-engine-db-postgis psql -U weedgo -d ai_engine -c \
  "SELECT * FROM ocs_inventory_movements ORDER BY created_at DESC LIMIT 5;"
```

---

## Additional Notes

### Why This Bug Went Unnoticed

1. **Silent Failure**: Exception handling catches the error without halting transaction
2. **Logging Only**: Warnings logged but not surfaced to user
3. **Order Still Completes**: Transaction succeeds, receipt prints, customer happy
4. **No Immediate Impact**: Inventory discrepancy not visible until physical count

### Recommended Monitoring

1. Add alerting for inventory update failures
2. Daily inventory accuracy reports
3. Batch-level stock movement dashboard
4. Audit log review for failed deductions

---

**End of Root Cause Analysis**
