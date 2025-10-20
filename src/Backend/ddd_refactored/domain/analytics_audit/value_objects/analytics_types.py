"""
Analytics Value Objects

Immutable value objects representing analytics domain concepts.
Following DDD principles:
- Value objects have no identity
- They are compared by value, not reference
- They are immutable (frozen dataclasses)
- They encapsulate business logic related to their data
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from enum import Enum


@dataclass(frozen=True)
class DateRange:
    """
    Value object representing a time period for analytics.

    Invariants:
    - start_date must be before or equal to end_date
    - Both dates must be valid
    - Supports common periods (daily, weekly, monthly, yearly)

    Examples:
        >>> range1 = DateRange.last_7_days()
        >>> range2 = DateRange.this_month()
        >>> range3 = DateRange(start_date=datetime(2025, 1, 1), end_date=datetime(2025, 1, 31))
    """

    start_date: datetime
    end_date: datetime

    def __post_init__(self):
        """Validate date range invariants."""
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be after or equal to start_date ({self.start_date})"
            )

    @property
    def duration_days(self) -> int:
        """Calculate duration in days."""
        return (self.end_date - self.start_date).days + 1

    @property
    def duration_hours(self) -> int:
        """Calculate duration in hours."""
        return int((self.end_date - self.start_date).total_seconds() / 3600)

    def contains(self, date: datetime) -> bool:
        """Check if a date falls within this range."""
        return self.start_date <= date <= self.end_date

    def overlaps_with(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another."""
        return (
            self.start_date <= other.end_date and
            self.end_date >= other.start_date
        )

    @classmethod
    def today(cls) -> 'DateRange':
        """Create range for today."""
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return cls(start_date=start, end_date=end)

    @classmethod
    def yesterday(cls) -> 'DateRange':
        """Create range for yesterday."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        start = yesterday
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return cls(start_date=start, end_date=end)

    @classmethod
    def last_7_days(cls) -> 'DateRange':
        """Create range for last 7 days."""
        end = datetime.utcnow()
        start = (end - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        return cls(start_date=start, end_date=end)

    @classmethod
    def last_30_days(cls) -> 'DateRange':
        """Create range for last 30 days."""
        end = datetime.utcnow()
        start = (end - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        return cls(start_date=start, end_date=end)

    @classmethod
    def this_month(cls) -> 'DateRange':
        """Create range for current month."""
        now = datetime.utcnow()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get last day of month
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        end = next_month - timedelta(microseconds=1)
        return cls(start_date=start, end_date=end)

    @classmethod
    def last_month(cls) -> 'DateRange':
        """Create range for previous month."""
        now = datetime.utcnow()
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = first_this_month - timedelta(microseconds=1)
        start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return cls(start_date=start, end_date=end)

    @classmethod
    def this_year(cls) -> 'DateRange':
        """Create range for current year."""
        now = datetime.utcnow()
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        return cls(start_date=start, end_date=end)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'duration_days': self.duration_days,
        }

    def __str__(self) -> str:
        return f"{self.start_date.date()} to {self.end_date.date()}"

    def __repr__(self) -> str:
        return f"DateRange(start={self.start_date.date()}, end={self.end_date.date()}, days={self.duration_days})"


class TrendDirection(str, Enum):
    """
    Enum representing the direction of a metric trend.

    Values:
    - UP: Metric increased
    - DOWN: Metric decreased
    - STABLE: Metric unchanged (within threshold)
    - NEW: No historical data to compare
    """

    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    NEW = "new"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MetricValue:
    """
    Value object representing a measured metric value with comparison.

    Encapsulates:
    - Current value
    - Previous period value
    - Change calculation
    - Trend direction

    Invariants:
    - Value must be a valid Decimal
    - Percent change is automatically calculated
    - Trend is determined by threshold (default 1%)
    """

    current_value: Decimal
    previous_value: Optional[Decimal] = None
    threshold_percent: Decimal = Decimal('1.0')  # 1% threshold for "stable"

    def __post_init__(self):
        """Validate and normalize values."""
        # Convert to Decimal if needed
        if not isinstance(self.current_value, Decimal):
            object.__setattr__(self, 'current_value', Decimal(str(self.current_value)))

        if self.previous_value is not None and not isinstance(self.previous_value, Decimal):
            object.__setattr__(self, 'previous_value', Decimal(str(self.previous_value)))

        if not isinstance(self.threshold_percent, Decimal):
            object.__setattr__(self, 'threshold_percent', Decimal(str(self.threshold_percent)))

    @property
    def absolute_change(self) -> Optional[Decimal]:
        """Calculate absolute change from previous period."""
        if self.previous_value is None:
            return None
        return self.current_value - self.previous_value

    @property
    def percent_change(self) -> Optional[Decimal]:
        """Calculate percent change from previous period."""
        if self.previous_value is None or self.previous_value == 0:
            return None

        change = ((self.current_value - self.previous_value) / self.previous_value) * Decimal('100')
        return change.quantize(Decimal('0.01'))

    @property
    def trend_direction(self) -> TrendDirection:
        """Determine trend direction based on percent change and threshold."""
        if self.percent_change is None:
            return TrendDirection.NEW

        if abs(self.percent_change) < self.threshold_percent:
            return TrendDirection.STABLE
        elif self.percent_change > 0:
            return TrendDirection.UP
        else:
            return TrendDirection.DOWN

    def is_improving(self, higher_is_better: bool = True) -> Optional[bool]:
        """
        Determine if trend is improving based on context.

        Args:
            higher_is_better: True for metrics like revenue (up is good),
                            False for metrics like churn (down is good)

        Returns:
            True if improving, False if declining, None if stable or new
        """
        if self.trend_direction in [TrendDirection.STABLE, TrendDirection.NEW]:
            return None

        is_increasing = self.trend_direction == TrendDirection.UP

        return is_increasing if higher_is_better else not is_increasing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'current_value': str(self.current_value),
            'previous_value': str(self.previous_value) if self.previous_value else None,
            'absolute_change': str(self.absolute_change) if self.absolute_change else None,
            'percent_change': str(self.percent_change) if self.percent_change else None,
            'trend_direction': self.trend_direction.value,
        }

    def __str__(self) -> str:
        if self.percent_change:
            return f"{self.current_value} ({self.percent_change:+.1f}%)"
        return str(self.current_value)

    def __repr__(self) -> str:
        return f"MetricValue(current={self.current_value}, trend={self.trend_direction.value})"


@dataclass(frozen=True)
class ChartDataPoint:
    """
    Value object representing a single data point in a time-series chart.

    Used for:
    - Revenue over time charts
    - Sales trend graphs
    - Inventory level tracking

    Invariants:
    - timestamp must be valid
    - value must be numeric
    - label is optional for display
    """

    timestamp: datetime
    value: Decimal
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate and normalize values."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))

        # Convert mutable dict to immutable
        if self.metadata is not None:
            object.__setattr__(self, 'metadata', dict(self.metadata))

    @property
    def display_label(self) -> str:
        """Get display label (custom or formatted timestamp)."""
        if self.label:
            return self.label
        return self.timestamp.strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': str(self.value),
            'label': self.display_label,
            'metadata': self.metadata or {},
        }

    def __str__(self) -> str:
        return f"{self.display_label}: {self.value}"

    def __repr__(self) -> str:
        return f"ChartDataPoint(time={self.timestamp.isoformat()}, value={self.value})"


@dataclass(frozen=True)
class RevenueTrend:
    """
    Value object encapsulating revenue trend analysis.

    Combines:
    - Current revenue metrics
    - Historical comparison
    - Trend visualization data
    - Growth insights

    Invariants:
    - total_revenue must be non-negative
    - Chart data points must be chronologically ordered
    """

    total_revenue: Decimal
    currency: str = 'CAD'
    comparison: Optional[MetricValue] = None
    chart_data: tuple = ()  # tuple of ChartDataPoint for immutability
    period: Optional[DateRange] = None

    def __post_init__(self):
        """Validate revenue trend invariants."""
        if not isinstance(self.total_revenue, Decimal):
            object.__setattr__(self, 'total_revenue', Decimal(str(self.total_revenue)))

        if self.total_revenue < 0:
            raise ValueError(f"Revenue cannot be negative: {self.total_revenue}")

        valid_currencies = ['CAD', 'USD']
        if self.currency not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}, got: {self.currency}")

        # Validate chart data chronological order
        if len(self.chart_data) > 1:
            for i in range(1, len(self.chart_data)):
                if self.chart_data[i].timestamp < self.chart_data[i-1].timestamp:
                    raise ValueError("Chart data points must be in chronological order")

    @property
    def has_growth(self) -> bool:
        """Check if revenue is growing."""
        if self.comparison is None:
            return False
        return self.comparison.trend_direction == TrendDirection.UP

    @property
    def is_declining(self) -> bool:
        """Check if revenue is declining."""
        if self.comparison is None:
            return False
        return self.comparison.trend_direction == TrendDirection.DOWN

    @property
    def average_daily_revenue(self) -> Optional[Decimal]:
        """Calculate average daily revenue if period is known."""
        if self.period is None:
            return None
        return self.total_revenue / Decimal(self.period.duration_days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total': str(self.total_revenue),
            'currency': self.currency,
            'trend': self.comparison.trend_direction.value if self.comparison else TrendDirection.NEW.value,
            'percent_change': str(self.comparison.percent_change) if self.comparison and self.comparison.percent_change else None,
            'chart_data': [point.to_dict() for point in self.chart_data],
            'average_daily': str(self.average_daily_revenue) if self.average_daily_revenue else None,
            'period': self.period.to_dict() if self.period else None,
        }

    def __str__(self) -> str:
        trend_symbol = {
            TrendDirection.UP: "↑",
            TrendDirection.DOWN: "↓",
            TrendDirection.STABLE: "→",
            TrendDirection.NEW: "★",
        }
        direction = self.comparison.trend_direction if self.comparison else TrendDirection.NEW
        return f"{self.currency} ${self.total_revenue:,.2f} {trend_symbol[direction]}"

    def __repr__(self) -> str:
        return f"RevenueTrend(total={self.total_revenue}, currency={self.currency})"
