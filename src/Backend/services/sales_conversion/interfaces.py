"""
Sales Conversion Pipeline Interfaces
Following SOLID principles with single responsibility for each interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum


class ISalesStateManager(ABC):
    """Interface for managing sales conversation states"""
    
    @abstractmethod
    def get_current_stage(self, session_id: str) -> str:
        """Get the current sales stage for a session"""
        pass
    
    @abstractmethod
    def transition_to(self, session_id: str, new_stage: str, context: Dict[str, Any]) -> bool:
        """Transition to a new sales stage"""
        pass
    
    @abstractmethod
    def get_stage_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the history of stage transitions"""
        pass
    
    @abstractmethod
    def can_transition(self, session_id: str, target_stage: str) -> bool:
        """Check if transition to target stage is allowed"""
        pass
    
    @abstractmethod
    def get_stage_context(self, session_id: str) -> Dict[str, Any]:
        """Get context data for current stage"""
        pass


class IUserProfiler(ABC):
    """Interface for user profile management"""
    
    @abstractmethod
    def get_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile for a session"""
        pass
    
    @abstractmethod
    def update_profile(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update user profile with new data"""
        pass
    
    @abstractmethod
    def collect_data(self, session_id: str, data_type: str, value: Any) -> bool:
        """Progressively collect user data"""
        pass
    
    @abstractmethod
    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        pass
    
    @abstractmethod
    def get_purchase_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get user's purchase history"""
        pass
    
    @abstractmethod
    def create_profile(self, session_id: str, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new user profile"""
        pass


class ISalesStrategy(ABC):
    """Interface for sales approach strategies"""
    
    @abstractmethod
    def select_approach(self, user_profile: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Select the appropriate sales approach"""
        pass
    
    @abstractmethod
    def get_response_style(self) -> Dict[str, Any]:
        """Get the response style configuration"""
        pass
    
    @abstractmethod
    def handle_objection(self, objection_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer objections"""
        pass
    
    @abstractmethod
    def get_persuasion_tactics(self, stage: str) -> List[str]:
        """Get persuasion tactics for a stage"""
        pass
    
    @abstractmethod
    def adjust_pressure(self, resistance_level: float) -> Dict[str, Any]:
        """Adjust sales pressure based on customer resistance"""
        pass


class ICartManager(ABC):
    """Interface for cart and session management"""
    
    @abstractmethod
    def create_cart(self, session_id: str) -> str:
        """Create a new cart for a session"""
        pass
    
    @abstractmethod
    def add_item(self, session_id: str, product_id: str, quantity: int) -> bool:
        """Add an item to the cart"""
        pass
    
    @abstractmethod
    def update_item(self, session_id: str, product_id: str, quantity: int) -> bool:
        """Update item quantity in cart"""
        pass
    
    @abstractmethod
    def remove_item(self, session_id: str, product_id: str) -> bool:
        """Remove an item from cart"""
        pass
    
    @abstractmethod
    def get_cart(self, session_id: str) -> Dict[str, Any]:
        """Get cart contents for a session"""
        pass
    
    @abstractmethod
    def calculate_total(self, session_id: str) -> Dict[str, float]:
        """Calculate cart totals including tax and discounts"""
        pass
    
    @abstractmethod
    def apply_discount(self, session_id: str, discount_code: str) -> bool:
        """Apply a discount code to the cart"""
        pass
    
    @abstractmethod
    def clear_cart(self, session_id: str) -> bool:
        """Clear all items from cart"""
        pass


class IRecommendationEngine(ABC):
    """Interface for product recommendation system"""
    
    @abstractmethod
    def get_personalized_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get personalized product recommendations"""
        pass
    
    @abstractmethod
    def get_similar_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get products similar to a given product"""
        pass
    
    @abstractmethod
    def get_upsell_items(self, cart_items: List[str]) -> List[Dict[str, Any]]:
        """Get upsell recommendations based on cart"""
        pass
    
    @abstractmethod
    def get_cross_sell_items(self, cart_items: List[str]) -> List[Dict[str, Any]]:
        """Get cross-sell recommendations based on cart"""
        pass
    
    @abstractmethod
    def get_trending_products(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trending products"""
        pass
    
    @abstractmethod
    def get_bundle_recommendations(self, product_id: str) -> List[Dict[str, Any]]:
        """Get bundle recommendations for a product"""
        pass


class IConversionTracker(ABC):
    """Interface for conversion tracking and analytics"""
    
    @abstractmethod
    def track_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """Track a conversion event"""
        pass
    
    @abstractmethod
    def track_stage_transition(
        self, 
        session_id: str, 
        from_stage: str, 
        to_stage: str, 
        duration: float
    ) -> bool:
        """Track stage transition metrics"""
        pass
    
    @abstractmethod
    def track_conversion(
        self, 
        session_id: str, 
        conversion_value: float, 
        items: List[Dict[str, Any]]
    ) -> bool:
        """Track successful conversion"""
        pass
    
    @abstractmethod
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a session"""
        pass
    
    @abstractmethod
    def get_conversion_rate(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """Get conversion rate for a period"""
        pass
    
    @abstractmethod
    def get_stage_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics by stage"""
        pass
    
    @abstractmethod
    def track_abandonment(self, session_id: str, stage: str, reason: Optional[str] = None) -> bool:
        """Track cart/session abandonment"""
        pass


class IOrderService(ABC):
    """Interface for order management"""
    
    @abstractmethod
    def create_order(self, cart_session_id: str, user_profile_id: str) -> str:
        """Create an order from cart"""
        pass
    
    @abstractmethod
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        pass
    
    @abstractmethod
    def process_payment(self, order_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment for order"""
        pass
    
    @abstractmethod
    def schedule_delivery(self, order_id: str, delivery_info: Dict[str, Any]) -> bool:
        """Schedule order delivery"""
        pass


class INotificationService(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification"""
        pass
    
    @abstractmethod
    def send_email(self, email: str, subject: str, body: str) -> bool:
        """Send email notification"""
        pass
    
    @abstractmethod
    def send_order_confirmation(self, order_id: str, contact_info: Dict[str, str]) -> bool:
        """Send order confirmation"""
        pass
    
    @abstractmethod
    def send_abandoned_cart_reminder(self, session_id: str, contact_info: Dict[str, str]) -> bool:
        """Send abandoned cart reminder"""
        pass