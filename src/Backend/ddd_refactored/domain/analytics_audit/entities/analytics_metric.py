"""
Analytics Metric Entities

Core entities in the analytics domain that represent various
business metrics and dashboard snapshots.

Following DDD principles:
- Entities have identity and lifecycle
- They enforce business invariants
- They raise domain events when significant changes occur
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal


@dataclass
class AnalyticsMetric:
    """
    Base entity for all analytics metrics.

    Represents a measured value at a specific point in time.
    This is the foundation for all specialized metrics.

    Business Invariants:
    - Metric name must be non-empty
    - Measured value must be present
    - Timestamp must be valid
    - Store context is required
    """

    # Identity
    id: UUID = field(default_factory=uuid4)

    # Core attributes
    metric_name: str = field(default=None)
    measured_value: Decimal = field(default=None)

    # Context
    store_id: UUID = field(default=None)
    measured_at: datetime = field(default_factory=datetime.utcnow)

    # Period information
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Metadata
    dimensions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate invariants after initialization."""
        if self.metric_name is None or not self.metric_name.strip():
            raise ValueError("metric_name is required and must be non-empty")
        if self.measured_value is None:
            raise ValueError("measured_value is required")
        if self.store_id is None:
            raise ValueError("store_id is required")

        # Convert to Decimal if not already
        if not isinstance(self.measured_value, Decimal):
            object.__setattr__(self, 'measured_value', Decimal(str(self.measured_value)))

    def add_dimension(self, key: str, value: Any) -> None:
        """
        Add a dimension to categorize this metric.

        Dimensions allow slicing and dicing metrics by:
        - Product category
        - Time period (daily, weekly, monthly)
        - Customer segment
        - Geographic region

        Args:
            key: Dimension name
            value: Dimension value
        """
        self.dimensions[key] = value
        self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update metric metadata.

        Metadata stores additional context like:
        - Calculation method
        - Data sources
        - Quality indicators

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': str(self.id),
            'metric_name': self.metric_name,
            'measured_value': str(self.measured_value),
            'store_id': str(self.store_id),
            'measured_at': self.measured_at.isoformat(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'dimensions': self.dimensions,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __str__(self) -> str:
        return f"AnalyticsMetric({self.metric_name}={self.measured_value})"

    def __repr__(self) -> str:
        return f"AnalyticsMetric(id={self.id}, name={self.metric_name}, value={self.measured_value})"


@dataclass
class RevenueMetric(AnalyticsMetric):
    """
    Specialized metric for revenue tracking.

    Extends AnalyticsMetric with revenue-specific attributes:
    - Currency support
    - Revenue source tracking
    - Tax and discount breakdown

    Business Invariants:
    - Total revenue must be non-negative
    - Currency must be valid
    - Tax amount cannot exceed total
    """

    currency: str = 'CAD'
    revenue_source: Optional[str] = None  # 'online', 'in-store', 'delivery'

    # Breakdown
    gross_revenue: Decimal = field(default_factory=lambda: Decimal('0.00'))
    tax_amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    discount_amount: Decimal = field(default_factory=lambda: Decimal('0.00'))

    # Comparison
    previous_period_value: Optional[Decimal] = None
    percent_change: Optional[Decimal] = None

    def __post_init__(self):
        """Validate revenue-specific invariants."""
        super().__post_init__()

        valid_currencies = ['CAD', 'USD']
        if self.currency not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}, got: {self.currency}")

        # Convert to Decimal
        for field_name in ['gross_revenue', 'tax_amount', 'discount_amount']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, field_name, Decimal(str(value)))

        # Validate non-negative
        if self.measured_value < 0:
            raise ValueError(f"Revenue cannot be negative: {self.measured_value}")

        if self.gross_revenue < 0:
            raise ValueError(f"Gross revenue cannot be negative: {self.gross_revenue}")

        if self.tax_amount < 0:
            raise ValueError(f"Tax amount cannot be negative: {self.tax_amount}")

        if self.discount_amount < 0:
            raise ValueError(f"Discount amount cannot be negative: {self.discount_amount}")

    def calculate_net_revenue(self) -> Decimal:
        """Calculate net revenue (gross - discounts)."""
        return self.gross_revenue - self.discount_amount

    def calculate_total_with_tax(self) -> Decimal:
        """Calculate total revenue including tax."""
        return self.calculate_net_revenue() + self.tax_amount

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including revenue-specific fields."""
        base = super().to_dict()
        base.update({
            'currency': self.currency,
            'revenue_source': self.revenue_source,
            'gross_revenue': str(self.gross_revenue),
            'tax_amount': str(self.tax_amount),
            'discount_amount': str(self.discount_amount),
            'net_revenue': str(self.calculate_net_revenue()),
            'total_with_tax': str(self.calculate_total_with_tax()),
            'previous_period_value': str(self.previous_period_value) if self.previous_period_value else None,
            'percent_change': str(self.percent_change) if self.percent_change else None,
        })
        return base


@dataclass
class SalesMetric(AnalyticsMetric):
    """
    Specialized metric for sales tracking.

    Tracks order volume and sales velocity:
    - Total orders
    - Average order value
    - Orders by status

    Business Invariants:
    - Order count must be non-negative integer
    - Average order value must be non-negative
    """

    total_orders: int = 0
    completed_orders: int = 0
    pending_orders: int = 0
    cancelled_orders: int = 0

    average_order_value: Decimal = field(default_factory=lambda: Decimal('0.00'))
    currency: str = 'CAD'

    def __post_init__(self):
        """Validate sales-specific invariants."""
        super().__post_init__()

        # Validate counts
        if self.total_orders < 0:
            raise ValueError(f"Total orders cannot be negative: {self.total_orders}")
        if self.completed_orders < 0:
            raise ValueError(f"Completed orders cannot be negative: {self.completed_orders}")
        if self.pending_orders < 0:
            raise ValueError(f"Pending orders cannot be negative: {self.pending_orders}")
        if self.cancelled_orders < 0:
            raise ValueError(f"Cancelled orders cannot be negative: {self.cancelled_orders}")

        # Convert to Decimal
        if not isinstance(self.average_order_value, Decimal):
            object.__setattr__(self, 'average_order_value', Decimal(str(self.average_order_value)))

        if self.average_order_value < 0:
            raise ValueError(f"Average order value cannot be negative: {self.average_order_value}")

    def calculate_completion_rate(self) -> Decimal:
        """Calculate percentage of completed orders."""
        if self.total_orders == 0:
            return Decimal('0.00')
        return (Decimal(self.completed_orders) / Decimal(self.total_orders)) * Decimal('100')

    def calculate_cancellation_rate(self) -> Decimal:
        """Calculate percentage of cancelled orders."""
        if self.total_orders == 0:
            return Decimal('0.00')
        return (Decimal(self.cancelled_orders) / Decimal(self.total_orders)) * Decimal('100')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including sales-specific fields."""
        base = super().to_dict()
        base.update({
            'total_orders': self.total_orders,
            'completed_orders': self.completed_orders,
            'pending_orders': self.pending_orders,
            'cancelled_orders': self.cancelled_orders,
            'average_order_value': str(self.average_order_value),
            'currency': self.currency,
            'completion_rate': str(self.calculate_completion_rate()),
            'cancellation_rate': str(self.calculate_cancellation_rate()),
        })
        return base


@dataclass
class InventoryMetric(AnalyticsMetric):
    """
    Specialized metric for inventory tracking.

    Tracks inventory levels and movement:
    - Stock levels
    - Low stock alerts
    - Inventory turnover

    Business Invariants:
    - Quantities must be non-negative
    - Low stock threshold must be positive
    """

    total_products: int = 0
    in_stock_products: int = 0
    low_stock_products: int = 0
    out_of_stock_products: int = 0

    total_quantity: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_value: Decimal = field(default_factory=lambda: Decimal('0.00'))
    currency: str = 'CAD'

    def __post_init__(self):
        """Validate inventory-specific invariants."""
        super().__post_init__()

        # Validate counts
        if self.total_products < 0:
            raise ValueError(f"Total products cannot be negative: {self.total_products}")
        if self.in_stock_products < 0:
            raise ValueError(f"In-stock products cannot be negative: {self.in_stock_products}")
        if self.low_stock_products < 0:
            raise ValueError(f"Low-stock products cannot be negative: {self.low_stock_products}")
        if self.out_of_stock_products < 0:
            raise ValueError(f"Out-of-stock products cannot be negative: {self.out_of_stock_products}")

        # Convert to Decimal
        if not isinstance(self.total_quantity, Decimal):
            object.__setattr__(self, 'total_quantity', Decimal(str(self.total_quantity)))
        if not isinstance(self.total_value, Decimal):
            object.__setattr__(self, 'total_value', Decimal(str(self.total_value)))

        if self.total_quantity < 0:
            raise ValueError(f"Total quantity cannot be negative: {self.total_quantity}")
        if self.total_value < 0:
            raise ValueError(f"Total value cannot be negative: {self.total_value}")

    def calculate_stock_coverage_rate(self) -> Decimal:
        """Calculate percentage of products in stock."""
        if self.total_products == 0:
            return Decimal('0.00')
        return (Decimal(self.in_stock_products) / Decimal(self.total_products)) * Decimal('100')

    def calculate_average_product_value(self) -> Decimal:
        """Calculate average value per product."""
        if self.total_products == 0:
            return Decimal('0.00')
        return self.total_value / Decimal(self.total_products)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including inventory-specific fields."""
        base = super().to_dict()
        base.update({
            'total_products': self.total_products,
            'in_stock_products': self.in_stock_products,
            'low_stock_products': self.low_stock_products,
            'out_of_stock_products': self.out_of_stock_products,
            'total_quantity': str(self.total_quantity),
            'total_value': str(self.total_value),
            'currency': self.currency,
            'stock_coverage_rate': str(self.calculate_stock_coverage_rate()),
            'average_product_value': str(self.calculate_average_product_value()),
        })
        return base


@dataclass
class CustomerMetric(AnalyticsMetric):
    """
    Specialized metric for customer behavior tracking.

    Tracks customer acquisition and engagement:
    - New vs returning customers
    - Customer lifetime value
    - Churn metrics

    Business Invariants:
    - Customer counts must be non-negative
    - Rates must be between 0 and 100
    """

    total_customers: int = 0
    new_customers: int = 0
    returning_customers: int = 0
    active_customers: int = 0

    average_customer_value: Decimal = field(default_factory=lambda: Decimal('0.00'))
    retention_rate: Optional[Decimal] = None
    currency: str = 'CAD'

    def __post_init__(self):
        """Validate customer-specific invariants."""
        super().__post_init__()

        # Validate counts
        if self.total_customers < 0:
            raise ValueError(f"Total customers cannot be negative: {self.total_customers}")
        if self.new_customers < 0:
            raise ValueError(f"New customers cannot be negative: {self.new_customers}")
        if self.returning_customers < 0:
            raise ValueError(f"Returning customers cannot be negative: {self.returning_customers}")
        if self.active_customers < 0:
            raise ValueError(f"Active customers cannot be negative: {self.active_customers}")

        # Convert to Decimal
        if not isinstance(self.average_customer_value, Decimal):
            object.__setattr__(self, 'average_customer_value', Decimal(str(self.average_customer_value)))

        if self.average_customer_value < 0:
            raise ValueError(f"Average customer value cannot be negative: {self.average_customer_value}")

        # Validate retention rate if present
        if self.retention_rate is not None:
            if not isinstance(self.retention_rate, Decimal):
                object.__setattr__(self, 'retention_rate', Decimal(str(self.retention_rate)))
            if self.retention_rate < 0 or self.retention_rate > 100:
                raise ValueError(f"Retention rate must be between 0 and 100: {self.retention_rate}")

    def calculate_new_customer_rate(self) -> Decimal:
        """Calculate percentage of new customers."""
        if self.total_customers == 0:
            return Decimal('0.00')
        return (Decimal(self.new_customers) / Decimal(self.total_customers)) * Decimal('100')

    def calculate_active_rate(self) -> Decimal:
        """Calculate percentage of active customers."""
        if self.total_customers == 0:
            return Decimal('0.00')
        return (Decimal(self.active_customers) / Decimal(self.total_customers)) * Decimal('100')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including customer-specific fields."""
        base = super().to_dict()
        base.update({
            'total_customers': self.total_customers,
            'new_customers': self.new_customers,
            'returning_customers': self.returning_customers,
            'active_customers': self.active_customers,
            'average_customer_value': str(self.average_customer_value),
            'retention_rate': str(self.retention_rate) if self.retention_rate else None,
            'currency': self.currency,
            'new_customer_rate': str(self.calculate_new_customer_rate()),
            'active_rate': str(self.calculate_active_rate()),
        })
        return base


@dataclass
class DashboardSnapshot:
    """
    Aggregate Root for dashboard analytics.

    Represents a complete snapshot of all dashboard metrics at a point in time.
    This aggregate combines multiple specialized metrics into a cohesive view.

    Business Invariants:
    - Store context is required
    - Snapshot timestamp must be valid
    - At least one metric must be present

    Responsibilities:
    - Coordinate multiple metrics
    - Enforce consistency across metrics
    - Provide unified dashboard view
    """

    # Identity
    id: UUID = field(default_factory=uuid4)

    # Context
    store_id: UUID = field(default=None)
    snapshot_at: datetime = field(default_factory=datetime.utcnow)

    # Period
    period_start: datetime = field(default=None)
    period_end: datetime = field(default=None)

    # Metrics (optional - will be populated by repository)
    revenue_metric: Optional[RevenueMetric] = None
    sales_metric: Optional[SalesMetric] = None
    inventory_metric: Optional[InventoryMetric] = None
    customer_metric: Optional[CustomerMetric] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events (not persisted)
    _domain_events: List = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants after initialization."""
        if self.store_id is None:
            raise ValueError("store_id is required")
        if self.period_start is None:
            raise ValueError("period_start is required")
        if self.period_end is None:
            raise ValueError("period_end is required")

        if self.period_end <= self.period_start:
            raise ValueError(f"period_end must be after period_start")

    def has_metrics(self) -> bool:
        """Check if snapshot has any metrics."""
        return any([
            self.revenue_metric is not None,
            self.sales_metric is not None,
            self.inventory_metric is not None,
            self.customer_metric is not None,
        ])

    def add_revenue_metric(self, metric: RevenueMetric) -> None:
        """Add revenue metric to snapshot."""
        self.revenue_metric = metric
        self.updated_at = datetime.utcnow()

    def add_sales_metric(self, metric: SalesMetric) -> None:
        """Add sales metric to snapshot."""
        self.sales_metric = metric
        self.updated_at = datetime.utcnow()

    def add_inventory_metric(self, metric: InventoryMetric) -> None:
        """Add inventory metric to snapshot."""
        self.inventory_metric = metric
        self.updated_at = datetime.utcnow()

    def add_customer_metric(self, metric: CustomerMetric) -> None:
        """Add customer metric to snapshot."""
        self.customer_metric = metric
        self.updated_at = datetime.utcnow()

    def _raise_event(self, event) -> None:
        """Add domain event to internal event list."""
        self._domain_events.append(event)

    @property
    def domain_events(self) -> List:
        """Get domain events for this aggregate."""
        return self._domain_events.copy()

    def clear_events(self) -> None:
        """Clear domain events after they've been published."""
        self._domain_events.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': str(self.id),
            'store_id': str(self.store_id),
            'snapshot_at': self.snapshot_at.isoformat(),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'revenue': self.revenue_metric.to_dict() if self.revenue_metric else None,
            'sales': self.sales_metric.to_dict() if self.sales_metric else None,
            'inventory': self.inventory_metric.to_dict() if self.inventory_metric else None,
            'customers': self.customer_metric.to_dict() if self.customer_metric else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __str__(self) -> str:
        return f"DashboardSnapshot(store={self.store_id}, period={self.period_start} to {self.period_end})"

    def __repr__(self) -> str:
        return f"DashboardSnapshot(id={self.id}, store={self.store_id}, has_metrics={self.has_metrics()})"
