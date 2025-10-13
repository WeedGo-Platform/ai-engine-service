"""
Notification Service - Handles email and SMS sending for verification
Supports email-only or email+SMS depending on verification tier
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending verification notifications via email and SMS"""

    def __init__(self):
        # Email configuration (from environment)
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@weedgo.com')

        # SMS configuration (Twilio or similar)
        self.sms_enabled = os.getenv('TWILIO_ACCOUNT_SID') is not None
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER')

        logger.info(f"NotificationService initialized (SMS enabled: {self.sms_enabled})")

    async def send_verification_email(
        self,
        to_email: str,
        code: str,
        store_name: str,
        verification_tier: str
    ) -> tuple[bool, Optional[str]]:
        """
        Send verification code via email

        Args:
            to_email: Recipient email address
            code: 6-digit verification code
            store_name: Store name from CRSA
            verification_tier: "auto_approved" or "manual_review"

        Returns:
            tuple of (success, error_message)
        """
        try:
            # Create email
            subject = "WeedGo Signup - Verification Code"

            # Different message based on verification tier
            if verification_tier == "auto_approved":
                tier_message = (
                    "Your email domain matches your business website, "
                    "so your account will be activated immediately upon verification."
                )
            else:
                tier_message = (
                    "For security, your account will be reviewed by our team within 24 hours. "
                    "You'll receive an email once your account is approved."
                )

            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">🌿 WeedGo</h1>
                    </div>

                    <div style="padding: 30px; background-color: #f5f5f5;">
                        <h2 style="color: #333;">Welcome to WeedGo, {store_name}!</h2>

                        <p style="font-size: 16px; color: #666;">
                            Thank you for signing up. To complete your account creation,
                            please use the verification code below:
                        </p>

                        <div style="background-color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                            <p style="font-size: 14px; color: #888; margin: 0 0 10px 0;">Verification Code:</p>
                            <h1 style="font-size: 36px; letter-spacing: 8px; color: #667eea; margin: 0; font-family: 'Courier New', monospace;">
                                {code}
                            </h1>
                        </div>

                        <p style="font-size: 14px; color: #666;">
                            {tier_message}
                        </p>

                        <p style="font-size: 14px; color: #666;">
                            This code will expire in <strong>5 minutes</strong>.
                            You have <strong>3 attempts</strong> to enter the correct code.
                        </p>

                        <p style="font-size: 14px; color: #999; margin-top: 30px;">
                            If you didn't request this code, please ignore this email.
                        </p>
                    </div>

                    <div style="padding: 20px; text-align: center; font-size: 12px; color: #999;">
                        <p>© 2025 WeedGo Platform. All rights reserved.</p>
                        <p>Questions? Contact us at support@weedgo.com</p>
                    </div>
                </body>
            </html>
            """

            # Plain text fallback
            text = f"""
            Welcome to WeedGo, {store_name}!

            Your verification code is: {code}

            {tier_message}

            This code will expire in 5 minutes. You have 3 attempts to enter the correct code.

            If you didn't request this code, please ignore this email.

            © 2025 WeedGo Platform
            """

            # For development: log instead of sending real email
            if not self.smtp_user or not self.smtp_password:
                logger.info(f"[DEV MODE] Email to {to_email}:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Code: {code}")
                logger.info(f"Store: {store_name}")
                logger.info(f"Tier: {verification_tier}")
                return True, None

            # Send real email in production
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Verification email sent to {to_email}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {e}")
            return False, f"Failed to send email: {str(e)}"

    async def send_verification_sms(
        self,
        to_phone: str,
        code: str,
        store_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Send verification code via SMS

        Args:
            to_phone: Recipient phone number (E.164 format)
            code: 6-digit verification code
            store_name: Store name from CRSA

        Returns:
            tuple of (success, error_message)
        """
        try:
            message = (
                f"WeedGo signup verification for {store_name}\n\n"
                f"Your code: {code}\n\n"
                f"Expires in 5 minutes."
            )

            # For development: log instead of sending real SMS
            if not self.sms_enabled:
                logger.info(f"[DEV MODE] SMS to {to_phone}:")
                logger.info(f"Message: {message}")
                return True, None

            # Send real SMS in production using Twilio
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)

            client.messages.create(
                body=message,
                from_=self.twilio_from_number,
                to=to_phone
            )

            logger.info(f"Verification SMS sent to {to_phone}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to send verification SMS to {to_phone}: {e}")
            return False, f"Failed to send SMS: {str(e)}"

    async def send_password_setup_email(
        self,
        to_email: str,
        store_name: str,
        setup_link: str,
        tenant_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Send password setup link after successful signup

        Args:
            to_email: Recipient email address
            store_name: Store name from CRSA
            setup_link: Password setup URL
            tenant_id: Created tenant ID

        Returns:
            tuple of (success, error_message)
        """
        try:
            subject = "WeedGo - Complete Your Account Setup"

            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">🎉 Welcome to WeedGo!</h1>
                    </div>

                    <div style="padding: 30px; background-color: #f5f5f5;">
                        <h2 style="color: #333;">Congratulations, {store_name}!</h2>

                        <p style="font-size: 16px; color: #666;">
                            Your WeedGo account has been created successfully.
                            You're just one step away from accessing your complete cannabis business platform!
                        </p>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{setup_link}"
                               style="display: inline-block; padding: 15px 40px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">
                                Set Up Your Password
                            </a>
                        </div>

                        <p style="font-size: 14px; color: #666;">
                            This link will expire in <strong>24 hours</strong>.
                            If you don't set your password within this time, you'll need to contact support.
                        </p>

                        <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #333; margin-top: 0;">What's Next?</h3>
                            <ul style="color: #666; line-height: 1.8;">
                                <li>Set your secure password</li>
                                <li>Access your dashboard</li>
                                <li>Configure your POS system</li>
                                <li>Set up your e-commerce store</li>
                                <li>Start selling immediately!</li>
                            </ul>
                        </div>

                        <p style="font-size: 12px; color: #999; margin-top: 30px;">
                            Your Tenant ID: <code style="background: #eee; padding: 2px 6px; border-radius: 3px;">{tenant_id}</code>
                        </p>
                    </div>

                    <div style="padding: 20px; text-align: center; font-size: 12px; color: #999;">
                        <p>© 2025 WeedGo Platform. All rights reserved.</p>
                        <p>Need help? Contact support@weedgo.com</p>
                    </div>
                </body>
            </html>
            """

            text = f"""
            Congratulations, {store_name}!

            Your WeedGo account has been created successfully.

            Complete your setup by clicking this link:
            {setup_link}

            This link expires in 24 hours.

            Your Tenant ID: {tenant_id}

            © 2025 WeedGo Platform
            """

            # For development: log instead of sending
            if not self.smtp_user or not self.smtp_password:
                logger.info(f"[DEV MODE] Password setup email to {to_email}:")
                logger.info(f"Setup Link: {setup_link}")
                logger.info(f"Tenant ID: {tenant_id}")
                return True, None

            # Send real email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Password setup email sent to {to_email}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to send password setup email to {to_email}: {e}")
            return False, f"Failed to send email: {str(e)}"


# Global singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service singleton"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
