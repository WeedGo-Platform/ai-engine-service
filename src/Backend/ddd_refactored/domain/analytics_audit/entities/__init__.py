"""
Analytics Domain Entities

Export all entity classes for easy importing.
"""

from .analytics_metric import (
    AnalyticsMetric,
    RevenueMetric,
    SalesMetric,
    InventoryMetric,
    CustomerMetric,
    DashboardSnapshot,
)

__all__ = [
    'AnalyticsMetric',
    'RevenueMetric',
    'SalesMetric',
    'InventoryMetric',
    'CustomerMetric',
    'DashboardSnapshot',
]
