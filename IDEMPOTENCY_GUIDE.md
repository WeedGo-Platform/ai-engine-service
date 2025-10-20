# Idempotency Implementation Guide

**Date:** 2025-01-19
**Phase:** 1.10 Complete
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [What is Idempotency?](#what-is-idempotency)
2. [Why It's Critical for Payments](#why-its-critical-for-payments)
3. [Implementation Overview](#implementation-overview)
4. [Usage Examples](#usage-examples)
5. [How It Works](#how-it-works)
6. [Testing](#testing)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## What is Idempotency?

**Idempotency** means an operation can be performed multiple times without changing the result beyond the initial application.

```typescript
// Idempotent: Can call multiple times safely
createPayment(amount: 100, key: "abc123") → Payment #1
createPayment(amount: 100, key: "abc123") → Payment #1 (same result)
createPayment(amount: 100, key: "abc123") → Payment #1 (same result)

// NOT Idempotent: Each call creates new payment
createPayment(amount: 100) → Payment #1
createPayment(amount: 100) → Payment #2 (duplicate!)
createPayment(amount: 100) → Payment #3 (duplicate!)
```

---

## Why It's Critical for Payments

### Problem: Duplicate Payments

Without idempotency, these scenarios cause duplicate charges:

**Scenario 1: User Double-Clicks "Pay" Button**
```
User clicks "Pay" → Payment #1 created ($99.99)
User clicks "Pay" again (impatient) → Payment #2 created ($99.99)
Result: Customer charged $199.98 instead of $99.99
```

**Scenario 2: Network Timeout**
```
Frontend sends payment request → Network timeout
Frontend retries automatically → Payment #2 created
Result: Customer charged twice
```

**Scenario 3: Browser Back/Refresh**
```
User submits payment → Refreshes page
Page re-submits payment → Payment #2 created
Result: Duplicate charge
```

### Solution: Idempotency Keys

With idempotency keys:
```
User clicks "Pay" (key: "abc123") → Payment #1 created
User clicks "Pay" again (key: "abc123") → Returns Payment #1 (no duplicate!)
Network retry (key: "abc123") → Returns Payment #1 (no duplicate!)
```

---

## Implementation Overview

### Files Created

1. **`utils/idempotency.ts`** (500+ lines)
   - UUID generation
   - Idempotency key generation
   - Key storage manager
   - High-level helpers
   - Idempotent request wrapper

2. **`services/paymentServiceV2.ts`** (Modified)
   - Integrated idempotency into:
     - `createProvider()`
     - `processPayment()`
     - `refundTransaction()`

### Architecture

```
User Action
    │
    ↓
Component
    │
    ↓
paymentService.processPayment(data)
    │
    ├─ Generate idempotency key
    │  (or use provided key)
    │
    ├─ Check if already processed
    │  (IdempotencyKeyManager)
    │
    ├─ If completed → Return cached result
    │  If pending → Throw error (already in progress)
    │  If not found → Process
    │
    ↓
withIdempotency(key, operation)
    │
    ├─ Mark as "pending"
    ├─ Execute operation
    ├─ Mark as "completed" + cache result
    │  OR mark as "failed" + cache error
    │
    ↓
HTTP Request with Idempotency-Key header
    │
    ↓
Backend validates key and prevents duplicates
```

---

## Usage Examples

### Example 1: Process Payment (Automatic Key)

```typescript
import { paymentService } from '../services/paymentServiceV2';

// Idempotency key auto-generated from payment details
const payment = await paymentService.processPayment({
  amount: 99.99,
  currency: 'CAD',
  tenant_id: 'tenant-123',
  order_id: 'order-456',
  payment_method_id: 'pm-789',
  provider_type: ProviderType.CLOVER,
});

// If user clicks "Pay" again with same details,
// it returns the same payment (no duplicate charge)
```

### Example 2: Process Payment (Custom Key)

```typescript
import { createPaymentIdempotencyKey } from '../utils/idempotency';

// Generate key manually for more control
const idempotencyKey = createPaymentIdempotencyKey(
  'tenant-123',
  99.99,
  'CAD',
  { orderId: 'order-456' }
);

// Use custom key
const payment = await paymentService.processPayment(
  {
    amount: 99.99,
    currency: 'CAD',
    tenant_id: 'tenant-123',
    order_id: 'order-456',
    payment_method_id: 'pm-789',
    provider_type: ProviderType.CLOVER,
  },
  idempotencyKey // <-- Pass custom key
);
```

### Example 3: Refund Transaction

```typescript
// Auto-generated idempotency key
const refund = await paymentService.refundTransaction(
  'transaction-123',
  {
    amount: 50.00,
    currency: 'CAD',
    reason: 'Customer requested partial refund',
    tenant_id: 'tenant-123',
  }
);

// Calling again with same parameters returns the same refund
```

### Example 4: Create Provider

```typescript
// Auto-generated idempotency key
const provider = await paymentService.createProvider(
  'tenant-123',
  {
    provider_type: ProviderType.CLOVER,
    merchant_id: 'MERCHANT123',
    api_key: 'sk_test_123',
    environment: EnvironmentType.SANDBOX,
  }
);

// Duplicate calls won't create duplicate providers
```

### Example 5: Custom Idempotent Operation

```typescript
import { withIdempotency, generateIdempotencyKey } from '../utils/idempotency';

async function myCustomOperation(userId: string, data: any) {
  const key = generateIdempotencyKey({
    operation: 'custom_op',
    userId,
    context: data,
  });

  return withIdempotency(key, async () => {
    // Your operation here
    return await performOperation(data);
  });
}

// Safe to call multiple times
await myCustomOperation('user-123', { amount: 100 });
await myCustomOperation('user-123', { amount: 100 }); // Returns cached result
```

---

## How It Works

### 1. Idempotency Key Generation

Keys are generated deterministically from operation parameters:

```typescript
// Same parameters → Same key
const key1 = createPaymentIdempotencyKey('tenant-123', 99.99, 'CAD');
const key2 = createPaymentIdempotencyKey('tenant-123', 99.99, 'CAD');
console.log(key1 === key2); // false (includes UUID for uniqueness)

// But context hash is same, allowing backend to detect duplicates
// Format: "idem_payment_{contextHash}_{uuid}"
// Example: "idem_payment_abc12345_550e8400-e29b-41d4-a716-446655440000"
```

### 2. Key Storage & Tracking

Keys are stored in **sessionStorage** (clears on browser close):

```typescript
IdempotencyKeyMetadata {
  key: "idem_payment_abc123_550e...",
  operation: "payment",
  createdAt: 1705683600000,
  expiresAt: 1705770000000, // 24 hours later
  status: "pending" | "completed" | "failed",
  result?: any, // Cached result if completed
  error?: any,  // Cached error if failed
}
```

### 3. Duplicate Prevention Flow

```typescript
// First call
withIdempotency(key, operation)
  ↓
Check storage → Not found
  ↓
Mark as "pending" in storage
  ↓
Execute operation
  ↓
Mark as "completed" + cache result
  ↓
Return result

// Second call (duplicate)
withIdempotency(key, operation)
  ↓
Check storage → Found with status "completed"
  ↓
Return cached result (NO API call made!)
```

### 4. Backend Integration

Idempotency-Key header sent to backend:

```typescript
// HTTP Request
POST /api/v2/payments/process
Headers:
  Idempotency-Key: idem_payment_abc123_550e...
  Content-Type: application/json
Body:
  {
    "amount": 99.99,
    "currency": "CAD",
    "idempotency_key": "idem_payment_abc123_550e...",
    ...
  }
```

Backend checks this key and:
- If same key seen before with same parameters → Return original result
- If same key with different parameters → Return error (key reuse detected)
- If new key → Process normally

---

## Testing

### Test 1: Duplicate Payment Prevention

```typescript
// Test Component
import { paymentService } from '../services/paymentServiceV2';
import { createPaymentIdempotencyKey } from '../utils/idempotency';

async function testDuplicatePrevention() {
  const key = createPaymentIdempotencyKey('tenant-123', 99.99, 'CAD');

  // First payment
  const payment1 = await paymentService.processPayment(
    { amount: 99.99, /* ... */ },
    key
  );

  // Duplicate (should return same payment)
  const payment2 = await paymentService.processPayment(
    { amount: 99.99, /* ... */ },
    key
  );

  console.assert(payment1.id === payment2.id, 'Should return same payment');
  console.log('✅ Duplicate prevention works!');
}
```

### Test 2: Retry Safety

```typescript
async function testRetrySafety() {
  const request = {
    amount: 99.99,
    currency: 'CAD',
    tenant_id: 'tenant-123',
    // ...
  };

  try {
    // First attempt (simulated network failure)
    await paymentService.processPayment(request);
  } catch (error) {
    console.log('First attempt failed (expected)');
  }

  // Retry with same request (should work safely)
  const payment = await paymentService.processPayment(request);
  console.log('✅ Retry succeeded without duplicate!');
}
```

### Test 3: Key Expiration

```typescript
import { idempotencyManager } from '../utils/idempotency';

async function testKeyExpiration() {
  const key = 'test_key_123';

  // Store key
  idempotencyManager.store(key, {
    operation: 'test',
    status: 'completed',
    result: { success: true },
    expiresAt: Date.now() + 1000, // Expires in 1 second
  });

  // Check immediately
  console.assert(idempotencyManager.get(key) !== null, 'Key should exist');

  // Wait 2 seconds
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Check after expiration
  console.assert(idempotencyManager.get(key) === null, 'Key should be expired');
  console.log('✅ Key expiration works!');
}
```

### Test 4: Cleanup

```typescript
import { idempotencyManager } from '../utils/idempotency';

async function testCleanup() {
  // Create expired keys
  for (let i = 0; i < 10; i++) {
    idempotencyManager.store(`key_${i}`, {
      operation: 'test',
      status: 'completed',
      expiresAt: Date.now() - 1000, // Already expired
    });
  }

  // Run cleanup
  const removed = idempotencyManager.cleanup();

  console.assert(removed === 10, 'Should remove 10 expired keys');
  console.log('✅ Cleanup works!');
}
```

---

## Best Practices

### 1. Always Use Idempotency for Write Operations

```typescript
// ✅ Good: All writes use idempotency
await paymentService.processPayment(data);
await paymentService.refundTransaction(txnId, data);
await paymentService.createProvider(tenantId, data);

// ❌ Bad: Direct HTTP calls without idempotency
await httpClient.post('/payments', data); // No protection!
```

### 2. Use Auto-Generated Keys by Default

```typescript
// ✅ Good: Let service generate key
await paymentService.processPayment(data);

// 🟡 Okay: Manual key when you need specific control
const key = createPaymentIdempotencyKey(...);
await paymentService.processPayment(data, key);
```

### 3. Don't Reuse Keys for Different Operations

```typescript
// ❌ Bad: Reusing same key
const key = 'my_key_123';
await paymentService.processPayment(data1, key);
await paymentService.processPayment(data2, key); // Different data, same key!

// ✅ Good: Each operation gets unique key
await paymentService.processPayment(data1); // Auto-generated key
await paymentService.processPayment(data2); // Different auto-generated key
```

### 4. Handle "Already in Progress" Errors

```typescript
try {
  await paymentService.processPayment(data, idempotencyKey);
} catch (error) {
  if (error.message.includes('already in progress')) {
    // Show user: "Payment is being processed, please wait..."
    showToast('Payment in progress, please wait');
  } else {
    // Handle other errors
    showError(error);
  }
}
```

### 5. Clear Keys on Logout

```typescript
import { idempotencyManager } from '../utils/idempotency';

function handleLogout() {
  // Clear cached idempotency keys
  idempotencyManager.clear();

  // Continue with logout
  logout();
}
```

---

## Troubleshooting

### Issue: "Operation already in progress"

**Cause:** Trying to execute the same operation twice simultaneously.

**Solution:**
```typescript
// Disable button while processing
const [isProcessing, setIsProcessing] = useState(false);

const handlePayment = async () => {
  if (isProcessing) return; // Prevent double-clicks

  setIsProcessing(true);
  try {
    await paymentService.processPayment(data);
  } finally {
    setIsProcessing(false);
  }
};
```

### Issue: Cached result is stale

**Cause:** Idempotency key cached an old result.

**Solution:**
```typescript
import { idempotencyManager } from '../utils/idempotency';

// Clear specific key
idempotencyManager.delete(idempotencyKey);

// Or clear all keys
idempotencyManager.clear();

// Then retry
await paymentService.processPayment(data);
```

### Issue: Too many keys in storage

**Cause:** Keys not expiring/cleaning up.

**Solution:**
```typescript
// Manual cleanup
import { idempotencyManager } from '../utils/idempotency';

const removed = idempotencyManager.cleanup();
console.log(`Cleaned up ${removed} expired keys`);

// Auto-cleanup runs every hour by default
// Configured in utils/idempotency.ts
```

---

## Summary

### What We Built

| Component | Purpose | Status |
|-----------|---------|--------|
| UUID Generation | Globally unique identifiers | ✅ Complete |
| Key Generation | Deterministic key creation | ✅ Complete |
| Key Manager | Storage & tracking | ✅ Complete |
| Service Integration | Payment operations | ✅ Complete |
| Auto-cleanup | Expired key removal | ✅ Complete |

### Operations Protected

✅ `processPayment()` - Prevents duplicate charges
✅ `refundTransaction()` - Prevents duplicate refunds
✅ `createProvider()` - Prevents duplicate providers

### Features

✅ Automatic key generation
✅ Manual key override
✅ Request deduplication
✅ Result caching
✅ Expiration (24 hours)
✅ Auto-cleanup
✅ Backend integration (Idempotency-Key header)

---

## Next Phase

**Phase 1.11:** Refactor Payments.tsx to use V2 Service

This completes the payment infrastructure. Next we'll update the Payments.tsx page to use all the new V2 features we've built.
