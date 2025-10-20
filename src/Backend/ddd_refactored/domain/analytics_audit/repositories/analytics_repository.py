"""
Analytics Repository Interface

Defines the contract for analytics data persistence.
Follows the Repository pattern from DDD.

This interface lives in the domain layer and is implemented
by the infrastructure layer (PostgresAnalyticsRepository).
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..entities import DashboardSnapshot, AnalyticsMetric, RevenueMetric, SalesMetric, InventoryMetric, CustomerMetric
from ..value_objects import DateRange, ChartDataPoint


class AnalyticsRepository(ABC):
    """
    Repository interface for analytics data.

    This defines the contract that infrastructure implementations must follow.
    The repository is responsible for:
    - Retrieving analytics data from data sources
    - Calculating metrics from raw data
    - Persisting analytics snapshots
    - Managing metric lifecycle
    """

    # ========== Dashboard Analytics ==========

    @abstractmethod
    async def get_dashboard_snapshot(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> DashboardSnapshot:
        """
        Get complete dashboard snapshot for a store and time period.

        This is the primary method for dashboard analytics, returning
        a complete snapshot with all metrics populated.

        Args:
            store_id: Store UUID
            period: Time period for analytics
            tenant_id: Optional tenant context for multi-tenancy

        Returns:
            DashboardSnapshot with all metrics

        Raises:
            StoreNotFoundError: If store doesn't exist
            InsufficientDataError: If no data exists for period
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_revenue_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        include_chart_data: bool = True,
        tenant_id: Optional[UUID] = None
    ) -> RevenueMetric:
        """
        Get revenue metrics for a store and time period.

        Args:
            store_id: Store UUID
            period: Time period for analytics
            include_chart_data: Whether to include time-series chart data
            tenant_id: Optional tenant context

        Returns:
            RevenueMetric with revenue data and optionally chart data

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_sales_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> SalesMetric:
        """
        Get sales metrics for a store and time period.

        Args:
            store_id: Store UUID
            period: Time period for analytics
            tenant_id: Optional tenant context

        Returns:
            SalesMetric with order statistics

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_inventory_metrics(
        self,
        store_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> InventoryMetric:
        """
        Get current inventory metrics for a store.

        Note: Inventory is point-in-time, not period-based.

        Args:
            store_id: Store UUID
            tenant_id: Optional tenant context

        Returns:
            InventoryMetric with current inventory status

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_customer_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> CustomerMetric:
        """
        Get customer metrics for a store and time period.

        Args:
            store_id: Store UUID
            period: Time period for analytics
            tenant_id: Optional tenant context

        Returns:
            CustomerMetric with customer statistics

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    # ========== Product Analytics ==========

    @abstractmethod
    async def get_product_performance(
        self,
        store_id: UUID,
        period: DateRange,
        limit: int = 10,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top performing products by revenue.

        Args:
            store_id: Store UUID
            period: Time period for analysis
            limit: Number of products to return
            tenant_id: Optional tenant context

        Returns:
            List of product performance dictionaries

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_low_stock_products(
        self,
        store_id: UUID,
        threshold: int = 10,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products below stock threshold.

        Args:
            store_id: Store UUID
            threshold: Stock level threshold
            tenant_id: Optional tenant context

        Returns:
            List of low stock products

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_category_performance(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales performance by product category.

        Args:
            store_id: Store UUID
            period: Time period for analysis
            tenant_id: Optional tenant context

        Returns:
            List of category performance dictionaries

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    # ========== Sales Trends ==========

    @abstractmethod
    async def get_revenue_chart_data(
        self,
        store_id: UUID,
        period: DateRange,
        granularity: str = 'daily',
        tenant_id: Optional[UUID] = None
    ) -> List[ChartDataPoint]:
        """
        Get revenue trend data for charting.

        Args:
            store_id: Store UUID
            period: Time period for chart
            granularity: 'hourly', 'daily', 'weekly', 'monthly'
            tenant_id: Optional tenant context

        Returns:
            List of ChartDataPoint for time-series visualization

        Raises:
            AnalyticsCalculationError: If calculation fails
            InvalidDateRangeError: If granularity doesn't match period
        """
        pass

    @abstractmethod
    async def get_sales_by_hour(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales distribution by hour of day.

        Args:
            store_id: Store UUID
            period: Time period for analysis
            tenant_id: Optional tenant context

        Returns:
            List of hourly sales data (0-23)

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_sales_by_day_of_week(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales distribution by day of week.

        Args:
            store_id: Store UUID
            period: Time period for analysis
            tenant_id: Optional tenant context

        Returns:
            List of daily sales data (Mon-Sun)

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    # ========== Snapshot Management ==========

    @abstractmethod
    async def save_snapshot(self, snapshot: DashboardSnapshot) -> None:
        """
        Save a complete dashboard snapshot.

        This allows caching/archiving of calculated analytics.

        Args:
            snapshot: DashboardSnapshot to save

        Raises:
            ConcurrentModificationError: If snapshot already exists
        """
        pass

    @abstractmethod
    async def find_snapshot_by_id(self, snapshot_id: UUID) -> Optional[DashboardSnapshot]:
        """
        Find snapshot by ID.

        Args:
            snapshot_id: Snapshot UUID

        Returns:
            DashboardSnapshot if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_snapshots_by_store(
        self,
        store_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[DashboardSnapshot]:
        """
        Find snapshots for a store with pagination.

        Args:
            store_id: Store UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of DashboardSnapshots (may be empty)
        """
        pass

    @abstractmethod
    async def find_latest_snapshot(
        self,
        store_id: UUID,
        before: Optional[datetime] = None
    ) -> Optional[DashboardSnapshot]:
        """
        Find most recent snapshot for a store.

        Args:
            store_id: Store UUID
            before: Optional cutoff date

        Returns:
            Most recent DashboardSnapshot if found, None otherwise
        """
        pass

    # ========== Metric Management ==========

    @abstractmethod
    async def save_metric(self, metric: AnalyticsMetric) -> None:
        """
        Save an individual analytics metric.

        Args:
            metric: AnalyticsMetric to save

        Raises:
            DataQualityError: If metric data is invalid
        """
        pass

    @abstractmethod
    async def find_metrics_by_name(
        self,
        store_id: UUID,
        metric_name: str,
        period: Optional[DateRange] = None,
        limit: int = 100
    ) -> List[AnalyticsMetric]:
        """
        Find metrics by name for a store.

        Args:
            store_id: Store UUID
            metric_name: Name of metric to find
            period: Optional time period filter
            limit: Maximum number of results

        Returns:
            List of AnalyticsMetrics (may be empty)
        """
        pass

    # ========== Comparison & Trends ==========

    @abstractmethod
    async def compare_periods(
        self,
        store_id: UUID,
        current_period: DateRange,
        comparison_period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Compare metrics between two time periods.

        Args:
            store_id: Store UUID
            current_period: Current period
            comparison_period: Period to compare against
            tenant_id: Optional tenant context

        Returns:
            Dictionary with comparison data for all metrics

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    # ========== Aggregations ==========

    @abstractmethod
    async def get_tenant_aggregate(
        self,
        tenant_id: UUID,
        period: DateRange
    ) -> DashboardSnapshot:
        """
        Get aggregated analytics across all stores for a tenant.

        Args:
            tenant_id: Tenant UUID
            period: Time period for analytics

        Returns:
            Aggregated DashboardSnapshot for tenant

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass

    @abstractmethod
    async def get_global_aggregate(
        self,
        period: DateRange
    ) -> DashboardSnapshot:
        """
        Get aggregated analytics across all tenants and stores.

        For super admin view.

        Args:
            period: Time period for analytics

        Returns:
            Global aggregated DashboardSnapshot

        Raises:
            AnalyticsCalculationError: If calculation fails
        """
        pass
