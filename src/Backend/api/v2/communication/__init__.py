"""
Communication V2 API

DDD-powered broadcast and messaging management using the Communication bounded context.

Features:
- Mass communication campaigns (SMS, email, push, WhatsApp)
- Audience segmentation and targeting
- Message templating with variable substitution
- Delivery scheduling and rate limiting
- Real-time delivery tracking and analytics
- Message retry logic with configurable limits
- Domain event tracking for audit trails
"""

from .communication_endpoints import router

__all__ = ["router"]
