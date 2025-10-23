# authApi.checkEmail Function Fix - Using Existing Endpoint

## Problem
The registration page was throwing an error: **"authApi.checkEmail is not a function"**

## Solution
Connected the frontend to the **existing** email check endpoint that was already implemented in the backend.

## What Was Wrong

1. The frontend was calling `authApi.checkEmail()` but this function didn't exist in the auth API service
2. There was already an endpoint at `/api/checkout/check-user/{email}` that checks if a user exists
3. The frontend just needed to be connected to this existing endpoint

## Fix Applied

### Frontend Update
**File:** `/src/Frontend/weedgo-commerce/src/api/auth.ts`

Added the `checkEmail` function that calls the existing endpoint:
```typescript
checkEmail: async (email: string): Promise<{ available: boolean; message?: string }> => {
  try {
    // Use the existing guest checkout endpoint to check if user exists
    const response = await apiClient.get<{ exists: boolean; requires_login: boolean }>(
      `/api/checkout/check-user/${encodeURIComponent(email)}`
    );

    // Convert the response: if email exists, it's NOT available
    return {
      available: !response.data.exists,
      message: response.data.exists
        ? 'An account with this email already exists. Please sign in instead.'
        : undefined
    };
  } catch (error: any) {
    console.error('Email check failed:', error);
    // Return available: true on error to allow registration to proceed
    return { available: true };
  }
}
```

### Register Component Update
**File:** `/src/Frontend/weedgo-commerce/src/pages/Register.tsx`

Fixed the response handling to use `available` property:
```typescript
const emailCheck = await authApi.checkEmail(formData.email.toLowerCase().trim());
if (!emailCheck.available) {
  toast.error(emailCheck.message || 'An account with this email already exists');
  setLoading(false);
  return;
}
```

## How It Works

1. User enters email in registration form
2. Frontend calls `authApi.checkEmail(email)`
3. Function makes GET request to `/api/checkout/check-user/{email}`
4. Backend checks if user exists in database
5. Backend returns `{ exists: boolean, requires_login: boolean }`
6. Frontend converts this to `{ available: boolean, message?: string }`
   - If `exists: true` → `available: false` (email is taken)
   - If `exists: false` → `available: true` (email can be used)
7. Registration form shows appropriate message based on availability

## Files Modified

1. `/src/Frontend/weedgo-commerce/src/api/auth.ts` - Added checkEmail function
2. `/src/Frontend/weedgo-commerce/src/pages/Register.tsx` - Fixed response property

## No Backend Changes Needed

The backend already had the necessary endpoint at `/api/checkout/check-user/{email}`. No duplicate endpoints were created.

## Result

- ✅ The "authApi.checkEmail is not a function" error is fixed
- ✅ Email availability checking works using the existing backend endpoint
- ✅ No duplicate code or endpoints
- ✅ Clean, efficient solution that reuses existing functionality