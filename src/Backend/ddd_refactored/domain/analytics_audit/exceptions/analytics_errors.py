"""
Analytics Domain Exceptions

Business rule violations and analytics-specific errors.
Following the pattern from payment_processing domain.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime


class AnalyticsError(Exception):
    """Base exception for all analytics-related errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        """
        Initialize analytics error.

        Args:
            message: Human-readable error message
            error_code: Optional machine-readable error code
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class AnalyticsCalculationError(AnalyticsError):
    """
    Raised when analytics calculation fails.

    Example: Database query timeout, insufficient data, calculation overflow.
    """

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        store_id: Optional[UUID] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize calculation error.

        Args:
            message: Error description
            metric_name: Name of metric that failed calculation
            store_id: Store context where calculation failed
            original_error: Original exception that caused the failure
        """
        self.metric_name = metric_name
        self.store_id = store_id
        self.original_error = original_error
        super().__init__(message, "ANALYTICS_CALCULATION_ERROR")


class InvalidDateRangeError(AnalyticsError):
    """
    Raised when date range is invalid for analytics.

    Business rules:
    - start_date must be before end_date
    - Date range cannot be in the future
    - Date range cannot exceed maximum allowed period
    """

    def __init__(
        self,
        message: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Initialize date range error.

        Args:
            message: Error description
            start_date: Invalid start date
            end_date: Invalid end date
        """
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(message, "INVALID_DATE_RANGE")


class MetricNotFoundError(AnalyticsError):
    """Raised when requested metric cannot be found."""

    def __init__(
        self,
        metric_name: str,
        store_id: Optional[UUID] = None,
        period: Optional[str] = None
    ):
        """
        Initialize metric not found error.

        Args:
            metric_name: Name of the metric that wasn't found
            store_id: Store context
            period: Time period that was queried
        """
        if store_id and period:
            message = f"Metric '{metric_name}' not found for store {store_id} in period {period}"
        elif store_id:
            message = f"Metric '{metric_name}' not found for store {store_id}"
        else:
            message = f"Metric '{metric_name}' not found"

        self.metric_name = metric_name
        self.store_id = store_id
        self.period = period
        super().__init__(message, "METRIC_NOT_FOUND")


class SnapshotNotFoundError(AnalyticsError):
    """Raised when analytics snapshot cannot be found."""

    def __init__(
        self,
        snapshot_id: Optional[UUID] = None,
        store_id: Optional[UUID] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize snapshot not found error.

        Args:
            snapshot_id: Snapshot UUID
            store_id: Store context
            timestamp: Snapshot timestamp
        """
        if snapshot_id:
            message = f"Analytics snapshot not found: {snapshot_id}"
        elif store_id and timestamp:
            message = f"Analytics snapshot not found for store {store_id} at {timestamp}"
        else:
            message = "Analytics snapshot not found"

        self.snapshot_id = snapshot_id
        self.store_id = store_id
        self.timestamp = timestamp
        super().__init__(message, "SNAPSHOT_NOT_FOUND")


class InsufficientDataError(AnalyticsError):
    """
    Raised when insufficient data exists for analytics calculation.

    Example:
    - No sales data for the requested period
    - Not enough historical data for trend analysis
    - Missing required data points
    """

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        required_data_points: Optional[int] = None,
        actual_data_points: Optional[int] = None
    ):
        """
        Initialize insufficient data error.

        Args:
            message: Error description
            metric_name: Metric that lacks data
            required_data_points: Minimum required data points
            actual_data_points: Actual data points available
        """
        self.metric_name = metric_name
        self.required_data_points = required_data_points
        self.actual_data_points = actual_data_points
        super().__init__(message, "INSUFFICIENT_DATA")


class DataQualityError(AnalyticsError):
    """
    Raised when data quality issues prevent accurate analytics.

    Example:
    - Duplicate records
    - Missing critical fields
    - Data inconsistencies
    - Outliers beyond acceptable range
    """

    def __init__(
        self,
        message: str,
        quality_issue: str,
        affected_records: Optional[int] = None
    ):
        """
        Initialize data quality error.

        Args:
            message: Error description
            quality_issue: Type of quality issue (e.g., 'duplicates', 'missing_values', 'outliers')
            affected_records: Number of records affected
        """
        self.quality_issue = quality_issue
        self.affected_records = affected_records
        super().__init__(message, "DATA_QUALITY_ERROR")


class StoreNotFoundError(AnalyticsError):
    """Raised when store context cannot be found."""

    def __init__(self, store_id: UUID):
        """
        Initialize store not found error.

        Args:
            store_id: Store UUID that wasn't found
        """
        message = f"Store not found: {store_id}"
        self.store_id = store_id
        super().__init__(message, "STORE_NOT_FOUND")


class ThresholdConfigurationError(AnalyticsError):
    """
    Raised when metric threshold configuration is invalid.

    Example:
    - Upper threshold less than lower threshold
    - Invalid threshold value
    - Missing required threshold parameters
    """

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        threshold_type: Optional[str] = None
    ):
        """
        Initialize threshold configuration error.

        Args:
            message: Error description
            metric_name: Metric with invalid threshold
            threshold_type: Type of threshold ('upper', 'lower', 'percentage')
        """
        self.metric_name = metric_name
        self.threshold_type = threshold_type
        super().__init__(message, "THRESHOLD_CONFIG_ERROR")


class ConcurrentModificationError(AnalyticsError):
    """
    Raised when concurrent modification of analytics data is detected.

    Example:
    - Snapshot being updated by multiple processes
    - Optimistic locking failure
    """

    def __init__(
        self,
        message: str,
        resource_id: UUID,
        resource_type: str = "snapshot"
    ):
        """
        Initialize concurrent modification error.

        Args:
            message: Error description
            resource_id: ID of resource being concurrently modified
            resource_type: Type of resource (snapshot, metric, etc.)
        """
        self.resource_id = resource_id
        self.resource_type = resource_type
        super().__init__(message, "CONCURRENT_MODIFICATION")


class PermissionDeniedError(AnalyticsError):
    """
    Raised when user lacks permission to access analytics data.

    Example:
    - User trying to access another store's analytics
    - Missing required role for sensitive metrics
    """

    def __init__(
        self,
        message: str,
        user_id: Optional[UUID] = None,
        required_permission: Optional[str] = None
    ):
        """
        Initialize permission denied error.

        Args:
            message: Error description
            user_id: User who was denied access
            required_permission: Permission that was required
        """
        self.user_id = user_id
        self.required_permission = required_permission
        super().__init__(message, "PERMISSION_DENIED")


class AnalyticsTimeoutError(AnalyticsError):
    """
    Raised when analytics calculation exceeds time limit.

    Example:
    - Long-running query timeout
    - Background job timeout
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[int] = None,
        operation: Optional[str] = None
    ):
        """
        Initialize timeout error.

        Args:
            message: Error description
            timeout_seconds: Configured timeout that was exceeded
            operation: Operation that timed out
        """
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        super().__init__(message, "ANALYTICS_TIMEOUT")
