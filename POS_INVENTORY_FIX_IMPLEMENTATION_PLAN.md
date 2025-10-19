# POS Inventory Fix - Implementation Plan

**Date:** 2025-10-18
**Developer:** Claude AI
**Priority:** CRITICAL - Severity 1
**Estimated Time:** 2-3 hours

---

## Overview

This document provides a step-by-step implementation plan to fix the POS inventory update bug identified in `POS_INVENTORY_ROOT_CAUSE_ANALYSIS.md`.

**Problem:** POS sales do not deduct inventory from `ocs_inventory` table or track batch-level deductions.

**Solution:** Fix backend endpoint to properly update inventory with batch tracking support.

---

## Implementation Steps

### Step 1: Update Pydantic Models to Accept Batch Data

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Lines:** 40-47 (add new model), 40-47 (modify existing)

#### 1.1 Add BatchInfo Model

**Location:** After imports, before POSCartItem model

```python
class BatchInfo(BaseModel):
    """Batch/lot information for inventory tracking"""
    batch_lot: str
    quantity_remaining: Optional[int] = None
    case_gtin: Optional[str] = None
    each_gtin: Optional[str] = None
    packaged_on_date: Optional[str] = None
    location_code: Optional[str] = None
```

**Why:** Frontend sends batch data but backend model doesn't accept it. This captures the batch information.

#### 1.2 Update POSCartItem Model

**Current:**
```python
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
```

**Fixed:**
```python
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    batch: Optional[BatchInfo] = None  # ✅ NEW: Accept batch data
```

**Why:** Allows backend to receive and process batch information from frontend.

---

### Step 2: Replace Broken Inventory Update Code

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Lines:** 195-210 (replace entire section)

#### 2.1 Remove Old Broken Code

**Delete this:**
```python
# Update inventory for each item
for item in transaction.items:
    product_id = item.product.get('id')
    if product_id:
        try:
            await conn.execute(
                """
                UPDATE products                          # ❌ Wrong table
                SET available_quantity = GREATEST(0, available_quantity - $1)
                WHERE id = $2::uuid
                """,
                item.quantity,
                product_id
            )
        except Exception as e:
            logger.warning(f"Failed to update inventory for product {product_id}: {e}")
```

#### 2.2 Add New Inventory Update Logic

**Replace with:**
```python
# Update inventory for each item with batch tracking
inventory_updates_successful = []
inventory_update_failures = []

for item in transaction.items:
    sku = item.product.get('sku') or item.product.get('id')
    batch_lot = None

    # Extract batch information if available
    if item.batch:
        batch_lot = item.batch.batch_lot

    if not sku:
        logger.warning(f"Item missing SKU: {item.product}")
        inventory_update_failures.append({
            'item': item.product.get('name', 'Unknown'),
            'reason': 'Missing SKU'
        })
        continue

    try:
        # Build WHERE clause dynamically based on batch presence
        where_conditions = ["store_id = $1", "sku = $2", "quantity_available >= $3"]
        params = [store_uuid, sku, item.quantity]
        param_count = 3

        # Add batch filter if batch data provided
        if batch_lot:
            param_count += 1
            where_conditions.append(f"batch_lot = ${param_count}")
            params.append(batch_lot)

        where_clause = " AND ".join(where_conditions)

        # Update inventory with batch awareness
        update_query = f"""
            UPDATE ocs_inventory
            SET quantity_available = quantity_available - $3,
                quantity_on_hand = quantity_on_hand - $3,
                last_sold = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE {where_clause}
            RETURNING id, sku, batch_lot, quantity_available, quantity_on_hand
        """

        result = await conn.fetchrow(update_query, *params)

        if result:
            # Success - log the inventory update
            await conn.execute(
                """
                INSERT INTO ocs_inventory_transactions (
                    store_id, sku, transaction_type, quantity, batch_lot,
                    reference_id, reference_type, notes, created_at
                ) VALUES ($1, $2, 'sale', $3, $4, $5, 'pos_transaction', $6, CURRENT_TIMESTAMP)
                """,
                store_uuid,
                sku,
                -item.quantity,  # Negative for deduction
                batch_lot,
                uuid.UUID(row['id']),  # Transaction ID from orders table
                f"POS sale - {transaction.receipt_number}"
            )

            inventory_updates_successful.append({
                'sku': sku,
                'batch': batch_lot or 'unbatched',
                'quantity_deducted': item.quantity,
                'remaining': result['quantity_available']
            })

            logger.info(
                f"Inventory updated: SKU={sku}, Batch={batch_lot or 'N/A'}, "
                f"Deducted={item.quantity}, Remaining={result['quantity_available']}"
            )
        else:
            # Failed - insufficient stock or SKU not found
            error_msg = f"Insufficient stock or SKU not found: {sku}"
            if batch_lot:
                error_msg += f", Batch: {batch_lot}"

            logger.error(error_msg)
            inventory_update_failures.append({
                'sku': sku,
                'batch': batch_lot,
                'quantity_requested': item.quantity,
                'reason': 'Insufficient stock or not found'
            })

    except Exception as e:
        logger.error(f"Failed to update inventory for SKU {sku}, Batch {batch_lot}: {e}")
        inventory_update_failures.append({
            'sku': sku,
            'batch': batch_lot,
            'quantity_requested': item.quantity,
            'reason': str(e)
        })

# Add inventory update results to response metadata
result['inventory_updates'] = {
    'successful': inventory_updates_successful,
    'failed': inventory_update_failures,
    'total_items': len(transaction.items),
    'updated_count': len(inventory_updates_successful),
    'failed_count': len(inventory_update_failures)
}

# Log warning if any updates failed
if inventory_update_failures:
    logger.warning(
        f"Transaction {row['id']} completed but {len(inventory_update_failures)} "
        f"inventory updates failed: {inventory_update_failures}"
    )
```

**Why:**
- ✅ Uses correct table: `ocs_inventory`
- ✅ Updates both `quantity_available` and `quantity_on_hand`
- ✅ Supports batch-level deduction when batch data provided
- ✅ Falls back to SKU-only deduction when no batch specified
- ✅ Logs transactions in `ocs_inventory_transactions` for audit trail
- ✅ Provides detailed success/failure reporting
- ✅ Updates `last_sold` timestamp for analytics

---

### Step 3: Add Inventory Validation (Optional - Recommended)

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Location:** Before creating the order (around line 108)

#### 3.1 Pre-Transaction Inventory Check

**Add this code block:**
```python
# Validate inventory availability before creating order
inventory_check_failures = []

for item in transaction.items:
    sku = item.product.get('sku') or item.product.get('id')
    batch_lot = item.batch.batch_lot if item.batch else None

    if not sku:
        continue

    # Check if sufficient inventory exists
    check_query = """
        SELECT quantity_available, batch_lot
        FROM ocs_inventory
        WHERE store_id = $1 AND sku = $2
    """
    check_params = [store_uuid, sku]

    if batch_lot:
        check_query += " AND batch_lot = $3"
        check_params.append(batch_lot)

    inventory_record = await conn.fetchrow(check_query, *check_params)

    if not inventory_record:
        inventory_check_failures.append({
            'sku': sku,
            'batch': batch_lot,
            'reason': 'Inventory record not found'
        })
    elif inventory_record['quantity_available'] < item.quantity:
        inventory_check_failures.append({
            'sku': sku,
            'batch': batch_lot,
            'requested': item.quantity,
            'available': inventory_record['quantity_available'],
            'reason': 'Insufficient stock'
        })

# If validation failed, return error before creating order
if inventory_check_failures:
    raise HTTPException(
        status_code=400,
        detail={
            'error': 'Insufficient inventory',
            'failures': inventory_check_failures,
            'message': 'One or more items have insufficient stock'
        }
    )
```

**Why:**
- ✅ Prevents overselling
- ✅ Validates inventory before committing transaction
- ✅ Returns clear error message to frontend
- ✅ Stops transaction early if inventory issues detected

---

### Step 4: Update Loyalty Points Section

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Lines:** 184-194 (move this section)

#### 4.1 Move Loyalty Points After Inventory Update

**Current location:** After creating order, before inventory update
**New location:** After successful inventory update

**Why:**
- ✅ Only award points if inventory successfully deducted
- ✅ Prevents points being awarded for failed sales
- ✅ Better transaction atomicity

**No code changes needed, just move the block:**
```python
# Update customer loyalty points if applicable
if user_id:
    try:
        points_earned = int(transaction.total)  # 1 point per dollar
        await conn.execute(
            "UPDATE profiles SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE user_id = $2",
            points_earned,
            user_id
        )
    except Exception as e:
        logger.warning(f"Failed to update loyalty points: {e}")
```

---

### Step 5: Add Comprehensive Error Handling

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Location:** Wrapping the entire inventory update section

#### 5.1 Add Transaction Rollback Support

**Wrap inventory updates with try/except:**
```python
try:
    # Update inventory for each item with batch tracking
    inventory_updates_successful = []
    inventory_update_failures = []

    # ... (all inventory update code from Step 2.2)

    # Check if ANY critical inventory updates failed
    if inventory_update_failures and transaction.status == 'completed':
        # For completed sales, we need inventory to be updated
        # Log critical error but don't fail transaction (legacy compatibility)
        logger.critical(
            f"CRITICAL: Transaction {row['id']} completed but inventory updates failed. "
            f"Manual inventory adjustment required. Failures: {inventory_update_failures}"
        )

        # TODO: Send alert to inventory management team
        # TODO: Create pending inventory adjustment record

except Exception as inventory_error:
    # Inventory update failed catastrophically
    logger.error(f"Critical inventory update error: {inventory_error}")

    # If this is a completed sale, we have a problem
    if transaction.status == 'completed':
        # Option 1: Fail the entire transaction (strict mode)
        # raise HTTPException(status_code=500, detail="Inventory update failed")

        # Option 2: Allow transaction but flag for manual review (lenient mode)
        result['inventory_update_error'] = str(inventory_error)
        result['requires_manual_inventory_adjustment'] = True
        logger.critical(
            f"Transaction {row['id']} completed without inventory update. "
            f"URGENT: Manual inventory adjustment required."
        )
```

**Why:**
- ✅ Prevents silent failures
- ✅ Provides options for strict vs. lenient error handling
- ✅ Enables manual review process
- ✅ Logs critical errors for monitoring

---

### Step 6: Update Response Model (Optional)

**File:** `src/Backend/api/pos_transaction_endpoints.py`
**Location:** In the result dictionary

#### 6.1 Add Inventory Update Status to Response

**Current result:**
```python
result = {
    'id': row['id'],
    'store_id': transaction.store_id,
    # ... other fields
    'timestamp': row['timestamp'].isoformat()
}
```

**Enhanced result:**
```python
result = {
    'id': row['id'],
    'store_id': transaction.store_id,
    # ... other fields
    'timestamp': row['timestamp'].isoformat(),
    'inventory_updates': {  # ✅ NEW
        'successful': inventory_updates_successful,
        'failed': inventory_update_failures,
        'total_items': len(transaction.items),
        'updated_count': len(inventory_updates_successful),
        'failed_count': len(inventory_update_failures)
    }
}
```

**Why:**
- ✅ Frontend can show inventory update status
- ✅ Helps with debugging
- ✅ Enables better user feedback

---

## Testing Plan

### Test Case 1: Simple Sale Without Batch

**Setup:**
```sql
-- Ensure inventory exists
INSERT INTO ocs_inventory (store_id, sku, quantity_on_hand, quantity_available)
VALUES ('5071d685-00dc-4e56-bb11-36e31b305c50', 'TEST_SKU_001', 100, 100);
```

**Test:**
```json
POST /api/pos/transactions
{
  "store_id": "5071d685-00dc-4e56-bb11-36e31b305c50",
  "items": [{
    "product": {"sku": "TEST_SKU_001", "name": "Test Product"},
    "quantity": 5
  }],
  "total": 25.00,
  ...
}
```

**Expected:**
- ✅ Transaction created
- ✅ Inventory quantity_available = 95
- ✅ Inventory quantity_on_hand = 95
- ✅ Transaction logged in ocs_inventory_transactions
- ✅ Response shows successful inventory update

**Verify:**
```sql
SELECT quantity_available, quantity_on_hand, last_sold
FROM ocs_inventory
WHERE sku = 'TEST_SKU_001';
-- Expected: quantity_available = 95, quantity_on_hand = 95

SELECT * FROM ocs_inventory_transactions
WHERE sku = 'TEST_SKU_001'
ORDER BY created_at DESC LIMIT 1;
-- Expected: transaction_type = 'sale', quantity = -5
```

---

### Test Case 2: Sale With Batch Tracking

**Setup:**
```sql
-- Ensure inventory exists with batch
INSERT INTO ocs_inventory (store_id, sku, quantity_on_hand, quantity_available, batch_lot)
VALUES ('5071d685-00dc-4e56-bb11-36e31b305c50', 'TEST_SKU_002', 50, 50, 'BATCH_A');
```

**Test:**
```json
POST /api/pos/transactions
{
  "store_id": "5071d685-00dc-4e56-bb11-36e31b305c50",
  "items": [{
    "product": {"sku": "TEST_SKU_002", "name": "Batch Product"},
    "quantity": 10,
    "batch": {
      "batch_lot": "BATCH_A",
      "quantity_remaining": 50
    }
  }],
  "total": 100.00,
  ...
}
```

**Expected:**
- ✅ Transaction created
- ✅ Inventory for BATCH_A: quantity_available = 40
- ✅ Transaction logged with batch_lot = 'BATCH_A'

**Verify:**
```sql
SELECT quantity_available, batch_lot
FROM ocs_inventory
WHERE sku = 'TEST_SKU_002' AND batch_lot = 'BATCH_A';
-- Expected: quantity_available = 40

SELECT batch_lot FROM ocs_inventory_transactions
WHERE sku = 'TEST_SKU_002'
ORDER BY created_at DESC LIMIT 1;
-- Expected: batch_lot = 'BATCH_A'
```

---

### Test Case 3: Insufficient Stock

**Setup:**
```sql
-- Create low stock item
INSERT INTO ocs_inventory (store_id, sku, quantity_on_hand, quantity_available)
VALUES ('5071d685-00dc-4e56-bb11-36e31b305c50', 'TEST_SKU_003', 2, 2);
```

**Test:**
```json
POST /api/pos/transactions
{
  "items": [{
    "product": {"sku": "TEST_SKU_003"},
    "quantity": 5  // More than available
  }],
  ...
}
```

**Expected (if validation enabled):**
- ❌ 400 Bad Request
- Response: "Insufficient inventory" error

**Expected (if validation disabled):**
- ✅ Transaction created
- ⚠️ Inventory update fails
- ⚠️ Response shows failed inventory update
- ⚠️ Critical log entry created

---

### Test Case 4: Multi-Batch Sale

**Setup:**
```sql
-- Create two batches of same product
INSERT INTO ocs_inventory (store_id, sku, quantity_on_hand, quantity_available, batch_lot)
VALUES
  ('5071d685-00dc-4e56-bb11-36e31b305c50', 'TEST_SKU_004', 30, 30, 'BATCH_X'),
  ('5071d685-00dc-4e56-bb11-36e31b305c50', 'TEST_SKU_004', 40, 40, 'BATCH_Y');
```

**Test:**
```json
POST /api/pos/transactions
{
  "items": [
    {
      "product": {"sku": "TEST_SKU_004"},
      "quantity": 5,
      "batch": {"batch_lot": "BATCH_X"}
    },
    {
      "product": {"sku": "TEST_SKU_004"},
      "quantity": 10,
      "batch": {"batch_lot": "BATCH_Y"}
    }
  ],
  ...
}
```

**Expected:**
- ✅ BATCH_X: quantity_available = 25
- ✅ BATCH_Y: quantity_available = 30
- ✅ Two separate inventory transaction records

**Verify:**
```sql
SELECT batch_lot, quantity_available
FROM ocs_inventory
WHERE sku = 'TEST_SKU_004'
ORDER BY batch_lot;
-- Expected:
-- BATCH_X | 25
-- BATCH_Y | 30

SELECT COUNT(*) FROM ocs_inventory_transactions
WHERE sku = 'TEST_SKU_004';
-- Expected: 2 records
```

---

## Implementation Checklist

### Code Changes

- [ ] **Step 1.1:** Add `BatchInfo` Pydantic model
- [ ] **Step 1.2:** Update `POSCartItem` model with `batch` field
- [ ] **Step 2.1:** Remove old broken inventory update code
- [ ] **Step 2.2:** Add new batch-aware inventory update logic
- [ ] **Step 3.1:** (Optional) Add pre-transaction inventory validation
- [ ] **Step 4.1:** Move loyalty points update after inventory update
- [ ] **Step 5.1:** Add comprehensive error handling and logging
- [ ] **Step 6.1:** (Optional) Enhance response with inventory update status

### Testing

- [ ] **Test 1:** Simple sale without batch tracking
- [ ] **Test 2:** Sale with batch tracking
- [ ] **Test 3:** Insufficient stock handling
- [ ] **Test 4:** Multi-batch sale
- [ ] **Test 5:** Mixed batch and non-batch items in same transaction
- [ ] **Test 6:** Verify inventory transaction logging
- [ ] **Test 7:** Verify last_sold timestamp updates
- [ ] **Test 8:** Test error handling for missing SKU

### Verification

- [ ] Check database after each test case
- [ ] Verify ocs_inventory quantities updated
- [ ] Verify ocs_inventory_transactions records created
- [ ] Check application logs for warnings/errors
- [ ] Test with real POS frontend
- [ ] Verify batch selection in frontend flows correctly
- [ ] Monitor for any performance issues

### Documentation

- [ ] Update API documentation with new response fields
- [ ] Document batch tracking requirements
- [ ] Update deployment notes with testing instructions
- [ ] Create runbook for inventory discrepancy resolution

---

## Rollback Plan

If issues arise after deployment:

### Immediate Rollback

1. **Revert code changes:**
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Redeploy previous version:**
   ```bash
   kubectl rollout undo deployment/ai-engine-service
   ```

### Data Cleanup (If Needed)

If bad inventory transactions were created:

```sql
-- Identify transactions from the buggy deployment
SELECT * FROM ocs_inventory_transactions
WHERE created_at > '2025-10-18 HH:MM:SS'  -- Time of deployment
  AND transaction_type = 'sale'
ORDER BY created_at DESC;

-- Reverse incorrect inventory deductions (if needed)
-- CAUTION: Only run this with proper analysis
UPDATE ocs_inventory SET
    quantity_available = quantity_available + <amount>,
    quantity_on_hand = quantity_on_hand + <amount>
WHERE sku = '<affected_sku>' AND batch_lot = '<affected_batch>';
```

---

## Post-Deployment Monitoring

### Key Metrics to Watch

1. **Inventory Transaction Rate**
   ```sql
   SELECT COUNT(*) as transactions_per_hour
   FROM ocs_inventory_transactions
   WHERE created_at > NOW() - INTERVAL '1 hour'
     AND transaction_type = 'sale';
   ```

2. **Failed Inventory Updates**
   ```bash
   # Check logs for warnings
   kubectl logs -f deployment/ai-engine-service | grep "Failed to update inventory"
   ```

3. **Negative Inventory (Should Not Happen)**
   ```sql
   SELECT sku, batch_lot, quantity_available, quantity_on_hand
   FROM ocs_inventory
   WHERE quantity_available < 0 OR quantity_on_hand < 0;
   ```

4. **Inventory Discrepancies**
   ```sql
   -- Compare transaction log sum vs. actual inventory
   SELECT
       i.sku,
       i.batch_lot,
       i.quantity_on_hand as current_quantity,
       COALESCE(SUM(t.quantity), 0) as transaction_sum
   FROM ocs_inventory i
   LEFT JOIN ocs_inventory_transactions t ON i.sku = t.sku AND i.batch_lot = t.batch_lot
   GROUP BY i.sku, i.batch_lot, i.quantity_on_hand
   HAVING i.quantity_on_hand != COALESCE(SUM(t.quantity), 0);
   ```

---

## Estimated Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| Code changes | 1 hour | Steps 1-6 |
| Unit testing | 30 min | Test cases 1-4 |
| Integration testing | 30 min | Frontend + Backend |
| Code review | 30 min | Peer review |
| Deployment | 15 min | Deploy to staging |
| Staging validation | 30 min | Full regression test |
| Production deployment | 15 min | Deploy to prod |
| Post-deploy monitoring | 2 hours | Watch metrics |
| **Total** | **5-6 hours** | Including monitoring |

---

## Success Criteria

✅ **Definition of Done:**

1. POS sales deduct inventory from `ocs_inventory` table
2. Batch-level inventory tracking functional
3. Inventory transactions logged in `ocs_inventory_transactions`
4. All test cases passing
5. No silent failures in logs
6. Inventory counts accurate after sales
7. Frontend receives inventory update status
8. Documentation updated

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance degradation | Low | Medium | Use indexes, test with load |
| Inventory discrepancies | Medium | High | Add pre-transaction validation |
| Transaction failures | Low | High | Comprehensive error handling |
| Batch data missing | High | Medium | Graceful fallback to SKU-only |
| Overselling | Medium | High | Pre-transaction inventory check |

---

## Questions to Resolve Before Implementation

1. **Should we enforce strict inventory validation?**
   - Option A: Block sale if insufficient inventory (strict)
   - Option B: Allow sale but flag for review (lenient)
   - **Recommendation:** Start with strict, add override capability later

2. **What to do with unbatched inventory?**
   - Option A: Require all items to have batch data
   - Option B: Allow NULL batch_lot for legacy items
   - **Recommendation:** Option B for backward compatibility

3. **Should we update existing unbatched inventory?**
   - Option A: Backfill batch data from ASN imports
   - Option B: Leave as-is, only track new batches
   - **Recommendation:** Option B initially, backfill as separate project

4. **Error handling mode?**
   - Option A: Fail entire transaction if inventory update fails
   - Option B: Complete transaction but log critical error
   - **Recommendation:** Option A for data integrity

---

**Implementation Plan Complete - Ready to Execute**
