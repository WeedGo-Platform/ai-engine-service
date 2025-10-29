# Email Failover System - How It Works

## Architecture Overview

The UnifiedMessagingService implements automatic provider failover using a **priority-based circuit breaker pattern**.

```
┌─────────────────────────────────────────────────────────────┐
│                  UnifiedMessagingService                     │
│                                                               │
│  Email Chain: AWS SES → SendGrid → Gmail SMTP               │
│  SMS Chain:   AWS SNS → Twilio → Console (dev only)         │
└─────────────────────────────────────────────────────────────┘
```

## Provider Priority Levels

```python
class ProviderPriority(Enum):
    PRIMARY = 1      # Try first (AWS SES/SNS)
    SECONDARY = 2    # Try second (SendGrid/Twilio)
    TERTIARY = 3     # Try third (Gmail SMTP)
    FALLBACK = 4     # Last resort (Console - dev only)
```

## How Failover Works

### 1. **Initialization** (on server start)

```python
# Email providers added in priority order:
self.email_providers = [
    (AWSSESProvider, PRIMARY, CircuitBreaker(failures=5, timeout=300s)),
    (EmailService/SendGrid, SECONDARY, CircuitBreaker(failures=3, timeout=180s)),
    (SMTPEmailProvider, TERTIARY, CircuitBreaker(failures=3, timeout=180s))
]
```

### 2. **Sending Flow** (when OTP email is sent)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User requests OTP email                                  │
│    ↓                                                         │
│ 2. UnifiedMessagingService.send_email()                     │
│    ↓                                                         │
│ 3. _send_with_failover() loops through providers            │
│    ↓                                                         │
│ 4. Check each provider's circuit breaker                    │
│    ↓                                                         │
│ 5. Try provider.send_single()                               │
│    ↓                                                         │
│ 6. IF SUCCESS → return (stop trying other providers)        │
│    IF FAILURE → record failure, try next provider           │
│    ↓                                                         │
│ 7. If all providers fail → return error                     │
└─────────────────────────────────────────────────────────────┘
```

### 3. **Circuit Breaker Pattern**

Each provider has a circuit breaker that tracks failures:

```python
class CircuitBreaker:
    failure_threshold = 5    # Open circuit after 5 failures
    timeout_seconds = 300    # Keep circuit open for 5 minutes
    
    States:
        CLOSED     → Normal operation, try provider
        OPEN       → Too many failures, skip provider  
        HALF_OPEN  → Testing if provider recovered
```

**Example Scenario:**

```
Time 00:00 - AWS SES fails (unverified recipient)
           → Circuit breaker: 1 failure
           → Try SendGrid

Time 00:01 - AWS SES fails again
           → Circuit breaker: 2 failures
           → Try SendGrid

Time 00:05 - AWS SES fails (5th time)
           → Circuit breaker: OPEN (skip for 5 minutes)
           → Skip AWS SES, try SendGrid directly

Time 00:10 - AWS SES circuit breaker: HALF_OPEN
           → Test AWS SES again
           → If success: circuit CLOSED
           → If failure: circuit OPEN again
```

## Email Provider Details

### Primary: AWS SES
```yaml
Priority: PRIMARY (1)
Circuit Breaker:
  - Failure Threshold: 5
  - Timeout: 300 seconds (5 minutes)
  
Triggers Failover When:
  - Email address not verified (sandbox mode)
  - Invalid AWS credentials
  - Rate limit exceeded
  - AWS service outage
  
Cost: $0.10 per 1,000 emails
Rate: 14 emails/second
```

### Secondary: SendGrid
```yaml
Priority: SECONDARY (2)
Circuit Breaker:
  - Failure Threshold: 3
  - Timeout: 180 seconds (3 minutes)
  
Triggers Failover When:
  - Invalid API key (401 error)
  - Rate limit exceeded
  - Account suspended
  - Service outage
  
Cost: Free tier (100 emails/day)
Rate: 10 emails/second
```

### Tertiary: Gmail SMTP
```yaml
Priority: TERTIARY (3)
Circuit Breaker:
  - Failure Threshold: 3
  - Timeout: 180 seconds (3 minutes)
  
Triggers Failover When:
  - Invalid SMTP credentials
  - Gmail blocks suspicious activity
  - Daily sending limit exceeded (500 emails/day)
  - Network issues
  
Cost: Free
Rate: 1 email/second (conservative)
```

## Code Example

### Automatic Failover in Action

```python
# In _send_with_failover():
for provider, priority, circuit_breaker in sorted(providers, key=lambda x: x[1].value):
    # Skip if circuit breaker is open
    if not circuit_breaker.can_attempt():
        logger.warning(f"Skipping {provider.__class__.__name__} - circuit breaker open")
        continue
    
    try:
        # Try to send
        result = await provider.send_single(recipient, message)
        
        if result.status == DeliveryStatus.SENT:
            # SUCCESS! Record success and return
            circuit_breaker.record_success()
            logger.info(f"✅ Message sent via {provider.__class__.__name__}")
            return result
        else:
            # Provider returned failure
            circuit_breaker.record_failure()
            logger.warning(f"❌ {provider.__class__.__name__} failed: {result.error_message}")
            # Continue to next provider
            
    except Exception as e:
        # Provider threw exception
        circuit_breaker.record_failure()
        logger.error(f"❌ {provider.__class__.__name__} exception: {e}")
        # Continue to next provider

# If we get here, all providers failed
return DeliveryResult(status=FAILED, error="All providers failed")
```

## Real-World Example

**Scenario:** User signs up with `user@example.com`

```
1. AWS SES (Primary) attempts to send
   ❌ FAILS: "Email address not verified" (sandbox mode)
   → Circuit breaker records failure (1/5)
   → Log: "Provider AWSSESProvider failed: MessageRejected"

2. SendGrid (Secondary) attempts to send  
   ❌ FAILS: "401 Unauthorized" (invalid API key)
   → Circuit breaker records failure (1/3)
   → Log: "Provider EmailService failed: Permission denied"

3. Gmail SMTP (Tertiary) attempts to send
   ✅ SUCCESS: Email sent via SMTP
   → Circuit breaker records success
   → Log: "✅ Message sent via SMTPEmailProvider (TERTIARY)"
   → Return success to user
```

## Why This Design?

### Benefits:

1. **Resilience**: Single provider failure doesn't break the system
2. **Cost Optimization**: Use cheaper providers (SES) first, expensive (Twilio) as fallback
3. **Performance**: Circuit breaker prevents wasting time on known-broken providers
4. **Flexibility**: Easy to add/remove providers or change priority
5. **Monitoring**: Clear logs show which provider succeeded/failed

### Trade-offs:

1. **Latency**: Failover adds slight delay (typically <1 second)
2. **Complexity**: More providers = more configuration to manage
3. **Debugging**: Need to check logs to see which provider was used

## Configuration

### Environment Variables Required:

```bash
# AWS SES (Primary)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# SendGrid (Secondary)
SENDGRID_API_KEY=your_key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Gmail SMTP (Tertiary)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password  # Not regular password!
```

### Gmail App Password Setup:

1. Go to: https://myaccount.google.com/apppasswords
2. Generate new app password
3. Use that password (not your regular Gmail password)

## Monitoring & Health Checks

### Get Provider Health Status:

```python
health = await unified_messaging.get_provider_health()

# Returns:
{
    'email_providers': [
        {
            'name': 'AWSSESProvider',
            'priority': 'PRIMARY',
            'circuit_breaker': 'closed',  # or 'open', 'half_open'
            'is_healthy': True,
            'failure_count': 0
        },
        {
            'name': 'EmailService',
            'priority': 'SECONDARY', 
            'circuit_breaker': 'closed',
            'is_healthy': True,
            'failure_count': 0
        },
        {
            'name': 'SMTPEmailProvider',
            'priority': 'TERTIARY',
            'circuit_breaker': 'closed',
            'is_healthy': True,
            'failure_count': 0
        }
    ]
}
```

## SMS Failover (Similar Pattern)

```
Priority Chain: AWS SNS (Primary) → Twilio (Secondary) → Console (Fallback)

Same circuit breaker logic:
- AWS SNS fails → try Twilio
- Twilio fails → print to console (dev mode)
- Console prints OTP code to backend.log for testing
```

## Summary

The failover system ensures **high availability** of email/SMS delivery by:

1. **Trying providers in priority order** (cheap → expensive)
2. **Skipping known-broken providers** (circuit breaker)
3. **Returning as soon as one succeeds** (fast path)
4. **Logging all attempts** (transparency)
5. **Self-healing** (circuit breaker auto-recovers)

This design makes the OTP system resilient to:
- Provider outages
- Invalid credentials
- Rate limits
- Network issues
- Configuration errors

**Result:** Users always receive their OTP codes, even if primary providers fail!
