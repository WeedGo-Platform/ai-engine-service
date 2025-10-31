# Signup Flow Fixes - Applied Changes

## ✅ Issue #1: OTP Creates User Prematurely - FIXED

### Changes Made:

1. **Backend: `auth_otp.py`**
   - Added `create_if_missing` parameter to `get_or_create_user_by_identifier()` function
   - Added `create_user_if_missing` field to `OTPRequest` model (defaults to True for backward compatibility)
   - Updated `/api/v1/auth/otp/send` endpoint to respect this flag

2. **Frontend: `tenantService.ts`**
   - Modified OTP send payload to include `create_user_if_missing: false`
   - This prevents user creation during signup email/phone verification

### How It Works Now:

**Before:**
1. User enters email in signup
2. OTP send creates user with email + password='OTP_AUTH'
3. Signup completes and tries to create user again → CONFLICT

**After:**
1. User enters email in signup
2. OTP send DOES NOT create user (create_user_if_missing=false)
3. OTP code stored without user_id
4. Signup completes and creates user properly with full info

### Testing Required:
- ✅ Send OTP during signup (should NOT create user)
- ✅ Complete signup (should create user successfully)
- ✅ Send OTP for login (should still create user if missing - backward compat)

---

## ⚠️ Remaining Issues

### Issue #2: Store Creation Province ID
**Status:** Code looks correct, needs testing

The code at lines 456-491 in `tenant_endpoints.py`:
1. Queries: `SELECT id FROM provinces_territories WHERE code = 'ON'`
2. Gets: `20095fb6-1196-4961-a8f1-4aa6284ec72b` ✅ (verified in DB)
3. Uses this in store INSERT

**Previous error:** Different UUID `cb702adf-7202-4396-b2bb-c5b676646126` was used (not in DB)
**Likely cause:** Old code or cached value

**Next Steps:** Test signup flow to verify store creation works

---

### Issue #3: Free Tier Shows Billing Cycle
**Location:** Frontend subscription component  
**Fix:** Hide "Monthly/Annual" selector when free tier is selected

Files to check:
- `src/Frontend/ai-admin-dashboard/src/components/signup/steps/SubscriptionStep.tsx`
- Or wherever subscription UI is rendered

---

### Issue #4: OTP Code Paste Doesn't Auto-Validate
**Location:** Frontend OTP input components
**Fix:** Trigger validation automatically when 6 digits entered

Files to modify:
- Email OTP input component
- Phone OTP input component

---

### Issue #5: Email Domain Validation (TLD Mismatch)
**Status:** Needs investigation

User claims:
- Domain: `potpalace.cc`
- Email: `support@potpalace.ca`
- Should NOT match (different TLD)

Need to check domain validation logic in signup flow.

---

### Issue #6: Login Tracking Timezone Error
**Error:** `can't subtract offset-naive and offset-aware datetimes`
**Location:** `login_tracking_service.py`
**Fix:** Ensure all datetime objects have timezone info

---

## Summary

✅ **FIXED:** OTP user creation issue  
⏳ **NEEDS TESTING:** Store creation with province_id  
📝 **TODO:** Hide billing cycle for free tier  
📝 **TODO:** Auto-validate OTP paste  
📝 **TODO:** Fix domain validation  
📝 **TODO:** Fix login tracking timezone  

---

## Next Steps

1. **Test Signup Flow End-to-End:**
   - Start signup
   - Enter email → verify OTP (should NOT create user)
   - Complete signup (should create user + tenant + store)
   - Login immediately

2. **If Store Creation Fails:**
   - Check error log for province_id value
   - Verify provinces_territories table has Ontario

3. **Fix Remaining UI Issues:**
   - Billing cycle visibility
   - OTP auto-validate

4. **Fix Domain Validation:**
   - Ensure TLD matches email domain
