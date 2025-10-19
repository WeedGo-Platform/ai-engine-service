# Purchase Order Receiving Implementation Plan

**Date:** 2025-10-18 (Updated)
**Feature:** Complete PO Receiving Workflow (Frontend UI for existing V1 API)
**Scope:** Build frontend receiving modal, use existing DDD-powered V1 endpoint

---

## 🎯 Goals

1. **Backend:** ✅ COMPLETE - V1 endpoint already fully implemented with DDD
2. **Frontend:** Create intuitive UI for receiving purchase orders in admin dashboard
3. **Architecture:** Use single V1 endpoint (no V2 duplication)
4. **UX:** Provide clear visibility into what's being received, batch tracking, and inventory updates

---

## 📋 Current State Analysis

### V1 Endpoint (✅ COMPLETE - Full DDD Implementation)
- **Endpoint:** `POST /api/inventory/purchase-orders/{po_id}/receive`
- **File:** `api/inventory_endpoints.py:234-340`
- **Status:** ✅ Fully implemented with DDD (migrated in Phase 1)
- **Services Used:**
  - `PurchaseOrderApplicationService.receive_purchase_order()`
  - `InventoryManagementService.receive_inventory()`
- **Request Format:**
  ```json
  {
    "items": [
      {
        "sku": "ABC123",
        "quantity_received": 100,
        "unit_cost": 25.50,
        "batch_lot": "LOT-2025-001",
        "case_gtin": "12345678901234",
        "packaged_on_date": "2025-10-15",
        "each_gtin": "98765432109876",
        "gtin_barcode": "11111111111111",
        "vendor": "Supplier Inc",
        "brand": "Brand Name"
      }
    ]
  }
  ```
- **Headers:** `X-User-ID`, `X-Store-ID`
- **Response:**
  ```json
  {
    "success": true,
    "message": "Received 5 items for PO abc-123",
    "po_details": {
      "id": "...",
      "order_number": "PO-2025-001",
      "total_received": 120,
      "status": "fully_received",
      "is_fully_received": true,
      "received_by": "...",
      "received_at": "2025-10-18T..."
    },
    "batches": [
      {
        "sku": "SKU-001",
        "batch_lot": "BATCH-001",
        "quantity_received": 24,
        "batch_id": "..."
      }
    ]
  }
  ```

### V2 Endpoint
- **Status:** ❌ REMOVED (Duplicate of V1)
- **Reason:** V1 already uses full DDD implementation. Creating V2 would duplicate ~100 LOC with no added value.
- **Decision:** Use V1 for both frontend and backend (single source of truth)

### Frontend
- **API Service:** `api.ts` needs `receive()` method for V1 endpoint
- **UI Components:** ❌ No receiving modal/UI exists
- **Pages:** PO list exists but no "Receive" action

---

## 🏗️ Design Decisions

### 1. Backend Endpoint Strategy ✅ DECIDED

**Decision:** Use V1 endpoint only - **No V2 duplication**

**Rationale:**
- V1 `/api/inventory/purchase-orders/{po_id}/receive` already uses full DDD implementation
- Creating V2 would duplicate ~100 LOC with no added value
- Both would call the same services (`PurchaseOrderApplicationService` + `InventoryManagementService`)
- Single source of truth is cleaner and easier to maintain

**V2 Status:** REMOVED (see `V1_V2_RECEIVE_ENDPOINT_ANALYSIS.md` for detailed analysis)

### 2. Request Model (V1 - Already Implemented)

**V1 `ReceivePurchaseOrderRequest`:**
```python
class ReceivePurchaseOrderItem(BaseModel):
    sku: str
    quantity_received: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    batch_lot: str  # Required - FIFO identifier
    case_gtin: str  # Required
    packaged_on_date: date  # Required
    gtin_barcode: Optional[str] = None
    each_gtin: str  # Required
    vendor: str  # Required
    brand: str  # Required

class ReceivePurchaseOrderRequest(BaseModel):
    items: List[ReceivePurchaseOrderItem]
```

**Headers:**
- `X-User-ID`: User ID who is receiving
- `X-Store-ID`: Store ID where items are being received

### 3. Response Model (V1 - Already Implemented)

**V1 Response Structure:**
```python
{
    'success': bool,
    'message': str,
    'po_details': {
        'id': str,
        'order_number': str,
        'total_received': int,
        'status': str,
        'is_fully_received': bool,
        'received_by': str,
        'received_at': str
    },
    'batches': [
        {
            'sku': str,
            'batch_lot': str,
            'quantity_received': int,
            'batch_id': str
        }
    ]
}
```

### 4. UI/UX Design

#### **Purchase Order Receiving Modal**

**Trigger Locations:**
1. PO List Page - "Receive" button on each row (status: APPROVED, CONFIRMED, SENT_TO_SUPPLIER)
2. PO Detail Page - "Receive Items" button in header
3. ASN Import - Optional "Auto-receive" checkbox

**Modal Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  Receive Purchase Order: PO-20251018-001                     │
│  Supplier: ABC Distributors                                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Order Information                                       │  │
│  │ • Expected Delivery: 2025-10-20                        │  │
│  │ • Total Items Ordered: 250 units                       │  │
│  │ • Total Amount: $5,250.00                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Items to Receive (3)                                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ✓ SKU: ABC-001 | Product: Blue Dream 3.5g             │  │
│  │   Ordered: 100 | Receive: [100] | Batch: [LOT-001]    │  │
│  │   Unit Cost: $25.00 | Packaged: [2025-10-15]          │  │
│  │   ○ Mark as damaged: [  ]  ○ Add to quarantine: [ ]   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ ✓ SKU: DEF-002 | Product: OG Kush 1oz                 │  │
│  │   Ordered: 50 | Receive: [50] | Batch: [LOT-002]      │  │
│  │   Unit Cost: $75.00 | Packaged: [2025-10-15]          │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ ✓ SKU: GHI-003 | Product: Edibles Pack                │  │
│  │   Ordered: 100 | Receive: [0] | Batch: [         ]    │  │
│  │   ⚠️ Not received - mark as backorder                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  📝 Receiving Notes:                                          │
│  [Shipment arrived in good condition. All items verified]    │
│                                                               │
│  ✓ Auto-approve this purchase order                          │
│                                                               │
│  [Cancel]                              [Receive Items (2/3)] │
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Pre-populate quantities with ordered amounts
- ✅ Allow partial receiving (receive less than ordered)
- ✅ Generate batch lot numbers automatically (format: `BATCH-{YYYYMMDD}-{SKU}-{SEQ}`)
- ✅ Packaged date defaults to today, editable
- ✅ Show running totals (items received vs ordered)
- ✅ Validation: Can't receive more than ordered (or show warning)
- ✅ Real-time cost calculation
- ✅ Support for damaged/quarantine marking

---

## 🔧 Implementation Plan

### **Phase 1: Backend** ✅ COMPLETE

**Status:** ✅ No work needed - V1 endpoint already implements full DDD

**Actions Taken:**
- ✅ Verified V1 endpoint uses `batch_lot` (not `batch_number`)
- ✅ Removed duplicate V2 receive endpoint
- ✅ Removed V2-specific DTOs from `dto_mappers.py`
- ✅ Updated implementation plan to use V1 only

**Endpoint to Use:** `POST /api/inventory/purchase-orders/{po_id}/receive`
**File:** `api/inventory_endpoints.py:234-340`

---

### **Phase 2: Frontend Dashboard UI** (Current Focus)

#### Task 2.1: Create Receive PO Modal Component
**File:** `src/Frontend/ai-admin-dashboard/src/components/ReceivePurchaseOrderModal.tsx`

**Component Structure:**
```tsx
interface ReceivePurchaseOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: PurchaseOrder;  // From API
  onSuccess: () => void;
}

interface ReceivingItem {
  sku: string;
  product_name: string;
  quantity_ordered: number;
  quantity_received: number;  // Editable
  unit_cost: number;
  batch_lot: string;  // Auto-generated or editable
  packaged_on_date: string;  // Defaults to today
  is_damaged: boolean;
  is_quarantined: boolean;
  notes: string;
}

const ReceivePurchaseOrderModal: React.FC<ReceivePurchaseOrderModalProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  onSuccess
}) => {
  // State
  const [receivingItems, setReceivingItems] = useState<ReceivingItem[]>([]);
  const [receivingNotes, setReceivingNotes] = useState('');
  const [autoApprove, setAutoApprove] = useState(true);
  const [loading, setLoading] = useState(false);

  // Initialize items from PO
  useEffect(() => {
    if (purchaseOrder?.line_items) {
      const items = purchaseOrder.line_items.map(item => ({
        sku: item.sku,
        product_name: item.product_name,
        quantity_ordered: item.quantity,
        quantity_received: item.quantity,  // Default to full quantity
        unit_cost: item.unit_price,
        batch_lot: generateBatchLot(item.sku),  // Auto-generate
        packaged_on_date: new Date().toISOString().split('T')[0],
        is_damaged: false,
        is_quarantined: false,
        notes: ''
      }));
      setReceivingItems(items);
    }
  }, [purchaseOrder]);

  // Helper: Generate batch lot number
  const generateBatchLot = (sku: string) => {
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const seq = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `BATCH-${date}-${sku}-${seq}`;
  };

  // Handle submit
  const handleReceive = async () => {
    setLoading(true);
    try {
      await api.purchaseOrders.receive(purchaseOrder.id, {
        items: receivingItems
          .filter(item => item.quantity_received > 0)
          .map(item => ({
            sku: item.sku,
            quantity_received: item.quantity_received,
            unit_cost: item.unit_cost,
            batch_lot: item.batch_lot,
            packaged_on_date: item.packaged_on_date,
            notes: item.notes
          })),
        auto_approve: autoApprove,
        receiving_notes: receivingNotes
      });

      toast.success(`Successfully received ${receivingItems.length} items`);
      onSuccess();
      onClose();
    } catch (error) {
      toast.error('Failed to receive purchase order');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Render component
  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="lg">
      {/* Modal content here */}
    </Dialog>
  );
};
```

**Estimated Time:** 3-4 hours

---

#### Task 2.2: Add Receive Action to PO Pages
**Files:**
- `src/Frontend/ai-admin-dashboard/src/pages/PurchaseOrders.tsx` (List page)
- `src/Frontend/ai-admin-dashboard/src/pages/PurchaseOrderDetail.tsx` (Detail page)

**Actions:**
- Add "Receive" button to PO list table (conditional on status)
- Add "Receive Items" button to PO detail header
- Wire up modal open/close handlers
- Add query invalidation after successful receive

**Estimated Time:** 1-2 hours

---

#### Task 2.3: Update API Service
**File:** `src/Frontend/ai-admin-dashboard/src/services/api.ts`

**Update:**
```typescript
purchaseOrders: {
  // ... existing methods ...
  receive: (id: string, data: {
    items: Array<{
      sku: string;
      quantity_received: number;
      unit_cost: number;
      batch_lot: string;
      packaged_on_date: string;
      notes?: string;
    }>;
    auto_approve?: boolean;
    receiving_notes?: string;
  }) => axiosInstance.post(`/api/v2/purchase-orders/${id}/receive`, data),
}
```

**Estimated Time:** 15 minutes

---

### **Phase 3: Testing & Integration**

#### Task 3.1: Backend Testing
- Unit tests for V2 endpoint
- Integration tests with real database
- Test partial receiving scenarios
- Test error cases (invalid PO ID, status validation)

**Estimated Time:** 2 hours

---

#### Task 3.2: Frontend Testing
- Test modal opening/closing
- Test item quantity editing
- Test batch lot generation
- Test validation (can't receive more than ordered)
- Test success/error toast messages

**Estimated Time:** 1-2 hours

---

#### Task 3.3: End-to-End Testing
1. Create PO via ASN import
2. Approve PO
3. Receive full shipment
4. Verify inventory updated
5. Verify batches created
6. Check PO status changed to FULLY_RECEIVED

**Estimated Time:** 1 hour

---

## 📊 Implementation Summary

### **Total Estimated Time: 10-14 hours**

| Phase | Tasks | Time |
|-------|-------|------|
| **Phase 1: Backend V2** | Update DTOs, Implement endpoint | 1.5 hours |
| **Phase 2: Frontend UI** | Modal component, Page integration, API service | 5-7 hours |
| **Phase 3: Testing** | Unit, Integration, E2E | 4-5 hours |

### **Milestones**

1. ✅ **Day 1**: Backend V2 endpoint complete, DTOs updated
2. ✅ **Day 2**: Frontend modal component complete
3. ✅ **Day 3**: Integration complete, testing done
4. ✅ **Day 4**: Production deployment

---

## 🎯 Success Criteria

✅ **Backend:**
- V2 `/receive` endpoint works identically to V1
- Returns detailed batch and inventory update info
- Proper error handling and validation

✅ **Frontend:**
- Intuitive receiving modal with clear item-by-item editing
- Auto-generation of batch lot numbers
- Real-time validation and feedback
- Success/error handling with toast notifications

✅ **Integration:**
- End-to-end workflow works smoothly
- PO status transitions correctly
- Inventory and batches update properly
- No regressions in existing functionality

---

## ⏱️ Updated Time Estimates

| Phase | Tasks | Time |
|-------|-------|------|
| **Phase 1: Backend** | ✅ COMPLETE (V1 already has full DDD) | 0 hours |
| **Phase 2: Frontend UI** | Modal component, Page integration, API service | 5-7 hours |
| **Phase 3: Testing** | Integration, E2E | 2-3 hours |
| **TOTAL** | | **7-10 hours** |

**Time Saved:** ~2 hours (by not duplicating V2 endpoint)

---

## 📝 Summary of Changes

### What Was Completed:
1. ✅ Analyzed V1 vs V2 duplication (see `V1_V2_RECEIVE_ENDPOINT_ANALYSIS.md`)
2. ✅ Removed duplicate V2 receive endpoint (~120 LOC removed)
3. ✅ Removed V2-specific DTOs from `dto_mappers.py` (~50 LOC removed)
4. ✅ Verified V1 uses correct field name (`batch_lot`, not `batch_number`)
5. ✅ Updated implementation plan to use V1 only

### What's Next:
- Create `ReceivePurchaseOrderModal.tsx` component
- Add "Receive" button to PO list page
- Update API service to call V1 endpoint
- Test end-to-end workflow

### Key Decision:
**Use V1 endpoint only** - V1 already implements full DDD with `PurchaseOrderApplicationService` + `InventoryManagementService`. Creating V2 would duplicate code with no added value.

---

## 🚀 Ready to Implement Frontend!

Backend is complete (V1 endpoint). Frontend implementation ready to start!
