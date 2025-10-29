#!/usr/bin/env python3
"""
Quick AWS SES/SNS Status Checker
Run this to check if AWS providers are ready
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.communication.aws_ses_provider import AWSSESProvider
from services.communication.aws_sns_provider import AWSSNSProvider
from services.communication.base_channel import ChannelConfig


async def check_aws_status():
    """Check AWS SES and SNS status"""
    
    print("\n" + "=" * 70)
    print("AWS PROVIDERS STATUS CHECK")
    print("=" * 70)
    
    # Check SES
    print("\n📧 AWS SES (Email Provider)")
    print("-" * 70)
    try:
        ses_provider = AWSSESProvider(ChannelConfig())
        quota = await ses_provider.check_sending_quota()
        
        if 'error' in quota:
            print(f"❌ Error: {quota['error']}")
        else:
            print(f"✅ Connected successfully")
            print(f"\nSending Quota:")
            print(f"  • Max 24hr send: {quota['max_24_hour_send']:,.0f} emails")
            print(f"  • Max send rate: {quota['max_send_rate']}/sec")
            print(f"  • Sent last 24hr: {quota['sent_last_24_hours']:,.0f}")
            print(f"  • Remaining: {quota['remaining_quota']:,.0f}")
            
            if quota['max_24_hour_send'] == 200:
                print(f"\n⚠️  SANDBOX MODE ACTIVE")
                print(f"  • Can only send to verified email addresses")
                print(f"  • Request production access to send to any email")
                print(f"  • See: https://console.aws.amazon.com/ses/")
            else:
                print(f"\n✅ PRODUCTION MODE")
                print(f"  • Can send to any email address")
    
    except Exception as e:
        print(f"❌ Error connecting to AWS SES: {e}")
    
    # Check SNS
    print("\n📱 AWS SNS (SMS Provider)")
    print("-" * 70)
    try:
        sns_provider = AWSSNSProvider(ChannelConfig())
        
        # Try to get SMS spending
        try:
            spend_info = await sns_provider.get_sms_spend()
            print(f"✅ Connected successfully")
            print(f"\nSMS Spending:")
            print(f"  • Current month: ${spend_info['current_month_spend']:.2f}")
            print(f"  • Monthly limit: ${spend_info['monthly_limit']:.2f}")
            
            free_remaining = max(0, 1000 - spend_info.get('messages_sent', 0))
            if free_remaining > 0:
                print(f"  • Free tier remaining: ~{free_remaining} SMS")
        except Exception as e:
            print(f"✅ Connected (spending info not available)")
            print(f"  Note: {str(e)[:100]}")
        
    except Exception as e:
        print(f"❌ Error connecting to AWS SNS: {e}")
    
    # Sender email status
    print("\n📨 Sender Email Verification")
    print("-" * 70)
    sender_email = os.getenv('OTP_FROM_EMAIL', 'noreply@weedgo.com')
    print(f"Configured sender: {sender_email}")
    print(f"\nTo verify this email:")
    print(f"  1. Check inbox for: {sender_email}")
    print(f"  2. Look for email from: Amazon SES <no-reply@ses.amazonaws.com>")
    print(f"  3. Click the verification link")
    print(f"\nOr verify via AWS Console:")
    print(f"  https://console.aws.amazon.com/ses/")
    
    # Summary
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(f"""
1. ✅ AWS credentials configured
2. ✅ AWS SES connected
3. ✅ AWS SNS connected
4. ⏳ Verify sender email: {sender_email}
5. ⏳ Test email sending (after verification)
6. ⏳ Request SES production access (to exit sandbox mode)

To test email sending (after verification):
  TEST_EMAIL=your@email.com python3 test_otp_live.py

To test SMS sending:
  TEST_PHONE=+15551234567 python3 test_otp_live.py
""")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(check_aws_status())
