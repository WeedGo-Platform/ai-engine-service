# Mobile App API v2 Migration Mapping

This document maps all current API endpoints used in the WeedGo mobile app to their new v2 equivalents.

## Migration Status

- ⏳ **Status**: Ready to migrate
- 📱 **App**: WeedGo Mobile (React Native/Expo)
- 🎯 **Goal**: Migrate from legacy/v1 endpoints to v2 DDD-based endpoints
- 📊 **Total Endpoints**: 60+ endpoints across 8 service modules

## Service Modules Overview

| Module | Current File | Endpoints | V2 Context | Priority |
|--------|--------------|-----------|------------|----------|
| Authentication | `services/api/auth.ts` | 10 | Identity & Access | 🔴 High |
| Products | `services/api/products.ts` | 15 | Product Catalog | 🔴 High |
| Cart | `services/api/cart.ts` | 13 | Order Management | 🔴 High |
| Orders | `services/api/orders.ts` | 10 | Order Management | 🟡 Medium |
| Stores | `services/api/stores.ts` | 11 | Tenant Management | 🟡 Medium |
| Delivery | `services/api/delivery.ts` | 11 | Delivery Management | 🟡 Medium |
| Chat | `services/chat/api.ts` | 6 | AI Conversation | 🟢 Low |
| Profile | `services/api/profile.ts` | TBD | Identity & Access | 🟡 Medium |

---

## 1. Authentication Endpoints (Identity & Access Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/api/v1/auth/customer/check-phone` | POST | `/api/v2/identity-access/auth/check-phone` | POST | ✅ Available |
| `/api/v1/auth/customer/register` | POST | `/api/v2/identity-access/users` | POST | ✅ Available |
| `/api/v1/auth/customer/login` | POST | `/api/v2/identity-access/auth/login` | POST | ✅ Available |
| `/api/v1/auth/otp/verify` | POST | `/api/v2/identity-access/auth/verify-otp` | POST | ✅ Available |
| `/api/v1/auth/otp/resend` | POST | `/api/v2/identity-access/auth/resend-otp` | POST | ✅ Available |
| `/api/v1/auth/refresh` | POST | `/api/v2/identity-access/auth/refresh` | POST | ✅ Available |
| `/api/v1/auth/logout` | POST | `/api/v2/identity-access/auth/logout` | POST | ✅ Available |
| `/api/v1/auth/validate` | GET | `/api/v2/identity-access/auth/validate` | GET | ✅ Available |
| `/api/v1/auth/password-reset/request` | POST | `/api/v2/identity-access/auth/password-reset` | POST | ✅ Available |
| `/api/v1/auth/password-reset/verify` | POST | `/api/v2/identity-access/auth/verify-reset` | POST | ✅ Available |
| `/api/v1/auth/password-reset/reset` | POST | `/api/v2/identity-access/auth/reset-password` | POST | ✅ Available |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/auth.ts`
- `src/Frontend/mobile/weedgo-mobile/services/api/client.ts` (interceptor refresh endpoint)

---

## 2. Product Catalog Endpoints (Product Catalog Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/api/search/products` | GET | `/api/v2/products/search` | GET | ✅ Available |
| `/api/products/{id}/details` | GET | `/api/v2/products/{id}` | GET | ✅ Available |
| `/api/products/search` | GET | `/api/v2/products/search` | GET | ✅ Available |
| `/api/products/{id}/recommendations` | GET | `/api/v2/products/{id}/recommendations` | GET | ⚠️ TBD |
| `/api/products/{id}/reviews` | GET | `/api/v2/customer-engagement/reviews/product/{id}` | GET | ✅ Available |

**Query Parameters Supported:**
- `q` / `search` - Search query
- `store_id` - Filter by store
- `category` - Filter by category
- `brand` - Filter by brand
- `strain_type` - Filter by strain (indica, sativa, hybrid, cbd)
- `thc_min`, `thc_max` - THC range
- `cbd_min`, `cbd_max` - CBD range
- `price_min`, `price_max` - Price range
- `limit`, `offset` - Pagination

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/products.ts`

---

## 3. Cart Endpoints (Order Management Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/api/cart/` | GET | `/api/v2/orders/cart` | GET | ✅ Available |
| `/api/cart/items` | POST | `/api/v2/orders/cart/items` | POST | ✅ Available |
| `/api/cart/items/{id}` | PUT | `/api/v2/orders/cart/items/{id}` | PUT | ✅ Available |
| `/api/cart/items/{id}` | DELETE | `/api/v2/orders/cart/items/{id}` | DELETE | ✅ Available |
| `/api/cart/` | DELETE | `/api/v2/orders/cart` | DELETE | ✅ Available |
| `/api/cart/promo` | POST | `/api/v2/pricing-promotions/apply` | POST | ✅ Available |
| `/api/cart/promo` | DELETE | `/api/v2/pricing-promotions/remove` | DELETE | ✅ Available |
| `/api/cart/validate` | POST | `/api/v2/orders/cart/validate` | POST | ✅ Available |
| `/api/cart/merge` | POST | `/api/v2/orders/cart/merge` | POST | ✅ Available |
| `/api/cart/delivery-fee` | POST | `/api/v2/delivery/calculate-fee` | POST | ✅ Available |
| `/api/cart/delivery-method` | POST | `/api/v2/orders/cart/delivery-method` | POST | ✅ Available |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/cart.ts`

---

## 4. Order Management Endpoints (Order Management Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/orders` | POST | `/api/v2/orders` | POST | ✅ Available |
| `/orders` | GET | `/api/v2/orders` | GET | ✅ Available |
| `/orders/{id}` | GET | `/api/v2/orders/{id}` | GET | ✅ Available |
| `/orders/{id}/cancel` | POST | `/api/v2/orders/{id}/cancel` | POST | ✅ Available |
| `/orders/{id}/track` | GET | `/api/v2/delivery/track/{order_id}` | GET | ✅ Available |
| `/orders/{id}/rate` | POST | `/api/v2/customer-engagement/reviews` | POST | ✅ Available |
| `/products/{id}` | GET | `/api/v2/products/{id}` | GET | ✅ Available |
| `/orders/validate` | POST | `/api/v2/orders/validate` | POST | ✅ Available |
| `/orders/promo` | POST | `/api/v2/pricing-promotions/validate` | POST | ✅ Available |
| `/orders/{id}/receipt` | GET | `/api/v2/orders/{id}/receipt` | GET | ✅ Available |
| `/orders/{id}/report-issue` | POST | `/api/v2/orders/{id}/issues` | POST | ⚠️ TBD |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/orders.ts`

---

## 5. Store/Tenant Endpoints (Tenant Management Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/api/stores/tenant/{id}` | GET | `/api/v2/tenants/{id}/stores` | GET | ✅ Available |
| `/api/stores/{id}` | GET | `/api/v2/tenants/stores/{id}` | GET | ✅ Available |
| `/api/stores/{id}/hours` | GET | `/api/v2/tenants/stores/{id}/hours` | GET | ⚠️ TBD |
| `/api/stores/{id}/availability` | GET | `/api/v2/tenants/stores/{id}/availability` | GET | ⚠️ TBD |
| `/api/stores/nearby` | GET | `/api/v2/tenants/stores/nearby` | GET | ⚠️ TBD |
| `/api/stores/nearest` | GET | `/api/v2/tenants/stores/nearest` | GET | ⚠️ TBD |
| `/api/stores/by-postal` | GET | `/api/v2/tenants/stores/by-postal-code` | GET | ⚠️ TBD |
| `/api/stores/{id}/delivery-check` | GET | `/api/v2/delivery/zones/check` | GET | ✅ Available |
| `/api/stores/{id}/delivery-zones` | GET | `/api/v2/delivery/zones/store/{id}` | GET | ✅ Available |
| `/api/stores/{id}/promotions` | GET | `/api/v2/pricing-promotions/store/{id}` | GET | ✅ Available |
| `/api/stores/{id}/reviews` | GET | `/api/v2/customer-engagement/reviews/store/{id}` | GET | ✅ Available |
| `/api/stores/{id}/reviews` | POST | `/api/v2/customer-engagement/reviews` | POST | ✅ Available |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/stores.ts`

---

## 6. Delivery Endpoints (Delivery Management Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/delivery/calculate-fee` | POST | `/api/v2/delivery/calculate-fee` | POST | ✅ Available |
| `/delivery/zones/{store_id}` | GET | `/api/v2/delivery/zones/store/{store_id}` | GET | ✅ Available |
| `/delivery/check-availability` | POST | `/api/v2/delivery/zones/check` | POST | ✅ Available |
| `/delivery/estimated-time` | POST | `/api/v2/delivery/estimate` | POST | ✅ Available |
| `/delivery/track/{order_id}` | GET | `/api/v2/delivery/track/{order_id}` | GET | ✅ Available |
| `/delivery/instruction-templates` | GET | `/api/v2/delivery/instructions/templates` | GET | ⚠️ TBD |
| `/delivery/report-issue/{order_id}` | POST | `/api/v2/delivery/{delivery_id}/issues` | POST | ⚠️ TBD |
| `/delivery/rate/{order_id}` | POST | `/api/v2/customer-engagement/reviews` | POST | ✅ Available |
| `/delivery/history` | GET | `/api/v2/delivery/history` | GET | ✅ Available |
| `/delivery/schedule` | POST | `/api/v2/delivery/schedule` | POST | ✅ Available |
| `/delivery/schedule/{id}` | DELETE | `/api/v2/delivery/schedule/{id}` | DELETE | ✅ Available |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/api/delivery.ts`

---

## 7. Chat/AI Conversation Endpoints (AI Conversation Context)

### Current → V2 Mapping

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| `/chat/session` | POST | `/api/v2/ai-conversation/sessions` | POST | ✅ Available |
| `/chat/session/{id}` | GET | `/api/v2/ai-conversation/sessions/{id}` | GET | ✅ Available |
| `/chat/message` | POST | `/api/v2/ai-conversation/messages` | POST | ✅ Available |
| `/chat/session/{id}` | DELETE | `/api/v2/ai-conversation/sessions/{id}` | DELETE | ✅ Available |
| `/chat/history/{user_id}` | GET | `/api/v2/ai-conversation/history/{user_id}` | GET | ✅ Available |
| `/chat/sessions` | GET | `/api/v2/ai-conversation/sessions` | GET | ✅ Available |
| **WebSocket** | | | | |
| `/api/v1/chat/ws` | WS | `/api/v2/ai-conversation/ws` | WS | ⚠️ TBD |

**Files to Update:**
- `src/Frontend/mobile/weedgo-mobile/services/chat/api.ts`
- `src/Frontend/mobile/weedgo-mobile/services/chat/websocket.ts`
- `src/Frontend/mobile/weedgo-mobile/config/api.ts` (update WS_URL)

---

## 8. Additional Endpoints Needed

### Profile Management (Identity & Access Context)

| Current Endpoint | Method | New V2 Endpoint | Method | Status |
|-----------------|--------|-----------------|---------|--------|
| N/A | GET | `/api/v2/identity-access/users/{id}/profile` | GET | ✅ Available |
| N/A | PUT | `/api/v2/identity-access/users/{id}/profile` | PUT | ✅ Available |
| N/A | GET | `/api/v2/identity-access/users/{id}/addresses` | GET | ✅ Available |
| N/A | POST | `/api/v2/identity-access/users/{id}/addresses` | POST | ✅ Available |
| N/A | PUT | `/api/v2/identity-access/users/{id}/addresses/{addr_id}` | PUT | ✅ Available |
| N/A | DELETE | `/api/v2/identity-access/users/{id}/addresses/{addr_id}` | DELETE | ✅ Available |

---

## Migration Strategy

### Phase 1: Authentication (🔴 Critical)
1. Update `services/api/auth.ts` to use v2 endpoints
2. Update `services/api/client.ts` refresh token endpoint
3. Test login, registration, OTP flows
4. Test token refresh interceptor

### Phase 2: Core Shopping Flow (🔴 High Priority)
1. Update `services/api/products.ts` → product search, details
2. Update `services/api/cart.ts` → cart operations
3. Update `services/api/orders.ts` → order creation, tracking
4. Test complete shopping flow: browse → add to cart → checkout

### Phase 3: Store & Delivery (🟡 Medium Priority)
1. Update `services/api/stores.ts` → store selection, details
2. Update `services/api/delivery.ts` → delivery fee, tracking
3. Test store selection and delivery flow

### Phase 4: Chat & Engagement (🟢 Low Priority)
1. Update `services/chat/api.ts` → chat sessions, messages
2. Update WebSocket connection URL
3. Test chat functionality

### Phase 5: Profile & Addresses
1. Create new `services/api/profile.ts` with v2 endpoints
2. Create new `services/api/addresses.ts` with v2 endpoints
3. Test profile editing and address management

---

## Implementation Checklist

- [ ] Create feature branch: `feature/mobile-api-v2-migration`
- [ ] Update API client configuration
  - [ ] Add v2 base path constant
  - [ ] Update interceptors if needed
- [ ] Migrate Authentication service
  - [ ] Update all auth endpoints
  - [ ] Update client refresh token logic
  - [ ] Test all auth flows
- [ ] Migrate Products service
  - [ ] Update search endpoint
  - [ ] Update product details endpoint
  - [ ] Test product browsing
- [ ] Migrate Cart service
  - [ ] Update all cart endpoints
  - [ ] Test add/remove/update cart
- [ ] Migrate Orders service
  - [ ] Update order creation
  - [ ] Update order tracking
  - [ ] Test order flow
- [ ] Migrate Stores service
  - [ ] Update store endpoints
  - [ ] Test store selection
- [ ] Migrate Delivery service
  - [ ] Update delivery endpoints
  - [ ] Test delivery tracking
- [ ] Migrate Chat service
  - [ ] Update chat endpoints
  - [ ] Update WebSocket URL
  - [ ] Test chat functionality
- [ ] Create Profile service (new)
  - [ ] Implement profile endpoints
  - [ ] Test profile management
- [ ] Create Addresses service (new)
  - [ ] Implement address endpoints
  - [ ] Test address management
- [ ] Update types if needed
  - [ ] Review DTOs match v2 responses
  - [ ] Update any changed field names
- [ ] Test complete app flows
  - [ ] Registration → Login
  - [ ] Browse → Add to Cart → Checkout
  - [ ] Order Tracking
  - [ ] Profile Management
- [ ] Update documentation
  - [ ] Update API documentation
  - [ ] Update developer onboarding docs

---

## Breaking Changes to Watch For

### Response Structure Changes
- V2 uses standardized DTOs with consistent naming
- Some field names may differ (e.g., `snake_case` vs `camelCase`)
- Error response format may be standardized

### Authentication
- Token format should remain the same (JWT)
- Refresh token flow remains similar
- Session management should be compatible

### Pagination
- V2 may use different pagination structure
- Check `limit`, `offset`, `total`, `page` fields

### Status Codes
- V2 follows RESTful conventions more strictly
- 200 (OK), 201 (Created), 204 (No Content)
- 400 (Bad Request), 401 (Unauthorized), 404 (Not Found)

---

## Testing Strategy

### Unit Tests
- Test each service module independently
- Mock API responses
- Verify request payloads

### Integration Tests
- Test complete user flows
- Test error handling
- Test token refresh

### Manual Testing
- Test on iOS simulator
- Test on Android emulator
- Test on physical devices
- Test offline scenarios
- Test poor network conditions

---

## Rollback Plan

If migration causes issues:

1. **Quick Rollback**: Feature flag to switch between v1 and v2
   ```typescript
   const USE_V2_API = process.env.EXPO_PUBLIC_USE_V2_API === 'true';
   const endpoint = USE_V2_API ? '/api/v2/products' : '/api/products';
   ```

2. **Gradual Migration**: Migrate one service at a time
   - Each service can be independently reverted
   - Monitor error rates per service

3. **Backend Compatibility**: Legacy endpoints remain available
   - No breaking changes on backend
   - v1 endpoints continue working during migration

---

## Notes

- All v2 endpoints require authentication unless explicitly marked as public
- Tenant ID and Store ID are passed via headers (`X-Tenant-ID`, `X-Store-ID`)
- Session ID for cart is passed via header (`X-Session-ID`)
- WebSocket connections need updated URLs and authentication strategy
- Some endpoints marked ⚠️ TBD may need backend implementation

---

**Last Updated**: 2025-10-10
**Migration Owner**: Development Team
**Target Completion**: TBD
