"""
AWS SNS SMS Provider
Cost-effective SMS sending with global reach
"""

import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os
import re

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


class AWSSNSProvider(ICommunicationChannel):
    """
    AWS Simple Notification Service SMS provider
    - 1,000 SMS/month free for 12 months
    - ~$0.00645 per SMS in US/Canada after
    - Global SMS delivery
    """

    def __init__(
        self,
        config: ChannelConfig,
        aws_region: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        sender_id: Optional[str] = None
    ):
        super().__init__(config)
        self.channel_type = ChannelType.SMS

        # AWS credentials
        self.aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
        self.aws_access_key = aws_access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')

        # SMS-specific settings
        self.sender_id = sender_id or os.getenv('AWS_SNS_SENDER_ID', 'WeedGo')
        self.default_message_type = 'Transactional'  # or 'Promotional'

        # Initialize SNS client
        self.sns_client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AWS SNS client"""
        try:
            session_config = {}
            if self.aws_access_key and self.aws_secret_key:
                session_config['aws_access_key_id'] = self.aws_access_key
                session_config['aws_secret_access_key'] = self.aws_secret_key

            session_config['region_name'] = self.aws_region

            self.sns_client = boto3.client('sns', **session_config)
            logger.info(f"AWS SNS client initialized for region: {self.aws_region}")

            # Set default SMS attributes
            self._set_sms_attributes()

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to initialize AWS SNS client: {e}")
            self.sns_client = None

    def _set_sms_attributes(self):
        """Set default SMS attributes"""
        if not self.sns_client:
            return

        try:
            self.sns_client.set_sms_attributes(
                attributes={
                    'DefaultSMSType': self.default_message_type,
                    'DefaultSenderID': self.sender_id
                }
            )
            logger.info(f"SNS SMS attributes set: Type={self.default_message_type}, SenderID={self.sender_id}")
        except ClientError as e:
            logger.warning(f"Failed to set SMS attributes (may not be supported in region): {e}")

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to E.164 format"""
        # Remove all non-numeric characters
        cleaned = re.sub(r'\D', '', phone)

        # Add +1 for North American numbers if not present
        if len(cleaned) == 10:
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"+{cleaned}"
        elif cleaned.startswith('+'):
            return phone
        else:
            return f"+{cleaned}"

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """Send single SMS via AWS SNS"""
        if not self.sns_client:
            return DeliveryResult(
                message_id=f"sns-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message="AWS SNS client not initialized",
                sent_at=datetime.now()
            )

        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"sns-invalid-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error,
                sent_at=datetime.now()
            )

        try:
            # Format phone number
            phone_number = self._format_phone_number(recipient.phone)

            # Prepare message attributes
            message_attributes = {
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': self.default_message_type
                }
            }

            # Add sender ID if specified
            if message.sender_phone:
                message_attributes['AWS.SNS.SMS.SenderID'] = {
                    'DataType': 'String',
                    'StringValue': message.sender_phone[:11]  # Max 11 characters
                }

            # Send SMS
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message.content,
                MessageAttributes=message_attributes
            )

            logger.info(f"SMS sent via AWS SNS to {phone_number}, MessageId: {response['MessageId']}")

            return DeliveryResult(
                message_id=response['MessageId'],
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=self._calculate_sms_cost(message.content),
                metadata={
                    'provider': 'aws_sns',
                    'phone_number': phone_number,
                    'message_type': self.default_message_type,
                    'segments': len(message.content) // 160 + 1
                }
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS SNS ClientError: {error_code} - {error_message}")

            return DeliveryResult(
                message_id=f"sns-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=f"SNS Error: {error_code} - {error_message}",
                sent_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"AWS SNS send failed: {e}")
            return DeliveryResult(
                message_id=f"sns-error-{datetime.now().timestamp()}",
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
        """Send batch SMS via AWS SNS"""
        results = []

        # AWS SNS doesn't have batch SMS sending
        # Send individually with rate limiting
        for recipient in recipients:
            result = await self.send_single(recipient, message)
            results.append(result)

            # Apply rate limiting
            await self._apply_rate_limiting()

        return results

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """Validate recipient phone number"""
        if not recipient.phone:
            return False, "Phone number is required"

        return MessageValidator.validate_phone(recipient.phone)

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent message
        Note: SNS doesn't provide delivery status via API
        Must configure SNS topics with delivery status logging
        """
        return DeliveryResult(
            message_id=message_id,
            recipient_id="unknown",
            status=DeliveryStatus.SENT,
            channel=self.channel_type,
            metadata={'note': 'Use CloudWatch Logs for delivery tracking'}
        )

    def _calculate_sms_cost(self, message_content: str) -> float:
        """Calculate SMS cost based on message length and segments"""
        # SMS segments (160 chars per segment for GSM-7, 70 for UCS-2)
        segments = len(message_content) // 160 + (1 if len(message_content) % 160 else 0)

        # AWS SNS pricing varies by country, using US/Canada rate as default
        cost_per_segment = 0.00645  # USD

        return segments * cost_per_segment

    async def get_sms_spend(self) -> Dict[str, Any]:
        """Get SMS spending statistics"""
        if not self.sns_client:
            return {'error': 'SNS client not initialized'}

        try:
            response = self.sns_client.get_sms_attributes(
                attributes=['MonthlySpendLimit']
            )
            return {
                'monthly_spend_limit': response.get('attributes', {}).get('MonthlySpendLimit', 'Not set'),
                'note': 'Check CloudWatch for actual spending'
            }
        except ClientError as e:
            logger.error(f"Failed to get SMS spend: {e}")
            return {'error': str(e)}

    async def set_monthly_spend_limit(self, limit_usd: float) -> bool:
        """Set monthly SMS spending limit"""
        if not self.sns_client:
            return False

        try:
            self.sns_client.set_sms_attributes(
                attributes={
                    'MonthlySpendLimit': str(limit_usd)
                }
            )
            logger.info(f"Monthly SMS spend limit set to ${limit_usd}")
            return True
        except ClientError as e:
            logger.error(f"Failed to set spend limit: {e}")
            return False
