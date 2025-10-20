# Error Boundary Implementation Guide

**Date:** 2025-01-19
**Phase:** 1.9 Complete
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Components Created](#components-created)
3. [Usage Examples](#usage-examples)
4. [What Error Boundaries Catch](#what-error-boundaries-catch)
5. [What They Don't Catch](#what-they-dont-catch)
6. [Best Practices](#best-practices)
7. [Testing](#testing)
8. [Integration with Error Reporting](#integration-with-error-reporting)

---

## Overview

Error Boundaries are React components that catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of crashing the entire application.

**Benefits:**
- ✅ Prevents entire app crashes
- ✅ Provides graceful degradation
- ✅ Offers user recovery options
- ✅ Improves user experience
- ✅ Enables error reporting integration

---

## Components Created

### 1. PaymentErrorBoundary

**Location:** `src/components/PaymentErrorBoundary.tsx`

**Purpose:** Full-page error boundary specifically for payment routes.

**Features:**
- Full-page error UI
- Multiple recovery options (Try Again, Reload, Go Home)
- Error count tracking
- Development error details
- Integration-ready for error reporting services

**Usage:**
```tsx
<PaymentErrorBoundary showDetails={isDevelopment}>
  <PaymentProvider>
    <TenantPaymentSettings />
  </PaymentProvider>
</PaymentErrorBoundary>
```

### 2. ErrorBoundary (Generic)

**Location:** `src/components/ErrorBoundary.tsx`

**Purpose:** Lightweight, reusable error boundary for any component.

**Features:**
- Minimal inline error UI
- Custom fallback support
- Optional reset callback
- Flexible error handling

**Usage:**
```tsx
<ErrorBoundary fallback={<CustomError />} onReset={handleReset}>
  <SomeComponent />
</ErrorBoundary>
```

### 3. Helper Components

**InlineError:**
```tsx
<InlineError message="Failed to load" onRetry={retry} />
```

**CardError:**
```tsx
<CardError
  title="Payment Failed"
  message="Unable to process payment"
  onRetry={retryPayment}
/>
```

---

## Usage Examples

### Example 1: Wrap Entire Route

```tsx
// App.tsx
{
  path: 'tenants/:tenantCode/payment-settings',
  element: (
    <PaymentErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
      <PaymentProvider>
        <TenantPaymentSettings />
      </PaymentProvider>
    </PaymentErrorBoundary>
  )
}
```

### Example 2: Wrap Individual Component

```tsx
// Inside a page component
<ErrorBoundary
  fallback={<div>Provider list unavailable</div>}
  onError={(error, info) => console.error(error)}
>
  <ProviderList providers={providers} />
</ErrorBoundary>
```

### Example 3: Custom Fallback

```tsx
<ErrorBoundary
  fallback={
    <CardError
      title="Failed to load transactions"
      message="Please check your connection and try again"
      onRetry={() => refetchTransactions()}
    />
  }
>
  <TransactionTable transactions={transactions} />
</ErrorBoundary>
```

### Example 4: With Error Reporting

```tsx
<PaymentErrorBoundary
  onError={(error, errorInfo) => {
    // Send to Sentry, Bugsnag, etc.
    errorTracker.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
    });
  }}
>
  <PaymentComponent />
</PaymentErrorBoundary>
```

---

## What Error Boundaries Catch

Error Boundaries catch errors that occur in:

✅ **Rendering phase**
```tsx
function BrokenComponent() {
  // This will be caught
  throw new Error('Render error');
}
```

✅ **Lifecycle methods**
```tsx
componentDidMount() {
  // This will be caught
  throw new Error('Lifecycle error');
}
```

✅ **Constructors**
```tsx
constructor(props) {
  // This will be caught
  throw new Error('Constructor error');
}
```

✅ **Child component errors**
```tsx
<ErrorBoundary>
  <ChildThatThrows /> {/* Caught */}
</ErrorBoundary>
```

---

## What They Don't Catch

Error Boundaries do NOT catch errors in:

❌ **Event handlers**
```tsx
function MyComponent() {
  const handleClick = () => {
    throw new Error('Not caught!'); // Use try-catch instead
  };

  return <button onClick={handleClick}>Click</button>;
}
```

**Solution:** Use try-catch in event handlers
```tsx
const handleClick = async () => {
  try {
    await doSomething();
  } catch (error) {
    setError(error);
  }
};
```

❌ **Async code**
```tsx
useEffect(() => {
  fetchData().catch(err => {
    // Error Boundary won't catch this
  });
}, []);
```

**Solution:** Use try-catch or .catch()
```tsx
useEffect(() => {
  const loadData = async () => {
    try {
      await fetchData();
    } catch (error) {
      setError(error);
    }
  };
  loadData();
}, []);
```

❌ **Server-side rendering**
❌ **Errors in the Error Boundary itself**

---

## Best Practices

### 1. Use Multiple Error Boundaries

Don't rely on a single top-level error boundary. Use them strategically:

```tsx
<App>
  <ErrorBoundary> {/* Top level */}
    <Navigation />
    <ErrorBoundary> {/* Route level */}
      <PaymentRoutes />
    </ErrorBoundary>
    <ErrorBoundary> {/* Feature level */}
      <ShoppingCart />
    </ErrorBoundary>
  </ErrorBoundary>
</App>
```

### 2. Provide Recovery Options

Always give users a way to recover:

```tsx
<ErrorBoundary
  fallback={
    <div>
      <p>Something went wrong</p>
      <button onClick={retry}>Try Again</button>
      <button onClick={goHome}>Go Home</button>
    </div>
  }
>
  <Component />
</ErrorBoundary>
```

### 3. Log Errors Appropriately

```tsx
<ErrorBoundary
  onError={(error, errorInfo) => {
    // Development: Console
    if (process.env.NODE_ENV === 'development') {
      console.error(error, errorInfo);
    }

    // Production: Error tracking service
    if (process.env.NODE_ENV === 'production') {
      errorTracker.captureException(error, { errorInfo });
    }
  }}
>
  <Component />
</ErrorBoundary>
```

### 4. Show Different UIs Based on Error Type

```tsx
const ErrorFallback = ({ error }) => {
  if (error.name === 'NetworkError') {
    return <NetworkErrorUI />;
  }
  if (error.name === 'AuthError') {
    return <AuthErrorUI />;
  }
  return <GenericErrorUI />;
};

<ErrorBoundary fallback={<ErrorFallback />}>
  <Component />
</ErrorBoundary>
```

### 5. Use Error Boundaries at Component Boundaries

Place error boundaries at meaningful component boundaries:

```tsx
// Good: Isolates provider list errors
<ErrorBoundary>
  <ProviderList />
</ErrorBoundary>
<ErrorBoundary>
  <TransactionList />
</ErrorBoundary>

// Bad: Wraps everything, no isolation
<ErrorBoundary>
  <ProviderList />
  <TransactionList />
</ErrorBoundary>
```

---

## Testing

### Manual Testing (Development)

Use the `ErrorBoundaryTest` component:

```tsx
import ErrorBoundaryTest from './components/__tests__/ErrorBoundaryTest';

// Add a development route
{
  path: 'dev/error-boundary-test',
  element: (
    <ErrorBoundary>
      <ErrorBoundaryTest />
    </ErrorBoundary>
  )
}
```

Then navigate to `/dev/error-boundary-test` and click the test buttons.

### Automated Testing

```tsx
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

const ThrowError = () => {
  throw new Error('Test error');
};

test('catches and displays error', () => {
  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});

test('calls onError callback', () => {
  const onError = jest.fn();

  render(
    <ErrorBoundary onError={onError}>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(onError).toHaveBeenCalled();
});
```

---

## Integration with Error Reporting

### Sentry Integration

```tsx
import * as Sentry from '@sentry/react';

<PaymentErrorBoundary
  onError={(error, errorInfo) => {
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
      tags: {
        errorBoundary: 'PaymentErrorBoundary',
      },
    });
  }}
>
  <PaymentComponent />
</PaymentErrorBoundary>
```

### Bugsnag Integration

```tsx
import Bugsnag from '@bugsnag/js';

<PaymentErrorBoundary
  onError={(error, errorInfo) => {
    Bugsnag.notify(error, (event) => {
      event.addMetadata('react', {
        componentStack: errorInfo.componentStack,
      });
    });
  }}
>
  <PaymentComponent />
</PaymentErrorBoundary>
```

### Custom Error Reporting

```tsx
const reportError = async (error: Error, errorInfo: ErrorInfo) => {
  await fetch('/api/error-reports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    }),
  });
};

<PaymentErrorBoundary onError={reportError}>
  <PaymentComponent />
</PaymentErrorBoundary>
```

---

## Troubleshooting

### Error Boundary Not Catching Errors

**Problem:** Error Boundary doesn't catch the error.

**Possible Causes:**
1. Error is in event handler → Use try-catch
2. Error is in async code → Use try-catch or .catch()
3. Error is in the Error Boundary itself → Move Error Boundary up
4. Error is thrown before React renders → Check initialization code

### Error Boundary Catching Too Much

**Problem:** Small errors crash entire sections.

**Solution:** Use more granular error boundaries:

```tsx
// Instead of wrapping everything
<ErrorBoundary>
  <Section1 />
  <Section2 />
  <Section3 />
</ErrorBoundary>

// Wrap each section
<ErrorBoundary><Section1 /></ErrorBoundary>
<ErrorBoundary><Section2 /></ErrorBoundary>
<ErrorBoundary><Section3 /></ErrorBoundary>
```

---

## Summary

✅ **PaymentErrorBoundary** wraps payment routes for full-page error handling
✅ **ErrorBoundary** provides reusable error catching for any component
✅ **Helper components** (InlineError, CardError) offer pre-built error UIs
✅ **Test component** available for development testing
✅ **Integration-ready** for error reporting services
✅ **Best practices** documented for production use

**Next Phase:** Idempotency Utilities (Phase 1.10)
