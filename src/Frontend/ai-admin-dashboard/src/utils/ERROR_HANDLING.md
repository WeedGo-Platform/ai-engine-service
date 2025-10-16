# Error Handling & Translation Guide

This document describes the centralized error handling and translation system for the WeedGo Admin Dashboard.

## Overview

The error handling system provides:
- ✅ Automatic translation of error messages to all 28 supported languages
- ✅ Consistent error handling patterns across the application
- ✅ Smart error type detection (network, auth, validation, etc.)
- ✅ Integration with axios interceptors for automatic error enhancement
- ✅ React hooks for easy component integration
- ✅ Toast notification integration for user-friendly error display

## Architecture

```
┌─────────────────────┐
│   API Request       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Axios Interceptor  │  ← Enhances error with code, statusCode, flags
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Error Translation  │  ← Maps error to translation key
│      Utility        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  useErrorHandler    │  ← React hook for components
│       Hook          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  User sees          │  ← Localized error message
│  translated message │
└─────────────────────┘
```

## Core Components

### 1. Enhanced API Error (api.ts)

The axios interceptor automatically enhances all errors with:

```typescript
interface ApiError extends Error {
  code?: string;              // Backend error code (e.g., 'TENANT_NOT_FOUND')
  statusCode?: number;        // HTTP status code (e.g., 404)
  details?: any;              // Additional error details from backend
  isNetworkError?: boolean;   // True if network/connection error
  isAuthError?: boolean;      // True if 401/403 error
  isValidationError?: boolean;// True if 400/422 error
  originalError?: any;        // Original axios error
}
```

### 2. Error Translation Utility (errorTranslation.ts)

Maps errors to translation keys using multiple strategies:

```typescript
import { translateError, translateOperationError, isErrorType } from '@/utils/errorTranslation';

// Basic error translation
const message = translateError(error, t, 'errors:general.unexpectedError');

// Operation-specific translation (provides better context)
const message = translateOperationError(error, t, 'load', 'tenant');
// Uses 'errors:tenant.loadFailed' as fallback

// Check error type
if (isErrorType(error, 'network')) {
  // Handle network errors specially
}
```

### 3. useErrorHandler Hook (useErrorHandler.ts)

React hook that simplifies error handling in components:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const MyComponent = () => {
  const { handleError, handleOperationError, handleErrorSmart } = useErrorHandler();

  const loadData = async () => {
    try {
      await api.getData();
    } catch (error) {
      handleOperationError(error, 'load', 'tenant');
      // Automatically shows toast with translated message
    }
  };
};
```

## Usage Patterns

### Pattern 1: Simple Error Handling

Use when you need basic error handling:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const MyComponent = () => {
  const { handleError } = useErrorHandler();

  const doSomething = async () => {
    try {
      await someApiCall();
    } catch (error) {
      handleError(error);
      // Shows generic translated error with toast
    }
  };
};
```

### Pattern 2: Operation-Specific Error Handling

Use when the operation type matters (recommended):

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const TenantManagement = () => {
  const { handleOperationError } = useErrorHandler();

  const createTenant = async (data: any) => {
    try {
      await tenantService.createTenant(data);
      toast.success(t('tenants:messages.createSuccess'));
    } catch (error) {
      handleOperationError(error, 'create', 'tenant');
      // Shows: "Failed to create tenant" (translated)
    }
  };

  const updateTenant = async (id: string, data: any) => {
    try {
      await tenantService.updateTenant(id, data);
      toast.success(t('tenants:messages.updateSuccess'));
    } catch (error) {
      handleOperationError(error, 'update', 'tenant');
      // Shows: "Failed to update tenant" (translated)
    }
  };
};
```

### Pattern 3: Smart Error Handling

Use when you want automatic handling based on error type:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const MyComponent = () => {
  const { handleErrorSmart } = useErrorHandler();

  const doSomething = async () => {
    try {
      await someApiCall();
    } catch (error) {
      handleErrorSmart(error);
      // Automatically:
      // - Extracts validation errors
      // - Shows network icon for network errors
      // - Silently handles auth errors (redirect happens)
      // - Shows appropriate toast for other errors
    }
  };
};
```

### Pattern 4: Validation Error Handling

Use when you need to display field-specific validation errors:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const FormComponent = () => {
  const { handleValidationErrors } = useErrorHandler();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const submitForm = async (data: any) => {
    try {
      await api.submitForm(data);
    } catch (error) {
      const validationErrors = handleValidationErrors(error);
      if (validationErrors) {
        setFieldErrors(validationErrors);
        // validationErrors = { email: "Invalid email", password: "Too short" }
      }
    }
  };

  return (
    <form>
      <input name="email" />
      {fieldErrors.email && <span className="error">{fieldErrors.email}</span>}
    </form>
  );
};
```

### Pattern 5: Error Handler Wrapper

Use when you want to wrap multiple operations:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const MyComponent = () => {
  const { withErrorHandler } = useErrorHandler();

  // Wrap async functions with automatic error handling
  const loadDataSafe = withErrorHandler(
    async (id: string) => {
      return await api.loadData(id);
    },
    'errors:general.dataLoadFailed'
  );

  useEffect(() => {
    loadDataSafe('123'); // Errors handled automatically
  }, []);
};
```

### Pattern 6: Conditional Error Handling

Use when you need different behavior based on error type:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

const MyComponent = () => {
  const { checkErrorType, handleError } = useErrorHandler();

  const doSomething = async () => {
    try {
      await someApiCall();
    } catch (error) {
      if (checkErrorType(error, 'network')) {
        // Show retry button for network errors
        setShowRetry(true);
      } else if (checkErrorType(error, 'validation')) {
        // Handle validation errors
        setErrors(extractValidationErrors(error));
      } else {
        // Generic error handling
        handleError(error);
      }
    }
  };
};
```

## Error Translation Keys

All error messages are stored in `/i18n/locales/{lang}/errors.json`:

### Available Error Categories

```typescript
// API Errors
'errors:api.networkError'
'errors:api.serverError'
'errors:api.timeout'
'errors:api.unauthorized'
'errors:api.forbidden'
'errors:api.notFound'
'errors:api.conflict'
'errors:api.validationError'
'errors:api.badRequest'

// Auth Errors
'errors:auth.invalidCredentials'
'errors:auth.sessionExpired'
'errors:auth.accountDisabled'
'errors:auth.tokenExpired'

// Tenant Errors
'errors:tenant.loadFailed'
'errors:tenant.createFailed'
'errors:tenant.updateFailed'
'errors:tenant.deleteFailed'
'errors:tenant.limitReached'

// Store Errors
'errors:store.loadFailed'
'errors:store.createFailed'
'errors:store.updateFailed'
'errors:store.notFound'

// Inventory Errors
'errors:inventory.loadFailed'
'errors:inventory.updateFailed'
'errors:inventory.lowStock'
'errors:inventory.outOfStock'

// Order Errors
'errors:order.loadFailed'
'errors:order.createFailed'
'errors:order.cancelFailed'
'errors:order.notFound'

// Payment Errors
'errors:payment.processingFailed'
'errors:payment.cardDeclined'
'errors:payment.insufficientFunds'

// General Errors
'errors:general.unexpectedError'
'errors:general.operationFailed'
'errors:general.permissionDenied'
```

## Backend Error Code Mapping

The system automatically maps backend error codes to translation keys:

```typescript
Backend Code              → Translation Key
─────────────────────────────────────────────────
'TENANT_NOT_FOUND'        → 'errors:tenant.loadFailed'
'INVALID_CREDENTIALS'     → 'errors:auth.invalidCredentials'
'NETWORK_ERROR'           → 'errors:api.networkError'
'VALIDATION_ERROR'        → 'errors:api.validationError'
'STORE_LIMIT_REACHED'     → 'errors:tenant.limitReached'
'CARD_DECLINED'           → 'errors:payment.cardDeclined'
// ... see errorTranslation.ts for complete mapping
```

## HTTP Status Code Mapping

```typescript
Status Code  → Translation Key
──────────────────────────────────────────
400          → 'errors:api.badRequest'
401          → 'errors:auth.unauthorized'
403          → 'errors:api.forbidden'
404          → 'errors:api.notFound'
409          → 'errors:api.conflict'
422          → 'errors:api.validationError'
429          → 'errors:api.tooManyRequests'
500          → 'errors:api.internalError'
503          → 'errors:api.serviceUnavailable'
```

## Best Practices

### ✅ DO

1. **Use operation-specific error handling:**
   ```typescript
   handleOperationError(error, 'create', 'tenant');
   ```

2. **Provide fallback keys for context:**
   ```typescript
   handleError(error, 'errors:tenant.loadFailed');
   ```

3. **Use smart error handling for mixed operations:**
   ```typescript
   handleErrorSmart(error);
   ```

4. **Log errors in development:**
   ```typescript
   handleError(error, undefined, { logError: true });
   ```

5. **Handle validation errors explicitly:**
   ```typescript
   const validationErrors = handleValidationErrors(error);
   if (validationErrors) {
     setFieldErrors(validationErrors);
   }
   ```

### ❌ DON'T

1. **Don't hardcode error messages:**
   ```typescript
   // ❌ Bad
   toast.error('Failed to load tenant');

   // ✅ Good
   handleOperationError(error, 'load', 'tenant');
   ```

2. **Don't ignore error types:**
   ```typescript
   // ❌ Bad
   catch (error) {
     toast.error('Error occurred');
   }

   // ✅ Good
   catch (error) {
     handleErrorSmart(error);
   }
   ```

3. **Don't lose error context:**
   ```typescript
   // ❌ Bad
   catch (error) {
     handleError(error); // Generic message
   }

   // ✅ Good
   catch (error) {
     handleOperationError(error, 'update', 'store');
   }
   ```

## Adding New Error Messages

To add new error messages:

1. **Add translation keys to errors.json:**
   ```json
   {
     "myFeature": {
       "loadFailed": "Failed to load feature data",
       "specificError": "Something specific went wrong"
     }
   }
   ```

2. **Use in components:**
   ```typescript
   handleError(error, 'errors:myFeature.loadFailed');
   ```

3. **Add backend error code mapping (if needed):**
   Edit `errorTranslation.ts`:
   ```typescript
   const codeMap: Record<string, string> = {
     // ...
     'MY_CUSTOM_ERROR_CODE': 'errors:myFeature.specificError',
   };
   ```

## Testing Error Handling

```typescript
import { translateError } from '@/utils/errorTranslation';
import { renderHook } from '@testing-library/react-hooks';
import { useErrorHandler } from '@/hooks/useErrorHandler';

describe('Error Handling', () => {
  it('should translate network errors', () => {
    const error = { code: 'NETWORK_ERROR' };
    const message = translateError(error, t);
    expect(message).toBe('Unable to connect to server. Please check your connection.');
  });

  it('should handle operation errors', () => {
    const { result } = renderHook(() => useErrorHandler());
    const message = result.current.handleOperationError(
      new Error('Test'),
      'load',
      'tenant',
      { showToast: false }
    );
    expect(message).toContain('Failed to load');
  });
});
```

## Migration Guide

To migrate existing error handling:

### Before:
```typescript
try {
  await api.loadTenants();
} catch (error) {
  toast.error('Failed to load tenant data');
}
```

### After:
```typescript
const { handleOperationError } = useErrorHandler();

try {
  await api.loadTenants();
} catch (error) {
  handleOperationError(error, 'load', 'tenant');
}
```

## Troubleshooting

### Error messages showing as keys (e.g., "errors:tenant.loadFailed")

- **Cause**: Translation key doesn't exist or i18n not initialized
- **Fix**: Check that the key exists in errors.json for all languages

### Toast not showing

- **Cause**: `showToast: false` option set
- **Fix**: Remove the option or set `showToast: true`

### Wrong error message displayed

- **Cause**: Error code/status not mapped correctly
- **Fix**: Add mapping in `errorTranslation.ts` or provide explicit fallback key

## Support

For questions or issues with error handling:
- Check this documentation
- Review examples in `TenantManagement.tsx` (refactored)
- See `errorTranslation.ts` for complete mapping
- Check `useErrorHandler.ts` for all available methods
