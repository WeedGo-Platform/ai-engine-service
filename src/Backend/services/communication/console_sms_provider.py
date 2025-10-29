"""
Console SMS Provider for Development/Testing
Logs SMS messages to console instead of actually sending them
"""

import logging
from datetime import datetime
from typing import Optional
from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    ProviderHealth,
    ProviderStatus
)

logger = logging.getLogger(__name__)


class ConsoleSMSProvider(ICommunicationChannel):
    """
    Console-based SMS provider for development and testing
    Logs messages instead of sending them
    """

    def __init__(self, config: ChannelConfig):
        self.config = config
        self.channel_type = ChannelType.SMS
        logger.info("🔧 Console SMS Provider initialized (development mode)")

    async def send_single(self, recipient: Recipient, message: Message) -> DeliveryResult:
        """Send single SMS (required by interface)"""
        return await self.send(recipient, message)

    async def send_batch(self, recipients: list, message: Message) -> list:
        """Send batch SMS (required by interface)"""
        results = []
        for recipient in recipients:
            result = await self.send(recipient, message)
            results.append(result)
        return results

    async def validate_recipient(self, recipient: Recipient) -> bool:
        """Validate recipient (always true for console)"""
        return True

    async def get_delivery_status(self, message_id: str) -> DeliveryStatus:
        """Get delivery status (always sent for console)"""
        return DeliveryStatus.SENT

    async def send(self, recipient: Recipient, message: Message) -> DeliveryResult:
        """
        'Send' SMS by logging to console
        """
        try:
            phone = recipient.phone or recipient.id

            # Log the message to console with visual formatting
            logger.info("=" * 80)
            logger.info("📱 CONSOLE SMS (DEVELOPMENT MODE)")
            logger.info("=" * 80)
            logger.info(f"To: {phone}")
            logger.info(f"From: {message.sender_phone or 'WeedGo'}")
            logger.info(f"Time: {datetime.now().isoformat()}")
            logger.info("-" * 80)
            logger.info(f"Message:\n{message.content}")
            logger.info("=" * 80)

            # Also print to stdout for visibility
            print("\n" + "=" * 80)
            print("📱 SMS MESSAGE (DEVELOPMENT MODE)")
            print("=" * 80)
            print(f"To: {phone}")
            print(f"Message: {message.content}")
            print("=" * 80 + "\n")

            return DeliveryResult(
                message_id=f"console-sms-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=ChannelType.SMS,
                sent_at=datetime.now(),
                metadata={
                    'provider': 'console',
                    'mode': 'development',
                    'phone': phone,
                    'message_length': len(message.content)
                }
            )

        except Exception as e:
            logger.error(f"Console SMS logging failed: {e}")
            return DeliveryResult(
                message_id=f"console-sms-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=ChannelType.SMS,
                error_message=str(e),
                sent_at=datetime.now()
            )

    async def get_health(self) -> ProviderHealth:
        """Console provider is always healthy"""
        return ProviderHealth(
            provider_name="Console SMS",
            status=ProviderStatus.HEALTHY,
            last_check=datetime.now(),
            message="Development console provider"
        )

    def get_channel_type(self) -> ChannelType:
        """Return channel type"""
        return ChannelType.SMS
