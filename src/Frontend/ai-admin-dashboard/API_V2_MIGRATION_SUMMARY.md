# AI Admin Dashboard API V2 Migration Summary

## Overview
This document summarizes the migration of the AI Admin Dashboard from legacy/v1 to v2 DDD-based API endpoints.

## Files Being Migrated
1. `src/services/api.ts` - Main API service (~50 endpoints)
2. `src/services/authService.ts` - Authentication service (~8 endpoints)
3. `src/services/communicationService.ts` - Communication settings (~3 endpoints)

## Endpoint Mappings

### Products API
| Current | New V2 | Status |
|---------|--------|--------|
| `/search/products` | `/api/v2/products/search` | ✅ Migrated |
| `/search/products/:id` | `/api/v2/products/:id` | ✅ Migrated |

### Inventory API
| Current | New V2 | Status |
|---------|--------|--------|
| `/inventory/search` | `/api/v2/inventory/search` | ✅ Migrated |
| `/inventory/status/:sku` | `/api/v2/inventory/sku/:sku` | ✅ Migrated |
| `/inventory/update` | `/api/v2/inventory/adjust` | ✅ Migrated |
| `/inventory/:id` | `/api/v2/inventory/:id` | ✅ Migrated |
| `/inventory/low-stock` | `/api/v2/inventory/low-stock` | ✅ Migrated |
| `/inventory/value-report` | `/api/v2/inventory/value-report` | ✅ Migrated |
| `/inventory/suppliers` | `/api/v2/purchase-orders/suppliers` | ✅ Migrated |
| `/inventory/check` | `/api/v2/inventory/check` | ✅ Migrated |

### Orders API
| Current | New V2 | Status |
|---------|--------|--------|
| `/orders/` | `/api/v2/orders` | ✅ Migrated |
| `/orders/:id` | `/api/v2/orders/:id` | ✅ Migrated |
| `/orders/by-number/:number` | `/api/v2/orders/by-number/:number` | ✅ Migrated |
| `/orders/create` | `/api/v2/orders` | ✅ Migrated |
| `/orders/:id/status` | `/api/v2/orders/:id/status` | ✅ Migrated |
| `/orders/:id/cancel` | `/api/v2/orders/:id/cancel` | ✅ Migrated |
| `/orders/:id/history` | `/api/v2/orders/:id/history` | ✅ Migrated |
| `/orders/analytics/summary` | `/api/v2/orders/analytics/summary` | ✅ Migrated |

### Customers API
| Current | New V2 | Status |
|---------|--------|--------|
| `/customers/search` | `/api/v2/identity-access/customers/search` | ✅ Migrated |
| `/customers/:id` | `/api/v2/identity-access/customers/:id` | ✅ Migrated |
| `/customers/:id/orders` | `/api/v2/orders/customer/:id` | ✅ Migrated |
| `/customers/:id/loyalty` | `/api/v2/identity-access/customers/:id/loyalty` | ✅ Migrated |

### Purchase Orders API
| Current | New V2 | Status |
|---------|--------|--------|
| `/inventory/purchase-orders` | `/api/v2/purchase-orders` | ✅ Migrated |
| `/inventory/purchase-orders/:id/receive` | `/api/v2/purchase-orders/:id/receive` | ✅ Migrated |

### Cart API (Admin Kiosk)
| Current | New V2 | Status |
|---------|--------|--------|
| `/cart/` | `/api/v2/orders/cart` | ✅ Migrated |
| `/cart/items` | `/api/v2/orders/cart/items` | ✅ Migrated |
| `/cart/items/:id` | `/api/v2/orders/cart/items/:id` | ✅ Migrated |
| `/cart/discount` | `/api/v2/pricing-promotions/apply` | ✅ Migrated |
| `/cart/delivery-address` | `/api/v2/orders/cart/delivery-address` | ✅ Migrated |
| `/cart/validate` | `/api/v2/orders/cart/validate` | ✅ Migrated |
| `/cart/merge` | `/api/v2/orders/cart/merge` | ✅ Migrated |

### Authentication API
| Current | New V2 | Status |
|---------|--------|--------|
| `/auth/login` | `/api/v2/identity-access/auth/login` | ✅ Migrated |
| `/auth/logout` | `/api/v2/identity-access/auth/logout` | ✅ Migrated |
| `/auth/refresh` | `/api/v2/identity-access/auth/refresh` | ✅ Migrated |
| `/auth/me` | `/api/v2/identity-access/users/me` | ✅ Migrated |
| `/auth/verify` | `/api/v2/identity-access/auth/validate` | ✅ Migrated |
| `/api/v1/auth/admin/create-admin` | `/api/v2/identity-access/users` | ✅ Migrated |
| `/api/v1/auth/admin/change-password` | `/api/v2/identity-access/users/change-password` | ✅ Migrated |

### Communication API
| Current | New V2 | Status |
|---------|--------|--------|
| `/api/v1/tenants/:id/communication-settings` | `/api/v2/tenants/:id/communication-settings` | ✅ Migrated |
| `/api/v1/tenants/:id/communication-settings/validate` | `/api/v2/tenants/:id/communication-settings/validate` | ✅ Migrated |

### Analytics & Admin APIs
| Current | Status | Notes |
|---------|--------|-------|
| `/admin/dashboard/stats` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/stats` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/metrics` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/api/analytics` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/sessions` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/system/health` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/admin/models` | ⚠️ Preserved | AI model management, pending v2 implementation |
| `/admin/agents` | ⚠️ Preserved | AI agent management, pending v2 implementation |
| `/admin/tools` | ⚠️ Preserved | AI tools management, pending v2 implementation |
| `/admin/tools/test` | ⚠️ Preserved | AI tools testing, pending v2 implementation |
| `/voice/*` | ⚠️ Preserved | Voice API, pending v2 implementation |
| `/admin/stores/:id/devices/*` | ⚠️ Preserved | Device management, pending v2 implementation |

## Implementation Notes

### Breaking Changes
- None - backward compatibility maintained
- Old endpoints continue to work during migration period

### Configuration Updates
- `authConfig.endpoints` updated to v2 paths
- Token refresh logic remains unchanged
- Authorization headers remain compatible

### Testing Requirements
1. Admin login flow
2. Product management (CRUD)
3. Inventory management
4. Order management
5. Customer lookup
6. Purchase orders
7. Kiosk cart functionality
8. Communication settings

### Preserved Legacy Endpoints
The following endpoints are preserved as-is because they don't have v2 equivalents yet:
- Admin analytics and statistics
- System health monitoring
- AI model/agent/tools management
- Voice API
- Device management

These will be migrated in a future phase when backend v2 implementations are available.

## Migration Statistics
- **Total Endpoints**: ~60
- **Migrated to V2**: ~40 (67%)
- **Preserved Legacy**: ~20 (33%)
- **Files Modified**: 3
- **Breaking Changes**: 0

## Next Steps
1. Test migrated endpoints
2. Monitor for any issues
3. Plan v2 implementations for remaining admin-specific endpoints
4. Gradual deprecation of v1 endpoints once all clients migrated

---

**Last Updated**: 2025-10-10
**Migration Status**: Complete (Phase 1 - Core Functionality)
