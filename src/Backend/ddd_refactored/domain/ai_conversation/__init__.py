"""
AI & Conversation Bounded Context - BASIC CHAT ONLY (NO AGI)

This context handles:
- Basic customer support chat conversations
- Agent assignment and messaging
- Conversation status tracking
- Customer satisfaction ratings
- Simple message exchange

INTENTIONALLY SIMPLE - No complex AI features, no AGI tables
"""

from .entities import (
    ChatConversation,
    ChatMessage,
    ConversationStarted,
    MessageReceived,
    AgentAssigned,
    ConversationResolved,
    ConversationClosed,
    SatisfactionProvided
)

from .value_objects import (
    ConversationStatus,
    MessageRole,
    MessageType,
    SatisfactionRating,
    MessageContent,
    ParticipantInfo,
    ConversationSummary,
    QuickReply
)

__all__ = [
    # Entities
    'ChatConversation',
    'ChatMessage',

    # Events
    'ConversationStarted',
    'MessageReceived',
    'AgentAssigned',
    'ConversationResolved',
    'ConversationClosed',
    'SatisfactionProvided',

    # Value Objects
    'ConversationStatus',
    'MessageRole',
    'MessageType',
    'SatisfactionRating',
    'MessageContent',
    'ParticipantInfo',
    'ConversationSummary',
    'QuickReply'
]
