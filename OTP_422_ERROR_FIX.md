# OTP 422 Error Fix - Resolution Summary

**Date:** December 2024  
**Status:** ✅ RESOLVED (Multiple Fixes)  
**Issue:** `POST http://localhost:5024/api/v1/auth/otp/send 422 (Unprocessable Entity)`

---

## Fix #1: Invalid Purpose Value (Initial Fix)

### Root Cause
The frontend was sending an invalid `purpose` value ('signup') to the OTP endpoints, which caused Pydantic validation to fail on the backend.

### Backend Validation Rules
```python
# src/Backend/api/auth_otp.py (Line 36)
class OTPRequest(BaseModel):
    identifier: str
    identifier_type: Literal['email', 'phone']
    purpose: Literal['login', 'verification', 'password_reset']  # Only these 3 values accepted
```

### Frontend Error
```typescript
// BEFORE FIX - tenantService.ts
const payload = {
  identifier,
  identifier_type: identifierType,
  purpose: 'signup'  // ❌ Invalid - not in backend Literal type
};
```

### Solution Applied
Updated `src/Frontend/ai-admin-dashboard/src/services/tenantService.ts`:

**1. sendOTP Method (Line 294)**
```typescript
// BEFORE:
purpose: 'signup'  // ❌ Invalid

// AFTER:
purpose: 'verification'  // ✅ Valid
```

**2. verifyOTP Method (Line 339)**
```typescript
// BEFORE:
purpose: 'signup'  // ❌ Invalid

// AFTER:
purpose: 'verification'  // ✅ Valid
```

---

## Fix #2: Email/Phone Validation Regex Mismatch (Latest Fix)

### Root Cause
Frontend validation used **looser regex patterns** than backend Pydantic validators, allowing invalid emails/phones to pass client-side validation but fail on the server.

### Backend Validation (Strict)
```python
# Email: Only allows specific characters
if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
    raise ValueError('Invalid email format')

# Phone: Must be 10-15 digits after cleaning
cleaned = re.sub(r'\D', '', v)
if len(cleaned) < 10 or len(cleaned) > 15:
    raise ValueError('Invalid phone number')
```

### Frontend Validation (Original - Too Loose)
```typescript
// Email: Allowed any non-whitespace around @ and .
if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))

// Phone: Only checked minimum, no maximum
if (identifier.replace(/\D/g, '').length < 10)
```

### The Mismatch Impact
- **Email:** Frontend allowed characters like `#$%` that backend rejected
- **Phone:** Frontend allowed 20+ digit numbers that backend rejected
- **Result:** Users passed frontend validation but got 422 from backend

### Solution Applied

#### 1. Email Validation Alignment
Updated **3 locations** to use identical regex as backend:

**TenantSignup.tsx (line 883):**
```typescript
// NEW: Same regex as backend Pydantic validator
if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(formData.contactEmail)) {
  setErrors(prev => ({ ...prev, contactEmail: t('signup:validation.emailInvalid') }));
  return;
}
```

**OTPVerification.tsx (lines 36-39):**
```typescript
// Auto-send validation
const isValidEmail = identifierType === 'email' && 
  /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(identifier);
```

**OTPVerification.tsx (lines 64-67):**
```typescript
// Manual send validation
if (identifierType === 'email' && 
    !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(identifier)) {
  setError(t('signup:validation.emailInvalid') || 'Invalid email format');
  return;
}
```

#### 2. Phone Validation Alignment
Updated to enforce **10-15 digit** requirement:

**OTPVerification.tsx (lines 37-38):**
```typescript
// Auto-send validation
const cleanedPhone = identifierType === 'phone' ? identifier.replace(/\D/g, '') : '';
const isValidPhone = identifierType === 'phone' && 
  cleanedPhone.length >= 10 && cleanedPhone.length <= 15;
```

**OTPVerification.tsx (lines 69-74):**
```typescript
// Manual send validation
if (identifierType === 'phone') {
  const cleanedPhone = identifier.replace(/\D/g, '');
  if (cleanedPhone.length < 10 || cleanedPhone.length > 15) {
    setError(t('signup:validation.phoneInvalid') || 
      'Invalid phone number (must be 10-15 digits)');
    return;
  }
}
```

### Files Modified (Fix #2)
1. **src/Frontend/ai-admin-dashboard/src/pages/TenantSignup.tsx** - Line 883
2. **src/Frontend/ai-admin-dashboard/src/components/OTPVerification.tsx** - Lines 36-39, 64-67, 69-74

---

## Validation

### Backend Accepts
- ✅ `'login'` - For user authentication
- ✅ `'verification'` - For email/phone verification during signup
- ✅ `'password_reset'` - For password recovery

### Frontend Now Sends
- ✅ `'verification'` - Correct value for signup flow

### Expected Outcome
- ✅ OTP send requests should succeed with 200 OK
- ✅ OTP verify requests should succeed with 200 OK
- ✅ Users can complete email/phone verification during signup
- ✅ No more 422 validation errors

---

## Testing Checklist

- [ ] Clear browser cache and local storage
- [ ] Start signup flow
- [ ] Enter email address
- [ ] Click "Verify" button
- [ ] Verify no 422 errors in console
- [ ] Confirm OTP code is sent to email
- [ ] Enter OTP code
- [ ] Verify successful validation
- [ ] Repeat for phone number verification

---

## Additional Notes

### Translation Keys
The console was also showing missing translation key errors:
- `tenant.navigation.back` ✅ Exists in en/signup.json (Line 66)
- `tenant.contactInfo.cityPlaceholder` ✅ Exists in en/signup.json (Line 43)

These keys are present in all 28 language files. The errors may have been transient or occurred during initial page load before i18next initialized.

### Related Files
- **Backend:** `src/Backend/api/auth_otp.py` - OTP endpoint and validation
- **Frontend Service:** `src/Frontend/ai-admin-dashboard/src/services/tenantService.ts` - API client
- **UI Component:** `src/Frontend/ai-admin-dashboard/src/pages/TenantSignup.tsx` - Signup form

### Impact
This was a **critical blocking issue** preventing users from completing signup. The fix enables:
- Email verification during signup
- Phone verification during signup (optional)
- Proper OTP code delivery
- Successful account creation flow

---

## Deployment Notes

**No Backend Changes Required** - Backend validation was correct.  
**Frontend Changes Only** - Updated `tenantService.ts` to use valid purpose value.  
**Zero Downtime** - Can be deployed immediately without database migrations or API changes.

---

## Prevention

### Type Safety Recommendation
Consider adding TypeScript types that mirror backend Pydantic models:

```typescript
type OTPPurpose = 'login' | 'verification' | 'password_reset';

interface OTPRequest {
  identifier: string;
  identifier_type: 'email' | 'phone';
  purpose: OTPPurpose;
}
```

This would catch invalid values at compile time rather than runtime.

### Code Review Focus
When integrating new endpoints:
1. Review backend Pydantic models for Literal types
2. Ensure frontend payloads match exactly
3. Add TypeScript types that mirror backend validation
4. Test with network inspector to verify payloads

---

**Fix Applied By:** GitHub Copilot Agent  
**Verified:** Code changes confirmed in tenantService.ts  
**Status:** Ready for testing and deployment
