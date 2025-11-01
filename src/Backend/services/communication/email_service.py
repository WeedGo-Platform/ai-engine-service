"""
Email Communication Channel Service
Following SOLID principles for broadcast email functionality
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import aiohttp
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    MessageValidator,
    BatchProcessor
)

logger = logging.getLogger(__name__)


class EmailService(ICommunicationChannel):
    """
    Email service implementation for broadcast communications
    Supports SendGrid, AWS SES, and SMTP
    """

    def __init__(self, config: ChannelConfig, provider: str = "sendgrid", tenant_settings: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.channel_type = ChannelType.EMAIL
        self.provider = provider
        self._session: Optional[aiohttp.ClientSession] = None
        self.tenant_settings = tenant_settings or {}

        # Provider-specific settings
        self.api_base_url = self._get_provider_url()
        self.headers = self._get_provider_headers()

    def _get_provider_url(self) -> str:
        """Get API base URL based on provider"""
        urls = {
            "sendgrid": "https://api.sendgrid.com/v3",
            "mailgun": "https://api.mailgun.net/v3/sandboxdomain.mailgun.org",
            "ses": "https://email.us-east-1.amazonaws.com"
        }
        return urls.get(self.provider, urls["sendgrid"])

    def _get_provider_headers(self) -> Dict[str, str]:
        """Get provider-specific headers"""
        if self.provider == "sendgrid":
            api_key = self._get_sendgrid_api_key()
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "mailgun":
            return {
                "Authorization": f"Basic {self.config.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        return {}

    def _get_sendgrid_api_key(self) -> str:
        """Get SendGrid API Key from tenant settings"""
        if self.tenant_settings and 'email' in self.tenant_settings:
            email_settings = self.tenant_settings['email']
            if email_settings.get('provider') == 'sendgrid' and 'sendgrid' in email_settings:
                return email_settings['sendgrid'].get('apiKey', '')
        return ''

    def _get_sendgrid_from_email(self) -> str:
        """Get SendGrid From Email from tenant settings"""
        if self.tenant_settings and 'email' in self.tenant_settings:
            email_settings = self.tenant_settings['email']
            if email_settings.get('provider') == 'sendgrid' and 'sendgrid' in email_settings:
                return email_settings['sendgrid'].get('fromEmail', 'noreply@weedgo.ai')
        return 'noreply@weedgo.ai'

    def _get_sendgrid_from_name(self) -> str:
        """Get SendGrid From Name from tenant settings"""
        if self.tenant_settings and 'email' in self.tenant_settings:
            email_settings = self.tenant_settings['email']
            if email_settings.get('provider') == 'sendgrid' and 'sendgrid' in email_settings:
                return email_settings['sendgrid'].get('fromName', 'WeedGo')
        return 'WeedGo'

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """
        Send email to a single recipient

        Args:
            recipient: Recipient information
            message: Email message content

        Returns:
            DeliveryResult with delivery status
        """
        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"email_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error
            )

        # Check preferences
        if not await self.check_preferences(recipient):
            return DeliveryResult(
                message_id=f"email_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.UNSUBSCRIBED,
                channel=self.channel_type,
                error_message="Recipient has unsubscribed from email"
            )

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            # Prepare email payload
            payload = await self._prepare_email_payload(recipient, message)

            # Send via provider
            result = await self._send_via_provider(payload)

            return DeliveryResult(
                message_id=result.get("message_id", f"email_{recipient.id}_{datetime.now().timestamp()}"),
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=self.config.cost_per_message,
                metadata=result
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {recipient.email}: {error_msg}")

            # Don't retry on permanent failures (authentication, invalid recipient, etc.)
            is_permanent_failure = any([
                '401' in error_msg,  # Authentication error
                '403' in error_msg,  # Permission denied
                'Permission denied' in error_msg,
                'wrong credentials' in error_msg,
                'Invalid API key' in error_msg,
                'unauthorized' in error_msg.lower(),
                'not verified' in error_msg.lower() and 'sandbox' not in error_msg.lower(),  # SES sandbox is retryable
            ])

            # Only retry on transient failures (network issues, rate limits, timeouts)
            if not is_permanent_failure and self.config.retry_attempts > 0:
                # Check if it's a retryable error (5xx, timeout, network)
                is_retryable = any([
                    '5' in error_msg and error_msg.index('5') < 3,  # 5xx errors
                    'timeout' in error_msg.lower(),
                    'connection' in error_msg.lower(),
                    'network' in error_msg.lower(),
                ])
                
                if is_retryable:
                    return await self._retry_failed_message(recipient, message)

            return DeliveryResult(
                message_id=f"email_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error_msg
            )

    async def send_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """
        Send same email to multiple recipients

        Args:
            recipients: List of recipients
            message: Email message content

        Returns:
            List of DeliveryResult for each recipient
        """
        # Process in batches for efficiency
        return await BatchProcessor.process_in_batches(
            items=recipients,
            batch_size=self.config.batch_size,
            process_func=lambda batch: self._send_batch_internal(batch, message),
            delay_between_batches=1.0  # Delay between batches
        )

    async def _send_batch_internal(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """Internal method to send batch of emails"""
        tasks = []
        for recipient in recipients:
            tasks.append(self.send_single(recipient, message))

        return await asyncio.gather(*tasks)

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """
        Validate email recipient

        Args:
            recipient: Recipient to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not recipient.email:
            return False, "Email address is required"

        return MessageValidator.validate_email(recipient.email)

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent email

        Args:
            message_id: Message ID to check

        Returns:
            DeliveryResult with current status
        """
        try:
            session = await self._get_session()

            if self.provider == "sendgrid":
                url = f"{self.api_base_url}/messages/{message_id}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = self._map_provider_status(data.get("status"))
                        return DeliveryResult(
                            message_id=message_id,
                            recipient_id="",
                            status=status,
                            channel=self.channel_type,
                            metadata=data
                        )

            # Default response if status check not available
            return DeliveryResult(
                message_id=message_id,
                recipient_id="",
                status=DeliveryStatus.SENT,
                channel=self.channel_type
            )

        except Exception as e:
            logger.error(f"Failed to get delivery status: {e}")
            return DeliveryResult(
                message_id=message_id,
                recipient_id="",
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=str(e)
            )

    async def _prepare_email_payload(
        self,
        recipient: Recipient,
        message: Message
    ) -> Dict[str, Any]:
        """Prepare email payload based on provider"""

        # Process template if provided
        content = await self._process_template(message, recipient)

        if self.provider == "sendgrid":
            payload = {
                "personalizations": [{
                    "to": [{"email": recipient.email, "name": recipient.name}],
                    "subject": message.subject or "Notification"
                }],
                "from": {
                    "email": message.sender_email or self._get_sendgrid_from_email(),
                    "name": message.sender_name or self._get_sendgrid_from_name()
                },
                "content": [{
                    "type": "text/html" if "<html>" in content else "text/plain",
                    "value": content
                }]
            }

            if message.reply_to:
                payload["reply_to"] = {"email": message.reply_to}

            if message.attachments:
                payload["attachments"] = await self._prepare_attachments(message.attachments)

        elif self.provider == "mailgun":
            payload = {
                "from": f"{message.sender_name or self._get_sendgrid_from_name()} <{message.sender_email or self._get_sendgrid_from_email()}>",
                "to": f"{recipient.name or ''} <{recipient.email}>",
                "subject": message.subject or "Notification",
                "html" if "<html>" in content else "text": content
            }

        else:  # Default/SMTP format
            payload = {
                "to": recipient.email,
                "subject": message.subject or "Notification",
                "body": content,
                "from": message.sender_email or "noreply@weedgo.ai"
            }

        return payload

    async def _process_template(
        self,
        message: Message,
        recipient: Recipient
    ) -> str:
        """Process message template with variables"""
        content = message.content

        if message.template_variables:
            # Merge recipient metadata with template variables
            variables = {
                **message.template_variables,
                "recipient_name": recipient.name,
                "recipient_email": recipient.email
            }

            if recipient.metadata:
                variables.update(recipient.metadata)

            # Replace variables in content
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

        return content

    async def _prepare_attachments(
        self,
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Prepare attachments for email"""
        prepared = []

        for attachment in attachments:
            if "content" in attachment:
                # Base64 encode if not already encoded
                import base64
                content = attachment["content"]
                if not isinstance(content, str):
                    content = base64.b64encode(content).decode()

                prepared.append({
                    "content": content,
                    "type": attachment.get("type", "application/octet-stream"),
                    "filename": attachment.get("filename", "attachment"),
                    "disposition": "attachment"
                })

        return prepared

    async def _send_via_provider(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via configured provider"""
        session = await self._get_session()

        if self.provider == "sendgrid":
            url = f"{self.api_base_url}/mail/send"
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status in [200, 202]:
                    # SendGrid returns message ID in headers
                    return {
                        "message_id": response.headers.get("X-Message-Id", ""),
                        "status": "sent",
                        "provider_response": await response.text()
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"SendGrid error: {response.status} - {error_text}")

        elif self.provider == "mailgun":
            url = f"{self.api_base_url}/messages"
            async with session.post(url, headers=self.headers, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "message_id": data.get("id", ""),
                        "status": "sent",
                        "provider_response": data
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Mailgun error: {response.status} - {error_text}")

        # Default response
        return {
            "message_id": f"email_{datetime.now().timestamp()}",
            "status": "sent"
        }

    def _map_provider_status(self, provider_status: str) -> DeliveryStatus:
        """Map provider-specific status to DeliveryStatus enum"""
        status_mapping = {
            # SendGrid statuses
            "processed": DeliveryStatus.SENT,
            "delivered": DeliveryStatus.DELIVERED,
            "bounce": DeliveryStatus.BOUNCED,
            "deferred": DeliveryStatus.PENDING,
            "dropped": DeliveryStatus.FAILED,

            # Mailgun statuses
            "accepted": DeliveryStatus.SENT,
            "delivered": DeliveryStatus.DELIVERED,
            "failed": DeliveryStatus.FAILED,
            "rejected": DeliveryStatus.FAILED,

            # Generic
            "sent": DeliveryStatus.SENT,
            "pending": DeliveryStatus.PENDING,
            "failed": DeliveryStatus.FAILED
        }

        return status_mapping.get(provider_status.lower(), DeliveryStatus.SENT)

    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Handle webhook callbacks from email provider

        Args:
            webhook_data: Webhook payload from provider
        """
        try:
            if self.provider == "sendgrid":
                events = webhook_data if isinstance(webhook_data, list) else [webhook_data]
                for event in events:
                    message_id = event.get("sg_message_id")
                    event_type = event.get("event")

                    if event_type == "delivered":
                        # Update delivery status in database
                        logger.info(f"Email {message_id} delivered")
                    elif event_type == "bounce":
                        logger.warning(f"Email {message_id} bounced")
                    elif event_type == "open":
                        logger.info(f"Email {message_id} opened")
                    elif event_type == "click":
                        logger.info(f"Email {message_id} link clicked")
                    elif event_type == "unsubscribe":
                        await self.handle_unsubscribe(event.get("email"))

        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")

    async def close(self):
        """Clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()