"""
AI & Conversation V2 API

DDD-powered customer support chat using the AI Conversation bounded context.
INTENTIONALLY SIMPLE - BASIC CHAT ONLY (NO COMPLEX AI/AGI FEATURES)

Features:
- Customer support conversations
- Agent assignment and messaging
- Conversation status tracking (active, waiting, resolved, closed, abandoned)
- Message history and read receipts
- Quick reply buttons for customer responses
- Customer satisfaction ratings
- Conversation duration and response time metrics
- Domain event tracking for audit trails

This is a simple text-based chat system for customer support, not a complex AI platform.
"""

from .ai_conversation_endpoints import router

__all__ = ["router"]
