"""
Sales Conversion Pipeline Module
AI-driven sales conversion system for converting browsers into customers
"""

from .interfaces import (
    ISalesStateManager,
    IUserProfiler,
    ISalesStrategy,
    ICartManager,
    IRecommendationEngine,
    IConversionTracker
)

from .models import (
    SalesStage,
    UserProfile,
    CartSession,
    ConversionEvent
)

__all__ = [
    'ISalesStateManager',
    'IUserProfiler',
    'ISalesStrategy',
    'ICartManager',
    'IRecommendationEngine',
    'IConversionTracker',
    'SalesStage',
    'UserProfile',
    'CartSession',
    'ConversionEvent'
]