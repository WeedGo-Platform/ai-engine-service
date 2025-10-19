# Purchase Order Data Population - Root Cause Analysis & Fixes

**Date:** 2025-10-18
**Status:** 🔧 ROOT CAUSES IDENTIFIED - READY TO FIX
**Apology:** I incorrectly removed columns instead of fixing why they weren't populated.

---

## ❌ My Mistake

I removed columns thinking they were unused, but they ARE needed:
- ✅ **REVERTED:** All columns have been restored
- 🔍 **ROOT CAUSES:** Now properly investigated below

---

## Issue #1: `item_name` Not Being Saved

### Root Cause: ✅ Field Name Mismatch

**Frontend Sends:**
```json
{
  "quantity_ordered": 12,  // ← Uses "quantity_ordered"
  "item_name": "Hybrid 3.5g"  // ← Correctly sends item_name
}
```

**Backend Expects:**
```python
# Line 321 in repositories/__init__.py
quantity = item['quantity']  # ❌ Looks for 'quantity'
```

**Also in Line 88:**
```python
# purchase_order_service.py
total_amount = sum(
    Decimal(str(item['quantity'])) * ...  # ❌ Looks for 'quantity'
)
```

### The Fix:

**File:** `src/Backend/ddd_refactored/domain/purchase_order/repositories/__init__.py`

**Line 321** - Change:
```python
# BEFORE:
quantity = item['quantity']

# AFTER:
quantity = item.get('quantity_ordered') or item.get('quantity')  # Support both
```

**File:** `src/Backend/ddd_refactored/application/services/purchase_order_service.py`

**Line 88** - Change:
```python
# BEFORE:
total_amount = sum(
    Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
    for item in items
)

# AFTER:
total_amount = sum(
    Decimal(str(item.get('quantity_ordered') or item.get('quantity'))) *
    Decimal(str(item['unit_cost']))
    for item in items
)
```

**Why It Worked in Logs But Not DB:**
- `item.get('item_name')` returns None when field is empty string `''`
- Empty string from Excel → None → NULL in database
- Actually the item_name IS being sent, just needs the quantity fix

---

## Issue #2: `tax_amount` and `subtotal` Not Being Saved

### Root Cause: ✅ Backend Doesn't Insert These Values

**Purchase Orders Table INSERT** (`purchase_order_service.py` line 107):
```python
purchase_order.subtotal = total_amount  # ✅ Sets in memory
# But repository doesn't save it to purchase_orders table!
```

**Repository Save** doesn't include these fields in INSERT:
```python
# Line ~200 in repositories/__init__.py
INSERT INTO purchase_orders
(po_number, store_id, supplier_id, order_date, expected_date,
 status, total_amount, notes, ...)
# ❌ Missing: subtotal, tax_amount
```

### The Fix:

**File:** `src/Backend/ddd_refactored/domain/purchase_order/repositories/__init__.py`

Find the INSERT query (around line 200) and add:
```python
INSERT INTO purchase_orders
(po_number, store_id, supplier_id, order_date, expected_date,
 status, total_amount, subtotal, tax_amount, notes, ...)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, ...)
```

And in the execute:
```python
await conn.fetchval(
    po_query,
    po.order_number,
    po.store_id,
    po.supplier_id,
    po.order_date,
    po.expected_delivery_date,
    po.status.value,
    po.total_amount,
    po.subtotal,  # ← ADD
    po.tax_amount,  # ← ADD
    po.internal_notes,
    ...
)
```

---

## Issue #3: User Columns Not Being Populated

### Root Cause #1: ✅ `created_by` Not Passed from Frontend

**Frontend Code** (ASNImportModal.tsx line 655):
```typescript
const purchaseOrder = {
  supplier_id: finalSupplierId,
  items: mappedItems,
  expected_date: expectedDate.toISOString(),
  excel_filename: uploadedFileName,
  notes: notes,
  shipment_id: shipmentId,
  container_id: containerId,
  vendor: vendorName,
  ocs_order_number: ocsOrderNumber,
  created_by: undefined,  // ❌ Never set!
};
```

### The Fix:

**File:** `src/Frontend/ai-admin-dashboard/src/components/ASNImportModal.tsx`

Around line 655, change:
```typescript
const purchaseOrder = {
  supplier_id: finalSupplierId,
  items: mappedItems,
  expected_date: expectedDate.toISOString(),
  excel_filename: uploadedFileName,
  notes: notes,
  shipment_id: shipmentId,
  container_id: containerId,
  vendor: vendorName,
  ocs_order_number: ocsOrderNumber,
  created_by: user?.id,  // ← ADD: Get from auth context
};
```

### Root Cause #2: ✅ `received_by` Not Set During Receiving

**Backend Code** (`inventory_service.py` line 273-358):
```python
async def receive_purchase_order(self, po_id: UUID,
                                received_items: List[Dict[str, Any]]) -> bool:
    # ... receives items ...

    # Update PO status
    status_query = """
        UPDATE purchase_orders
        SET status = 'received',
            received_date = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """
    # ❌ Doesn't set received_by!
```

### The Fix:

**File:** `src/Backend/services/inventory_service.py`

Line ~350, change:
```python
# BEFORE:
async def receive_purchase_order(self, po_id: UUID,
                                received_items: List[Dict[str, Any]]) -> bool:

# AFTER:
async def receive_purchase_order(self, po_id: UUID,
                                received_items: List[Dict[str, Any]],
                                received_by: Optional[UUID] = None) -> bool:
```

And update the query:
```python
status_query = """
    UPDATE purchase_orders
    SET status = 'received',
        received_date = CURRENT_TIMESTAMP,
        received_by = $2,  # ← ADD
        updated_at = CURRENT_TIMESTAMP
    WHERE id = $1
"""
await self.db.execute(status_query, po_id, received_by)  # ← Pass parameter
```

**Also update the API endpoint** (`inventory_endpoints.py` line 228):
```python
@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: UUID,
    request: ReceivePurchaseOrderRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),  # ← ADD
    service: InventoryService = Depends(get_inventory_service)
):
    # Get user ID from header or JWT
    user_id = UUID(x_user_id) if x_user_id else None

    success = await service.receive_purchase_order(
        po_id,
        [item.dict() for item in request.items],
        received_by=user_id  # ← ADD
    )
```

**Frontend must send user ID** in header:
```typescript
const response = await fetch(..., {
  headers: {
    'X-User-ID': user.id,  // ← ADD
    ...
  }
});
```

### Root Cause #3: ✅ `approved_by` - No Approval Workflow

**Current State:** No approval step exists in the workflow.

**Options:**

**A) Don't Use (Recommended for Now):**
- Remove `approved_by` column (not needed yet)
- Add back when approval workflow is implemented

**B) Auto-Approve on Creation:**
```python
# In purchase_order_service.py
purchase_order.approved_by = created_by  # Same person approves
purchase_order.approved_at = datetime.utcnow()
```

**C) Add Approval Step (Future):**
- Create `/purchase-orders/{id}/approve` endpoint
- Add approval UI in frontend
- Track who approved

---

## Complete Fix Summary

### Backend Fixes Needed:

1. **`repositories/__init__.py` (Line 321)**
   ```python
   quantity = item.get('quantity_ordered') or item.get('quantity')
   ```

2. **`purchase_order_service.py` (Line 88)**
   ```python
   Decimal(str(item.get('quantity_ordered') or item.get('quantity')))
   ```

3. **`repositories/__init__.py` (Line ~200)**
   ```python
   # Add subtotal, tax_amount to INSERT query
   ```

4. **`inventory_service.py` (Line ~273 & ~350)**
   ```python
   # Add received_by parameter and update query
   ```

5. **`inventory_endpoints.py` (Line 228)**
   ```python
   # Add X-User-ID header handling
   ```

### Frontend Fixes Needed:

1. **`ASNImportModal.tsx` (Line 655)**
   ```typescript
   created_by: user?.id
   ```

2. **Receive PO API Call** (wherever that is)
   ```typescript
   headers: {
     'X-User-ID': user.id
   }
   ```

---

## Testing Plan

After fixes:

1. **Import New ASN:**
   ```sql
   SELECT
       item_name,  -- Should have product names
       quantity_ordered
   FROM purchase_order_items
   WHERE purchase_order_id = ...;
   ```

2. **Check PO Header:**
   ```sql
   SELECT
       subtotal,  -- Should have value
       tax_amount,  -- Should have value (or NULL if not in Excel)
       created_by,  -- Should have user UUID
       total_amount
   FROM purchase_orders
   WHERE id = ...;
   ```

3. **Receive PO:**
   ```sql
   SELECT
       received_by,  -- Should have user UUID
       received_date,  -- Should have timestamp
       status  -- Should be 'received'
   FROM purchase_orders
   WHERE id = ...;
   ```

---

## Priority Order:

1. **HIGH:** Fix `quantity_ordered` vs `quantity` mismatch (blocking PO creation)
2. **HIGH:** Add `created_by` from frontend
3. **MEDIUM:** Add `subtotal`/`tax_amount` to repository INSERT
4. **MEDIUM:** Add `received_by` to receive flow
5. **LOW:** Handle `approved_by` (no workflow yet)

---

**Next Steps:**
1. Apply fixes in order listed
2. Test with real ASN import
3. Verify all columns populated correctly
