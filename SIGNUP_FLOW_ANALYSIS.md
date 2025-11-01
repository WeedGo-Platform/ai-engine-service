# Signup Flow Issues - Analysis & Fixes

## Issues Identified (in order of priority)

### 1. **OTP Service Creates User Before Signup** ❌ CRITICAL
**Problem:** When OTP is sent for email verification during signup, it creates a user record. Then when the actual signup happens, it detects user already exists and fails.

**Root Cause:** OTP service is creating users unconditionally

**Solution Required:**
- Add `create_user` parameter to OTP service (defaults to True for backward compatibility)
- When called from signup flow, set `create_user=False`
- Track OTP codes separately without creating user records
- Update user record ONLY when signup completes (update password, tenant_id, etc.)

**Files to modify:**
- `src/Backend/services/otp_service.py` - Add create_user flag
- `src/Backend/api/tenant_endpoints.py` - Pass create_user=False during signup OTP

---

### 2. **Monthly/Annual Billing Cycle Shows for Free Tier** ❌ MINOR UI
**Problem:** Free tier shows billing cycle selector (Monthly/Annual) when it should be hidden

**Solution:** Hide billing cycle UI when free tier selected

**Files to modify:**
- Frontend subscription step component

---

### 3. **OTP Code Paste Doesn't Auto-Validate** ❌ UX ISSUE
**Problem:** When user pastes 6-digit code, it shows as "invalid" until they click verify button

**Solution:** Auto-trigger validation when all 6 digits are entered (paste or type)

**Files to modify:**
- Frontend OTP input component for both email and phone

---

### 4. **Store Creation from CRSA** ⚠️ ALREADY FIXED (verify)
**Problem:** Store creation was failing with foreign key constraint error

**Current Code:** Lines 456-491 in `tenant_endpoints.py` correctly:
1. Queries for Ontario province: `SELECT id FROM provinces_territories WHERE code = 'ON'`
2. Gets valid province_id: `20095fb6-1196-4961-a8f1-4aa6284ec72b`
3. Uses it in store INSERT

**Verification Needed:** Test that store creation works now

---

### 5. **Email Domain Validation** ⚠️ NEEDS VERIFICATION
**Problem:** User claims potpalace.cc domain should not match support@potpalace.ca (TLD mismatch)

**Current Logic:** Need to verify if domain validation is checking TLD correctly

**Expected:** 
- potpalace.cc should only match emails @potpalace.cc
- potpalace.ca should only match emails @potpalace.ca

---

### 6. **Login Tracking Error** ⚠️ TIMEZONE ISSUE
**Error:** `can't subtract offset-naive and offset-aware datetimes`

**Solution:** Fix datetime timezone handling in login_tracking_service.py

---

## Secondary Issues (Not Blocking Signup)

### 7. SMTP Failover (Already Configured)
- AWS SES: Not verified emails
- SendGrid: Wrong credentials  
- Gmail SMTP: Password saved in .env but not committed to git ✅

### 8. Database Errors (Not Related to Signup)
- Analytics dashboard: `column "quantity" does not exist` - legacy issue
- Audit log: Foreign key violation - different issue

---

## Current Database State

### Provinces Table ✅ POPULATED
```
Ontario ID: 20095fb6-1196-4961-a8f1-4aa6284ec72b
Code: ON
Name: Ontario
```

All 13 Canadian provinces/territories are present.

---

## Priority Fix Order

1. **FIX OTP User Creation** (CRITICAL - blocks signups)
2. **Test Store Creation** (verify current code works)
3. **Fix Email Domain Validation** (if broken)
4. **Fix OTP Auto-Validate UX** (user experience)
5. **Hide Billing Cycle for Free Tier** (cosmetic)
6. **Fix Login Tracking Timezone** (non-critical error)

---

## Testing Required After Fixes

1. Complete signup flow end-to-end
2. Verify store created successfully with correct province
3. Verify user can log in immediately after signup
4. Verify OTP code paste auto-validates
5. Verify free tier doesn't show billing options
