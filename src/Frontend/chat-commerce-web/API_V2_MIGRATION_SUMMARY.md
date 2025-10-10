# Chat Commerce Web API V2 Migration Summary

## Overview
This document summarizes the migration of the Chat Commerce Web frontend from legacy/v1 to v2 DDD-based API endpoints.

## Files Being Migrated
1. `src/services/api.ts` - Main API service (~22 endpoints)

## Endpoint Mappings

### Chat API
| Current | New V2 | Status |
|---------|--------|--------|
| `/api/v1/chat/message` | `/api/v2/ai-conversation/messages` | ✅ Migrated |

### Voice API
| Current | New V2 | Status |
|---------|--------|--------|
| `/api/v1/auth/voice/voices` | `/api/v2/ai-conversation/voice/voices` | ✅ Migrated |
| `/api/v1/auth/voice/voice` | `/api/v2/ai-conversation/voice` | ✅ Migrated |
| `/api/v1/auth/voice/synthesize` | `/api/v2/ai-conversation/voice/synthesize` | ✅ Migrated |

### Authentication API (Customer)
| Current | New V2 | Status |
|---------|--------|--------|
| `/api/v1/auth/customer/login` | `/api/v2/identity-access/auth/customer/login` | ✅ Migrated |
| `/api/v1/auth/customer/register` | `/api/v2/identity-access/auth/customer/register` | ✅ Migrated |
| `/api/v1/auth/customer/logout` | `/api/v2/identity-access/auth/customer/logout` | ✅ Migrated |
| `/api/v1/auth/customer/verify` | `/api/v2/identity-access/auth/customer/validate` | ✅ Migrated |
| `/api/v1/auth/customer/me` | `/api/v2/identity-access/users/me` | ✅ Migrated |
| `/api/v1/auth/otp/send` | `/api/v2/identity-access/auth/otp/send` | ✅ Migrated |
| `/api/v1/auth/otp/verify` | `/api/v2/identity-access/auth/otp/verify` | ✅ Migrated |

### Admin/Model Management APIs
| Current | Status | Notes |
|---------|--------|-------|
| `/api/admin/models` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/agents` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/agents/:id/personalities` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/agents/:id/config` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/active-tools` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/model/status` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/model` | ⚠️ Preserved | Admin-specific, pending v2 implementation |
| `/api/admin/agents/:id/personality` | ⚠️ Preserved | Admin-specific, pending v2 implementation |

## Implementation Notes

### Breaking Changes
- None - backward compatibility maintained
- Old endpoints continue to work during migration period

### Testing Requirements
1. Customer login/register flow
2. OTP authentication
3. Chat message sending
4. Voice synthesis and selection
5. Admin model/agent management (preserved endpoints)

### Preserved Legacy Endpoints
The following endpoints are preserved as-is because they don't have v2 equivalents yet:
- Admin model management
- Agent configuration
- Active tools listing
- Model status monitoring

These will be migrated in a future phase when backend v2 implementations are available.

## Migration Statistics
- **Total Endpoints**: ~22
- **Migrated to V2**: ~11 (50%)
- **Preserved Legacy**: ~11 (50%)
- **Files Modified**: 1
- **Breaking Changes**: 0

## Next Steps
1. Test migrated endpoints
2. Monitor for any issues
3. Plan v2 implementations for remaining admin-specific endpoints
4. Gradual deprecation of v1 endpoints once all clients migrated

---

**Last Updated**: 2025-10-10
**Migration Status**: Complete (Phase 1 - Core Functionality)
