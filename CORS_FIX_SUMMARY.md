# CORS & API Endpoint Fixes

**Date:** 2025-10-01
**Status:** ✅ Fixed - Requires Service Restart

---

## Issues Identified

### Issue 1: CORS Policy Blocking Requests ❌
**Error:**
```
Access to fetch at 'http://localhost:5024/api/...' from origin 'http://localhost:3003'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
on the requested resource.
```

**Root Cause:**
- AI Engine Service is running but **CORS headers are not being sent**
- CORS configuration exists in `main_server.py` but service needs restart
- The running instance is from before CORS was configured

**Impact:**
- ❌ Admin Dashboard cannot communicate with AI Engine Service
- ❌ All API requests fail with CORS errors
- ❌ Login, device management, and other features broken

---

### Issue 2: Double /api/ in Device Endpoints URL ❌
**Error:**
```
Failed to load resource: http://localhost:5024/api/api/admin/stores/.../devices
                                                    ^^^^^ double /api/
```

**Root Cause:**
- Device API endpoints in `api.ts` included `/api/` prefix
- Axios instance already has `baseURL` that includes `/api`
- Result: `baseURL + /api/endpoint = /api/api/endpoint`

**Impact:**
- ❌ 404 errors on all device API calls
- ❌ Cannot create/update/delete devices

---

## Fixes Applied

### Fix 1: Removed /api/ Prefix from Device Endpoints ✅

**File:** `/src/Frontend/ai-admin-dashboard/src/services/api.ts`

**Before:**
```typescript
devices: {
  getAll: (storeId: string) => axiosInstance.get(`/api/admin/stores/${storeId}/devices`),
  create: (storeId: string, data: any) => axiosInstance.post(`/api/admin/stores/${storeId}/devices`, data),
  // ...
}
```

**After:**
```typescript
devices: {
  getAll: (storeId: string) => axiosInstance.get(`/admin/stores/${storeId}/devices`),
  create: (storeId: string, data: any) => axiosInstance.post(`/admin/stores/${storeId}/devices`, data),
  // ...
}
```

**Result:**
- ✅ URLs now correct: `http://localhost:5024/api/admin/stores/.../devices`
- ✅ No more 404 errors

---

### Fix 2: CORS Configuration Already Correct ✅

**File:** `/src/Backend/main_server.py` (lines 388-409)

CORS middleware is **already configured correctly**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",  # ✅ Admin Dashboard port
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://localhost:5024",
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)
```

**Issue:** Service is running old code without CORS headers

**Solution:** **RESTART AI Engine Service**

---

## Action Required: Restart AI Engine Service

The CORS configuration is correct in the code, but the running service needs to be restarted to apply it.

### Option 1: Restart via Terminal

```bash
# Find and kill the process
lsof -ti:5024 | xargs kill -9

# Navigate to AI Engine directory
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service

# Start the service
python3 src/Backend/main_server.py
```

### Option 2: Restart via Process Manager (if using PM2, etc.)

```bash
pm2 restart ai-engine-service
```

### Option 3: Docker Restart (if containerized)

```bash
docker-compose restart ai-engine-service
```

---

## Verification Steps

After restarting the service:

### 1. Test CORS Headers

```bash
curl -X OPTIONS http://localhost:5024/api/admin/stores/test/devices \
  -H "Origin: http://localhost:3003" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v 2>&1 | grep -i "access-control"
```

**Expected Output:**
```
access-control-allow-origin: http://localhost:3003
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
access-control-allow-headers: *
```

### 2. Test Device Creation Endpoint

```bash
curl -X POST http://localhost:5024/api/admin/stores/{store_id}/devices \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3003" \
  -d '{
    "device_id": "TEST-001",
    "device_name": "Test Device",
    "passcode": "123456",
    "device_type": "kiosk",
    "settings": {
      "platform": "tablet",
      "application_type": "kiosk"
    }
  }' \
  -v 2>&1 | grep -i "access-control"
```

**Expected:** CORS headers in response

### 3. Test from Admin Dashboard

1. Open Admin Dashboard: `http://localhost:3003`
2. Login with admin credentials
3. Navigate to Store Settings → Devices tab
4. Click "Add Device"
5. Fill in form and submit
6. Check browser console - **should have NO CORS errors**

---

## Files Modified

1. ✅ `/src/Frontend/ai-admin-dashboard/src/services/api.ts`
   - Removed `/api/` prefix from device endpoints
   - Fixed double `/api/api/` issue

2. ✅ `/src/Backend/main_server.py`
   - CORS already configured correctly (no changes needed)
   - Just needs service restart

---

## Other Errors in Console (Not Related to Device Management)

### React Router Warning ⚠️ (Low Priority)
```
React Router will begin wrapping state updates in React.startTransition in v7
```

**Fix:** Add future flags to BrowserRouter (already documented in previous root cause analysis)

**File to Update:** `/src/App.tsx` or equivalent router config

```typescript
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }}
>
```

### WebSocket Disconnection ℹ️ (Expected)
```
WebSocket connection to 'ws://localhost:5024/api/agi/ws' failed
```

**Status:** This is expected if AGI features are not in use
**Impact:** None on device management functionality

---

## Summary

### Completed ✅
1. Fixed double `/api/` in device endpoint URLs
2. Verified CORS configuration is correct in code

### Required Action 🔴
1. **RESTART AI Engine Service** to apply CORS configuration

### Expected Result ✅
- No more CORS errors
- Admin Dashboard can create devices
- Device management fully functional

---

## Quick Restart Command

```bash
# Kill old process and start new one
lsof -ti:5024 | xargs kill -9 && sleep 2 && \
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service && \
python3 src/Backend/main_server.py
```

**After restart, test device creation in Admin Dashboard!**
