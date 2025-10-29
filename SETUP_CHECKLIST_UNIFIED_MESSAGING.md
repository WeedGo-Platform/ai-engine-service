# Unified Messaging System - Quick Setup Checklist

## ✅ Completed
- [x] AWS SES Provider implemented
- [x] AWS SNS Provider implemented
- [x] Unified Messaging Service with Circuit Breaker
- [x] OTP Service integration
- [x] Multi-provider failover (AWS → SendGrid/Twilio → SMTP/Console)
- [x] Health monitoring
- [x] Migration documentation

## 🔧 Setup Steps (Do Next)

### 1. Install Dependencies (IMMEDIATE)
```bash
cd src/Backend
pip install boto3>=1.28.0 botocore>=1.31.0
```

### 2. Configure AWS Credentials (DEVELOPMENT)

**Option A: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

**Option B: AWS CLI**
```bash
aws configure
# Follow prompts
```

**Option C: IAM Role (Production - Recommended)**
- Attach IAM role to EC2/Lambda/Cloud Run
- No credentials in code!

### 3. Configure Email Sender Info
```bash
export OTP_FROM_EMAIL=noreply@weedgo.com
export OTP_FROM_NAME=WeedGo
```

### 4. Verify SES Sender Email (CRITICAL)

**Before you can send emails with AWS SES, you MUST verify the sender email:**

```python
# Method 1: Python script
from services.communication.aws_ses_provider import AWSSESProvider
from services.communication.base_channel import ChannelConfig

config = ChannelConfig()
provider = AWSSESProvider(config)
await provider.verify_sender_email("noreply@weedgo.com")
# Check email inbox and click verification link
```

**OR Method 2: AWS Console**
1. Go to AWS SES Console
2. Click "Verified identities"
3. Click "Create identity"
4. Select "Email address"
5. Enter: noreply@weedgo.com
6. Click "Create identity"
7. Check inbox and click verification link

### 5. Request SES Production Access (FOR PRODUCTION)

**By default, SES is in SANDBOX mode** - can only send to verified addresses.

To send to any email:
1. AWS SES Console → Account dashboard
2. Click "Request production access"
3. Fill out form:
   - Use case: Transactional OTP codes for user authentication
   - Website URL: https://weedgo.com
   - Expected daily volume: [your estimate]
4. Submit (usually approved within 24 hours)

### 6. Run Integration Tests
```bash
cd src/Backend

# Basic health check (no actual sending)
python test_unified_messaging.py

# Test email sending (requires verified sender)
TEST_EMAIL=your-email@example.com python test_unified_messaging.py

# Test SMS sending (requires AWS SNS or Twilio configured)
TEST_PHONE=+15551234567 python test_unified_messaging.py

# Test both
TEST_EMAIL=your-email@example.com TEST_PHONE=+15551234567 python test_unified_messaging.py
```

### 7. Add Health Check Endpoint (RECOMMENDED)

In your FastAPI app (e.g., `api/health.py` or `api/monitoring.py`):

```python
from fastapi import APIRouter, Depends
from services.otp_service import OTPService

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/messaging")
async def get_messaging_health(otp_service: OTPService = Depends()):
    """Get health status of all messaging providers"""
    return await otp_service.get_messaging_health()
```

Test endpoint:
```bash
curl http://localhost:8000/health/messaging
```

Expected response:
```json
{
  "email_providers": [
    {"name": "AWSSESProvider", "priority": "PRIMARY", "circuit_breaker": "closed", "is_healthy": true},
    {"name": "EmailService", "priority": "SECONDARY", "circuit_breaker": "closed", "is_healthy": true}
  ],
  "sms_providers": [
    {"name": "AWSSNSProvider", "priority": "PRIMARY", "circuit_breaker": "closed", "is_healthy": true},
    {"name": "SMSService", "priority": "SECONDARY", "circuit_breaker": "closed", "is_healthy": true}
  ]
}
```

## 📊 Verification Checklist

### Provider Configuration
- [ ] AWS credentials configured (SES + SNS)
- [ ] SendGrid API key configured (fallback)
- [ ] Twilio credentials configured (fallback)
- [ ] SMTP credentials configured (backup)
- [ ] OTP sender email/name configured

### AWS SES Setup
- [ ] Sender email verified in SES
- [ ] SES production access requested (if sending to public)
- [ ] SES sending quota checked (default: 200/day in sandbox)
- [ ] DKIM records added to DNS (optional but recommended)

### Testing
- [ ] Health check shows all providers healthy
- [ ] Email OTP sends successfully via AWS SES
- [ ] SMS OTP sends successfully via AWS SNS
- [ ] Failover works (disable AWS, should use SendGrid/Twilio)
- [ ] Circuit breaker opens after 5 failures
- [ ] Circuit breaker auto-recovers after 60 seconds
- [ ] Database logs show provider used
- [ ] No console errors in OTP flow

### Monitoring
- [ ] Health check endpoint added to API
- [ ] Monitoring alerts configured for circuit breaker state
- [ ] Cost tracking enabled (AWS SNS spend limits)
- [ ] Logging shows which provider was used

## 🚨 Common Issues

### Issue: boto3 not found
**Solution:** `pip install boto3 botocore`

### Issue: AWS credentials not configured
**Solution:** 
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### Issue: SES EmailNotVerifiedException
**Solution:** Verify sender email in SES Console or via Python script (see step 4)

### Issue: SES MessageRejected (sandbox mode)
**Solution:** Request production access (see step 5) OR verify recipient email

### Issue: All providers failing
**Check:**
1. Are credentials configured? `echo $AWS_ACCESS_KEY_ID`
2. Is sender email verified? Check SES Console
3. Are network connections working? Check firewall
4. Check logs for specific error messages

### Issue: Circuit breaker stuck open
**Solution:** Circuit breakers auto-recover after 60 seconds. If stuck, restart service.

## 💰 Cost Optimization

### Free Tiers (as of 2024)
- **AWS SES:** 62,000 emails/month free (on EC2/Lambda)
- **AWS SNS:** 1,000 SMS/month free (first 12 months)
- **SendGrid:** 3,000 emails/month free (always free tier)
- **Twilio:** Trial credits only (~$15)

### Set AWS Spending Limits
```python
from services.communication.aws_sns_provider import AWSSNSProvider

provider = AWSSNSProvider(config)
await provider.set_monthly_spend_limit(100.00)  # $100/month cap
```

### Monitor Costs
```python
# Check current SMS spend
spend = await provider.get_sms_spend()
print(f"Current month: ${spend['current_month_spend']}")
print(f"Limit: ${spend['monthly_limit']}")
```

## 📖 Next Steps

1. **Complete setup checklist above** ✅
2. **Run integration tests** ✅
3. **Monitor logs for 24-48 hours** 📊
4. **Add health check to monitoring dashboard** 📈
5. **Configure alerting for circuit breaker state changes** 🔔
6. **Review AWS billing after first month** 💰

## 📚 Documentation

- Full migration guide: `UNIFIED_MESSAGING_MIGRATION_GUIDE.md`
- AWS SES documentation: https://docs.aws.amazon.com/ses/
- AWS SNS documentation: https://docs.aws.amazon.com/sns/
- Circuit Breaker pattern: Martin Fowler's blog

## 🎯 Success Criteria

✅ **System is ready when:**
1. Health check returns all providers as healthy
2. Email OTP sends successfully via AWS SES
3. SMS OTP sends successfully via AWS SNS  
4. Failover to secondary providers works
5. Circuit breakers protect against cascading failures
6. No breaking changes to existing OTP API
7. Database logs show provider usage
8. Cost tracking configured

---

**Status:** Integration complete ✅ | Testing pending ⏳ | Production deployment pending 🚀
