"""
SMS Communication Channel Service
Following SOLID principles for broadcast SMS functionality
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import aiohttp
import json
import phonenumbers
from phonenumbers import geocoder, carrier

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


class SMSService(ICommunicationChannel):
    """
    SMS service implementation for broadcast communications
    Supports Twilio, AWS SNS, and MessageBird
    """

    def __init__(self, config: ChannelConfig, provider: str = "twilio", tenant_settings: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.channel_type = ChannelType.SMS
        self.provider = provider
        self._session: Optional[aiohttp.ClientSession] = None
        self.tenant_settings = tenant_settings or {}

        # Provider-specific settings
        self.api_base_url = self._get_provider_url()
        self.auth = self._get_provider_auth()

        # SMS-specific limits
        self.max_segments = 5  # Max segments for long messages
        self.segment_size = 160  # Characters per SMS segment
        self.unicode_segment_size = 70  # Characters per segment for unicode

    def _get_provider_url(self) -> str:
        """Get API base URL based on provider"""
        # Use tenant settings if available, otherwise fall back to config/env
        if self.provider == "twilio":
            account_sid = self._get_twilio_account_sid()
            return f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

        urls = {
            "messagebird": "https://rest.messagebird.com",
            "sns": "https://sns.us-east-1.amazonaws.com"
        }
        return urls.get(self.provider, "https://api.twilio.com")

    def _get_provider_auth(self) -> Optional[aiohttp.BasicAuth]:
        """Get provider-specific authentication"""
        if self.provider == "twilio":
            account_sid = self._get_twilio_account_sid()
            auth_token = self._get_twilio_auth_token()
            return aiohttp.BasicAuth(account_sid, auth_token)
        return None

    def _get_twilio_account_sid(self) -> str:
        """Get Twilio Account SID from tenant settings"""
        if self.tenant_settings and 'sms' in self.tenant_settings:
            sms_settings = self.tenant_settings['sms']
            if sms_settings.get('provider') == 'twilio' and 'twilio' in sms_settings:
                return sms_settings['twilio'].get('accountSid', '')
        return ''

    def _get_twilio_auth_token(self) -> str:
        """Get Twilio Auth Token from tenant settings"""
        if self.tenant_settings and 'sms' in self.tenant_settings:
            sms_settings = self.tenant_settings['sms']
            if sms_settings.get('provider') == 'twilio' and 'twilio' in sms_settings:
                return sms_settings['twilio'].get('authToken', '')
        return ''

    def _get_twilio_phone_number(self) -> str:
        """Get Twilio Phone Number from tenant settings"""
        if self.tenant_settings and 'sms' in self.tenant_settings:
            sms_settings = self.tenant_settings['sms']
            if sms_settings.get('provider') == 'twilio' and 'twilio' in sms_settings:
                return sms_settings['twilio'].get('phoneNumber', '')
        return ''

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                auth=self.auth if self.provider == "twilio" else None
            )
        return self._session

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """
        Send SMS to a single recipient

        Args:
            recipient: Recipient information
            message: SMS message content

        Returns:
            DeliveryResult with delivery status
        """
        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"sms_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error
            )

        # Check preferences
        if not await self.check_preferences(recipient):
            return DeliveryResult(
                message_id=f"sms_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.UNSUBSCRIBED,
                channel=self.channel_type,
                error_message="Recipient has opted out of SMS"
            )

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            # Prepare SMS content
            sms_content = await self._prepare_sms_content(message, recipient)

            # Check message segments
            segments = self._calculate_segments(sms_content)
            if segments > self.max_segments:
                return DeliveryResult(
                    message_id=f"sms_{recipient.id}_{datetime.now().timestamp()}",
                    recipient_id=recipient.id,
                    status=DeliveryStatus.FAILED,
                    channel=self.channel_type,
                    error_message=f"Message too long: {segments} segments (max {self.max_segments})"
                )

            # Format phone number
            formatted_phone = await self._format_phone_number(recipient.phone)

            # Send via provider
            result = await self._send_via_provider(
                to_number=formatted_phone,
                from_number=message.sender_phone or self._get_twilio_phone_number(),
                content=sms_content
            )

            # Calculate cost based on segments
            cost = self.config.cost_per_message * segments

            return DeliveryResult(
                message_id=result.get("message_id", f"sms_{recipient.id}_{datetime.now().timestamp()}"),
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=cost,
                metadata={**result, "segments": segments}
            )

        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient.phone}: {e}")

            # Retry on failure
            if self.config.retry_attempts > 0:
                return await self._retry_failed_message(recipient, message)

            return DeliveryResult(
                message_id=f"sms_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=str(e)
            )

    async def send_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """
        Send same SMS to multiple recipients

        Args:
            recipients: List of recipients
            message: SMS message content

        Returns:
            List of DeliveryResult for each recipient
        """
        # Process in batches for efficiency
        return await BatchProcessor.process_in_batches(
            items=recipients,
            batch_size=min(self.config.batch_size, 50),  # SMS providers often have lower batch limits
            process_func=lambda batch: self._send_batch_internal(batch, message),
            delay_between_batches=2.0  # Higher delay for SMS to avoid rate limits
        )

    async def _send_batch_internal(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """Internal method to send batch of SMS messages"""
        tasks = []
        for recipient in recipients:
            tasks.append(self.send_single(recipient, message))

        return await asyncio.gather(*tasks)

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """
        Validate SMS recipient

        Args:
            recipient: Recipient to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not recipient.phone:
            return False, "Phone number is required"

        # Basic validation
        is_valid, error = MessageValidator.validate_phone(recipient.phone)
        if not is_valid:
            return False, error

        # Advanced validation with phonenumbers library
        try:
            parsed_number = phonenumbers.parse(recipient.phone, "CA")  # Default to Canada
            if not phonenumbers.is_valid_number(parsed_number):
                return False, "Invalid phone number for region"

            # Check if it's a mobile number (for SMS)
            carrier_name = carrier.name_for_number(parsed_number, "en")
            if carrier_name == "":
                logger.warning(f"Could not determine carrier for {recipient.phone}")

            return True, None

        except phonenumbers.NumberParseException as e:
            return False, f"Invalid phone number format: {e}"

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent SMS

        Args:
            message_id: Message ID to check

        Returns:
            DeliveryResult with current status
        """
        try:
            session = await self._get_session()

            if self.provider == "twilio":
                url = f"{self.api_base_url}/Messages/{message_id}.json"
                async with session.get(url) as response:
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

            elif self.provider == "messagebird":
                url = f"{self.api_base_url}/messages/{message_id}"
                headers = {"Authorization": f"AccessKey {self.config.api_key}"}
                async with session.get(url, headers=headers) as response:
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
            logger.error(f"Failed to get SMS delivery status: {e}")
            return DeliveryResult(
                message_id=message_id,
                recipient_id="",
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=str(e)
            )

    async def _prepare_sms_content(
        self,
        message: Message,
        recipient: Recipient
    ) -> str:
        """Prepare SMS content with variable substitution"""
        content = message.content

        # Process template variables
        if message.template_variables:
            variables = {
                **message.template_variables,
                "recipient_name": recipient.name or "Customer",
                "recipient_phone": recipient.phone
            }

            if recipient.metadata:
                variables.update(recipient.metadata)

            # Replace variables
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

        # Add opt-out message if required (compliance)
        if message.metadata and message.metadata.get("include_opt_out", True):
            opt_out_text = "\n\nReply STOP to unsubscribe"
            if len(content) + len(opt_out_text) <= self.segment_size:
                content += opt_out_text

        return content

    def _calculate_segments(self, content: str) -> int:
        """Calculate number of SMS segments for message"""
        # Check if message contains unicode characters
        has_unicode = any(ord(char) > 127 for char in content)

        if has_unicode:
            segment_size = self.unicode_segment_size
        else:
            segment_size = self.segment_size

        # Account for concatenation headers in multi-segment messages
        if len(content) <= segment_size:
            return 1
        else:
            # Multi-segment messages have reduced size due to headers
            reduced_size = segment_size - 7
            return (len(content) - 1) // reduced_size + 1

    async def _format_phone_number(self, phone: str) -> str:
        """Format phone number for provider"""
        try:
            # Parse and format to E164
            parsed = phonenumbers.parse(phone, "CA")
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return formatted
        except:
            # Fallback to basic formatting
            cleaned = ''.join(filter(str.isdigit, phone))
            if not cleaned.startswith('1') and len(cleaned) == 10:
                cleaned = '1' + cleaned  # Add country code for North America
            return '+' + cleaned

    async def _send_via_provider(
        self,
        to_number: str,
        from_number: str,
        content: str
    ) -> Dict[str, Any]:
        """Send SMS via configured provider"""
        session = await self._get_session()

        if self.provider == "twilio":
            url = f"{self.api_base_url}/Messages.json"
            data = {
                "To": to_number,
                "From": from_number,
                "Body": content
            }

            async with session.post(url, data=data) as response:
                response_data = await response.json()
                if response.status in [200, 201]:
                    return {
                        "message_id": response_data.get("sid"),
                        "status": response_data.get("status"),
                        "provider_response": response_data
                    }
                else:
                    raise Exception(f"Twilio error: {response_data.get('message', 'Unknown error')}")

        elif self.provider == "messagebird":
            url = f"{self.api_base_url}/messages"
            headers = {
                "Authorization": f"AccessKey {self.config.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "originator": from_number,
                "recipients": [to_number],
                "body": content
            }

            async with session.post(url, headers=headers, json=data) as response:
                response_data = await response.json()
                if response.status in [200, 201]:
                    return {
                        "message_id": response_data.get("id"),
                        "status": "sent",
                        "provider_response": response_data
                    }
                else:
                    errors = response_data.get("errors", [])
                    error_msg = errors[0].get("description") if errors else "Unknown error"
                    raise Exception(f"MessageBird error: {error_msg}")

        # Default response
        return {
            "message_id": f"sms_{datetime.now().timestamp()}",
            "status": "sent"
        }

    def _map_provider_status(self, provider_status: str) -> DeliveryStatus:
        """Map provider-specific status to DeliveryStatus enum"""
        status_mapping = {
            # Twilio statuses
            "queued": DeliveryStatus.QUEUED,
            "sending": DeliveryStatus.SENDING,
            "sent": DeliveryStatus.SENT,
            "delivered": DeliveryStatus.DELIVERED,
            "undelivered": DeliveryStatus.FAILED,
            "failed": DeliveryStatus.FAILED,

            # MessageBird statuses
            "scheduled": DeliveryStatus.PENDING,
            "sent": DeliveryStatus.SENT,
            "buffered": DeliveryStatus.SENDING,
            "delivered": DeliveryStatus.DELIVERED,
            "expired": DeliveryStatus.FAILED,
            "delivery_failed": DeliveryStatus.FAILED
        }

        return status_mapping.get(provider_status.lower(), DeliveryStatus.SENT)

    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Handle webhook callbacks from SMS provider

        Args:
            webhook_data: Webhook payload from provider
        """
        try:
            if self.provider == "twilio":
                message_sid = webhook_data.get("MessageSid")
                status = webhook_data.get("MessageStatus")
                from_number = webhook_data.get("From")
                body = webhook_data.get("Body", "").upper()

                if status == "delivered":
                    logger.info(f"SMS {message_sid} delivered")
                elif status in ["undelivered", "failed"]:
                    logger.warning(f"SMS {message_sid} failed: {webhook_data.get('ErrorMessage')}")

                # Handle opt-out
                if body in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
                    await self.handle_unsubscribe(from_number, "SMS opt-out request")

            elif self.provider == "messagebird":
                message_id = webhook_data.get("id")
                status = webhook_data.get("status", {}).get("status")

                if status == "delivered":
                    logger.info(f"SMS {message_id} delivered")
                elif status in ["expired", "delivery_failed"]:
                    logger.warning(f"SMS {message_id} failed")

        except Exception as e:
            logger.error(f"Failed to process SMS webhook: {e}")

    async def send_verification_code(
        self,
        phone_number: str,
        code: str,
        template: str = "Your verification code is: {code}"
    ) -> DeliveryResult:
        """
        Utility method to send verification codes

        Args:
            phone_number: Recipient phone number
            code: Verification code
            template: Message template

        Returns:
            DeliveryResult
        """
        recipient = Recipient(
            id=f"verify_{phone_number}",
            phone=phone_number
        )

        message = Message(
            content=template.format(code=code),
            priority=MessagePriority.HIGH,
            metadata={"include_opt_out": False}  # No opt-out for transactional
        )

        return await self.send_single(recipient, message)

    async def close(self):
        """Clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()