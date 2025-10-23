# Checkout Implementations Investigation Report

## Executive Summary
The backend has two distinct checkout implementations designed for different user types:
1. **Registered User Checkout** - Fully operational at `/api/orders/`
2. **Guest Checkout** - Implemented but NOT operational (router not registered)

## 1. Registered User Checkout (OPERATIONAL)

### Location
- **File**: `/src/Backend/api/order_endpoints.py`
- **Router Prefix**: `/api/orders`
- **Status**: ✅ WORKING - Router is registered in `api_server.py`

### Key Endpoints
- **POST `/api/orders/`** - Create order for authenticated users
- **GET `/api/orders/{order_id}`** - Get order details
- **PUT `/api/orders/{order_id}/status`** - Update order status
- **DELETE `/api/orders/{order_id}/cancel`** - Cancel order

### Features
1. **Authentication Required**
   - Validates user_id from JWT token or request body
   - Ensures payment method belongs to the authenticated user

2. **Cart Locking Mechanism**
   - Uses `CartLockService` to prevent concurrent modifications during checkout
   - 10-second timeout for cart lock acquisition
   - Prevents race conditions and double-orders

3. **Server-Side Price Recalculation**
   - `OrderPricingService` recalculates all prices server-side
   - Prevents price manipulation from frontend
   - Includes subtotal, tax, delivery fees, and discounts

4. **Inventory Validation & Reservation**
   - `InventoryValidator` checks stock availability
   - Reserves inventory during checkout
   - Auto-releases reservation if order creation fails
   - Returns detailed unavailable items list on failure

5. **Order Creation Flow**
   ```
   1. Acquire cart lock
   2. Validate payment method ownership
   3. Recalculate prices server-side
   4. Validate and reserve inventory
   5. Create order record
   6. Release cart lock
   7. (On failure: release inventory reservation)
   ```

### Request Structure
```typescript
{
  cart_session_id: UUID,
  user_id?: UUID,  // Optional if in JWT
  store_id: UUID,
  delivery_type: "delivery" | "pickup",
  delivery_address?: {
    street: string,
    city: string,
    province: string,
    postal_code: string
  },
  payment_method_id: string,  // UUID from user's saved methods
  tip_amount: number,
  special_instructions?: string,
  promo_code?: string
}
```

## 2. Guest Checkout (NOT OPERATIONAL)

### Location
- **File**: `/src/Backend/api/guest_checkout_endpoints.py`
- **Router Prefix**: `/api/checkout`
- **Status**: ❌ NOT WORKING - Router NOT registered in `api_server.py`
- **Added**: Commit `966b877` - "feat: Add production-ready authentication, checkout, and infrastructure enhancements"

### Key Endpoints (Would Be Available If Registered)
- **POST `/api/checkout/guest-user`** - Create/validate guest user
- **GET `/api/checkout/check-user/{email}`** - Check if email exists

### Intended Functionality

#### A. Guest User Creation (`/guest-user`)
Supports BOTH anonymous and existing user detection:

1. **New Guest User Flow**
   - Accepts email and optional phone
   - Creates passwordless user account
   - Generates temporary secure password
   - Sets `age_verified=true`, `email_verified=false`
   - Sends verification email with magic link
   - Returns: `{user_exists: false, user_id, access_token, refresh_token}`

2. **Existing User Detection**
   - Checks if email/phone already exists
   - Returns: `{user_exists: true, requires_login: true}`
   - Frontend should redirect to login page

3. **Hybrid Approach Benefits**
   - Allows true guest checkout (no password required)
   - Prevents duplicate accounts
   - Enables order history tracking
   - Supports future account upgrade (add password later)

#### B. Email Check (`/check-user/{email}`)
- Quick existence check without creating user
- Returns: `{exists: boolean, requires_login: boolean}`
- Used by frontend during registration to prevent duplicates

### Implementation Details
```python
# Key logic in guest_checkout_endpoints.py
async def create_guest_user(request: GuestUserRequest):
    # 1. Check if user exists
    existing_user = await check_existing_user(email, phone)
    if existing_user:
        return {
            "user_exists": True,
            "requires_login": True,
            "message": "User already exists. Please login."
        }

    # 2. Create passwordless guest account
    temp_password = generate_secure_password()
    user = await create_user(
        email=email,
        password=temp_password,  # Not shared with user
        age_verified=True,       # Skip age gate for checkout
        email_verified=False     # Require email verification
    )

    # 3. Send verification email
    await send_verification_email(user.id, email)

    # 4. Generate tokens for immediate checkout
    access_token = create_jwt_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "user_exists": False,
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }
```

## 3. Frontend Integration Status

### Current Implementation
The frontend (`/src/Frontend/weedgo-commerce/src/api/auth.ts`) is configured to use guest checkout:
```typescript
checkEmail: async (email: string) => {
  const response = await apiClient.get(
    `/api/checkout/check-user/${encodeURIComponent(email)}`
  );
  return {
    available: !response.data.exists,
    message: response.data.exists
      ? 'Account exists. Please sign in.'
      : undefined
  };
}
```

### Problem
- Frontend calls `/api/checkout/check-user/{email}` → **404 Not Found**
- Guest checkout router is NOT registered in `api_server.py`
- The endpoints exist in code but are never mounted to the application

## 4. Why Two Checkout Systems?

### Business Requirements
1. **Registered Users** (Regular customers)
   - Full account with saved payment methods
   - Order history and tracking
   - Loyalty programs and preferences
   - Requires password and full registration

2. **Guest Users** (One-time or new customers)
   - Quick checkout without registration
   - No password required initially
   - Creates account for order tracking
   - Can upgrade to full account later

### Technical Benefits
- **Conversion Optimization**: Reduces cart abandonment
- **Compliance**: Tracks all orders for regulatory requirements
- **User Experience**: Offers choice based on customer preference
- **Data Collection**: Captures emails for marketing (with consent)

## 5. Current Architecture Issues

### Issue 1: Unregistered Guest Checkout Router
```python
# In api_server.py - THIS IS MISSING:
from api.guest_checkout_endpoints import router as guest_checkout_router
app.include_router(guest_checkout_router)  # NOT PRESENT
```

### Issue 2: Path Mismatches
- Frontend expects: `/api/auth/me`
- Backend provides: `/api/v1/auth/customer/me`

### Issue 3: Inconsistent API Versioning
- Some endpoints: `/api/v1/...`
- Others: `/api/...`
- V2 DDD: `/api/v2/...`

## 6. How Guest Checkout Should Work (When Fixed)

### Complete Guest Checkout Flow
```
1. User adds items to cart
2. Proceeds to checkout without login
3. Enters email/phone
4. Frontend calls POST /api/checkout/guest-user
5. Backend either:
   a. Creates guest account → Continue checkout
   b. Detects existing user → Redirect to login
6. Guest user completes order
7. Receives order confirmation email
8. Can track order with email/order number
9. Can later add password to upgrade account
```

## 7. Recommendations (NOT IMPLEMENTED - Report Only)

### Immediate Fix
1. Register guest_checkout router in `api_server.py`
2. Test both checkout flows end-to-end

### Long-term Improvements
1. Unify API versioning strategy
2. Document API contracts
3. Add integration tests for both checkout flows
4. Consider consolidating to single checkout with user type parameter

## Conclusion

The system was designed with sophisticated dual checkout support:
- **Registered checkout** is fully operational
- **Guest checkout** is fully implemented but not connected

The guest checkout implementation is well-designed, supporting both anonymous users and existing user detection. It just needs to be registered in the API server to become operational.

**Git History Note**: Guest checkout was added in commit `966b877` as part of "production-ready authentication, checkout, and infrastructure enhancements" but was never registered in `api_server.py`, suggesting it may have been overlooked during deployment.