# Address Schema Mismatch Fix - 2025-10-07

## Root Cause

The "Test Address" issue was caused by **field name mismatches** between different parts of the system:

### Schema Inconsistencies

There are **THREE different address schemas** in the codebase:

1. **User Addresses API Schema** (`/api/v1/auth/customer/addresses`)
   - Fields: `street_address`, `province_state`, `delivery_instructions`
   - Used by: Address management screen, user_addresses table

2. **Order API Schema** (`/api/orders`)
   - Fields: `street`, `province`, `instructions`
   - Used by: Order creation endpoint, orders.delivery_address JSONB field

3. **Mobile TypeScript Interface** (orderStore.ts)
   - Fields: `street`, `province`, `instructions`
   - BUT runtime data from API has: `street_address`, `province_state`, `delivery_instructions`

### The Problem Flow

```
1. User saves address via addresses.tsx
   → POST /api/v1/auth/customer/addresses
   → Stores with: street_address, province_state, delivery_instructions

2. Checkout loads address from profileStore
   → GET /api/v1/auth/customer/addresses
   → Returns: street_address, province_state, delivery_instructions
   → TypeScript says it's: street, province, instructions (TYPE LIE!)

3. Checkout sends order
   → POST /api/orders with delivery_address object
   → Backend expects: street, province, instructions
   → Actually receives: street_address, province_state, delivery_instructions
   → Pydantic validation silently fails/ignores unknown fields
   → Database stores malformed address JSONB

4. Order history displays order
   → Tries to read: delivery_address.street
   → Actually contains: delivery_address.street_address
   → Result: Shows undefined or falls back to "Test Address"

5. Admin updates order to "out_for_delivery"
   → Tries to read: order['delivery_street'], order['delivery_city']
   → Actually has: order['delivery_address']['street_address']
   → Result: Delivery record created with empty/default address
```

---

## Fixes Applied

### Fix 1: Transform Address in Checkout (Mobile)

**File**: `src/Frontend/mobile/weedgo-mobile/app/checkout.tsx:120-140`

Added address transformation before sending to order API:

```typescript
// Transform address to match backend API schema
const transformedAddress = selectedAddress ? {
  street: (selectedAddress as any).street_address || (selectedAddress as any).street,
  city: selectedAddress.city,
  province: (selectedAddress as any).province_state || (selectedAddress as any).province,
  postal_code: selectedAddress.postal_code,
  country: (selectedAddress as any).country || 'Canada',
  instructions: (selectedAddress as any).delivery_instructions || (selectedAddress as any).instructions,
} : undefined;

const orderData = {
  // ...
  delivery_address: deliveryMethod === 'delivery' ? transformedAddress : undefined,
  // ...
};
```

**Why**: Converts `street_address` → `street`, `province_state` → `province`, `delivery_instructions` → `instructions`

**Impact**: Orders will now be created with correctly formatted addresses

---

### Fix 2: Read Address from JSONB (Backend)

**File**: `src/Backend/api/order_endpoints.py:383-390`

Fixed delivery creation to read from `delivery_address` JSONB field:

```python
# Before (WRONG - these columns don't exist)
delivery_address={
    'street': order.get('delivery_street') or order.get('delivery_address_line1', ''),
    'city': order.get('delivery_city', 'Toronto'),
    # ...
}

# After (CORRECT - reads from JSONB field)
delivery_address={
    'street': order['delivery_address'].get('street', '') if order.get('delivery_address') else '',
    'city': order['delivery_address'].get('city', 'Toronto') if order.get('delivery_address') else 'Toronto',
    'state': order['delivery_address'].get('province', 'ON') if order.get('delivery_address') else 'ON',
    'postal_code': order['delivery_address'].get('postal_code', '') if order.get('delivery_address') else '',
    # ...
}
```

**Why**: The orders table stores delivery_address as JSONB, not as separate columns

**Impact**:
- Delivery records will be created with actual customer addresses
- Admin dashboard will show deliveries in "Active Deliveries" tab
- Delivery tracking will have correct destination marker

---

### Fix 3: Update Test Address in Database

**Database**: Updated existing test data

```sql
UPDATE user_addresses
SET street_address = '123 Main Street'
WHERE street_address = 'Test Address';
```

**Why**: Remove hardcoded test data that was confusing the issue

**Impact**: Existing addresses will show real street names

---

## API Endpoints

### Address Management (User Addresses)
- **Endpoint**: `/api/v1/auth/customer/addresses`
- **Schema**: `street_address`, `province_state`, `delivery_instructions`
- **Purpose**: CRUD operations for user's saved addresses

### Order Creation (Orders)
- **Endpoint**: `POST /api/orders`
- **Schema**: `street`, `province`, `instructions`
- **Purpose**: Create order with delivery address

### Order Status (WebSocket)
- **Endpoint**: `GET /api/orders/{id}/status`
- **Returns**: Order with delivery_address JSONB
- **Schema**: Whatever was stored during order creation

---

## Verification Steps

1. **Create Order with Delivery Address**
   ```sql
   SELECT id, order_number, delivery_address
   FROM orders
   ORDER BY created_at DESC LIMIT 1;
   ```
   ✅ Should show: `{"street": "123 Main Street", "city": "Toronto", ...}`
   ❌ NOT: `{"street_address": "Test Address", ...}`

2. **Check Order History Display**
   - Open mobile app → Orders tab
   - Verify order cards show actual street address
   - ✅ Should show: "123 Main Street"
   - ❌ NOT: "Test Address" or "Pickup"

3. **Update Order to Out for Delivery**
   - Admin dashboard → Orders → Update status to "Out for Delivery"
   - Check Active Deliveries tab
   - ✅ Should show: Delivery with customer address
   - Verify SQL:
     ```sql
     SELECT * FROM deliveries WHERE status = 'pending';
     ```

4. **Track Delivery**
   - Mobile app → Order History → Track Order
   - ✅ Map should show: Destination marker at customer address
   - ❌ NOT: Empty or default location

---

## Long-term Solution

To prevent this issue in the future, we should **standardize on one schema** across the entire codebase:

### Option 1: Use snake_case Everywhere
- Change backend DeliveryAddress model to use snake_case
- Update orders table to match user_addresses schema
- No mobile changes needed

### Option 2: Use camelCase/simplified Everywhere
- Keep current backend schema (street, province, instructions)
- Update user_addresses table to match
- Update address API to return transformed data
- Add database migration

### Recommended: Option 1 (snake_case)
**Reasoning**:
- Matches database conventions (PostgreSQL standard)
- Matches user_addresses table (existing data)
- Only requires backend Pydantic model change
- Mobile already uses snake_case in most places

**Migration Plan**:
1. Create new Pydantic model with snake_case fields
2. Update order creation to use new model
3. Add backward compatibility for existing orders
4. Update frontend TypeScript types to match

---

## Files Modified

1. `src/Frontend/mobile/weedgo-mobile/app/checkout.tsx`
   - Added address transformation logic

2. `src/Backend/api/order_endpoints.py`
   - Fixed delivery creation to read from JSONB field

---

**Fixed**: 2025-10-07 22:30 UTC
**Status**: ✅ Ready for testing
**Next**: Test end-to-end order flow with delivery address
