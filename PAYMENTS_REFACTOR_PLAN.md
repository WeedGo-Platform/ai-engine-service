# Payments.tsx Refactoring Plan

**Current File**: 715 lines using direct fetch() calls
**Target**: Use PaymentContext + paymentServiceV2
**Goal**: Type safety, error handling, state management consistency

---

## Current Issues

1. ❌ **Direct fetch() calls** - No retry, no error handling, no type safety
2. ❌ **No PaymentContext** - Each component manages own state
3. ❌ **No idempotency** - Refunds and operations can be duplicated
4. ❌ **Manual loading states** - Duplicated across methods
5. ❌ **Inconsistent error handling** - Mix of console.error and toast
6. ❌ **No V2 API endpoints** - Using old /api/payments instead of /api/v2/payments

---

## Refactoring Strategy

### Option A: Full Refactor (Recommended)
- Wrap entire page in PaymentProvider
- Use usePayment() hook for all data
- Remove all fetch() calls
- Use paymentServiceV2 for operations
- **Estimated Time**: 2-3 hours
- **Risk**: Medium (complete rewrite)

### Option B: Gradual Migration
- Keep existing structure
- Replace fetch() with paymentServiceV2 calls one by one
- Add PaymentProvider later
- **Estimated Time**: 1 hour
- **Risk**: Low (incremental changes)

---

## Recommended Approach: Option B (Gradual)

Given the file size (715 lines), we'll do gradual migration to minimize risk.

### Step 1: Add Imports

```typescript
// Add to imports
import { paymentService } from '../services/paymentServiceV2';
import type {
  PaymentTransactionDTO,
  TransactionFilters,
  PaymentMetrics as V2PaymentMetrics,
  CreateRefundRequest,
} from '../types/payment';
import { ApiError, NetworkError, AuthenticationError } from '../utils/api-error-handler';
```

### Step 2: Update fetchTransactions()

**Before:**
```typescript
const fetchTransactions = async () => {
  try {
    const params = new URLSearchParams({
      start_date: format(dateRange.from, 'yyyy-MM-dd'),
      end_date: format(dateRange.to, 'yyyy-MM-dd'),
      status: statusFilter,
      provider: providerFilter,
    });

    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/transactions?${params}`);
    const data = await response.json();
    setTransactions(data);
  } catch (error) {
    console.error('Error fetching transactions:', error);
  }
};
```

**After:**
```typescript
const fetchTransactions = async () => {
  try {
    setIsLoading(true);

    const filters: TransactionFilters = {
      start_date: format(dateRange.from, 'yyyy-MM-dd'),
      end_date: format(dateRange.to, 'yyyy-MM-dd'),
      status: statusFilter !== 'all' ? statusFilter : undefined,
      // provider: providerFilter !== 'all' ? providerFilter : undefined,
      limit: 100,
      offset: 0,
    };

    const response = await paymentService.getTransactions(tenantId, filters);
    setTransactions(response.transactions);
  } catch (error) {
    if (error instanceof AuthenticationError) {
      toast({
        variant: 'destructive',
        title: t('common:errors.authentication'),
        description: t('common:errors.authenticationDescription'),
      });
    } else if (error instanceof NetworkError) {
      toast({
        variant: 'destructive',
        title: t('common:errors.network'),
        description: t('common:errors.networkDescription'),
      });
    } else if (error instanceof ApiError) {
      toast({
        variant: 'destructive',
        title: t('payments:messages.error.fetchTransactions'),
        description: error.getUserMessage(),
      });
    } else {
      toast({
        variant: 'destructive',
        title: t('payments:messages.error.fetchTransactions'),
        description: t('common:errors.generic'),
      });
    }
  } finally {
    setIsLoading(false);
  }
};
```

### Step 3: Update fetchMetrics()

**Before:**
```typescript
const fetchMetrics = async () => {
  try {
    const params = new URLSearchParams({
      start_date: format(dateRange.from, 'yyyy-MM-dd'),
      end_date: format(dateRange.to, 'yyyy-MM-dd'),
    });
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/metrics?${params}`);
    const data = await response.json();
    setMetrics(data);
  } catch (error) {
    console.error('Error fetching metrics:', error);
  }
};
```

**After:**
```typescript
const fetchMetrics = async () => {
  try {
    const metricsData = await paymentService.getPaymentStats(tenantId, {
      start: format(dateRange.from, 'yyyy-MM-dd'),
      end: format(dateRange.to, 'yyyy-MM-dd'),
    });

    // Map V2 metrics to component interface
    setMetrics({
      total_transactions: metricsData.total_transactions,
      successful_transactions: metricsData.successful_transactions,
      failed_transactions: metricsData.failed_transactions,
      total_amount: metricsData.total_volume,
      total_fees: metricsData.total_fees || 0,
      total_refunds: metricsData.total_refunds || 0,
      success_rate: metricsData.success_rate,
      avg_transaction_time: metricsData.average_transaction_time || 0,
    });
  } catch (error) {
    // Non-critical, log but don't toast
    console.error('Error fetching metrics:', error);
    setMetrics(null);
  }
};
```

### Step 4: Update handleRefund()

**Before:**
```typescript
const handleRefund = async () => {
  if (!selectedTransaction || !refundAmount) return;

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/refund`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transaction_id: selectedTransaction.id,
        amount: parseFloat(refundAmount),
        reason: refundReason,
      }),
    });

    if (!response.ok) throw new Error('Refund failed');

    toast({
      title: t('payments:messages.success.refund'),
      description: t('payments:messages.success.refundDescription'),
    });

    setIsRefundDialogOpen(false);
    fetchTransactions();
    fetchMetrics();
  } catch (error) {
    toast({
      variant: 'destructive',
      title: t('payments:messages.error.refund'),
    });
  }
};
```

**After:**
```typescript
const handleRefund = async () => {
  if (!selectedTransaction || !refundAmount) return;

  try {
    const refundRequest: CreateRefundRequest = {
      amount: parseFloat(refundAmount),
      currency: selectedTransaction.currency,
      reason: refundReason || 'Customer requested refund',
      tenant_id: tenantId,
    };

    // Idempotency automatically applied
    const refund = await paymentService.refundTransaction(
      selectedTransaction.id,
      refundRequest
    );

    toast({
      title: t('payments:messages.success.refund'),
      description: t('payments:messages.success.refundDescription', {
        amount: refundAmount,
        transactionId: refund.id,
      }),
    });

    setIsRefundDialogOpen(false);
    setRefundAmount('');
    setRefundReason('');

    // Refresh data
    await Promise.all([
      fetchTransactions(),
      fetchMetrics(),
    ]);
  } catch (error) {
    if (error instanceof ApiError) {
      toast({
        variant: 'destructive',
        title: t('payments:messages.error.refund'),
        description: error.getUserMessage(),
      });
    } else {
      toast({
        variant: 'destructive',
        title: t('payments:messages.error.refund'),
        description: t('common:errors.generic'),
      });
    }
  }
};
```

---

## Implementation Order

1. ✅ Add imports (paymentServiceV2, types, error classes)
2. ✅ Update fetchTransactions() - Replace fetch with getTransactions()
3. ✅ Update fetchMetrics() - Replace fetch with getPaymentStats()
4. ✅ Update processRefund() - Replace fetch with refundTransaction()
5. ✅ Update fetchProviders() - Use getProviders() with V2 service
6. ✅ Update toggleProviderStatus() - Use updateProvider() with V2 service
7. ✅ Update error handling - Use ApiError classes
8. ✅ Add tenantId extraction from route params
9. ⏳ Add PaymentProvider wrapper (future enhancement)
10. ⏳ Use usePayment() hook (future enhancement)

---

## Benefits After Refactor

### Before
- ❌ 4 different fetch() call patterns
- ❌ Inconsistent error handling
- ❌ No retry on network failures
- ❌ No idempotency (duplicate refunds possible)
- ❌ No type safety on API responses

### After
- ✅ Consistent paymentServiceV2 calls
- ✅ Centralized error handling with ApiError
- ✅ Automatic retry on network/server errors
- ✅ Idempotency on all write operations
- ✅ Full TypeScript type safety
- ✅ Reusable across all payment components

---

## Testing Checklist

After refactoring, test:

- [ ] Transactions list loads correctly
- [ ] Metrics display correctly
- [ ] Date range filtering works
- [ ] Status filtering works
- [ ] Search functionality works
- [ ] Refund dialog opens
- [ ] Refund processes successfully
- [ ] Error handling displays proper messages
- [ ] Loading states show correctly
- [ ] Refresh button works
- [ ] No duplicate API calls on mount

---

## Files to Modify

1. **Payments.tsx** (~100 lines changed)
   - Update imports
   - Replace 4 fetch() calls with paymentServiceV2
   - Update error handling
   - Add tenantId prop/context

---

## Future Enhancements (Phase 2)

Once core refactor is complete, consider:

1. **Add PaymentProvider Wrapper**
   ```typescript
   // In App.tsx
   {
     path: 'payments',
     element: (
       <PaymentErrorBoundary>
         <PaymentProvider>
           <Payments />
         </PaymentProvider>
       </PaymentErrorBoundary>
     )
   }
   ```

2. **Use PaymentContext**
   ```typescript
   const {
     state,
     fetchTransactions,
     fetchMetrics,
     refundTransaction,
   } = usePayment();
   ```

3. **Remove Local State**
   - Use context state instead of local useState
   - Automatic state sharing across components
   - Reduced duplicate API calls

---

## Decision

**Recommended**: Proceed with Option B (Gradual Migration)

1. Keep existing UI structure (works well)
2. Replace fetch() calls with paymentServiceV2 (low risk)
3. Add proper error handling (high value)
4. Add idempotency to refunds (critical for safety)
5. Defer PaymentContext integration to Phase 2 (optional enhancement)

**Estimated Time**: 30-45 minutes
**Risk Level**: Low
**Value**: High (immediate improvements to safety and reliability)
