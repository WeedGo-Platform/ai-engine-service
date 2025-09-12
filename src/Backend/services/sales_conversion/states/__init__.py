"""
Sales Conversion States Module
Implementation of State pattern for conversation flow management
"""

from .base import ConversationStateBase, StateContext
from .greeting import GreetingState
from .age_verification import AgeVerificationState
from .discovery import DiscoveryState
from .needs_assessment import NeedsAssessmentState
from .education import EducationState
from .recommendation import RecommendationState
from .consideration import ConsiderationState
from .objection_handling import ObjectionHandlingState
from .cart_building import CartBuildingState
from .upselling import UpsellingState
from .checkout import CheckoutState
from .payment import PaymentState
from .order_confirmation import OrderConfirmationState
from .follow_up import FollowUpState
from .abandoned import AbandonedState

__all__ = [
    'ConversationStateBase',
    'StateContext',
    'GreetingState',
    'AgeVerificationState',
    'DiscoveryState',
    'NeedsAssessmentState',
    'EducationState',
    'RecommendationState',
    'ConsiderationState',
    'ObjectionHandlingState',
    'CartBuildingState',
    'UpsellingState',
    'CheckoutState',
    'PaymentState',
    'OrderConfirmationState',
    'FollowUpState',
    'AbandonedState'
]