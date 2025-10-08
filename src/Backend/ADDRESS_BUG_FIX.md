# Address Bug Fix

**Date**: October 6, 2025
**Status**: ✅ FIXED

---

## Problem

Mobile app checkout failed when users tried to add delivery addresses.

**Root Cause**: Field name mismatch
- Frontend sent: `street`, `province`, `unit`, `instructions`, `name`, `type`
- Backend expected: `street_address`, `province_state`, `unit_number`, `delivery_instructions`, `label`, `address_type`

---

## Solution

**Updated frontend to match backend field names exactly.**

### Files Changed

#### 1. Frontend Interface
**File**: `src/Frontend/mobile/weedgo-mobile/services/api/addresses.ts`

Updated `DeliveryAddress` interface to use exact backend field names:
```typescript
export interface DeliveryAddress {
  id?: string;
  label?: string;                    // was: name
  street_address: string;            // was: street
  city: string;
  province_state: string;            // was: province
  postal_code: string;
  unit_number?: string;              // was: unit
  delivery_instructions?: string;    // was: instructions
  is_default?: boolean;
  address_type: 'delivery' | 'billing';  // was: type
  phone_number?: string;
  country?: string;
}
```

#### 2. Frontend Component
**File**: `src/Frontend/mobile/weedgo-mobile/components/checkout/AddressSection.tsx`

Updated all field references to match backend:
- `newAddress.street` → `newAddress.street_address`
- `newAddress.province` → `newAddress.province_state`
- `newAddress.unit` → `newAddress.unit_number`
- `newAddress.instructions` → `newAddress.delivery_instructions`

#### 3. Backend (Reverted)
**File**: `src/Backend/api/customer_auth.py`

Removed unnecessary field mapping complexity. Backend now uses simple Pydantic validation:
```python
@router.post("/addresses")
async def create_user_address(
    address: AddressRequest,
    current_user: Dict = Depends(get_current_user_flexible)
):
    """Create a new address for the current user"""
    # Direct Pydantic validation - no mapping needed
```

---

## Field Mapping Reference

| Frontend Field | Backend Field | Changed |
|----------------|---------------|---------|
| `label` | `label` | ✅ Renamed from `name` |
| `street_address` | `street_address` | ✅ Renamed from `street` |
| `province_state` | `province_state` | ✅ Renamed from `province` |
| `unit_number` | `unit_number` | ✅ Renamed from `unit` |
| `delivery_instructions` | `delivery_instructions` | ✅ Renamed from `instructions` |
| `address_type` | `address_type` | ✅ Renamed from `type` |
| `city` | `city` | No change |
| `postal_code` | `postal_code` | No change |
| `phone_number` | `phone_number` | No change |
| `is_default` | `is_default` | No change |

---

## Status

✅ **Frontend updated to match backend exactly**
✅ **No unnecessary mapping code**
✅ **No backwards compatibility overhead**
✅ **Clean, simple, direct**

---

**Fix Type**: Frontend field name alignment
**Complexity**: Low
**Resource Usage**: Minimal
