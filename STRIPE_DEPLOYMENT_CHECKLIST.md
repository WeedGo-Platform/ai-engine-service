# Stripe Subscription Deployment Checklist

## ✅ Backend Implementation Complete

- [x] Stripe payment provider (`stripe_provider.py`) - 870 lines
- [x] Subscription API endpoints (`subscription_endpoints.py`) - 607 lines
- [x] Webhook handler (`stripe_webhooks.py`) - 378 lines
- [x] Repository enhancements (subscription queries)
- [x] Payment provider factory integration
- [x] Documentation (setup guide, quick start, summary)
- [x] Git commit (8 files, 3,245+ insertions)

## 🔧 Configuration Steps (Required)

### 1. Stripe Account Setup

- [ ] Create Stripe account at https://dashboard.stripe.com/register
- [ ] Verify email and business details
- [ ] Enable Canadian currency (CAD) support
- [ ] Get test API keys from https://dashboard.stripe.com/test/apikeys
- [ ] Get production API keys from https://dashboard.stripe.com/apikeys (later)

### 2. Create Products and Prices in Stripe

**Option A: Using Stripe Dashboard**

- [ ] Go to https://dashboard.stripe.com/test/products
- [ ] Create "WeedGo Professional Plan" product
  - [ ] Add monthly price: $199.00 CAD, recurring monthly
  - [ ] Add quarterly price: $537.00 CAD, recurring every 3 months
  - [ ] Add annual price: $1,990.00 CAD, recurring yearly
  - [ ] Copy all 3 price IDs
- [ ] Create "WeedGo Enterprise Plan" product
  - [ ] Add monthly price: $499.00 CAD, recurring monthly
  - [ ] Add quarterly price: $1,347.00 CAD, recurring every 3 months
  - [ ] Add annual price: $4,990.00 CAD, recurring yearly
  - [ ] Copy all 3 price IDs

**Option B: Using Stripe CLI** (faster)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe
stripe login

# Run the automated setup script (see STRIPE_QUICK_START.md)
# This creates products and prints price IDs
```

### 3. Update Code with Price IDs

- [ ] Open `src/Backend/api/subscription_endpoints.py`
- [ ] Find `SUBSCRIPTION_PRICING` dictionary (around line 75)
- [ ] Replace placeholder price IDs with actual Stripe price IDs:
  ```python
  "professional": {
      "stripe_price_id": {
          "monthly": "price_XXXXX",    # Replace with actual ID
          "quarterly": "price_XXXXX",  # Replace with actual ID
          "annual": "price_XXXXX"      # Replace with actual ID
      },
  }
  ```
- [ ] Save file

### 4. Configure Environment Variables

- [ ] Create or update `.env` file in project root:
  ```bash
  STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXX
  STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXX
  STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXX
  STRIPE_ENVIRONMENT=test
  ```
- [ ] Verify `.env` is in `.gitignore` (NEVER commit API keys)

### 5. Set Up Webhooks

**For Local Development:**

- [ ] Install Stripe CLI: `brew install stripe/stripe-cli/stripe`
- [ ] Run webhook forwarder: `stripe listen --forward-to http://localhost:8000/api/webhooks/stripe`
- [ ] Copy webhook signing secret (starts with `whsec_`)
- [ ] Add to `.env` as `STRIPE_WEBHOOK_SECRET`

**For Production:**

- [ ] Go to https://dashboard.stripe.com/webhooks
- [ ] Click "Add endpoint"
- [ ] Endpoint URL: `https://your-domain.com/api/webhooks/stripe`
- [ ] Select events:
  - [ ] `invoice.payment_succeeded`
  - [ ] `invoice.payment_failed`
  - [ ] `customer.subscription.deleted`
  - [ ] `customer.subscription.updated`
  - [ ] `customer.subscription.trial_will_end`
- [ ] Click "Add endpoint"
- [ ] Copy webhook signing secret
- [ ] Add to production environment as `STRIPE_WEBHOOK_SECRET`

### 6. Register API Routes

- [ ] Open `src/Backend/main.py` (or your main FastAPI app file)
- [ ] Add imports:
  ```python
  from api.subscription_endpoints import router as subscription_router
  from webhooks.stripe_webhooks import router as webhook_router
  ```
- [ ] Register routers:
  ```python
  app.include_router(subscription_router)
  app.include_router(webhook_router)
  ```
- [ ] Save file

### 7. Database Setup

- [ ] Verify `tenant_subscriptions` table exists
- [ ] Run index creation if needed:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
  CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_status ON tenant_subscriptions(status);
  CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_stripe_sub_id ON tenant_subscriptions((metadata->>'stripe_subscription_id'));
  ```

## 🧪 Testing (Required Before Production)

### 1. Start Server and Webhook Listener

Terminal 1 - Webhook Forwarder:
```bash
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe
```

Terminal 2 - Application Server:
```bash
cd src/Backend
python main.py
# or
uvicorn main:app --reload
```

### 2. Test Subscription Creation

- [ ] Run test API call:
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

- [ ] Verify response contains:
  - `subscription_id`
  - `status: "trialing"`
  - `stripe_subscription_id`
  - `trial_end_date` (14 days from now)

- [ ] Check Stripe dashboard:
  - [ ] Customer created
  - [ ] Subscription created with trial
  - [ ] Status shows "trialing"

### 3. Test Payment Success

- [ ] Trigger payment success webhook:
  ```bash
  stripe trigger invoice.payment_succeeded
  ```

- [ ] Check logs for:
  - "Processing Stripe webhook: invoice.payment_succeeded"
  - "Recording successful payment for subscription..."
  - "Subscription renewed until..."

- [ ] Verify in database:
  ```sql
  SELECT status, payment_status, next_billing_date 
  FROM tenant_subscriptions 
  WHERE tenant_id = '123e4567-e89b-12d3-a456-426614174000';
  ```

### 4. Test Payment Failure

- [ ] Trigger payment failure webhook:
  ```bash
  stripe trigger invoice.payment_failed
  ```

- [ ] Check logs for:
  - "Payment failed for subscription..."
  - "Subscription marked as PAST_DUE"

- [ ] Verify status changed to `past_due` in database

### 5. Test Subscription Upgrade

- [ ] Get subscription ID from creation response
- [ ] Run upgrade API call:
  ```bash
  curl -X PATCH http://localhost:8000/api/subscriptions/{subscription_id}/upgrade \
    -H "Content-Type: application/json" \
    -d '{"new_tier": "enterprise"}'
  ```

- [ ] Verify response shows new tier and price
- [ ] Check Stripe dashboard shows updated subscription

### 6. Test Subscription Cancellation

- [ ] Run cancellation API call:
  ```bash
  curl -X DELETE http://localhost:8000/api/subscriptions/{subscription_id}/cancel \
    -H "Content-Type: application/json" \
    -d '{
      "cancel_immediately": false,
      "reason": "Testing cancellation"
    }'
  ```

- [ ] Verify response shows cancellation scheduled
- [ ] Check Stripe dashboard shows "Cancels at period end"

## 🎨 Frontend Integration (Pending)

- [ ] Install Stripe.js in frontend:
  ```bash
  cd src/Frontend/ai-admin-dashboard
  npm install @stripe/stripe-js @stripe/react-stripe-js
  ```

- [ ] Update `TenantSignup.tsx` with Stripe Elements
  - [ ] Import Stripe libraries
  - [ ] Wrap payment form in `<Elements>` provider
  - [ ] Add `<CardElement>` for secure card input
  - [ ] Create payment method on form submit
  - [ ] Send payment method ID to backend

- [ ] Add subscription management UI
  - [ ] Display current subscription details
  - [ ] Show invoice history
  - [ ] Add "Upgrade Plan" button
  - [ ] Add "Cancel Subscription" button
  - [ ] Add "Update Payment Method" form

- [ ] Test frontend flow:
  - [ ] User selects plan
  - [ ] User enters card details
  - [ ] Payment method created successfully
  - [ ] Subscription created in backend
  - [ ] User sees confirmation with trial period

## 📧 Email Notifications (Pending)

- [ ] Set up email service (SendGrid, AWS SES, etc.)
- [ ] Create email templates:
  - [ ] Payment confirmation
  - [ ] Payment failure notification
  - [ ] Trial ending reminder (3 days before)
  - [ ] Subscription cancellation confirmation
  - [ ] Invoice receipt

- [ ] Implement email sending in webhook handlers:
  - [ ] Update `send_payment_confirmation_email()` in `stripe_webhooks.py`
  - [ ] Update `send_payment_failure_email()`
  - [ ] Update `send_trial_ending_email()`
  - [ ] Update `send_cancellation_email()`

## 🚀 Production Deployment

### Pre-Production

- [ ] Create production Stripe account (if different from test)
- [ ] Get production API keys
- [ ] Create production products and prices
- [ ] Update price IDs in code for production
- [ ] Set up production webhook endpoint (HTTPS required)
- [ ] Configure production environment variables
- [ ] Use secrets manager (AWS Secrets Manager / Azure Key Vault)
- [ ] Enable Stripe Radar for fraud detection
- [ ] Configure SSL/TLS certificate for webhook endpoint
- [ ] Set up monitoring and alerting

### Production Launch

- [ ] Deploy backend with production Stripe keys
- [ ] Verify webhook endpoint is accessible
- [ ] Test with Stripe test mode in production environment
- [ ] Switch to live Stripe keys
- [ ] Test with real card (small amount)
- [ ] Monitor first 10 real subscriptions closely
- [ ] Set up customer support process
- [ ] Enable invoice email delivery in Stripe

### Post-Launch Monitoring

- [ ] Monitor subscription creation rate
- [ ] Track payment success/failure rates
- [ ] Review webhook processing logs
- [ ] Monitor database performance
- [ ] Track revenue metrics (MRR, ARR)
- [ ] Review customer feedback
- [ ] Set up alerts for payment failures

## 📊 Monitoring Setup

### Key Metrics to Track

- [ ] Set up dashboard for:
  - Subscription creation rate (daily/weekly/monthly)
  - Trial-to-paid conversion rate
  - Payment success rate (target: >95%)
  - Payment failure rate
  - Churn rate (target: <5% monthly)
  - Monthly Recurring Revenue (MRR)
  - Annual Recurring Revenue (ARR)
  - Average Revenue Per User (ARPU)

### Alerts to Configure

- [ ] Payment failure rate > 5%
- [ ] Webhook processing errors
- [ ] API response time > 500ms
- [ ] Failed payment count > 2 for any subscription
- [ ] Subscription creation failures

## 🔒 Security Checklist

- [ ] Verify `.env` file is in `.gitignore`
- [ ] Never commit API keys to git
- [ ] Use HTTPS for production webhook endpoint
- [ ] Validate all webhook signatures
- [ ] Implement rate limiting on subscription endpoints
- [ ] Add tenant ownership verification middleware
- [ ] Configure firewall to allow only Stripe IPs for webhooks
- [ ] Enable Stripe Radar for fraud detection
- [ ] Set up PCI compliance scanning
- [ ] Implement proper error handling (no key leakage)
- [ ] Use secrets manager in production
- [ ] Rotate API keys periodically
- [ ] Log security events

## 📚 Documentation

- [x] Setup guide created (`STRIPE_SUBSCRIPTION_SETUP_GUIDE.md`)
- [x] Quick start guide created (`STRIPE_QUICK_START.md`)
- [x] Implementation summary created (`STRIPE_IMPLEMENTATION_SUMMARY.md`)
- [ ] Add API documentation to OpenAPI/Swagger
- [ ] Create runbook for common issues
- [ ] Document escalation procedures
- [ ] Create customer onboarding guide

## ✨ Next Steps (Future Enhancements)

- [ ] Implement usage-based billing
- [ ] Add add-on products (extra stores, users)
- [ ] Add promo codes and discounts
- [ ] Implement affiliate/referral tracking
- [ ] Add multi-currency support
- [ ] Integrate Stripe Tax for automatic tax calculation
- [ ] Add Stripe Customer Portal for self-service
- [ ] Implement dunning management workflow
- [ ] Add revenue recognition reporting
- [ ] Create admin dashboard for subscription analytics

## 🆘 Troubleshooting Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe Support**: https://support.stripe.com
- **Stripe Status**: https://status.stripe.com
- **Application Logs**: `logs/application.log`
- **Database Queries**: See `STRIPE_SUBSCRIPTION_SETUP_GUIDE.md`
- **Test Cards**: See `STRIPE_QUICK_START.md`

## ✅ Sign-Off

### Development Complete
- [ ] All backend code implemented and tested
- [ ] Documentation complete
- [ ] Code committed to git
- [ ] Code reviewed
- [ ] Sign-off: ____________________ Date: __________

### Configuration Complete
- [ ] Stripe account set up
- [ ] Products and prices created
- [ ] Environment variables configured
- [ ] Webhooks configured
- [ ] Routes registered
- [ ] Sign-off: ____________________ Date: __________

### Testing Complete
- [ ] API endpoints tested
- [ ] Webhook processing tested
- [ ] Payment flows tested
- [ ] Error scenarios tested
- [ ] Sign-off: ____________________ Date: __________

### Production Ready
- [ ] Production Stripe account configured
- [ ] Production webhooks set up
- [ ] Security review complete
- [ ] Monitoring configured
- [ ] Customer support ready
- [ ] Sign-off: ____________________ Date: __________

---

**Current Status**: ✅ Backend implementation complete. Ready for configuration and testing.

**Next Immediate Action**: Configure Stripe account and set up products/prices (see steps 1-2 above).

**Estimated Time to Production**: 2-3 hours (configuration + testing)
