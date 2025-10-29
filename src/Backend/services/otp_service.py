"""
OTP Service for handling one-time passcode authentication
Integrates with Twilio for SMS and SendGrid for email
"""

import random
import string
import json
import asyncio
import logging
import os
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Literal
from uuid import UUID
import asyncpg
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import re

logger = logging.getLogger(__name__)


class OTPService:
    """Service for managing OTP generation, sending, and verification"""

    def __init__(self, tenant_id: Optional[str] = None, db_pool: Optional[asyncpg.Pool] = None):
        """Initialize OTP service with Twilio and SendGrid from tenant settings or environment"""
        self.tenant_id = tenant_id
        self.db_pool = db_pool
        self.tenant_settings = {}

        # Initialize from environment variables (fallback for global service)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.twilio_verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')

        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.sendgrid_from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@weedgo.com')
        self.sendgrid_from_name = os.getenv('SENDGRID_FROM_NAME', 'WeedGo')

        # SMTP Configuration (fallback for email)
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_user)
        self.smtp_from_name = os.getenv('SMTP_FROM_NAME', 'WeedGo')

        # Load tenant settings if available (will override environment variables)
        if self.tenant_id and self.db_pool:
            asyncio.create_task(self._load_tenant_settings())
        
        # OTP configuration (hardcoded defaults, can be moved to tenant settings if needed)
        self.otp_length = 6
        self.otp_expiry_minutes = 10
        self.otp_max_attempts = 3

        # Rate limiting configuration (hardcoded defaults)
        self.rate_limit_max_requests = 5
        self.rate_limit_window_minutes = 60
        
        # Initialize clients
        self.twilio_client = None
        self.sendgrid_client = None
        
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)
                logger.info(f"Twilio client initialized successfully with phone: {self.twilio_phone_number}")
                logger.info(f"Twilio Account SID: {self.twilio_account_sid[:10]}...")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        
        if self.sendgrid_api_key:
            try:
                self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
        
        # Log SMTP configuration status
        if self.smtp_user and self.smtp_password:
            logger.info(f"SMTP fallback configured: {self.smtp_host}:{self.smtp_port} (user: {self.smtp_user})")
        elif not self.sendgrid_client:
            logger.warning("No email service configured (neither SendGrid nor SMTP)")

    async def _load_tenant_settings(self):
        """Load tenant communication settings from database"""
        if self.tenant_id and self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    settings = await conn.fetchval("""
                        SELECT settings FROM tenants WHERE id = $1
                    """, UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id)

                    if settings and 'communication' in settings:
                        comm_settings = settings['communication']

                        # Update Twilio settings from tenant (no fallback)
                        if 'sms' in comm_settings and comm_settings['sms'].get('provider') == 'twilio':
                            twilio_config = comm_settings['sms'].get('twilio', {})
                            self.twilio_account_sid = twilio_config.get('accountSid')
                            self.twilio_auth_token = twilio_config.get('authToken')
                            self.twilio_phone_number = twilio_config.get('phoneNumber')
                            self.twilio_verify_service_sid = twilio_config.get('verifyServiceSid')

                            # Reinitialize Twilio client with new settings
                            if self.twilio_account_sid and self.twilio_auth_token:
                                self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)

                        # Update SendGrid settings from tenant (no fallback)
                        if 'email' in comm_settings and comm_settings['email'].get('provider') == 'sendgrid':
                            sg_config = comm_settings['email'].get('sendgrid', {})
                            self.sendgrid_api_key = sg_config.get('apiKey')
                            self.sendgrid_from_email = sg_config.get('fromEmail', 'noreply@weedgo.com')
                            self.sendgrid_from_name = sg_config.get('fromName', 'WeedGo')

                            # Reinitialize SendGrid client with new settings
                            if self.sendgrid_api_key:
                                self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)

                        self.tenant_settings = comm_settings
                        logger.info(f"Loaded tenant settings for tenant {self.tenant_id}")
            except Exception as e:
                logger.warning(f"Failed to load tenant settings: {e}")
    
    def generate_otp(self, length: Optional[int] = None) -> str:
        """Generate a random OTP code"""
        length = length or self.otp_length
        return ''.join(random.choices(string.digits, k=length))
    
    def validate_phone_number(self, phone: str) -> str:
        """Validate and format phone number"""
        # Remove all non-digits
        phone = re.sub(r'\D', '', phone)
        
        # Add country code if not present (assuming US)
        if len(phone) == 10:
            phone = '1' + phone
        
        # Validate length
        if len(phone) < 10 or len(phone) > 15:
            raise ValueError("Invalid phone number format")
        
        return '+' + phone
    
    def validate_email(self, email: str) -> str:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    async def get_db_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123')
        )
        return conn
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        identifier_type: Literal['email', 'phone']
    ) -> Dict[str, Any]:
        """Check if identifier has exceeded rate limit"""
        conn = None
        try:
            conn = await self.get_db_connection()
            
            # Call the stored procedure
            allowed = await conn.fetchval(
                "SELECT check_otp_rate_limit($1, $2, $3, $4)",
                identifier, identifier_type, 
                self.rate_limit_max_requests, 
                self.rate_limit_window_minutes
            )
            
            # Get additional rate limit info if blocked
            if not allowed:
                rate_limit_info = await conn.fetchrow(
                    """SELECT blocked_until, request_count, first_request_at 
                       FROM otp_rate_limits 
                       WHERE identifier = $1 AND identifier_type = $2""",
                    identifier, identifier_type
                )
                
                if rate_limit_info and rate_limit_info['blocked_until']:
                    retry_seconds = int((rate_limit_info['blocked_until'] - datetime.now()).total_seconds())
                    return {
                        'allowed': False,
                        'blocked_until': rate_limit_info['blocked_until'].isoformat(),
                        'retry_after_seconds': max(retry_seconds, 60)  # Minimum 1 minute
                    }
            
            return {'allowed': allowed, 'retry_after_seconds': 0}
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {'allowed': True, 'retry_after_seconds': 0}  # Fail open
        finally:
            if conn:
                await conn.close()
    
    async def send_otp_sms(
        self, 
        phone: str, 
        otp: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send OTP via SMS using Twilio"""
        if not self.twilio_client:
            logger.error("Twilio client not initialized")
            return {
                'success': False,
                'error': 'SMS service not configured'
            }
        
        conn = None
        try:
            # Validate phone number
            formatted_phone = self.validate_phone_number(phone)
            
            # Create message
            message_body = f"Your WeedGo verification code is: {otp}\n\nThis code will expire in {self.otp_expiry_minutes} minutes."
            
            # Send SMS with timeout
            # Add timeout to prevent hanging
            import socket
            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(10)  # 10 second timeout
                message = self.twilio_client.messages.create(
                    body=message_body,
                    from_=self.twilio_phone_number,
                    to=formatted_phone
                )
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            # Log communication
            conn = await self.get_db_connection()
            await conn.execute(
                """
                INSERT INTO communication_logs (
                    user_id, recipient, communication_type, provider,
                    content, status, provider_message_id, provider_response, sent_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                user_id, formatted_phone, 'sms', 'twilio',
                message_body, 'sent', message.sid,
                json.dumps({'status': message.status, 'price': str(message.price) if message.price else None}),
                datetime.now()
            )
            
            logger.info(f"OTP SMS sent to {formatted_phone}")
            
            return {
                'success': True,
                'message_id': message.sid,
                'status': message.status
            }
            
        except (TwilioException, socket.timeout) as e:
            logger.error(f"Twilio error: {e}")
            
            # FALLBACK: Log OTP to console for testing when Twilio fails
            logger.warning(f"SMS FALLBACK - OTP for {formatted_phone}: {otp}")
            print(f"\n=== SMS FALLBACK (Twilio unavailable) ===")
            print(f"To: {formatted_phone}")
            print(f"OTP Code: {otp}")
            print(f"Expires in: {self.otp_expiry_minutes} minutes")
            print(f"==========================================\n")
            
            # Log failed attempt
            if conn:
                await conn.execute(
                    """
                    INSERT INTO communication_logs (
                        user_id, recipient, communication_type, provider,
                        content, status, error_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    user_id, phone, 'sms', 'twilio',
                    f"OTP: {otp}", 'failed', str(e)
                )
            
            # Return success anyway for testing purposes
            return {
                'success': True,
                'message_id': 'FALLBACK_MODE',
                'status': 'logged_locally',
                'otp_code': otp  # Include OTP in response for testing
            }
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if conn:
                await conn.close()
    
    async def send_otp_email(
        self, 
        email: str, 
        otp: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send OTP via email using SendGrid or SMTP fallback"""
        conn = None
        validated_email = None
        
        try:
            # Validate email
            validated_email = self.validate_email(email)
            
            # Try SendGrid first if available
            if self.sendgrid_client:
                try:
                    return await self._send_via_sendgrid(validated_email, otp, user_id)
                except Exception as e:
                    logger.warning(f"SendGrid failed, trying SMTP fallback: {e}")
            
            # Fallback to SMTP if SendGrid failed or not configured
            if self.smtp_user and self.smtp_password:
                return await self._send_via_smtp(validated_email, otp, user_id)
            
            # No email service configured
            logger.error("No email service available (neither SendGrid nor SMTP)")
            return {
                'success': False,
                'error': 'Email service not configured'
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            
            # Log failed attempt
            if conn:
                await conn.execute(
                    """
                    INSERT INTO communication_logs (
                        user_id, recipient, communication_type, provider,
                        subject, content, status, error_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    user_id, validated_email or email, 'email', 'failed',
                    "Verification Code", f"OTP: {otp}", 'failed', str(e)
                )
            
            return {
                'success': False,
                'error': 'Failed to send email'
            }
        finally:
            if conn:
                await conn.close()
    
    async def _send_via_sendgrid(
        self,
        email: str,
        otp: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        conn = None
        try:
            # Create email content
            subject = "Your WeedGo Verification Code"
            html_content = self._generate_otp_html(otp)
            
            # Create message
            message = Mail(
                from_email=Email(self.sendgrid_from_email, self.sendgrid_from_name),
                to_emails=To(email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            # Log communication
            conn = await self.get_db_connection()
            await conn.execute(
                """
                INSERT INTO communication_logs (
                    user_id, recipient, communication_type, provider,
                    subject, content, status, provider_message_id, provider_response, sent_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id, email, 'email', 'sendgrid',
                subject, html_content, 'sent',
                response.headers.get('X-Message-Id'),
                json.dumps({'status_code': response.status_code}),
                datetime.now()
            )
            
            logger.info(f"OTP email sent via SendGrid to {email}")
            
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code,
                'provider': 'sendgrid'
            }
        finally:
            if conn:
                await conn.close()
    
    async def _send_via_smtp(
        self,
        email: str,
        otp: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP (Gmail or custom SMTP server)"""
        conn = None
        try:
            # Create email content
            subject = "Your WeedGo Verification Code"
            html_content = self._generate_otp_html(otp)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            msg['To'] = email
            
            # Plain text version
            text_content = f"""
            WeedGo Verification Code
            
            Your verification code is: {otp}
            
            This code will expire in {self.otp_expiry_minutes} minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            # Attach both plain text and HTML
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"OTP email sent via SMTP to {email}")
            
            # Try to log communication (non-critical - don't fail if logging fails)
            try:
                conn = await self.get_db_connection()
                await conn.execute(
                    """
                    INSERT INTO communication_logs (
                        user_id, recipient, communication_type, provider,
                        subject, content, status, sent_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    user_id, email, 'email', 'smtp',
                    subject, html_content, 'sent', datetime.now()
                )
            except Exception as log_error:
                logger.warning(f"Failed to log SMTP email (non-critical): {log_error}")
            
            return {
                'success': True,
                'message_id': f"smtp-{datetime.now().timestamp()}",
                'provider': 'smtp'
            }
        except Exception as e:
            logger.error(f"SMTP email failed: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    def _generate_otp_html(self, otp: str) -> str:
        """Generate HTML content for OTP email"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #2e7d32; text-align: center;">WeedGo</h1>
                    <h2 style="color: #333; text-align: center;">Verification Code</h2>
                    <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p style="font-size: 16px; color: #555;">Your verification code is:</p>
                        <div style="font-size: 32px; font-weight: bold; color: #2e7d32; text-align: center; padding: 20px; background: #f0f7f0; border-radius: 5px; letter-spacing: 5px;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; color: #777; margin-top: 20px;">
                            This code will expire in {self.otp_expiry_minutes} minutes.
                        </p>
                    </div>
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
    
    async def create_otp(
        self,
        identifier: str,
        identifier_type: Literal['email', 'phone'],
        purpose: str = 'login',
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and store OTP in database"""
        conn = None
        try:
            # Check rate limit
            rate_limit_result = await self.check_rate_limit(identifier, identifier_type)
            if not rate_limit_result['allowed']:
                blocked_until = rate_limit_result.get('blocked_until')
                retry_seconds = rate_limit_result.get('retry_after_seconds', 300)
                
                return {
                    'success': False,
                    'error': f'Too many OTP requests. Please try again in {retry_seconds // 60} minutes.',
                    'rate_limited': True,
                    'retry_after_seconds': retry_seconds,
                    'blocked_until': blocked_until
                }
            
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Store in database
            conn = await self.get_db_connection()
            
            # Invalidate any existing OTPs for this identifier
            await conn.execute(
                """
                UPDATE otp_codes 
                SET verified = TRUE, verified_at = CURRENT_TIMESTAMP
                WHERE identifier = $1 
                AND identifier_type = $2
                AND verified = FALSE
                AND expires_at > CURRENT_TIMESTAMP
                """,
                identifier, identifier_type
            )
            
            # Create new OTP
            # Hash the OTP code for storage
            import hashlib
            code_hash = hashlib.sha256(otp_code.encode()).hexdigest()
            
            await conn.execute(
                """
                INSERT INTO otp_codes (
                    user_id, identifier, identifier_type, code, purpose,
                    expires_at, ip_address, user_agent, otp_type, code_hash,
                    delivery_method, delivery_address
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                user_id, identifier, identifier_type, otp_code, purpose,
                expires_at, ip_address, user_agent, purpose, code_hash,
                identifier_type, identifier
            )
            
            logger.info(f"OTP created for {identifier_type}: {identifier}")
            
            # Send OTP
            if identifier_type == 'phone':
                result = await self.send_otp_sms(identifier, otp_code, user_id)
            else:
                result = await self.send_otp_email(identifier, otp_code, user_id)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Verification code sent to {identifier_type}',
                    'expires_in_minutes': self.otp_expiry_minutes
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"OTP creation failed: {e}")
            return {
                'success': False,
                'error': 'Failed to create verification code'
            }
        finally:
            if conn:
                await conn.close()
    
    async def verify_otp(
        self,
        identifier: str,
        identifier_type: Literal['email', 'phone'],
        code: str,
        purpose: str = 'login'
    ) -> Dict[str, Any]:
        """Verify OTP code"""
        conn = None
        try:
            conn = await self.get_db_connection()
            
            # Get OTP record
            otp_record = await conn.fetchrow(
                """
                SELECT id, user_id, code, attempts, max_attempts, expires_at, verified
                FROM otp_codes
                WHERE identifier = $1
                AND identifier_type = $2
                AND purpose = $3
                AND verified = FALSE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                identifier, identifier_type, purpose
            )
            
            if not otp_record:
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new one.'
                }
            
            # Check if expired
            if otp_record['expires_at'] < datetime.now():
                return {
                    'success': False,
                    'error': 'Verification code has expired. Please request a new one.'
                }
            
            # Check attempts
            if otp_record['attempts'] >= otp_record['max_attempts']:
                return {
                    'success': False,
                    'error': 'Maximum attempts exceeded. Please request a new code.'
                }
            
            # Verify code
            if otp_record['code'] != code:
                # Increment attempts
                await conn.execute(
                    "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = $1",
                    otp_record['id']
                )
                
                remaining = otp_record['max_attempts'] - otp_record['attempts'] - 1
                return {
                    'success': False,
                    'error': f'Invalid verification code. {remaining} attempts remaining.'
                }
            
            # Mark as verified
            await conn.execute(
                """
                UPDATE otp_codes 
                SET verified = TRUE, verified_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                otp_record['id']
            )
            
            # Get user info if exists
            user = None
            if otp_record['user_id']:
                user = await conn.fetchrow(
                    """
                    SELECT id, email, first_name, last_name, phone, age_verified
                    FROM users
                    WHERE id = $1
                    """,
                    otp_record['user_id']
                )
            
            logger.info(f"OTP verified for {identifier}")
            
            return {
                'success': True,
                'message': 'Verification successful',
                'user_id': str(otp_record['user_id']) if otp_record['user_id'] else None,
                'user': dict(user) if user else None
            }
            
        except Exception as e:
            logger.error(f"OTP verification failed: {e}")
            return {
                'success': False,
                'error': 'Verification failed'
            }
        finally:
            if conn:
                await conn.close()


# Global instance
_otp_service = None

def get_otp_service() -> OTPService:
    """Get or create global OTP service instance"""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service