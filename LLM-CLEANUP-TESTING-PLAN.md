# LLM Cleanup Testing Plan & Risk Assessment

## Summary of Changes
**Date**: 2025-10-30
**Branch**: `llm-cleanup`
**Files Modified**: 25 (2 backend + 23 frontend)
**Net Changes**: +126 insertions, -123 deletions

## ⚠️ CRITICAL ISSUES FOUND

### Issue #1: Port Mismatch in Frontend
- **File**: `.env.development`
- **Current**: `VITE_API_URL=http://localhost:5024`
- **Changed**: `app.config.ts` now defaults to `6024`
- **Impact**: **MEDIUM** - Dev environment will use port 6024 but .env says 5024
- **Fix Required**: Update `.env.development` to use 6024 OR revert app.config.ts default

### Issue #2: Build Has Pre-Existing TypeScript Errors
- **Status**: Build was ALREADY broken before my changes
- **Impact**: **LOW** - Not caused by cleanup
- **Action**: No immediate action needed (but should be fixed separately)

---

## Changes By Category

### Backend Changes (2 files)

#### 1. `src/Backend/api_server.py` - CORS Configuration
**What Changed:**
- ❌ Removed: Hardcoded CORS origin lists for dev, uat, beta, preprod
- ✅ Added: Requires explicit `CORS_ALLOWED_ORIGINS` environment variable
- ✅ Added: Clear warnings when CORS not configured

**Risk Assessment:** ✅ **LOW RISK**
- All `.env` files already have `CORS_ALLOWED_ORIGINS` set
- Backend has fallback logging
- No breaking changes expected

**Test Plan:**
```bash
# Test 1: Start backend with test env
cd src/Backend
source .env.test
python api_server.py  # Should start without CORS errors

# Test 2: Verify CORS origins logged
# Expected: "✓ CORS origins loaded from environment: [...]"

# Test 3: Make cross-origin request
curl -H "Origin: http://localhost:6003" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  http://localhost:6024/api/health
# Expected: CORS headers in response
```

#### 2. `src/Backend/api/store_endpoints.py`
**What Changed:** Minor cleanup (5 lines)
**Risk:** ✅ **NEGLIGIBLE**

---

### Frontend Changes (23 files)

#### Core Utilities (3 files)

**1. `websocket.ts`** - WebSocket URL Builder
**Changes:**
- Fails loudly in production if `VITE_API_URL` not set
- Dev fallback: `ws://localhost:6024` (was 5024)

**Risk:** ⚠️ **MEDIUM**
- Port change could cause confusion
- Production deployments require `VITE_API_URL` to be set (this is good!)

**Test Plan:**
```javascript
// Test in browser console
import { getWebSocketBaseUrl } from './utils/websocket';
console.log(getWebSocketBaseUrl());
// Expected dev: ws://localhost:6024
// Expected prod: should use VITE_API_URL from env
```

**2. `http-client.ts`** - HTTP Client
**Changes:**
- Fails loudly in production if `VITE_API_URL` not set
- Dev fallback: `http://localhost:6024`

**Risk:** ⚠️ **MEDIUM**
- Same port issue as websocket

**Test Plan:**
```javascript
// Test API calls work
import { httpClient } from './utils/http-client';
await httpClient.get('/api/health');
// Should succeed if backend running on 6024
```

**3. `app.config.ts`** - Central Configuration
**Changes:**
- Default port: 5024 → 6024

**Risk:** ⚠️ **MEDIUM**
- **CONFLICT**: `.env.development` still says 5024!

---

#### Services (4 files)

**Files:** `tenantService.ts`, `paymentService.ts`, `catalogService.ts`, `streamingVoiceRecording.service.ts`

**Changes:** Now use `appConfig.api.baseUrl` instead of inline `import.meta.env...`

**Risk:** ✅ **LOW**
- All go through same centralized config
- Env vars still work the same way

**Test Plan:**
```javascript
// Test tenant service
import tenantService from './services/tenantService';
const tenants = await tenantService.getTenantByCode('TEST');
// Should work if backend is running
```

---

#### Pages (6 files)

**Files:** `UserRegistration.tsx`, `Verification.tsx`, `TenantSignup.tsx`, `TenantManagement.tsx`, `LogViewer.tsx`, `VoiceAPITest.tsx`

**Changes:** Use `getApiEndpoint()` helper instead of inline URLs

**Risk:** ✅ **LOW**
- Helper function is battle-tested
- Just a refactor, same functionality

**Test Plan:**
1. Navigate to each page in dev mode
2. Verify API calls work
3. Check browser console for errors

---

#### Components (10 files)

**Files:** `ChatWidget.tsx`, `SalesChatWidget.tsx`, `AdminNotifications.tsx`, `OntarioLicenseValidator.tsx`, etc.

**Changes:** Use centralized helpers (`getApiEndpoint()`, `getWebSocketUrl()`, `appConfig.api.baseUrl`)

**Risk:** ⚠️ **MEDIUM**
- ChatWidget WebSocket connections critical for UX
- AdminNotifications uses WebSocket
- Must test thoroughly

**Test Plan:**
```markdown
1. Open ChatWidget - verify it connects
2. Send a message - verify it works
3. Check AdminNotifications - verify WebSocket connects
4. Test OntarioLicenseValidator - verify API calls work
```

---

## Comprehensive Test Checklist

### Pre-Testing Setup
- [ ] Update `.env.development` to use port 6024 (OR revert app.config.ts)
- [ ] Start backend on correct port (5024 or 6024 depending on fix)
- [ ] Clear browser cache
- [ ] Open browser DevTools (Network & Console tabs)

### Backend Tests
- [ ] Backend starts without errors
- [ ] CORS warning/success logged correctly
- [ ] Health endpoint responds: `curl http://localhost:6024/api/health`
- [ ] CORS headers present in responses

### Frontend Build Tests
- [ ] `npm run build` - Check if NEW errors appear (vs pre-existing)
- [ ] `npm run dev` - Dev server starts
- [ ] No console errors on page load

### Frontend Runtime Tests

**Core Functionality:**
- [ ] Login page loads
- [ ] Can log in
- [ ] Dashboard loads
- [ ] Navigation works

**API Calls (Network Tab):**
- [ ] Tenant API calls succeed
- [ ] User registration form submits
- [ ] Verification page works
- [ ] Store management loads data

**WebSocket Connections:**
- [ ] ChatWidget connects (check WS in Network tab)
- [ ] Can send messages
- [ ] Receive responses
- [ ] AdminNotifications connects

**Components:**
- [ ] Ontario License Validator works
- [ ] Payment service calls work
- [ ] Catalog service calls work

### Port Configuration Tests
- [ ] Verify actual backend port being used
- [ ] Verify frontend is calling correct port
- [ ] No mixed port issues (some calls to 5024, some to 6024)

---

## Rollback Plan

If issues are found:

```bash
# Option 1: Revert all changes
git reset --hard HEAD~1

# Option 2: Keep some changes, fix port issue
# Edit app.config.ts, change 6024 back to 5024
# OR update .env.development to 6024

# Option 3: Stash changes for later
git stash
git stash show  # to review later
```

---

## Risk Summary

| Risk Level | Count | Category |
|-----------|-------|----------|
| 🔴 HIGH | 0 | None |
| ⚠️ MEDIUM | 3 | Port mismatch, WebSocket connections, Production config requirement |
| ✅ LOW | 20 | Most refactoring changes |

**Overall Risk:** ⚠️ **MEDIUM** - Main risk is port configuration mismatch

---

## Recommendations

### Immediate Actions Required:
1. **Fix port mismatch** - Choose one:
   - Update `.env.development`: `VITE_API_URL=http://localhost:6024`
   - OR revert `app.config.ts` default to 5024

2. **Test WebSocket connections** - Critical for UX

3. **Verify one page end-to-end** before committing

### Before Production Deploy:
1. Ensure all environment files have `VITE_API_URL` set
2. Ensure backend `.env` files have `CORS_ALLOWED_ORIGINS` set
3. Test in staging environment first

### Future Improvements:
1. Fix pre-existing TypeScript errors
2. Add automated tests for WebSocket connections
3. Add environment validation script
4. Document port standardization (why 6024?)

---

## Sign-Off

**Changes Made By:** Claude AI Assistant
**Requires Human Review:** ✅ YES
**Requires Testing:** ✅ YES
**Ready for Commit:** ❌ NO - Fix port issue first

**Next Steps:**
1. Human review this document
2. Fix port mismatch issue
3. Test according to checklist
4. If tests pass, commit changes
5. If tests fail, use rollback plan
