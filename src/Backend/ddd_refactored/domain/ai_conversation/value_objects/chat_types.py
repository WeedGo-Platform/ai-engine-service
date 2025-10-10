"""
AI & Conversation Value Objects - BASIC CHAT ONLY (NO AGI)
Following DDD Architecture Document Section 2.13
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from ....shared.domain_base import ValueObject


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "active"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ABANDONED = "abandoned"


class MessageRole(str, Enum):
    """Who sent the message"""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Type of message content"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    QUICK_REPLY = "quick_reply"


class SatisfactionRating(str, Enum):
    """Customer satisfaction rating"""
    VERY_SATISFIED = "very_satisfied"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    DISSATISFIED = "dissatisfied"
    VERY_DISSATISFIED = "very_dissatisfied"


@dataclass(frozen=True)
class MessageContent(ValueObject):
    """
    Basic message content - text only for simplicity
    """
    text: str
    message_type: MessageType = MessageType.TEXT

    # Optional media
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image/png, image/jpeg, etc.

    def __post_init__(self):
        """Validate message content"""
        if not self.text or not self.text.strip():
            raise ValueError("Message text cannot be empty")

        if len(self.text) > 5000:
            raise ValueError("Message text too long (max 5000 characters)")

        # If media URL provided, validate media type
        if self.media_url and not self.media_type:
            raise ValueError("Media type required when media URL is provided")

    def has_media(self) -> bool:
        """Check if message has media attachment"""
        return self.media_url is not None


@dataclass(frozen=True)
class ParticipantInfo(ValueObject):
    """
    Information about conversation participant
    """
    participant_id: str
    participant_role: MessageRole
    display_name: str

    # Contact info (for agent)
    email: Optional[str] = None
    department: Optional[str] = None

    def __post_init__(self):
        """Validate participant info"""
        if not self.participant_id:
            raise ValueError("Participant ID is required")

        if not self.display_name:
            raise ValueError("Display name is required")

    def is_customer(self) -> bool:
        """Check if participant is a customer"""
        return self.participant_role == MessageRole.CUSTOMER

    def is_agent(self) -> bool:
        """Check if participant is an agent"""
        return self.participant_role == MessageRole.AGENT


@dataclass(frozen=True)
class ConversationSummary(ValueObject):
    """
    Summary of conversation for reporting
    """
    total_messages: int
    customer_messages: int
    agent_messages: int
    duration_minutes: int

    # Satisfaction
    satisfaction_rating: Optional[SatisfactionRating] = None
    satisfaction_comment: Optional[str] = None

    # Resolution
    was_resolved: bool = False
    resolution_time_minutes: Optional[int] = None

    def __post_init__(self):
        """Validate conversation summary"""
        if self.total_messages < 0:
            raise ValueError("Total messages cannot be negative")

        if self.customer_messages < 0:
            raise ValueError("Customer messages cannot be negative")

        if self.agent_messages < 0:
            raise ValueError("Agent messages cannot be negative")

        if self.duration_minutes < 0:
            raise ValueError("Duration cannot be negative")

        # Validate message counts add up
        if self.customer_messages + self.agent_messages > self.total_messages:
            raise ValueError("Participant message counts exceed total")

    def get_average_response_time(self) -> Optional[float]:
        """Get average response time (rough estimate)"""
        if self.agent_messages == 0:
            return None

        return self.duration_minutes / self.agent_messages


@dataclass(frozen=True)
class QuickReply(ValueObject):
    """
    Predefined quick reply option for customer
    """
    reply_id: str
    reply_text: str
    reply_value: str  # Value sent when clicked

    def __post_init__(self):
        """Validate quick reply"""
        if not self.reply_id:
            raise ValueError("Reply ID is required")

        if not self.reply_text:
            raise ValueError("Reply text is required")

        if not self.reply_value:
            raise ValueError("Reply value is required")

        if len(self.reply_text) > 100:
            raise ValueError("Reply text too long (max 100 characters)")
