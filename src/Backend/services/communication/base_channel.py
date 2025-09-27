"""
Base Communication Channel Interface
Following SOLID principles - Interface Segregation & Dependency Inversion
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Supported communication channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class Recipient:
    """Recipient information"""
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    """Message content"""
    subject: Optional[str] = None
    content: str = ""
    template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: MessagePriority = MessagePriority.NORMAL

    # Channel-specific fields
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    sender_phone: Optional[str] = None
    reply_to: Optional[str] = None

    # Push notification specific
    push_title: Optional[str] = None
    push_image_url: Optional[str] = None
    push_action_url: Optional[str] = None
    push_badge_count: Optional[int] = None
    push_sound: Optional[str] = None


@dataclass
class DeliveryResult:
    """Result of message delivery"""
    message_id: str
    recipient_id: str
    status: DeliveryStatus
    channel: ChannelType
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cost: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChannelConfig:
    """Channel configuration"""
    enabled: bool = True
    rate_limit: int = 100  # messages per second
    retry_attempts: int = 3
    retry_delay: int = 60  # seconds
    batch_size: int = 100
    timeout: int = 30  # seconds

    # Provider-specific settings
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    sandbox_mode: bool = False

    # Cost settings
    cost_per_message: float = 0.0
    cost_currency: str = "CAD"


class ICommunicationChannel(ABC):
    """
    Abstract base class for communication channels
    Following Single Responsibility Principle
    """

    def __init__(self, config: ChannelConfig):
        self.config = config
        self.channel_type: ChannelType = None
        self._rate_limiter = None
        self._retry_queue = []

    @abstractmethod
    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """
        Send a single message to a recipient

        Args:
            recipient: Recipient information
            message: Message content

        Returns:
            DeliveryResult with status and metadata
        """
        pass

    @abstractmethod
    async def send_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """
        Send the same message to multiple recipients

        Args:
            recipients: List of recipients
            message: Message content

        Returns:
            List of DeliveryResult for each recipient
        """
        pass

    @abstractmethod
    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """
        Validate recipient contact information

        Args:
            recipient: Recipient to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a sent message

        Args:
            message_id: Message ID to check

        Returns:
            DeliveryResult with current status
        """
        pass

    async def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get current rate limit status

        Returns:
            Dictionary with rate limit information
        """
        return {
            "limit": self.config.rate_limit,
            "remaining": self._get_remaining_quota(),
            "reset_at": self._get_rate_limit_reset_time()
        }

    async def check_preferences(
        self,
        recipient: Recipient,
        message_type: str = "promotional"
    ) -> bool:
        """
        Check if recipient has opted in for this channel and message type

        Args:
            recipient: Recipient to check
            message_type: Type of message (promotional, transactional, alert)

        Returns:
            True if recipient can receive messages
        """
        if not recipient.preferences:
            return True  # Default to opt-in if no preferences

        channel_key = f"channel_{self.channel_type.value}"
        if not recipient.preferences.get(channel_key, True):
            return False

        if not recipient.preferences.get(message_type, True):
            return False

        return True

    async def calculate_cost(
        self,
        recipients_count: int,
        message: Message
    ) -> Dict[str, Any]:
        """
        Calculate estimated cost for sending messages

        Args:
            recipients_count: Number of recipients
            message: Message content

        Returns:
            Cost estimation dictionary
        """
        base_cost = self.config.cost_per_message * recipients_count

        # Additional costs for SMS based on message length
        if self.channel_type == ChannelType.SMS and message.content:
            segments = len(message.content) // 160 + (1 if len(message.content) % 160 else 0)
            base_cost *= segments

        return {
            "estimated_cost": base_cost,
            "currency": self.config.cost_currency,
            "recipients": recipients_count,
            "cost_per_message": self.config.cost_per_message
        }

    async def handle_unsubscribe(self, recipient_id: str, reason: Optional[str] = None):
        """
        Handle unsubscribe request

        Args:
            recipient_id: Recipient ID
            reason: Optional unsubscribe reason
        """
        # This will be implemented by the unsubscribe service
        logger.info(f"Unsubscribe request for {recipient_id} on {self.channel_type.value}")

    def _get_remaining_quota(self) -> int:
        """Get remaining messages in rate limit quota"""
        # Implementation would track actual usage
        return self.config.rate_limit

    def _get_rate_limit_reset_time(self) -> datetime:
        """Get when rate limit resets"""
        # Implementation would return actual reset time
        from datetime import timedelta
        return datetime.now() + timedelta(seconds=60)

    async def _apply_rate_limiting(self):
        """Apply rate limiting before sending"""
        # Implementation would use actual rate limiting logic
        await asyncio.sleep(1.0 / self.config.rate_limit)

    async def _retry_failed_message(
        self,
        recipient: Recipient,
        message: Message,
        attempt: int = 1
    ) -> Optional[DeliveryResult]:
        """
        Retry failed message with exponential backoff

        Args:
            recipient: Recipient information
            message: Message to retry
            attempt: Current attempt number

        Returns:
            DeliveryResult if successful, None if all retries failed
        """
        if attempt > self.config.retry_attempts:
            return None

        delay = self.config.retry_delay * (2 ** (attempt - 1))
        await asyncio.sleep(delay)

        try:
            return await self.send_single(recipient, message)
        except Exception as e:
            logger.error(f"Retry {attempt} failed: {e}")
            return await self._retry_failed_message(recipient, message, attempt + 1)


class BatchProcessor:
    """
    Utility class for processing messages in batches
    Following Single Responsibility Principle
    """

    @staticmethod
    async def process_in_batches(
        items: List[Any],
        batch_size: int,
        process_func,
        delay_between_batches: float = 0.1
    ) -> List[Any]:
        """
        Process items in batches with delay between batches

        Args:
            items: Items to process
            batch_size: Size of each batch
            process_func: Async function to process each batch
            delay_between_batches: Delay in seconds between batches

        Returns:
            Combined results from all batches
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await process_func(batch)
            results.extend(batch_results)

            if i + batch_size < len(items):
                await asyncio.sleep(delay_between_batches)

        return results


class MessageValidator:
    """
    Utility class for validating messages
    Following Single Responsibility Principle
    """

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, None
        return False, "Invalid email format"

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number"""
        import re
        # Remove all non-numeric characters
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) == 10 or len(cleaned) == 11:
            return True, None
        return False, "Invalid phone number format"

    @staticmethod
    def validate_push_token(token: str) -> Tuple[bool, Optional[str]]:
        """Validate push notification token"""
        if token and len(token) > 10:
            return True, None
        return False, "Invalid push token"