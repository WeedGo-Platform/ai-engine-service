"""
Sales Conversion Pipeline Data Models
Domain models and enums for the sales conversion system
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class SalesStage(Enum):
    """Sales pipeline stages"""
    GREETING = "greeting"
    AGE_VERIFICATION = "age_verification"
    DISCOVERY = "discovery"
    NEEDS_ASSESSMENT = "needs_assessment"
    EDUCATION = "education"
    RECOMMENDATION = "recommendation"
    CONSIDERATION = "consideration"
    OBJECTION_HANDLING = "objection_handling"
    CART_BUILDING = "cart_building"
    UPSELLING = "upselling"
    CHECKOUT = "checkout"
    PAYMENT = "payment"
    ORDER_CONFIRMATION = "order_confirmation"
    FOLLOW_UP = "follow_up"
    ABANDONED = "abandoned"


class UserIntent(Enum):
    """User intent classifications"""
    GREETING = "greeting"
    BROWSING = "browsing"
    SPECIFIC_REQUEST = "specific_request"
    PRICE_INQUIRY = "price_inquiry"
    PRODUCT_QUESTION = "product_question"
    MEDICAL_INQUIRY = "medical_inquiry"
    RECREATIONAL_INQUIRY = "recreational_inquiry"
    COMPARISON = "comparison"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT = "checkout"
    OBJECTION = "objection"
    SUPPORT = "support"
    FEEDBACK = "feedback"
    EXIT = "exit"


class ObjectionType(Enum):
    """Types of customer objections"""
    PRICE = "price"
    QUALITY = "quality"
    EFFECTS = "effects"
    SAFETY = "safety"
    LEGAL = "legal"
    DELIVERY = "delivery"
    PAYMENT = "payment"
    TRUST = "trust"
    ALTERNATIVES = "alternatives"
    NOT_READY = "not_ready"


class CustomerProfile(Enum):
    """Customer profile types"""
    NEW_USER = "new_user"
    EXPERIENCED_USER = "experienced_user"
    MEDICAL_PATIENT = "medical_patient"
    RECREATIONAL_USER = "recreational_user"
    BULK_BUYER = "bulk_buyer"
    PRICE_CONSCIOUS = "price_conscious"
    QUALITY_FOCUSED = "quality_focused"
    EXPLORER = "explorer"


@dataclass
class UserProfile:
    """User profile data model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    age_verified: bool = False
    customer_type: Optional[CustomerProfile] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    needs: List[str] = field(default_factory=list)
    experience_level: Optional[str] = None
    medical_conditions: List[str] = field(default_factory=list)
    preferred_categories: List[str] = field(default_factory=list)
    preferred_effects: List[str] = field(default_factory=list)
    price_range: Optional[Dict[str, float]] = None
    purchase_history: List[Dict[str, Any]] = field(default_factory=list)
    interaction_count: int = 0
    language: str = "en"
    timezone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "email": self.email,
            "phone": self.phone,
            "age_verified": self.age_verified,
            "customer_type": self.customer_type.value if self.customer_type else None,
            "preferences": self.preferences,
            "needs": self.needs,
            "experience_level": self.experience_level,
            "medical_conditions": self.medical_conditions,
            "preferred_categories": self.preferred_categories,
            "preferred_effects": self.preferred_effects,
            "price_range": self.price_range,
            "purchase_history": self.purchase_history,
            "interaction_count": self.interaction_count,
            "language": self.language,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ConversationState:
    """Conversation state data model"""
    session_id: str
    current_stage: SalesStage
    previous_stage: Optional[SalesStage] = None
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    intent_history: List[UserIntent] = field(default_factory=list)
    resistance_level: float = 0.0  # 0-1 scale
    engagement_score: float = 0.5  # 0-1 scale
    stage_start_time: datetime = field(default_factory=datetime.now)
    total_duration: float = 0.0
    message_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_stage_transition(self, new_stage: SalesStage, reason: str = ""):
        """Record stage transition"""
        duration = (datetime.now() - self.stage_start_time).total_seconds()
        self.stage_history.append({
            "from": self.current_stage.value,
            "to": new_stage.value,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "reason": reason
        })
        self.previous_stage = self.current_stage
        self.current_stage = new_stage
        self.stage_start_time = datetime.now()
        self.total_duration += duration


@dataclass
class CartItem:
    """Cart item data model"""
    product_id: str
    product_name: str
    category: str
    quantity: int
    unit_price: float
    total_price: float
    thc_content: Optional[float] = None
    cbd_content: Optional[float] = None
    strain_type: Optional[str] = None
    discount_applied: float = 0.0
    added_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "thc_content": self.thc_content,
            "cbd_content": self.cbd_content,
            "strain_type": self.strain_type,
            "discount_applied": self.discount_applied,
            "added_at": self.added_at.isoformat()
        }


@dataclass
class CartSession:
    """Shopping cart session data model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    user_profile_id: Optional[str] = None
    items: List[CartItem] = field(default_factory=list)
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    delivery_fee: float = 0.0
    total_amount: float = 0.0
    discount_codes: List[str] = field(default_factory=list)
    status: str = "active"  # active, abandoned, converted
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_item(self, item: CartItem):
        """Add item to cart"""
        existing = next((i for i in self.items if i.product_id == item.product_id), None)
        if existing:
            existing.quantity += item.quantity
            existing.total_price = existing.unit_price * existing.quantity
        else:
            self.items.append(item)
        self.recalculate_totals()
    
    def recalculate_totals(self):
        """Recalculate cart totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = self.subtotal * 0.15  # Configurable tax rate
        self.total_amount = self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        self.updated_at = datetime.now()


@dataclass
class ConversionEvent:
    """Conversion tracking event"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    event_type: str = ""  # view, add_to_cart, checkout_start, purchase, abandonment
    stage: Optional[SalesStage] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "stage": self.stage.value if self.stage else None,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SalesMetrics:
    """Sales conversion metrics"""
    session_id: str
    total_messages: int = 0
    total_duration: float = 0.0
    stages_completed: List[str] = field(default_factory=list)
    conversion_events: List[ConversionEvent] = field(default_factory=list)
    cart_value: float = 0.0
    converted: bool = False
    conversion_value: float = 0.0
    abandonment_stage: Optional[SalesStage] = None
    abandonment_reason: Optional[str] = None
    engagement_score: float = 0.0
    objections_raised: List[str] = field(default_factory=list)
    objections_resolved: List[str] = field(default_factory=list)
    recommendations_shown: int = 0
    recommendations_clicked: int = 0
    upsell_accepted: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    """Order data model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cart_session_id: str = ""
    user_profile_id: str = ""
    order_number: str = ""
    items: List[CartItem] = field(default_factory=list)
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    delivery_fee: float = 0.0
    total_amount: float = 0.0
    payment_status: str = "pending"  # pending, processing, completed, failed
    payment_method: Optional[str] = None
    delivery_status: str = "pending"  # pending, scheduled, in_transit, delivered
    delivery_address: Optional[Dict[str, str]] = None
    delivery_time: Optional[datetime] = None
    special_instructions: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)