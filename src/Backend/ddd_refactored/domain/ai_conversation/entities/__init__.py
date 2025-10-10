"""
AI & Conversation Context Entities - BASIC CHAT ONLY
"""

from .chat_conversation import (
    ChatConversation,
    ChatMessage,
    ConversationStarted,
    MessageReceived,
    AgentAssigned,
    ConversationResolved,
    ConversationClosed,
    SatisfactionProvided
)

__all__ = [
    # Chat Conversation
    'ChatConversation',
    'ChatMessage',

    # Events
    'ConversationStarted',
    'MessageReceived',
    'AgentAssigned',
    'ConversationResolved',
    'ConversationClosed',
    'SatisfactionProvided'
]
