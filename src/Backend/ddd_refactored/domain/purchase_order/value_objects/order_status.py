"""
Purchase Order Status Value Objects
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime

from ....shared.domain_base import ValueObject


class PurchaseOrderStatus(str, Enum):
    """Purchase Order Status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SENT_TO_SUPPLIER = "sent_to_supplier"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Approval Status for purchase orders"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"


class ReceivingStatus(str, Enum):
    """Receiving Status for deliveries"""
    NOT_RECEIVED = "not_received"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    RECEIVED_WITH_ISSUES = "received_with_issues"


class PaymentTerms(str, Enum):
    """Payment Terms for suppliers"""
    COD = "cod"  # Cash on delivery
    NET_15 = "net_15"
    NET_30 = "net_30"
    NET_45 = "net_45"
    NET_60 = "net_60"
    NET_90 = "net_90"
    DUE_ON_RECEIPT = "due_on_receipt"
    PREPAID = "prepaid"


@dataclass(frozen=True)
class OrderStatusTransition(ValueObject):
    """
    Value Object for tracking status transitions
    """
    from_status: PurchaseOrderStatus
    to_status: PurchaseOrderStatus
    transitioned_at: datetime
    transitioned_by: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Validate status transition"""
        if not self._is_valid_transition():
            raise ValueError(f"Invalid transition from {self.from_status} to {self.to_status}")

    def _is_valid_transition(self) -> bool:
        """Check if the status transition is valid"""
        valid_transitions = {
            PurchaseOrderStatus.DRAFT: [
                PurchaseOrderStatus.SUBMITTED,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.SUBMITTED: [
                PurchaseOrderStatus.APPROVED,
                PurchaseOrderStatus.DRAFT,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.APPROVED: [
                PurchaseOrderStatus.SENT_TO_SUPPLIER,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.SENT_TO_SUPPLIER: [
                PurchaseOrderStatus.CONFIRMED,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.CONFIRMED: [
                PurchaseOrderStatus.PARTIALLY_RECEIVED,
                PurchaseOrderStatus.FULLY_RECEIVED,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.PARTIALLY_RECEIVED: [
                PurchaseOrderStatus.FULLY_RECEIVED,
                PurchaseOrderStatus.CLOSED,
                PurchaseOrderStatus.CANCELLED
            ],
            PurchaseOrderStatus.FULLY_RECEIVED: [
                PurchaseOrderStatus.CLOSED
            ],
            PurchaseOrderStatus.CLOSED: [],
            PurchaseOrderStatus.CANCELLED: []
        }

        return self.to_status in valid_transitions.get(self.from_status, [])


@dataclass(frozen=True)
class ShippingMethod(ValueObject):
    """
    Value Object for shipping methods
    """
    carrier: str
    service_type: str  # ground, express, overnight, etc.
    tracking_enabled: bool = True
    estimated_days: Optional[int] = None

    def __post_init__(self):
        """Validate shipping method"""
        if not self.carrier:
            raise ValueError("Carrier is required")
        if not self.service_type:
            raise ValueError("Service type is required")

    def format_for_display(self) -> str:
        """Format shipping method for display"""
        if self.estimated_days:
            return f"{self.carrier} - {self.service_type} ({self.estimated_days} days)"
        return f"{self.carrier} - {self.service_type}"


@dataclass(frozen=True)
class DeliverySchedule(ValueObject):
    """
    Value Object for delivery scheduling
    """
    preferred_delivery_date: Optional[datetime] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    delivery_instructions: Optional[str] = None
    requires_appointment: bool = False

    def __post_init__(self):
        """Validate delivery schedule"""
        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_start >= self.delivery_window_end:
                raise ValueError("Delivery window start must be before end")

    def is_flexible(self) -> bool:
        """Check if delivery schedule is flexible"""
        return not self.preferred_delivery_date and not self.requires_appointment

    def has_time_window(self) -> bool:
        """Check if a specific time window is set"""
        return bool(self.delivery_window_start and self.delivery_window_end)