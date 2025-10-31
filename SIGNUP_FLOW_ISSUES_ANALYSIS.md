# Tenant Signup Flow - Issue Analysis & Status

## Date: 2025-10-31

## Critical Issues Identified

### 1. ❌ OTP Service Creating Users Prematurely
**Problem:** OTP verification is creating user records before tenant signup completes, causing "user already exists" error during final signup.

**Root Cause:** The OTP /verify endpoint may be creating a user record in the database.

**Impact:** HIGH - Blocks tenant signup completion

**Fix Required:** 
- OTP service should NOT create user records
- Only verify codes and mark as verified
- User creation should happen ONLY in tenant_endpoints.py during signup

---

### 2. ❌ Store Creation Fails with FK Constraint
**Problem:** Store creation fails with foreign key violation on province_territory_id

**Error:**
```
insert or update on table "stores" violates foreign key constraint "stores_province_territory_id_fkey"
DETAIL: Key (province_territory_id)=(cb702adf-7202-4396-b2bb-c5b676646126) is not present in table "provinces_territories".
```

**Root Cause:** The province_territory_id from CRSA validation doesn't match the actual ID in the database

**Actual Ontario ID:** `20095fb6-1196-4961-a8f1-4aa6284ec72b`

**Impact:** HIGH - Default store not created during signup

**Fix Required:**
- Query the provinces_territories table to get the correct ID for "Ontario"
- Don't hardcode or trust external IDs

---

### 3. ❌ Free Tier Shows Billing Cycle UI
**Problem:** Monthly/Annual billing cycle selector shows even for free tier

**Location:** Subscription step in TenantSignup.tsx

**Impact:** MEDIUM - Confusing UX

**Fix Required:**
- Conditionally hide billing cycle section when selected plan is 'community_and_new_business' (free tier)

---

### 4. ❌ Login Tracking Timezone Error
**Problem:** Login tracking service fails with timezone mismatch

**Error:**
```
Failed to track login: invalid input for query argument $3: datetime.datetime(2025, 10, 31, 23, 7, 4... (can't subtract offset-naive and offset-aware datetimes)
```

**Location:** core/services/login_tracking_service.py

**Impact:** LOW - Login works but tracking fails

**Fix Required:**
- Ensure all datetime objects are timezone-aware (UTC)
- Use datetime.now(UTC) instead of datetime.now()

---

### 5. ✅ Email OTP Auto-Paste Working
**Status:** FIXED - Pasting code triggers automatic validation

---

### 6. ⚠️ Phone OTP Auto-Paste Not Working
**Status:** NEEDS FIX - Should match email behavior

---

### 7. ❌ Domain Validation Too Strict
**Problem:** Email domain must match tenant website domain (including TLD)

**Example:** `support@potpalace.ca` doesn't match `potpalace.cc`

**Impact:** MEDIUM - May block legitimate signups

**Current Behavior:** TLD must match
**Required Behavior:** Only base domain needs to match (potpalace = potpalace)

---

### 8. ❌ Store Listing Query Error  
**Problem:** AttributeError: 'NoneType' object has no attribute 'HTTP_500_INTERNAL_SERVER_ERROR'

**Location:** api/store_endpoints.py line 1096

**Root Cause:** Missing import for status module

**Impact:** MEDIUM - Store listing fails after login

---

### 9. ❌ Analytics Dashboard Query Error
**Problem:** column "quantity" does not exist

**Location:** Analytics dashboard endpoint

**Impact:** LOW - Dashboard shows partial data

---

## Signup Flow Sequence (Current State)

```
1. Company Info → WORKING ✅
2. Contact Details → WORKING ✅
   - Email OTP → WORKING ✅
   - Phone OTP → PARTIALLY WORKING ⚠️ (no auto-paste)
3. Ontario Licensing → WORKING ✅
   - CRSA Validation → WORKING ✅
   - Auto-create checkbox → WORKING ✅
4. Account Settings → WORKING ✅
5. Subscription → PARTIAL ⚠️ (shows billing for free tier)
   - Terms/Privacy modals → WORKING ✅
6. Submit → FAILS ❌
   - Tenant created → WORKING ✅
   - User exists error → FAILING ❌ (OTP created it)
   - Store not created → FAILING ❌ (FK constraint)
```

## Data Flow Issues

### User Creation Flow (BROKEN)
```
Current (WRONG):
OTP /verify → Creates user in DB
Signup /tenants/signup → Finds user exists → ERROR

Required (CORRECT):
OTP /verify → Only verifies code, NO user creation
Signup /tenants/signup → Creates user with password and tenant_id
```

### Store Creation Flow (BROKEN)
```
Current:
CRSA validation → Returns province_territory_id from external source
Signup creates store → Uses external ID → FK FAILS

Required:
CRSA validation → Returns province name "Ontario"
Signup queries DB → SELECT id FROM provinces_territories WHERE name='Ontario'
Signup creates store → Uses queried ID → SUCCESS
```

## Environment Issues

### SMTP Configuration
- Gmail app password provided but stored in wrong location
- Created unnecessary .env.smtp file
- Should be in main .env as SMTP_PASSWORD

### Database Connection
- DATABASE_URL correctly points to localhost:5434/ai_engine
- Ontario province exists with correct ID
- All required tables exist

## Recommended Fix Order

1. **URGENT:** Fix OTP service to NOT create users
2. **URGENT:** Fix store creation to query province_territory_id from DB
3. **HIGH:** Fix store_endpoints.py import issue
4. **MEDIUM:** Hide billing cycle for free tier
5. **MEDIUM:** Fix login tracking timezone
6. **LOW:** Add phone OTP auto-paste
7. **LOW:** Fix analytics dashboard query

## Files Requiring Changes

1. `src/Backend/services/otp_service.py` - Remove user creation logic
2. `src/Backend/api/tenant_endpoints.py` - Query province_territory_id from DB
3. `src/Backend/api/store_endpoints.py` - Fix status import
4. `src/Backend/core/services/login_tracking_service.py` - Fix timezone
5. `ai-admin-dashboard/src/pages/TenantSignup.tsx` - Hide billing for free tier
6. `ai-admin-dashboard/src/pages/TenantSignup.tsx` - Add phone OTP auto-paste

## Git History Analysis

Recent commits show multiple attempts to fix transaction isolation and store creation:
- `864ffda` - OTP paste auto-verify  
- `f419d33` - Store endpoints import fix
- `d79092a` - Add province_territory_id to store creation
- `e1aaabf` - Remove duplicate code
- `bcb6a99` - Pass transaction connection
- `71465ca` - Fix store schema

The core issue is that fixes are being layered without addressing root cause:
**OTP should never create users in the first place.**
