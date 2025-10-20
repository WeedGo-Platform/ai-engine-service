"""
Analytics Domain Events

Events that represent significant business occurrences in the analytics domain.
These events can trigger side effects like:
- Cache invalidation
- Real-time dashboard updates
- Notifications
- Audit logging
- Webhook triggers
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal


# Base domain event (following payment_processing pattern)
@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_type: str = field(init=False, default="")

    def __post_init__(self):
        """Set event_type from class name."""
        object.__setattr__(self, 'event_type', self.__class__.__name__)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
        }


# Analytics-specific events

@dataclass(frozen=True)
class AnalyticsCalculated(DomainEvent):
    """
    Raised when analytics metrics are calculated.

    Triggers:
    - Cache update
    - Real-time dashboard refresh
    - Data quality checks
    - Audit logging

    This is the primary event for analytics computation completion.
    """

    snapshot_id: UUID
    store_id: UUID
    period_start: datetime
    period_end: datetime
    metrics_calculated: List[str]  # List of metric names calculated
    calculation_duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'snapshot_id': str(self.snapshot_id),
            'store_id': str(self.store_id),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'metrics_calculated': self.metrics_calculated,
            'calculation_duration_ms': self.calculation_duration_ms,
        })
        return base


@dataclass(frozen=True)
class DashboardRefreshed(DomainEvent):
    """
    Raised when dashboard data is refreshed.

    Triggers:
    - WebSocket notification to connected clients
    - Cache invalidation
    - UI state update

    This event indicates that fresh analytics data is available
    and dashboards should be updated.
    """

    store_id: UUID
    snapshot_id: UUID
    refresh_type: str  # 'manual', 'scheduled', 'triggered'
    triggered_by: Optional[UUID] = None  # User who triggered refresh

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'snapshot_id': str(self.snapshot_id),
            'refresh_type': self.refresh_type,
            'triggered_by': str(self.triggered_by) if self.triggered_by else None,
        })
        return base


@dataclass(frozen=True)
class MetricThresholdExceeded(DomainEvent):
    """
    Raised when a metric exceeds configured thresholds.

    Triggers:
    - Alert notifications
    - Automated actions (e.g., reorder inventory)
    - Manager notifications
    - Incident creation

    Business rules:
    - Revenue drop > 20%
    - Inventory below safety stock
    - Order cancellation rate > 10%
    """

    store_id: UUID
    metric_name: str
    current_value: Decimal
    threshold_value: Decimal
    threshold_type: str  # 'upper', 'lower', 'percentage_change'
    severity: str  # 'low', 'medium', 'high', 'critical'
    alert_message: str

    def __post_init__(self):
        """Validate threshold event."""
        super().__post_init__()

        # Validate threshold type
        valid_types = ['upper', 'lower', 'percentage_change']
        if self.threshold_type not in valid_types:
            raise ValueError(f"threshold_type must be one of {valid_types}, got: {self.threshold_type}")

        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}, got: {self.severity}")

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical alert."""
        return self.severity == 'critical'

    @property
    def requires_immediate_action(self) -> bool:
        """Check if immediate action is required."""
        return self.severity in ['high', 'critical']

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'metric_name': self.metric_name,
            'current_value': str(self.current_value),
            'threshold_value': str(self.threshold_value),
            'threshold_type': self.threshold_type,
            'severity': self.severity,
            'alert_message': self.alert_message,
            'is_critical': self.is_critical,
            'requires_immediate_action': self.requires_immediate_action,
        })
        return base


@dataclass(frozen=True)
class RevenueGoalAchieved(DomainEvent):
    """
    Raised when revenue goal is achieved.

    Triggers:
    - Celebration notifications
    - Bonus calculations
    - Goal tracking updates
    - Team notifications
    """

    store_id: UUID
    goal_id: UUID
    goal_name: str
    target_amount: Decimal
    achieved_amount: Decimal
    currency: str = 'CAD'
    achievement_percentage: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'goal_id': str(self.goal_id),
            'goal_name': self.goal_name,
            'target_amount': str(self.target_amount),
            'achieved_amount': str(self.achieved_amount),
            'currency': self.currency,
            'achievement_percentage': str(self.achievement_percentage) if self.achievement_percentage else None,
        })
        return base


@dataclass(frozen=True)
class InventoryAlertTriggered(DomainEvent):
    """
    Raised when inventory levels trigger alerts.

    Triggers:
    - Purchase order suggestions
    - Supplier notifications
    - Manager alerts
    - Automated reordering
    """

    store_id: UUID
    alert_type: str  # 'low_stock', 'out_of_stock', 'overstock', 'expiring_soon'
    product_count: int
    affected_categories: List[str]
    total_value_at_risk: Optional[Decimal] = None
    currency: str = 'CAD'

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'alert_type': self.alert_type,
            'product_count': self.product_count,
            'affected_categories': self.affected_categories,
            'total_value_at_risk': str(self.total_value_at_risk) if self.total_value_at_risk else None,
            'currency': self.currency,
        })
        return base


@dataclass(frozen=True)
class SalesTrendDetected(DomainEvent):
    """
    Raised when significant sales trend is detected.

    Triggers:
    - Trend analysis reports
    - Inventory adjustments
    - Marketing campaign triggers
    - Pricing strategy updates

    Examples:
    - Sudden spike in product category
    - Declining sales in time period
    - Seasonal pattern detected
    """

    store_id: UUID
    trend_type: str  # 'spike', 'decline', 'seasonal', 'anomaly'
    metric_name: str
    current_value: Decimal
    expected_value: Decimal
    deviation_percent: Decimal
    confidence_level: Decimal  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'trend_type': self.trend_type,
            'metric_name': self.metric_name,
            'current_value': str(self.current_value),
            'expected_value': str(self.expected_value),
            'deviation_percent': str(self.deviation_percent),
            'confidence_level': str(self.confidence_level),
        })
        return base


@dataclass(frozen=True)
class AnalyticsCalculationFailed(DomainEvent):
    """
    Raised when analytics calculation fails.

    Triggers:
    - Error logging
    - Admin notifications
    - Fallback data loading
    - Retry scheduling
    """

    store_id: UUID
    error_code: str
    error_message: str
    failed_metrics: List[str]
    retry_count: int = 0
    is_recoverable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'store_id': str(self.store_id),
            'error_code': self.error_code,
            'error_message': self.error_message,
            'failed_metrics': self.failed_metrics,
            'retry_count': self.retry_count,
            'is_recoverable': self.is_recoverable,
        })
        return base


# Export all events
__all__ = [
    'DomainEvent',
    'AnalyticsCalculated',
    'DashboardRefreshed',
    'MetricThresholdExceeded',
    'RevenueGoalAchieved',
    'InventoryAlertTriggered',
    'SalesTrendDetected',
    'AnalyticsCalculationFailed',
]
