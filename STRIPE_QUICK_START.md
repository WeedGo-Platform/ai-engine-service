# Stripe Subscription Quick Start

## 5-Minute Setup

### 1. Get Stripe Keys (2 minutes)

```bash
# Go to: https://dashboard.stripe.com/test/apikeys
# Copy both keys and add to .env:

STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXX  # Get from webhooks section
STRIPE_ENVIRONMENT=test
```

### 2. Create Stripe Products (2 minutes)

Using Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe
stripe login

# Create Professional Plan
PROF_PROD=$(stripe products create \
  --name="WeedGo Professional Plan" \
  --description="Up to 5 stores, 25 users, 10,000 products" \
  -ojson | jq -r .id)

# Create Monthly Price ($199 CAD)
PROF_MONTHLY=$(stripe prices create \
  --product=$PROF_PROD \
  --currency=cad \
  --unit_amount=19900 \
  --recurring[interval]=month \
  -ojson | jq -r .id)

# Create Enterprise Plan
ENT_PROD=$(stripe products create \
  --name="WeedGo Enterprise Plan" \
  --description="Unlimited stores, users, and products" \
  -ojson | jq -r .id)

# Create Monthly Price ($499 CAD)
ENT_MONTHLY=$(stripe prices create \
  --product=$ENT_PROD \
  --currency=cad \
  --unit_amount=49900 \
  --recurring[interval]=month \
  -ojson | jq -r .id)

echo "Professional Monthly Price ID: $PROF_MONTHLY"
echo "Enterprise Monthly Price ID: $ENT_MONTHLY"
```

### 3. Update Code with Price IDs (1 minute)

Edit `src/Backend/api/subscription_endpoints.py`:

```python
SUBSCRIPTION_PRICING = {
    "professional": {
        "stripe_price_id": {
            "monthly": "price_XXXXX",  # Paste $PROF_MONTHLY here
            "quarterly": "price_XXXXX",
            "annual": "price_XXXXX"
        },
        # ...
    },
    "enterprise": {
        "stripe_price_id": {
            "monthly": "price_XXXXX",  # Paste $ENT_MONTHLY here
            "quarterly": "price_XXXXX",
            "annual": "price_XXXXX"
        },
        # ...
    }
}
```

### 4. Start Webhook Listener (<1 minute)

Terminal 1:
```bash
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe
# Copy the webhook signing secret (whsec_...) to .env
```

Terminal 2:
```bash
# Start your server
cd src/Backend
python main.py
```

### 5. Test Subscription Creation

```bash
curl -X POST http://localhost:8000/api/subscriptions/create \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "plan_tier": "professional",
    "billing_frequency": "monthly",
    "customer_email": "test@example.com",
    "customer_name": "Test Company",
    "trial_days": 14
  }'
```

Expected output:
```json
{
  "subscription_id": "...",
  "status": "trialing",
  "stripe_subscription_id": "sub_...",
  "trial_end_date": "2025-11-08"
}
```

✅ **Done!** Your subscription system is ready.

## Test Payment Flow

### Add Payment Method

```bash
# Create payment method with test card 4242 4242 4242 4242
curl -X POST http://localhost:8000/api/subscriptions/create \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "plan_tier": "professional",
    "billing_frequency": "monthly",
    "payment_method_id": "pm_card_visa",
    "customer_email": "test@example.com",
    "customer_name": "Test Company"
  }'
```

### Simulate Successful Payment

```bash
stripe trigger invoice.payment_succeeded
```

Check logs:
```bash
# You should see:
# "Recording successful payment for subscription..."
# "Subscription renewed until..."
```

### Simulate Failed Payment

```bash
stripe trigger invoice.payment_failed
```

Check logs:
```bash
# You should see:
# "Payment failed for subscription..."
# "Subscription marked as PAST_DUE"
```

## API Endpoints Cheat Sheet

```bash
# Create subscription
POST /api/subscriptions/create

# Get subscription
GET /api/subscriptions/{tenant_id}

# Upgrade plan
PATCH /api/subscriptions/{subscription_id}/upgrade
{
  "new_tier": "enterprise"
}

# Cancel subscription
DELETE /api/subscriptions/{subscription_id}/cancel
{
  "cancel_immediately": false,
  "reason": "Customer request"
}

# Reactivate subscription
POST /api/subscriptions/{subscription_id}/reactivate

# Webhook endpoint
POST /api/webhooks/stripe
```

## Common Test Cards

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Declined |
| 4000 0000 0000 9995 | Insufficient funds |
| 4000 0000 0000 0069 | Expired card |

Expiry: Any future date (e.g., 12/25)  
CVC: Any 3 digits (e.g., 123)

## Troubleshooting

### "Stripe payment provider not configured"
→ Check `STRIPE_SECRET_KEY` in `.env`

### Webhook signature validation fails
→ Use Stripe CLI forwarding for local testing:
```bash
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe
```

### Subscription not created in Stripe
→ Verify price IDs in `SUBSCRIPTION_PRICING` match Stripe dashboard

## Next Steps

1. **Frontend Integration**: Add Stripe Elements to `TenantSignup.tsx`
2. **Email Notifications**: Implement payment confirmation emails
3. **Customer Portal**: Add self-service subscription management
4. **Production Setup**: Switch to live Stripe keys and create production webhook endpoint

## Full Documentation

See [STRIPE_SUBSCRIPTION_SETUP_GUIDE.md](./STRIPE_SUBSCRIPTION_SETUP_GUIDE.md) for complete details.
