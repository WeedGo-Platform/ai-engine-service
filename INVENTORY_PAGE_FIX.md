# Inventory Page Fix - Authentication Token Issue

**Date**: 2025-01-20  
**Issue**: Inventory page showing "No auth token found" and "Authentication required" error  
**Status**: FIXED ✅

---

## Root Cause Analysis

The Inventory page was failing to load with **"No auth token found"** because:

### Issue: Wrong localStorage Key ❌
The component was looking for the token in `localStorage.getItem('authToken')`, but the authentication system stores it under a different key: **`weedgo_auth_access_token`**

```typescript
// BEFORE (Wrong key)
const token = localStorage.getItem('authToken'); // ❌ This key doesn't exist!

// ACTUAL key used by AuthContext
const token = storage.getItem(getStorageKey('access_token')); 
// Resolves to: 'weedgo_auth_access_token'
```

**Impact**: Token was never found → All API requests failed with "Authentication required" → Empty inventory list

---

## Solution Applied

### Use the `useAuth` Hook ✅
Instead of manually reading from localStorage with the wrong key, use the `useAuth` hook which provides the token directly:

```typescript
// AFTER (Correct approach)
import { useAuth } from '../contexts/AuthContext';

const Inventory: React.FC = () => {
  const { token } = useAuth(); // ✅ Gets token from auth context
  
  const { data: inventory, isLoading, error: queryError } = useQuery({
    queryFn: async () => {
      if (!token) {
        console.error('No auth token available from useAuth');
        throw new Error('Authentication required');
      }
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`, // ✅ Uses token from context
          // ...
        }
      });
      // ...
    },
    enabled: !!currentStore && !!token, // ✅ Only fetch when token is available
  });
};
```

---

## Files Modified

### `src/pages/Inventory.tsx`
- **Line 25**: Added `import { useAuth } from '../contexts/AuthContext'`
- **Line 107**: Added `const { token } = useAuth()` to get token from context
- **Lines 112-116**: Changed token check from `localStorage.getItem('authToken')` to `!token` from useAuth
- **Line 119**: Added debug log showing token presence
- **Line 166**: Changed `enabled` condition to `!!currentStore && !!token`

**Key Changes**:
```diff
+ import { useAuth } from '../contexts/AuthContext';

  const Inventory: React.FC = () => {
+   const { token } = useAuth();
    
    const { data: inventory } = useQuery({
      queryFn: async () => {
-       const token = localStorage.getItem('authToken');
        if (!token) {
-         console.error('No auth token found');
+         console.error('No auth token available from useAuth');
          throw new Error('Authentication required');
        }
        // ... rest of fetch logic
      },
-     enabled: !!currentStore,
+     enabled: !!currentStore && !!token,
    });
  };
```

---

## Why This Fix Works

### Before (Broken):
- ❌ Looked for token in `localStorage['authToken']`
- ❌ Key doesn't exist (auth system uses `weedgo_auth_access_token`)
- ❌ Token check always fails
- ❌ Query attempts to run without valid token
- ❌ Backend rejects request → 401/403 error

### After (Fixed):
- ✅ Gets token directly from `useAuth()` hook
- ✅ Token is managed by AuthContext with correct storage keys
- ✅ Token is automatically kept in sync with auth state
- ✅ Query only runs when token is available (`enabled: !!token`)
- ✅ Backend receives valid token → Data loads successfully

---

## Authentication Token Storage

The auth system uses these localStorage keys (with prefix `weedgo_auth_`):

| Key | Value | Purpose |
|-----|-------|---------|
| `weedgo_auth_access_token` | JWT string | API authentication |
| `weedgo_auth_refresh_token` | JWT string | Token refresh |
| `weedgo_auth_token_expiry` | Timestamp | Token expiration time |
| `weedgo_auth_user` | JSON object | User profile data |

**Configuration** (from `auth.config.ts`):
```typescript
storage: {
  keyPrefix: import.meta.env.VITE_AUTH_STORAGE_PREFIX || 'weedgo_auth_',
  useSessionStorage: import.meta.env.VITE_USE_SESSION_STORAGE === 'true',
}
```

---

## Testing Checklist

### ✅ Verify Fix Works
1. Log in to admin dashboard
2. Select a store from the store selection modal
3. Navigate to Inventory page
4. **Expected**: Inventory items load successfully
5. **Check Console**: Should see:
   ```
   Fetching inventory for store: <uuid>
   Using endpoint: http://localhost:5024/api/store-inventory/list
   Query params: {store_id: "..."}
   Auth token present: true
   Inventory API response: {totalItems: X, total: X, firstItem: {...}}
   ```

### ⚠️ Edge Cases
- **User not logged in**: Query disabled, no API call made
- **Token expired**: AuthContext handles refresh automatically
- **No store selected**: Query disabled, shows empty state
- **Backend error**: Error displayed in UI with retry option

---

## Related Components Using Same Pattern

Other components that should use `useAuth` hook for token access:
- ✅ `Dashboard.tsx` (already wrapped in auth check)
- ✅ `Orders.tsx` (uses api.ts with interceptors)
- ✅ `Customers.tsx` (uses api.ts with interceptors)
- ⚠️ Any component using raw `fetch` should follow this pattern

---

## Best Practices

### ✅ DO:
- Use `useAuth()` hook to get authentication token
- Check `!!token` in query `enabled` condition
- Use AuthContext for all auth-related state
- Trust the auth system's token management

### ❌ DON'T:
- Manually read from localStorage with custom keys
- Hardcode localStorage key names
- Bypass the auth context system
- Make API calls without checking token availability

---

## Commit Message

```bash
git add src/Frontend/ai-admin-dashboard/src/pages/Inventory.tsx
git commit -m "fix(inventory): use useAuth hook instead of localStorage for token

- Changed from localStorage.getItem('authToken') to useAuth() hook
- Token now properly retrieved from AuthContext
- Added token availability check in query enabled condition
- Fixes 'No auth token found' error preventing inventory from loading

The auth system stores tokens with prefix 'weedgo_auth_', but the component
was looking for 'authToken' key which doesn't exist. Using useAuth() hook
ensures correct token retrieval and automatic sync with auth state."
```
