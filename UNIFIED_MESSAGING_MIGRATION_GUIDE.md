# Unified Messaging Service - Migration Guide

## Overview
The new Unified Messaging Service provides enterprise-grade email and SMS delivery with automatic failover across multiple providers.

## Architecture

### Provider Priority Chain

**Email Providers:**
1. **AWS SES** (Primary) - 62,000 emails/month free, $0.10/1000 after
2. **SendGrid** (Secondary) - 3,000 emails/month free
3. **Gmail SMTP** (Tertiary) - 500 emails/day free

**SMS Providers:**
1. **AWS SNS** (Primary) - 1,000 SMS/month free (12 months), ~$0.00645 per SMS after
2. **Twilio** (Secondary) - Trial credit, then ~$0.0075 per SMS
3. **Console Log** (Development) - Free testing fallback

### Circuit Breaker Pattern
- Automatically disables failing providers
- Prevents cascading failures
- Auto-recovery after timeout period
- Configurable failure thresholds

## Environment Variables

### AWS Configuration (Primary Providers)
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1  # or ca-central-1 for Canada

# AWS SES (Email)
AWS_SES_FROM_EMAIL=noreply@weedgo.com
AWS_SES_FROM_NAME=WeedGo
AWS_SES_CONFIGURATION_SET=weedgo-emails  # Optional: for tracking

# AWS SNS (SMS)
AWS_SNS_SENDER_ID=WeedGo  # Shows as sender name
```

### SendGrid Configuration (Email Fallback)
```bash
SENDGRID_API_KEY=SG.your_api_key
SENDGRID_FROM_EMAIL=noreply@weedgo.com
SENDGRID_FROM_NAME=WeedGo
```

### Twilio Configuration (SMS Fallback)
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
```

### SMTP Configuration (Last Resort)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=WeedGo
```

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements-messaging.txt
```

### 2. Configure AWS (If Using AWS Providers)

#### Option A: AWS CLI Configuration (Recommended)
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region: us-east-1 or ca-central-1
# Enter default output format: json
```

#### Option B: Environment Variables
Add to your `.env` file or environment:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

### 3. Verify SES Sender Email (Required for AWS SES)
```python
from services.communication.aws_ses_provider import AWSSESProvider

# Verify your sender email
provider = AWSSESProvider(config)
await provider.verify_sender_email("noreply@weedgo.com")
# Check email and click verification link
```

**OR** use AWS Console:
1. Go to AWS SES Console
2. Verified identities → Create identity
3. Enter email address
4. Click verification link in email

### 4. (Optional) Move Out of SES Sandbox
By default, SES is in sandbox mode (can only send to verified emails).

**To send to any email:**
1. Go to AWS SES Console
2. Account dashboard → Request production access
3. Fill out the form (usually approved within 24 hours)

## Usage

### Basic Usage (Replaces Old OTP Service)

```python
from services.communication.unified_messaging_service import UnifiedMessagingService

# Initialize service
messaging = UnifiedMessagingService(db_pool=pool)

# Send Email (auto-failover: AWS SES → SendGrid → SMTP)
result = await messaging.send_email(
    to="customer@example.com",
    subject="Your Verification Code",
    html_content="<h1>Your code is: 123456</h1>",
    text_content="Your code is: 123456",
    from_email="noreply@weedgo.com",
    from_name="WeedGo"
)

# Send SMS (auto-failover: AWS SNS → Twilio → Console)
result = await messaging.send_sms(
    to="+15551234567",
    message_body="Your WeedGo verification code is: 123456",
    metadata={'purpose': 'otp', 'user_id': '123'}
)

# Check result
if result.status == DeliveryStatus.SENT:
    print(f"Sent via {result.metadata['provider']}")
else:
    print(f"Failed: {result.error_message}")
```

### Integration with Existing OTP Service

Update `otp_service.py`:

```python
from services.communication.unified_messaging_service import UnifiedMessagingService

class OTPService:
    def __init__(self, tenant_id: Optional[str] = None, db_pool: Optional[asyncpg.Pool] = None):
        # ... existing code ...
        
        # Replace individual providers with unified service
        self.messaging = UnifiedMessagingService(db_pool=db_pool)
    
    async def send_otp_email(self, email: str, otp: str, user_id: Optional[str] = None):
        """Send OTP via email using unified service"""
        html_content = self._generate_otp_html(otp)
        
        result = await self.messaging.send_email(
            to=email,
            subject="Your WeedGo Verification Code",
            html_content=html_content,
            text_content=f"Your verification code is: {otp}",
            metadata={'purpose': 'otp', 'user_id': user_id}
        )
        
        return {
            'success': result.status == DeliveryStatus.SENT,
            'message_id': result.message_id,
            'provider': result.metadata.get('provider') if result.metadata else None,
            'error': result.error_message
        }
    
    async def send_otp_sms(self, phone: str, otp: str, user_id: Optional[str] = None):
        """Send OTP via SMS using unified service"""
        message = f"Your WeedGo verification code is: {otp}\\n\\nThis code will expire in {self.otp_expiry_minutes} minutes."
        
        result = await self.messaging.send_sms(
            to=phone,
            message_body=message,
            metadata={'purpose': 'otp', 'user_id': user_id}
        )
        
        return {
            'success': result.status == DeliveryStatus.SENT,
            'message_id': result.message_id,
            'provider': result.metadata.get('provider') if result.metadata else None,
            'error': result.error_message
        }
```

### Health Monitoring

```python
# Check provider health
health = await messaging.get_provider_health()

# Example output:
{
    'email_providers': [
        {
            'name': 'AWSSESProvider',
            'priority': 'PRIMARY',
            'circuit_breaker': 'closed',
            'is_healthy': True,
            'failure_count': 0
        },
        {
            'name': 'EmailService',
            'priority': 'SECONDARY',
            'circuit_breaker': 'closed',
            'is_healthy': True,
            'failure_count': 0
        }
    ],
    'sms_providers': [
        {
            'name': 'AWSSNSProvider',
            'priority': 'PRIMARY',
            'circuit_breaker': 'half_open',
            'is_healthy': True,
            'failure_count': 2
        },
        {
            'name': 'SMSService',
            'priority': 'SECONDARY',
            'circuit_breaker': 'closed',
            'is_healthy': True,
            'failure_count': 0
        }
    ]
}
```

## Testing

### Test Email Sending
```bash
python -c "
import asyncio
from services.communication.unified_messaging_service import UnifiedMessagingService

async def test():
    messaging = UnifiedMessagingService()
    result = await messaging.send_email(
        to='your-email@example.com',
        subject='Test Email',
        html_content='<h1>Test from Unified Messaging Service</h1>',
        text_content='Test from Unified Messaging Service'
    )
    print(f'Status: {result.status}')
    print(f'Provider: {result.metadata}')

asyncio.run(test())
"
```

### Test SMS Sending
```bash
python -c "
import asyncio
from services.communication.unified_messaging_service import UnifiedMessagingService

async def test():
    messaging = UnifiedMessagingService()
    result = await messaging.send_sms(
        to='+15551234567',  # Your phone number
        message_body='Test SMS from Unified Messaging Service'
    )
    print(f'Status: {result.status}')
    print(f'Provider: {result.metadata}')

asyncio.run(test())
"
```

## Cost Optimization

### Free Tier Limits
- **AWS SES**: 62,000 emails/month (if sending from EC2/Lambda)
- **AWS SNS**: 1,000 SMS/month (first 12 months)
- **SendGrid**: 3,000 emails/month
- **Gmail SMTP**: 15,000 emails/month (500/day)

### Recommended Setup for Cannabis Business

**Startup Phase (< 10K messages/month):**
- Use free tiers only
- AWS SES (primary) + SendGrid (backup) for email
- AWS SNS (primary) + Twilio trial for SMS

**Growth Phase (10K-100K messages/month):**
- AWS SES for email (~$10/month for 100K emails)
- AWS SNS for SMS (~$650/month for 100K SMS)
- Keep SendGrid/Twilio as backups

**Scale Phase (100K+ messages/month):**
- Primarily AWS (lowest cost at scale)
- SendGrid/Twilio for geographic failover
- Consider dedicated IP for deliverability

## Monitoring & Alerts

### CloudWatch Metrics (AWS)
- SES: Sends, Bounces, Complaints, Delivery attempts
- SNS: SMS delivery status, pricing tiers

### Application Logging
All providers log to standard logging:
```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs will show:
# - Provider attempts and failures
# - Circuit breaker state changes
# - Delivery results
# - Cost information
```

## Troubleshooting

### Email Not Sending

1. **Check SES Sandbox Mode**
   - Can only send to verified emails in sandbox
   - Request production access

2. **Verify Sender Email**
   - Must verify email in SES console
   - Check for verification email

3. **Check Circuit Breaker**
   - Provider may be temporarily disabled
   - Check health endpoint

4. **Review Logs**
   - Check application logs for errors
   - Check CloudWatch Logs for AWS errors

### SMS Not Sending

1. **Phone Number Format**
   - Must be E.164 format: +1XXXXXXXXXX
   - SNS provider auto-formats North American numbers

2. **SNS Spending Limits**
   - Default $1/month limit
   - Increase via AWS Console

3. **Geographic Restrictions**
   - Some countries require sender registration
   - Check AWS SNS documentation for country support

## Security Best Practices

1. **Use IAM Roles** (if running on AWS)
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ses:SendEmail",
           "ses:SendRawEmail",
           "sns:Publish"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

2. **Rotate API Keys**
   - Rotate SendGrid/Twilio keys every 90 days
   - Use AWS Secrets Manager for sensitive data

3. **Enable DKIM/SPF**
   - Configure for better deliverability
   - Set up in SES domain verification

4. **Monitor for Abuse**
   - Set spending limits
   - Monitor bounce rates
   - Implement rate limiting per user

## Migration Checklist

- [ ] Install boto3 dependencies
- [ ] Configure AWS credentials
- [ ] Verify SES sender email
- [ ] Request SES production access (if needed)
- [ ] Update OTP service to use UnifiedMessagingService
- [ ] Test email sending with all providers
- [ ] Test SMS sending with all providers
- [ ] Set up CloudWatch monitoring
- [ ] Configure spending limits
- [ ] Update documentation
- [ ] Train team on new system

## Support

For issues or questions:
1. Check logs first
2. Verify environment variables
3. Test providers individually
4. Check AWS Console for quota/limit issues
5. Review CircuitBreaker health status
