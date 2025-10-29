"""
AWS SES Email Provider
High-volume, low-cost email sending with excellent deliverability
"""

import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os

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


class AWSSESProvider(ICommunicationChannel):
    """
    AWS Simple Email Service provider
    - 62,000 emails/month free when sending from EC2/Lambda
    - $0.10 per 1,000 emails after
    - Excellent deliverability
    """

    def __init__(
        self,
        config: ChannelConfig,
        aws_region: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        configuration_set: Optional[str] = None
    ):
        super().__init__(config)
        self.channel_type = ChannelType.EMAIL

        # AWS credentials
        self.aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
        self.aws_access_key = aws_access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.configuration_set = configuration_set or os.getenv('AWS_SES_CONFIGURATION_SET')

        # Default sender
        self.default_from_email = os.getenv('AWS_SES_FROM_EMAIL', 'noreply@weedgo.com')
        self.default_from_name = os.getenv('AWS_SES_FROM_NAME', 'WeedGo')

        # Initialize SES client
        self.ses_client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AWS SES client"""
        try:
            session_config = {}
            if self.aws_access_key and self.aws_secret_key:
                session_config['aws_access_key_id'] = self.aws_access_key
                session_config['aws_secret_access_key'] = self.aws_secret_key

            session_config['region_name'] = self.aws_region

            self.ses_client = boto3.client('ses', **session_config)
            logger.info(f"AWS SES client initialized for region: {self.aws_region}")

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to initialize AWS SES client: {e}")
            self.ses_client = None

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """Send single email via AWS SES"""
        if not self.ses_client:
            return DeliveryResult(
                message_id=f"ses-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message="AWS SES client not initialized",
                sent_at=datetime.now()
            )

        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"ses-invalid-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error,
                sent_at=datetime.now()
            )

        try:
            # Build email
            sender = f"{message.sender_name or self.default_from_name} <{message.sender_email or self.default_from_email}>"
            destination = {'ToAddresses': [recipient.email]}

            email_message = {
                'Subject': {'Data': message.subject or 'No Subject', 'Charset': 'UTF-8'},
                'Body': {}
            }

            # Add HTML body
            if message.content:
                email_message['Body']['Html'] = {
                    'Data': message.content,
                    'Charset': 'UTF-8'
                }

            # Add plain text version if available
            if message.template_variables and 'text_content' in message.template_variables:
                email_message['Body']['Text'] = {
                    'Data': message.template_variables['text_content'],
                    'Charset': 'UTF-8'
                }

            # Send email
            send_params = {
                'Source': sender,
                'Destination': destination,
                'Message': email_message
            }

            # Add reply-to if specified
            if message.reply_to:
                send_params['ReplyToAddresses'] = [message.reply_to]

            # Add configuration set for tracking
            if self.configuration_set:
                send_params['ConfigurationSetName'] = self.configuration_set

            # Add tags for categorization
            if message.metadata:
                tags = [
                    {'Name': key, 'Value': str(value)}
                    for key, value in message.metadata.items()
                    if len(key) <= 256 and len(str(value)) <= 256
                ][:50]  # SES allows max 50 tags
                if tags:
                    send_params['Tags'] = tags

            response = self.ses_client.send_email(**send_params)

            logger.info(f"Email sent via AWS SES to {recipient.email}, MessageId: {response['MessageId']}")

            return DeliveryResult(
                message_id=response['MessageId'],
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=self.config.cost_per_message,
                metadata={
                    'provider': 'aws_ses',
                    'request_id': response['ResponseMetadata']['RequestId'],
                    'region': self.aws_region
                }
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS SES ClientError: {error_code} - {error_message}")

            return DeliveryResult(
                message_id=f"ses-error-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=f"SES Error: {error_code} - {error_message}",
                sent_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"AWS SES send failed: {e}")
            return DeliveryResult(
                message_id=f"ses-error-{datetime.now().timestamp()}",
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
        """Send batch emails via AWS SES"""
        results = []

        # AWS SES doesn't have true batch sending for personalized emails
        # We send individually but could optimize with SendBulkTemplatedEmail
        for recipient in recipients:
            result = await self.send_single(recipient, message)
            results.append(result)

            # Apply rate limiting
            await self._apply_rate_limiting()

        return results

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """Validate recipient email address"""
        if not recipient.email:
            return False, "Email address is required"

        return MessageValidator.validate_email(recipient.email)

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent message
        Note: SES doesn't provide real-time status via API
        Must use SNS notifications with configuration sets
        """
        # This would require checking a database where SNS notifications are stored
        return DeliveryResult(
            message_id=message_id,
            recipient_id="unknown",
            status=DeliveryStatus.SENT,
            channel=self.channel_type,
            metadata={'note': 'Use SNS notifications for real-time tracking'}
        )

    async def verify_sender_email(self, email: str) -> bool:
        """Verify an email address for sending (required by SES)"""
        if not self.ses_client:
            return False

        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Verification email sent to {email}")
            return True
        except ClientError as e:
            logger.error(f"Failed to verify email {email}: {e}")
            return False

    async def check_sending_quota(self) -> Dict[str, Any]:
        """Check AWS SES sending quota"""
        if not self.ses_client:
            return {'error': 'SES client not initialized'}

        try:
            response = self.ses_client.get_send_quota()
            return {
                'max_24_hour_send': response['Max24HourSend'],
                'max_send_rate': response['MaxSendRate'],
                'sent_last_24_hours': response['SentLast24Hours'],
                'remaining_quota': response['Max24HourSend'] - response['SentLast24Hours']
            }
        except ClientError as e:
            logger.error(f"Failed to get send quota: {e}")
            return {'error': str(e)}
