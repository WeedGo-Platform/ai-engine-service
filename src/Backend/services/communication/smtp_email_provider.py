"""
SMTP Email Provider (Gmail/Generic SMTP)
Tertiary fallback email provider using standard SMTP protocol
"""

import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Any, Tuple
from datetime import datetime

from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    MessageValidator
)

logger = logging.getLogger(__name__)


class SMTPEmailProvider(ICommunicationChannel):
    """
    SMTP email provider for sending emails via standard SMTP
    Works with Gmail, Outlook, or any custom SMTP server
    
    Automatic failover chain: AWS SES (Primary) → SendGrid (Secondary) → SMTP (Tertiary)
    """

    def __init__(
        self,
        config: ChannelConfig,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_email: Optional[str] = None,
        smtp_from_name: Optional[str] = None,
        use_tls: bool = True
    ):
        super().__init__(config)
        self.channel_type = ChannelType.EMAIL

        # SMTP configuration from parameters or environment
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.smtp_from_email = smtp_from_email or os.getenv('SMTP_FROM_EMAIL', self.smtp_user)
        self.smtp_from_name = smtp_from_name or os.getenv('SMTP_FROM_NAME', 'WeedGo')
        self.use_tls = use_tls

        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured - provider will be unavailable")

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection with TLS"""
        try:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.config.timeout)
            
            if self.use_tls:
                smtp.starttls()
            
            smtp.login(self.smtp_user, self.smtp_password)
            return smtp
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """
        Send single email via SMTP
        
        This is called by UnifiedMessagingService when:
        1. AWS SES fails (e.g., sandbox mode, unverified recipient)
        2. SendGrid fails (e.g., invalid API key, rate limit)
        3. SMTP is the last resort before giving up
        """
        
        if not self.smtp_user or not self.smtp_password:
            return DeliveryResult(
                message_id=f"smtp-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message="SMTP credentials not configured",
                sent_at=datetime.now()
            )

        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"smtp-invalid-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error,
                sent_at=datetime.now()
            )

        try:
            # Create MIME message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject or 'WeedGo Notification'
            msg['From'] = f"{message.sender_name or self.smtp_from_name} <{message.sender_email or self.smtp_from_email}>"
            msg['To'] = recipient.email

            # Add plain text version if provided in template_variables
            if message.template_variables and message.template_variables.get('text_content'):
                text_part = MIMEText(message.template_variables['text_content'], 'plain')
                msg.attach(text_part)

            # Add HTML content (primary content)
            if message.content:
                html_part = MIMEText(message.content, 'html')
                msg.attach(html_part)

            # Send via SMTP
            smtp = self._create_smtp_connection()
            smtp.send_message(msg)
            smtp.quit()

            logger.info(f"Email sent via SMTP to {recipient.email}")

            return DeliveryResult(
                message_id=f"smtp-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=0.0,  # SMTP/Gmail is free
                metadata={
                    'provider': 'smtp',
                    'smtp_host': self.smtp_host,
                    'smtp_port': self.smtp_port,
                    'smtp_user': self.smtp_user
                }
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return DeliveryResult(
                message_id=f"smtp-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=f"SMTP authentication failed: {str(e)}",
                sent_at=datetime.now()
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return DeliveryResult(
                message_id=f"smtp-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=f"SMTP error: {str(e)}",
                sent_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return DeliveryResult(
                message_id=f"smtp-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=str(e),
                sent_at=datetime.now()
            )

    async def send_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """
        Send batch emails via SMTP
        
        SMTP is slow compared to API-based providers (SES/SendGrid),
        so we send individually with rate limiting
        """
        results = []

        for recipient in recipients:
            result = await self.send_single(recipient, message)
            results.append(result)

            # Apply rate limiting (1 email/second for SMTP)
            await self._apply_rate_limiting()

        return results

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """Validate email recipient"""
        if not recipient.email:
            return False, "Email address is required"

        return MessageValidator.validate_email(recipient.email)

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent email
        
        Note: Standard SMTP doesn't provide delivery tracking
        For delivery confirmations, need to use AWS SES or SendGrid
        """
        return DeliveryResult(
            message_id=message_id,
            recipient_id="unknown",
            status=DeliveryStatus.SENT,
            channel=self.channel_type,
            metadata={'note': 'SMTP does not provide delivery tracking - use SES or SendGrid for tracking'}
        )
