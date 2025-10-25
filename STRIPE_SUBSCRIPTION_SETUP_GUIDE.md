# Stripe Subscription Integration Guide

## Overview

WeedGo now supports tenant subscription billing through Stripe integration. This document provides complete setup instructions, configuration details, and testing procedures.

## Architecture

### Components

1. **Stripe Payment Provider** (`stripe_provider.py`)
   - Handles all Stripe API interactions
   - Customer management
   - Subscription lifecycle
   - Payment method tokenization
   - Webhook signature validation

2. **Subscription API Endpoints** (`subscription_endpoints.py`)
   - `POST /api/subscriptions/create` - Create new subscription
   - `GET /api/subscriptions/{tenant_id}` - Get active subscription
   - `PATCH /api/subscriptions/{id}/upgrade` - Upgrade/downgrade plan
   - `DELETE /api/subscriptions/{id}/cancel` - Cancel subscription
   - `POST /api/subscriptions/{id}/reactivate` - Reactivate cancelled subscription

3. **Webhook Handler** (`stripe_webhooks.py`)
   - `POST /api/webhooks/stripe` - Process Stripe events
   - Handles: payment_succeeded, payment_failed, subscription_deleted, subscription_updated, trial_will_end

4. **Subscription Repository** (`subscription_repository.py`)
   - Database persistence layer
   - Queries by tenant_id, subscription_id, stripe_subscription_id
   - CRUD operations with domain model

## Setup Instructions

### 1. Create Stripe Account

1. Go to https://dashboard.stripe.com/register
2. Complete account registration
3. Verify your email and business details
4. Enable Canadian currency (CAD) support

### 2. Get API Keys

#### Test Keys (for development)
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy the **Publishable key** (starts with `pk_test_`)
3. Copy the **Secret key** (starts with `sk_test_`)

#### Production Keys (for live deployment)
1. Go to https://dashboard.stripe.com/apikeys
2. Copy the **Publishable key** (starts with `pk_live_`)
3. Copy the **Secret key** (starts with `sk_live_`)

### 3. Create Products and Prices

You need to create recurring prices in Stripe for each plan tier and billing frequency.

#### Using Stripe Dashboard

1. Go to https://dashboard.stripe.com/test/products
2. Click "Add product"

**Professional Plan:**
- Name: "WeedGo Professional Plan"
- Description: "Up to 5 stores, 25 users, 10,000 products"
- Click "Add pricing"
  
  **Monthly:**
  - Price: $199.00 CAD
  - Billing period: Monthly
  - Save the Price ID (e.g., `price_1234567890`)
  
  **Quarterly:**
  - Price: $537.00 CAD (10% discount)
  - Billing period: Every 3 months
  - Save the Price ID
  
  **Annual:**
  - Price: $1,990.00 CAD (17% discount)
  - Billing period: Yearly
  - Save the Price ID

**Enterprise Plan:**
- Name: "WeedGo Enterprise Plan"
- Description: "Unlimited stores, users, and products"
- Create monthly ($499), quarterly ($1,347), and annual ($4,990) prices

#### Using Stripe CLI (Alternative)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe
stripe login

# Create Professional Plan Product
stripe products create \
  --name="WeedGo Professional Plan" \
  --description="Up to 5 stores, 25 users, 10,000 products"

# Create Monthly Price (replace prod_XXX with product ID)
stripe prices create \
  --product=prod_XXX \
  --currency=cad \
  --unit_amount=19900 \
  --recurring[interval]=month

# Create Quarterly Price
stripe prices create \
  --product=prod_XXX \
  --currency=cad \
  --unit_amount=53700 \
  --recurring[interval]=month \
  --recurring[interval_count]=3

# Create Annual Price
stripe prices create \
  --product=prod_XXX \
  --currency=cad \
  --unit_amount=199000 \
  --recurring[interval]=year
```

### 4. Update Price IDs in Code

Edit `src/Backend/api/subscription_endpoints.py`:

```python
SUBSCRIPTION_PRICING = {
    "professional": {
        "stripe_price_id": {
            "monthly": "price_XXXXXXXXXXXXX",     # Replace with actual Stripe price ID
            "quarterly": "price_XXXXXXXXXXXXX",   # Replace with actual Stripe price ID
            "annual": "price_XXXXXXXXXXXXX"       # Replace with actual Stripe price ID
        },
        # ... other config
    },
    "enterprise": {
        "stripe_price_id": {
            "monthly": "price_XXXXXXXXXXXXX",     # Replace with actual Stripe price ID
            "quarterly": "price_XXXXXXXXXXXXX",   # Replace with actual Stripe price ID
            "annual": "price_XXXXXXXXXXXXX"       # Replace with actual Stripe price ID
        },
        # ... other config
    }
}
```

### 5. Configure Webhooks

Stripe webhooks notify your application about subscription events (payments, cancellations, etc.).

#### Local Development (using Stripe CLI)

```bash
# Forward webhooks to local server
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe

# Copy the webhook signing secret (starts with whsec_)
# Add to .env file
```

#### Production Deployment

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://your-domain.com/api/webhooks/stripe`
4. Select events to listen for:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
   - `customer.subscription.trial_will_end`
5. Copy the webhook signing secret
6. Add to production environment variables

### 6. Environment Variables

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_ENVIRONMENT=test  # or 'production'
```

**⚠️ SECURITY WARNING:**
- NEVER commit `.env` file to git
- Use secure secrets management in production (AWS Secrets Manager, Azure Key Vault, etc.)
- Rotate keys if accidentally exposed

### 7. Update API Gateway

Ensure the subscription and webhook routes are registered in your FastAPI app.

Edit `src/Backend/main.py` or your main application file:

```python
from api.subscription_endpoints import router as subscription_router
from webhooks.stripe_webhooks import router as webhook_router

# Register routers
app.include_router(subscription_router)
app.include_router(webhook_router)
```

### 8. Database Migration

Ensure the `tenant_subscriptions` table exists with required fields.

```sql
-- If not exists, create tenant_subscriptions table
CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    billing_frequency VARCHAR(20) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) DEFAULT 0,
    trial_end_date DATE,
    next_billing_date DATE,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    failed_payment_count INT DEFAULT 0,
    last_payment_date TIMESTAMP,
    payment_method_id VARCHAR(100),
    auto_renew BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_tenant_subscriptions_status ON tenant_subscriptions(status);
CREATE INDEX idx_tenant_subscriptions_stripe_sub_id ON tenant_subscriptions((metadata->>'stripe_subscription_id'));
```

## Testing

### 1. Test Customer Creation

```bash
curl -X POST http://localhost:8000/api/subscriptions/create \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "plan_tier": "professional",
    "billing_frequency": "monthly",
    "customer_email": "test@example.com",
    "customer_name": "Test Tenant",
    "trial_days": 14
  }'
```

Expected Response:
```json
{
  "subscription_id": "sub_...",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "professional",
  "status": "trialing",
  "billing_frequency": "monthly",
  "base_price": 199.00,
  "next_billing_date": "2025-11-08",
  "trial_end_date": "2025-11-08",
  "stripe_subscription_id": "sub_...",
  "stripe_customer_id": "cus_...",
  "payment_status": "pending",
  "auto_renew": true,
  "created_at": "2025-10-25T..."
}
```

### 2. Test Stripe Test Cards

Use these test card numbers:

- **Success:** `4242 4242 4242 4242`
- **Declined:** `4000 0000 0000 0002`
- **Insufficient funds:** `4000 0000 0000 9995`
- **Expired card:** `4000 0000 0000 0069`

Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)

### 3. Test Webhook Events

If using Stripe CLI:

```bash
# Trigger payment success event
stripe trigger invoice.payment_succeeded

# Trigger payment failure event
stripe trigger invoice.payment_failed

# Trigger subscription cancellation
stripe trigger customer.subscription.deleted
```

Check logs to verify webhook processing:
```bash
tail -f logs/application.log | grep "Stripe webhook"
```

### 4. Test Subscription Upgrade

```bash
curl -X PATCH http://localhost:8000/api/subscriptions/{subscription_id}/upgrade \
  -H "Content-Type: application/json" \
  -d '{
    "new_tier": "enterprise"
  }'
```

### 5. Test Subscription Cancellation

```bash
curl -X DELETE http://localhost:8000/api/subscriptions/{subscription_id}/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "cancel_immediately": false,
    "reason": "Testing cancellation flow"
  }'
```

## Pricing Configuration

Current pricing structure (CAD):

| Tier | Monthly | Quarterly | Annual | Max Stores | Max Users | Max Products |
|------|---------|-----------|--------|------------|-----------|--------------|
| Community | $0 | $0 | $0 | 1 | 3 | 100 |
| Professional | $199 | $537 | $1,990 | 5 | 25 | 10,000 |
| Enterprise | $499 | $1,347 | $4,990 | Unlimited | Unlimited | Unlimited |

**Discounts:**
- Quarterly: ~10% discount vs monthly
- Annual: ~17% discount vs monthly

## Webhook Event Flow

### Successful Payment
1. Stripe charges customer
2. `invoice.payment_succeeded` webhook sent
3. Webhook handler processes event
4. Subscription renewed in database
5. `next_billing_date` updated
6. Payment confirmation email sent (TODO)

### Failed Payment
1. Stripe attempts to charge customer
2. `invoice.payment_failed` webhook sent
3. Webhook handler processes event
4. Subscription marked as `PAST_DUE`
5. `failed_payment_count` incremented
6. Payment failure email sent (TODO)
7. If 3+ failures: Subscription suspended

### Subscription Cancelled
1. Customer cancels via Stripe portal or API
2. `customer.subscription.deleted` webhook sent
3. Webhook handler processes event
4. Subscription marked as `CANCELLED`
5. Cancellation email sent (TODO)

## Frontend Integration

### Stripe Elements Setup

Install Stripe.js in frontend:

```bash
cd src/Frontend/ai-admin-dashboard
npm install @stripe/stripe-js @stripe/react-stripe-js
```

Update `TenantSignup.tsx`:

```tsx
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

// Initialize Stripe
const stripePromise = loadStripe('pk_test_XXXXXXXXXXXXXXXXXXXXXXXX');

function PaymentForm() {
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!stripe || !elements) return;

    // Create payment method
    const { error, paymentMethod } = await stripe.createPaymentMethod({
      type: 'card',
      card: elements.getElement(CardElement),
    });

    if (error) {
      console.error(error);
      return;
    }

    // Send to backend
    const response = await fetch('/api/subscriptions/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: tenantId,
        plan_tier: selectedPlan,
        billing_frequency: billingCycle,
        payment_method_id: paymentMethod.id,
        customer_email: email,
        customer_name: name,
        trial_days: 14
      })
    });

    const result = await response.json();
    console.log('Subscription created:', result);
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement />
      <button type="submit" disabled={!stripe}>
        Start Free Trial
      </button>
    </form>
  );
}

// Wrap in Elements provider
function Checkout() {
  return (
    <Elements stripe={stripePromise}>
      <PaymentForm />
    </Elements>
  );
}
```

## Security Best Practices

1. **API Keys Protection**
   - Store in environment variables, never in code
   - Use different keys for test/production
   - Rotate keys if compromised

2. **Webhook Validation**
   - Always validate webhook signatures
   - Reject requests with invalid signatures
   - Log suspicious webhook attempts

3. **Payment Method Security**
   - Never store raw card numbers
   - Use Stripe Elements for PCI compliance
   - Only store Stripe payment method IDs

4. **Subscription Access Control**
   - Verify tenant ownership before showing subscription details
   - Implement role-based access control (RBAC)
   - Log all subscription modifications

## Troubleshooting

### Issue: "Stripe payment provider not configured"

**Cause:** Missing or invalid `STRIPE_SECRET_KEY` environment variable

**Solution:**
1. Verify `.env` file contains `STRIPE_SECRET_KEY`
2. Restart the server after updating environment variables
3. Check key starts with `sk_test_` (test) or `sk_live_` (production)

### Issue: Webhook signature validation fails

**Cause:** Incorrect webhook secret or signature mismatch

**Solution:**
1. Verify `STRIPE_WEBHOOK_SECRET` matches the value from Stripe dashboard
2. For local testing, use Stripe CLI forwarding
3. Check that raw request body is used for validation (not parsed JSON)

### Issue: Subscription not created in Stripe

**Cause:** Invalid price ID or missing payment method

**Solution:**
1. Verify price IDs in `SUBSCRIPTION_PRICING` match Stripe dashboard
2. Ensure payment method is attached to customer
3. Check Stripe dashboard logs for detailed error messages

### Issue: Payment fails immediately

**Cause:** Invalid card, insufficient funds, or bank decline

**Solution:**
1. Use Stripe test cards for testing
2. Check card expiry date is in the future
3. Verify billing address if required
4. Review Stripe dashboard for decline reason

## Monitoring

### Key Metrics to Monitor

1. **Subscription Creation Rate**
   - Track new subscriptions per day
   - Monitor conversion from trial to paid

2. **Payment Failure Rate**
   - Alert on failed_payment_count > 2
   - Track decline reasons

3. **Churn Rate**
   - Monitor cancellations per month
   - Analyze cancellation reasons

4. **Revenue Metrics**
   - Monthly Recurring Revenue (MRR)
   - Annual Recurring Revenue (ARR)
   - Average Revenue Per User (ARPU)

### Logging

All subscription events are logged:

```bash
# View subscription creation logs
grep "Created subscription" logs/application.log

# View payment processing logs
grep "payment_succeeded\|payment_failed" logs/application.log

# View webhook processing
grep "Stripe webhook" logs/application.log
```

## Next Steps

1. ✅ Stripe provider implementation
2. ✅ Subscription API endpoints
3. ✅ Webhook handlers
4. ⏳ Frontend Stripe Elements integration
5. ⏳ Email notification system
6. ⏳ Customer portal for self-service
7. ⏳ Usage-based billing (future enhancement)
8. ⏳ Dunning management for failed payments

## Support

For Stripe-specific issues:
- Stripe Documentation: https://stripe.com/docs
- Stripe Support: https://support.stripe.com
- Stripe Status: https://status.stripe.com

For WeedGo integration issues:
- Check application logs
- Review this documentation
- Contact development team
