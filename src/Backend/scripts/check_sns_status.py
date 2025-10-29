#!/usr/bin/env python3
"""
Check AWS SNS status and sandbox mode
"""

import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_sns_status():
    """Check if SNS is in sandbox mode and get account limits"""
    
    # Initialize SNS client
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        sns_client = boto3.client('sns', region_name=aws_region)
        
        print("🔍 Checking AWS SNS Status...\n")
        
        # Get SMS attributes
        print("📱 SMS Attributes:")
        try:
            response = sns_client.get_sms_attributes()
            attributes = response.get('attributes', {})
            
            for key, value in attributes.items():
                print(f"  • {key}: {value}")
            
            # Check if in sandbox
            if not attributes:
                print("\n⚠️  WARNING: No SMS attributes found - SNS might be in sandbox mode!")
            
        except ClientError as e:
            print(f"  ❌ Error getting SMS attributes: {e}")
        
        # Check SMS spending
        print("\n💰 SMS Spending Limit:")
        try:
            response = sns_client.get_sms_attributes(
                attributes=['MonthlySpendLimit']
            )
            limit = response.get('attributes', {}).get('MonthlySpendLimit', 'Not set')
            print(f"  • Monthly Spend Limit: ${limit}")
        except ClientError as e:
            print(f"  ❌ Error: {e}")
        
        # Test sending to a number
        print("\n🧪 Testing SMS Send Capability:")
        print("  ℹ️  If SNS is in SANDBOX mode, you can only send to verified numbers")
        print("  ℹ️  To verify a number: AWS Console → SNS → Text messaging (SMS) → Sandbox destinations")
        
        # Check IAM permissions
        print("\n🔐 IAM Permission Test:")
        try:
            # Try to list SMS sandbox phone numbers (only works if in sandbox)
            try:
                response = sns_client.list_sms_sandbox_phone_numbers()
                verified_numbers = response.get('PhoneNumbers', [])
                
                print("  ⚠️  SNS IS IN SANDBOX MODE")
                print(f"  • Verified numbers: {len(verified_numbers)}")
                
                if verified_numbers:
                    print("\n  📞 Verified Numbers:")
                    for num in verified_numbers:
                        print(f"    • {num.get('PhoneNumber')} - Status: {num.get('Status')}")
                else:
                    print("  ❌ No verified numbers! Add +14168802544 to sandbox destinations")
                    print("\n  📋 Steps to verify:")
                    print("     1. AWS Console → SNS → Text messaging (SMS)")
                    print("     2. Click 'Sandbox destination phone numbers'")
                    print("     3. Click 'Add phone number'")
                    print("     4. Enter +14168802544")
                    print("     5. Enter verification code sent to phone")
                
            except ClientError as list_error:
                if 'VerifiedAccessOnly' in str(list_error) or 'InSandbox' in str(list_error):
                    print("  ⚠️  SNS IS IN SANDBOX MODE")
                    print("  ❌ Cannot list verified numbers (IAM permission issue)")
                else:
                    print("  ✅ SNS IS IN PRODUCTION MODE")
                    print("  • Can send to any phone number")
        
        except Exception as e:
            print(f"  ❌ Error checking sandbox status: {e}")
        
        # Request production access instructions
        print("\n📤 To Request Production Access:")
        print("   1. AWS Console → SNS → Text messaging (SMS)")
        print("   2. Click 'Request production access' button")
        print("   3. Fill out the form:")
        print("      - Use case: Two-factor authentication and account verification")
        print("      - Company: WeedGo Platform")
        print("      - Expected volume: 1000-5000 messages/month")
        print("   4. Submit and wait 24-48 hours for approval")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Failed to initialize SNS client: {e}")
        print("\n🔍 Check your AWS credentials:")
        print(f"  • AWS_REGION: {os.getenv('AWS_REGION', 'Not set')}")
        print(f"  • AWS_ACCESS_KEY_ID: {'Set' if os.getenv('AWS_ACCESS_KEY_ID') else 'Not set'}")
        print(f"  • AWS_SECRET_ACCESS_KEY: {'Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Not set'}")

if __name__ == '__main__':
    check_sns_status()
