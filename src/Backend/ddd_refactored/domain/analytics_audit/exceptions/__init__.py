"""
Analytics Domain Exceptions

Export all exception classes for easy importing.
"""

from .analytics_errors import (
    AnalyticsError,
    AnalyticsCalculationError,
    InvalidDateRangeError,
    MetricNotFoundError,
    SnapshotNotFoundError,
    InsufficientDataError,
    DataQualityError,
    StoreNotFoundError,
    ThresholdConfigurationError,
    ConcurrentModificationError,
    PermissionDeniedError,
    AnalyticsTimeoutError,
)

__all__ = [
    'AnalyticsError',
    'AnalyticsCalculationError',
    'InvalidDateRangeError',
    'MetricNotFoundError',
    'SnapshotNotFoundError',
    'InsufficientDataError',
    'DataQualityError',
    'StoreNotFoundError',
    'ThresholdConfigurationError',
    'ConcurrentModificationError',
    'PermissionDeniedError',
    'AnalyticsTimeoutError',
]
