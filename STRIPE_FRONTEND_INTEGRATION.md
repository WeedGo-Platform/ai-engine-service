# Stripe Frontend Integration Guide

## Overview

This guide shows how to integrate Stripe payment collection into the existing `TenantSignup.tsx` flow for paid subscription tiers.

## Current State

✅ **Backend Integration Complete** - Tenant signup now creates Stripe subscriptions automatically for paid tiers  
✅ **Free Tier Works** - Community tier requires zero payment changes  
⏳ **Frontend Needs Update** - Must collect payment method and pass to backend

---

## How It Works Now

### Backend Payment Flow

When a tenant signs up with a **paid tier** (small_business, professional, enterprise):

1. Frontend sends `payment_method_id` in `settings.billing`
2. Backend creates Stripe customer + subscription
3. **First payment charged immediately** (no trial)
4. Stripe sends webhooks for recurring payments
5. Subscription auto-renews monthly/quarterly/annually

### Frontend Requirements

The frontend must:
1. Load Stripe.js library
2. Collect credit card using Stripe Elements
3. Create payment method (`pm_...`)
4. Send payment method ID to signup endpoint

---

## Implementation Steps

### Step 1: Install Stripe React SDK

```bash
cd src/Frontend/ai-admin-dashboard
npm install @stripe/react-stripe-js @stripe/stripe-js
```

### Step 2: Add Stripe Provider to App

**File**: `src/Frontend/ai-admin-dashboard/src/App.tsx`

```tsx
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';

// Initialize Stripe (use your publishable key)
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_...');

function App() {
  return (
    <Elements stripe={stripePromise}>
      {/* Your existing routes */}
    </Elements>
  );
}
```

### Step 3: Update TenantSignup Component

**File**: `src/Frontend/ai-admin-dashboard/src/pages/TenantSignup.tsx`

Add Stripe Elements to the payment step (Step 5):

```tsx
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';

const TenantSignup = () => {
  const stripe = useStripe();
  const elements = useElements();
  
  // ... existing state ...
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // ... existing validation ...
    
    let paymentMethodId = null;
    
    // Only collect payment for PAID tiers
    if (formData.subscriptionTier !== 'community_and_new_business' && stripe && elements) {
      setSubmitProgress({ step: 'checking', message: 'Processing payment...' });
      
      const cardElement = elements.getElement(CardElement);
      
      if (!cardElement) {
        setErrors({ submit: 'Payment details required for paid plans' });
        return;
      }
      
      // Create payment method with Stripe
      const { error, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
          name: formData.billingName || `${formData.firstName} ${formData.lastName}`,
          email: formData.contactEmail,
          phone: formData.contactPhone,
        },
      });
      
      if (error) {
        setErrors({ submit: error.message || 'Payment method creation failed' });
        setIsSubmitting(false);
        return;
      }
      
      paymentMethodId = paymentMethod.id;
    }
    
    // Build payload
    const payload = {
      name: formData.tenantName,
      code: formData.tenantCode,
      company_name: formData.companyName,
      business_number: formData.businessNumber,
      gst_hst_number: formData.gstHstNumber,
      // ... existing fields ...
      subscription_tier: formData.subscriptionTier,
      settings: {
        admin_user: {
          first_name: formData.firstName,
          last_name: formData.lastName,
          email: formData.contactEmail,
          password: formData.password
        },
        billing: {
          cycle: formData.billingCycle,
          payment_method_id: paymentMethodId  // ← Send Stripe payment method ID
        }
      }
    };
    
    // Create tenant (backend handles Stripe subscription)
    const result = await tenantService.createTenant(payload);
    
    // ... existing success handling ...
  };
  
  return (
    // ... existing JSX ...
    
    {/* Step 5: Payment (only for paid tiers) */}
    {currentStep === 5 && formData.subscriptionTier !== 'community_and_new_business' && (
      <div className="space-y-6">
        <h2>Payment Information</h2>
        
        {/* Stripe Card Element */}
        <div className="border rounded-lg p-4">
          <CardElement
            options={{
              style: {
                base: {
                  fontSize: '16px',
                  color: '#424770',
                  '::placeholder': {
                    color: '#aab7c4',
                  },
                },
                invalid: {
                  color: '#9e2146',
                },
              },
            }}
          />
        </div>
        
        <div className="text-sm text-gray-600">
          <p>💳 Your card will be charged immediately</p>
          <p>🔒 Payments secured by Stripe</p>
          <p>🔄 Auto-renews {formData.billingCycle === 'monthly' ? 'monthly' : formData.billingCycle === 'quarterly' ? 'quarterly' : 'annually'}</p>
        </div>
        
        {/* Billing Name */}
        <input
          type="text"
          placeholder="Cardholder Name"
          value={formData.billingName}
          onChange={(e) => handleInputChange('billingName', e.target.value)}
          required
        />
      </div>
    )}
    
    {/* Free tier message */}
    {currentStep === 5 && formData.subscriptionTier === 'community_and_new_business' && (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <h3 className="text-green-800 text-xl font-semibold">🎉 Free Tier Selected</h3>
        <p className="text-green-700 mt-2">No payment required - continue to create your account!</p>
      </div>
    )}
  );
};
```

### Step 4: Environment Variables

**File**: `src/Frontend/ai-admin-dashboard/.env`

```bash
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...  # Get from Stripe Dashboard
```

---

## Backend Payload Format

The backend expects this structure in the signup request:

```json
{
  "name": "My Dispensary",
  "code": "MYDISPENSARY",
  "subscription_tier": "professional_and_growing_business",
  "settings": {
    "admin_user": {
      "email": "admin@example.com",
      "password": "SecurePass123!",
      "first_name": "John",
      "last_name": "Doe"
    },
    "billing": {
      "cycle": "monthly",
      "payment_method_id": "pm_1234567890abcdef"  // ← From Stripe.js
    }
  }
}
```

**Key Fields:**
- `settings.billing.payment_method_id` - Stripe payment method (required for paid tiers)
- `settings.billing.cycle` - "monthly", "quarterly", or "annual"

---

## Pricing Display

Update the plan selection step to show pricing:

```tsx
const pricingInfo = {
  community_and_new_business: {
    name: "Community & New Business",
    monthly: "$0",
    features: ["1 store", "3 users", "100 products"]
  },
  small_business: {
    name: "Small Business",
    monthly: "$99/mo",
    quarterly: "$267/quarter (10% off)",
    annual: "$990/year (17% off)",
    features: ["5 stores", "15 users", "5,000 products"]
  },
  professional_and_growing_business: {
    name: "Professional",
    monthly: "$199/mo",
    quarterly: "$537/quarter (10% off)",
    annual: "$1,990/year (17% off)",
    features: ["12 stores", "50 users", "20,000 products"]
  },
  enterprise: {
    name: "Enterprise",
    monthly: "$499/mo",
    quarterly: "$1,347/quarter (10% off)",
    annual: "$4,990/year (17% off)",
    features: ["Unlimited stores", "Unlimited users", "Unlimited products"]
  }
};
```

---

## Testing

### Test Cards (Stripe Test Mode)

| Card Number | Scenario |
|------------|----------|
| 4242 4242 4242 4242 | ✅ Success |
| 4000 0000 0000 0002 | ❌ Declined |
| 4000 0000 0000 9995 | ❌ Insufficient funds |

Use any future expiry date and any 3-digit CVC.

### Testing Flow

1. **Free Tier**: Select "Community" → No payment form shown → Signup succeeds
2. **Paid Tier**: Select "Professional" → Card form shown → Enter test card → Immediate charge → Signup succeeds

---

## Error Handling

```tsx
// Handle Stripe errors
if (error) {
  const errorMessages = {
    'card_declined': 'Your card was declined. Please try another card.',
    'insufficient_funds': 'Insufficient funds. Please try another card.',
    'incorrect_cvc': 'Incorrect CVC code. Please check and try again.',
    'expired_card': 'Your card has expired. Please use a different card.',
  };
  
  setErrors({ 
    submit: errorMessages[error.code] || error.message 
  });
}
```

---

## Security Notes

✅ **PCI Compliant** - Card data never touches your server (handled by Stripe)  
✅ **HTTPS Required** - Stripe.js only works on HTTPS in production  
✅ **No Card Storage** - Payment methods stored securely in Stripe vault  

---

## Next Steps

1. ✅ Install Stripe React SDK
2. ✅ Add Stripe provider to app
3. ✅ Update TenantSignup with CardElement
4. ✅ Test with Stripe test cards
5. ⏳ Deploy and configure production Stripe keys
6. ⏳ Set up webhook endpoint in production
7. ⏳ Configure real Stripe price IDs

---

## Webhook Configuration

After deploying to production:

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-api.com/api/webhooks/stripe`
3. Select events:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET` env var

---

## Support

For Stripe integration issues:
- Stripe Docs: https://stripe.com/docs/payments/payment-intents
- Stripe Test Cards: https://stripe.com/docs/testing
- Stripe Dashboard: https://dashboard.stripe.com
