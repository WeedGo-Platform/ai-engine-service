# 📊 UNIFIED MESSAGING SYSTEM - ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER SIGNUP/LOGIN FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   Frontend (React)    │
                          │  Tenant Signup Form   │
                          └───────────────────────┘
                                      │
                         POST /api/v1/auth/otp/send
                         { email/phone, purpose: "verification" }
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OTP SERVICE (REFACTORED)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  services/otp_service.py                                            │   │
│  │  ───────────────────────                                            │   │
│  │  • create_otp()          → Generate 6-digit code                    │   │
│  │  • send_otp_email()      → Calls UnifiedMessagingService           │   │
│  │  • send_otp_sms()        → Calls UnifiedMessagingService           │   │
│  │  • verify_otp()          → Check code validity                      │   │
│  │  • get_messaging_health() → Provider health status                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED MESSAGING SERVICE (NEW)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  services/communication/unified_messaging_service.py                │   │
│  │  ──────────────────────────────────────────────────                 │   │
│  │  • send_email(to, subject, html, text, metadata)                    │   │
│  │  • send_sms(to, message, metadata)                                  │   │
│  │  • _send_with_failover() → Core failover logic                      │   │
│  │  • get_provider_health() → Health monitoring                        │   │
│  │                                                                      │   │
│  │  CIRCUIT BREAKER PATTERN:                                           │   │
│  │  • States: CLOSED → OPEN → HALF_OPEN → CLOSED                      │   │
│  │  • Threshold: 5 failures = open, 60s timeout, 2 success = close    │   │
│  │  • Protection: Prevents cascading failures                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                         ┌────────────┴───────────┐
                         │                        │
                         ▼                        ▼
┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│       EMAIL PROVIDERS              │  │       SMS PROVIDERS                │
│                                    │  │                                    │
│  Priority 1: AWS SES               │  │  Priority 1: AWS SNS               │
│  ┌──────────────────────────────┐  │  │  ┌──────────────────────────────┐  │
│  │ aws_ses_provider.py          │  │  │  │ aws_sns_provider.py          │  │
│  │ ──────────────────────────── │  │  │  │ ──────────────────────────── │  │
│  │ • 62,000 emails/month FREE   │  │  │  │ • 1,000 SMS/month FREE       │  │
│  │ • $0.10 per 1,000 after      │  │  │  │ • $0.00645 per SMS after     │  │
│  │ • HTML/text support          │  │  │  │ • E.164 phone formatting     │  │
│  │ • Attachments, tags, CC/BCC  │  │  │  │ • Cost calculation           │  │
│  │ Status: ⏳ Needs credentials  │  │  │  │ Status: ⏳ Needs credentials  │  │
│  └──────────────────────────────┘  │  │  └──────────────────────────────┘  │
│           │ Circuit Breaker        │  │           │ Circuit Breaker        │
│           ▼ (if open, skip)        │  │           ▼ (if open, skip)        │
│                                    │  │                                    │
│  Priority 2: SendGrid              │  │  Priority 2: Twilio                │
│  ┌──────────────────────────────┐  │  │  ┌──────────────────────────────┐  │
│  │ email_service.py (existing)  │  │  │  │ sms_service.py (existing)    │  │
│  │ ──────────────────────────── │  │  │  │ ──────────────────────────── │  │
│  │ • 3,000 emails/month FREE    │  │  │  │ • ~$0.0075 per SMS           │  │
│  │ • $0.067 per 1,000 after     │  │  │  │ • Reliable delivery          │  │
│  │ • HTML/text support          │  │  │  │ • Status tracking            │  │
│  │ Status: ✅ ACTIVE & WORKING   │  │  │  │ Status: ✅ ACTIVE & WORKING   │  │
│  └──────────────────────────────┘  │  │  └──────────────────────────────┘  │
│           │ Circuit Breaker        │  │           │ Circuit Breaker        │
│           ▼ (if open, skip)        │  │           ▼ (if open, skip)        │
│                                    │  │                                    │
│  Priority 3: SMTP/Gmail            │  │  Priority 3: Console (dev only)    │
│  ┌──────────────────────────────┐  │  │  ┌──────────────────────────────┐  │
│  │ SMTP via otp_service         │  │  │  │ Logs to console              │  │
│  │ ──────────────────────────── │  │  │  │ ──────────────────────────── │  │
│  │ • 15,000 emails/month FREE   │  │  │  │ • Development testing        │  │
│  │ • 500 per day limit          │  │  │  │ • No actual SMS sent         │  │
│  │ • Basic HTML/text support    │  │  │  │ Status: ✅ ACTIVE             │  │
│  │ Status: ✅ ACTIVE & WORKING   │  │  │  └──────────────────────────────┘  │
│  └──────────────────────────────┘  │  │                                    │
│                                    │  │                                    │
└────────────────────────────────────┘  └────────────────────────────────────┘
                         │                        │
                         └────────────┬───────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE LOGGING                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  communication_logs table                                           │   │
│  │  ────────────────────────                                           │   │
│  │  • message_id, recipient, status, provider_used                     │   │
│  │  • sent_at, delivered_at, cost, error_message                       │   │
│  │  • metadata (purpose, user_id, tenant_id)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                               FAILOVER EXAMPLE
═══════════════════════════════════════════════════════════════════════════════

SCENARIO: User signs up, needs email OTP

Step 1: OTP Service
    ↓
    await messaging.send_email(
        to="user@example.com",
        subject="Your OTP Code",
        html_content="<h1>123456</h1>",
        metadata={'purpose': 'otp'}
    )

Step 2: UnifiedMessagingService Checks Providers
    ↓
    Provider List (sorted by priority):
    1. AWSSESProvider (PRIMARY) - Circuit: OPEN (invalid credentials)
    2. EmailService/SendGrid (SECONDARY) - Circuit: CLOSED (healthy)
    3. SMTP/Gmail (TERTIARY) - Circuit: CLOSED (healthy)

Step 3: Failover Logic
    ↓
    Try AWSSESProvider → Skip (circuit open)
    Try EmailService → SUCCESS! ✅
    │
    ├─ Record success
    ├─ Update circuit breaker (failure_count = 0)
    ├─ Log to database (provider: 'sendgrid')
    └─ Return result

Step 4: Result
    ↓
    {
        'success': True,
        'message_id': 'sendgrid-msg-id-123',
        'status': 'sent',
        'provider': 'sendgrid',
        'cost': 0.0
    }

Step 5: Database Log
    ↓
    INSERT INTO communication_logs (
        message_id='sendgrid-msg-id-123',
        recipient='user@example.com',
        status='sent',
        provider_used='sendgrid',
        channel='email',
        purpose='otp',
        cost=0.0,
        sent_at=NOW()
    )


═══════════════════════════════════════════════════════════════════════════════
                            CIRCUIT BREAKER STATES
═══════════════════════════════════════════════════════════════════════════════

CLOSED (Normal Operation)
┌────────────────────────┐
│   Provider Healthy     │  ← Request comes in
│   Allow all requests   │  → Forward to provider
│   Track failures: 0/5  │  ← Provider succeeds
└────────────────────────┘
         │
         │ 5 consecutive failures
         ▼
OPEN (Provider Down)
┌────────────────────────┐
│   Provider Failing     │  ← Request comes in
│   Block all requests   │  → Skip provider (instant)
│   Timeout: 60 seconds  │  ← Try next provider
└────────────────────────┘
         │
         │ After 60 seconds
         ▼
HALF_OPEN (Testing Recovery)
┌────────────────────────┐
│   Testing Provider     │  ← Request comes in
│   Allow 1 test request │  → Forward to provider
│   Need 2 successes     │  ← Check result
└────────────────────────┘
         │
         ├─ If success x2 → CLOSED (recovered)
         └─ If failure   → OPEN (still down)


═══════════════════════════════════════════════════════════════════════════════
                              COST COMPARISON
═══════════════════════════════════════════════════════════════════════════════

Scenario: 10,000 users signup (20,000 emails + 20,000 SMS)

┌─────────────────────────────────────────────────────────────────────────────┐
│  WITHOUT AWS (Current State)                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Email:                                                                     │
│    SendGrid:  3,000 free + 17,000 paid = $0 + $1.14 = $1.14               │
│    SMTP:      17,000 emails = FREE (within 15K/month limit)               │
│    TOTAL:     $0 (within free tiers)                                       │
│                                                                             │
│  SMS:                                                                       │
│    Twilio:    20,000 × $0.0075 = $150.00                                  │
│                                                                             │
│  MONTHLY TOTAL: $150.00                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WITH AWS (Future State)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Email:                                                                     │
│    AWS SES:   20,000 emails = FREE (within 62K limit)                     │
│    Fallback:  SendGrid/SMTP (not needed)                                  │
│    TOTAL:     $0                                                            │
│                                                                             │
│  SMS:                                                                       │
│    AWS SNS:   1,000 free + 19,000 × $0.00645 = $0 + $122.55              │
│    Fallback:  Twilio (not needed)                                         │
│    TOTAL:     $122.55                                                      │
│                                                                             │
│  MONTHLY TOTAL: $122.55                                                    │
│  SAVINGS:       $27.45/month (18.3% reduction)                            │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                           HEALTH MONITORING API
═══════════════════════════════════════════════════════════════════════════════

Endpoint: GET /health/messaging

Response:
{
  "timestamp": "2025-10-29T10:30:00Z",
  "email_providers": [
    {
      "name": "AWSSESProvider",
      "priority": "PRIMARY",
      "circuit_breaker": "open",          ← Currently failing
      "is_healthy": false,
      "failure_count": 5,
      "last_error": "InvalidClientTokenId"
    },
    {
      "name": "EmailService",
      "priority": "SECONDARY",
      "circuit_breaker": "closed",        ← Healthy & active
      "is_healthy": true,
      "failure_count": 0
    }
  ],
  "sms_providers": [
    {
      "name": "AWSSNSProvider",
      "priority": "PRIMARY",
      "circuit_breaker": "open",
      "is_healthy": false,
      "failure_count": 5
    },
    {
      "name": "SMSService",
      "priority": "SECONDARY",
      "circuit_breaker": "closed",        ← Healthy & active
      "is_healthy": true,
      "failure_count": 0
    }
  ],
  "overall_status": "healthy",            ← System working (has fallbacks)
  "active_providers": {
    "email": "EmailService (SendGrid)",
    "sms": "SMSService (Twilio)"
  }
}


═══════════════════════════════════════════════════════════════════════════════
                         DEPLOYMENT ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ENVIRONMENT                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌──────────────────┐                         │
│  │  Load Balancer  │────────▶│   API Server     │                         │
│  └─────────────────┘         │   (FastAPI)      │                         │
│                               │                  │                         │
│                               │  ┌────────────┐  │                         │
│                               │  │ OTPService │  │                         │
│                               │  └──────┬─────┘  │                         │
│                               │         │        │                         │
│                               │  ┌──────▼──────────────────┐              │
│                               │  │ UnifiedMessagingService │              │
│                               │  │                         │              │
│                               │  │ ┌─────────────────────┐ │              │
│                               │  │ │ Email Providers:    │ │              │
│                               │  │ │ • AWS SES          │ │              │
│                               │  │ │ • SendGrid         │ │              │
│                               │  │ │ • SMTP/Gmail       │ │              │
│                               │  │ └─────────────────────┘ │              │
│                               │  │                         │              │
│                               │  │ ┌─────────────────────┐ │              │
│                               │  │ │ SMS Providers:      │ │              │
│                               │  │ │ • AWS SNS          │ │              │
│                               │  │ │ • Twilio           │ │              │
│                               │  │ └─────────────────────┘ │              │
│                               │  └─────────────────────────┘              │
│                               └──────────────────┘                         │
│                                      │                                     │
│                                      ▼                                     │
│                               ┌──────────────────┐                         │
│                               │   PostgreSQL     │                         │
│                               │   Database       │                         │
│                               │                  │                         │
│                               │  • otp_codes     │                         │
│                               │  • comm_logs     │                         │
│                               └──────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Environment Variables (Production):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ AWS_ACCESS_KEY_ID (or use IAM role)
✅ AWS_SECRET_ACCESS_KEY (or use IAM role)
✅ TWILIO_ACCOUNT_SID
✅ TWILIO_AUTH_TOKEN
✅ SENDGRID_API_KEY
✅ SMTP_USER, SMTP_PASSWORD
✅ OTP_FROM_EMAIL, OTP_FROM_NAME


═══════════════════════════════════════════════════════════════════════════════
                            CREATED: October 29, 2025
                            STATUS: ✅ PRODUCTION READY
═══════════════════════════════════════════════════════════════════════════════
```
