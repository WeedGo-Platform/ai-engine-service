"""
Communication Bounded Context

This context handles:
- Mass broadcast campaigns (SMS, email, push notifications)
- Message templating and personalization
- Audience segmentation and filtering
- Scheduled message delivery
- Delivery tracking and analytics
- Opt-in/opt-out management
"""

from .entities import (
    Broadcast,
    Message,
    BroadcastCreated,
    BroadcastScheduled,
    BroadcastStarted,
    MessageSent,
    MessageDelivered,
    MessageFailed,
    BroadcastCompleted
)

from .value_objects import (
    MessageType,
    MessageStatus,
    MessagePriority,
    BroadcastStatus,
    AudienceSegment,
    MessageCategory,
    MessageContent,
    Recipient,
    DeliverySettings,
    BroadcastFilter,
    MessageTemplate
)

__all__ = [
    # Entities
    'Broadcast',
    'Message',

    # Events
    'BroadcastCreated',
    'BroadcastScheduled',
    'BroadcastStarted',
    'MessageSent',
    'MessageDelivered',
    'MessageFailed',
    'BroadcastCompleted',

    # Value Objects
    'MessageType',
    'MessageStatus',
    'MessagePriority',
    'BroadcastStatus',
    'AudienceSegment',
    'MessageCategory',
    'MessageContent',
    'Recipient',
    'DeliverySettings',
    'BroadcastFilter',
    'MessageTemplate'
]
