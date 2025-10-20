"""
Analytics Management Application Service

Orchestrates analytics use cases using domain entities and infrastructure.
Coordinates between repository, domain entities, and API layer.
"""

import asyncpg
import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta

from ...domain.analytics_audit.entities import (
    DashboardSnapshot,
    RevenueMetric,
    SalesMetric,
    InventoryMetric,
    CustomerMetric
)
from ...domain.analytics_audit.repositories import AnalyticsRepository
from ...domain.analytics_audit.value_objects import (
    DateRange,
    ChartDataPoint,
    MetricValue,
    RevenueTrend,
    TrendDirection
)
from ...domain.analytics_audit.exceptions import (
    AnalyticsCalculationError,
    StoreNotFoundError,
    InsufficientDataError,
    InvalidDateRangeError
)
from ...domain.analytics_audit.events import (
    AnalyticsCalculated,
    DashboardRefreshed,
    MetricThresholdExceeded
)

logger = logging.getLogger(__name__)


class AnalyticsManagementService:
    """
    Application service for analytics management.

    Responsibilities:
    - Orchestrate analytics calculation use cases
    - Coordinate between repository and domain entities
    - Apply business rules for analytics
    - Publish domain events
    - Transform domain entities to DTOs for API layer

    This service follows the Application Service pattern from DDD,
    keeping calculation logic in repository while orchestrating
    the overall workflow and applying domain rules.
    """

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        db_pool: asyncpg.Pool
    ):
        """
        Initialize analytics service with dependencies.

        Args:
            analytics_repo: Repository for analytics data
            db_pool: Database connection pool (for direct queries if needed)
        """
        self.analytics_repo = analytics_repo
        self.db_pool = db_pool
        self.logger = logger

    # ========== Dashboard Analytics Use Cases ==========

    async def get_dashboard_analytics(
        self,
        store_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get complete dashboard analytics.

        This is the main use case for dashboard analytics.
        Handles multi-tenancy: super admin, tenant admin, store manager.

        Args:
            store_id: Optional store UUID (None for tenant/global aggregation)
            tenant_id: Optional tenant UUID (None for global aggregation)
            period_days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with all dashboard metrics formatted for API

        Raises:
            StoreNotFoundError: If store doesn't exist
            AnalyticsCalculationError: If calculation fails
        """
        try:
            start_time = datetime.utcnow()

            # Create date range
            period = DateRange(
                start_date=datetime.utcnow() - timedelta(days=period_days - 1),
                end_date=datetime.utcnow()
            )

            # Determine which aggregation level to use
            if store_id:
                # Store-level analytics
                snapshot = await self.analytics_repo.get_dashboard_snapshot(
                    store_id=store_id,
                    period=period,
                    tenant_id=tenant_id
                )
            elif tenant_id:
                # Tenant-level aggregation
                snapshot = await self.analytics_repo.get_tenant_aggregate(
                    tenant_id=tenant_id,
                    period=period
                )
            else:
                # Global aggregation (super admin)
                snapshot = await self.analytics_repo.get_global_aggregate(
                    period=period
                )

            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Publish analytics calculated event
            metrics_calculated = []
            if snapshot.revenue_metric:
                metrics_calculated.append('revenue')
            if snapshot.sales_metric:
                metrics_calculated.append('sales')
            if snapshot.inventory_metric:
                metrics_calculated.append('inventory')
            if snapshot.customer_metric:
                metrics_calculated.append('customers')

            # TODO: Publish event to event bus
            event = AnalyticsCalculated(
                snapshot_id=snapshot.id,
                store_id=snapshot.store_id,
                period_start=period.start_date,
                period_end=period.end_date,
                metrics_calculated=metrics_calculated,
                calculation_duration_ms=duration_ms
            )
            self.logger.info(f"Analytics calculated: {event.to_dict()}")

            # Transform to API response format
            return self._format_dashboard_response(snapshot, period)

        except Exception as e:
            self.logger.error(f"Dashboard analytics failed: {str(e)}", exc_info=True)
            raise AnalyticsCalculationError(
                message=f"Failed to get dashboard analytics: {str(e)}",
                store_id=store_id,
                original_error=e
            )

    def _format_dashboard_response(
        self,
        snapshot: DashboardSnapshot,
        period: DateRange
    ) -> Dict[str, Any]:
        """
        Format dashboard snapshot for API response.

        Transforms domain entities into API-friendly format.
        """
        response = {
            'snapshot_id': str(snapshot.id),
            'store_id': str(snapshot.store_id),
            'period': {
                'start': period.start_date.isoformat(),
                'end': period.end_date.isoformat(),
                'days': period.duration_days
            },
            'generated_at': snapshot.created_at.isoformat()
        }

        # Revenue metrics
        if snapshot.revenue_metric:
            rev = snapshot.revenue_metric
            response['revenue'] = {
                'total': float(rev.measured_value),
                'currency': rev.currency,
                'gross': float(rev.gross_revenue),
                'tax': float(rev.tax_amount),
                'discounts': float(rev.discount_amount),
                'net': float(rev.calculate_net_revenue()),
                'trend': float(rev.percent_change) if rev.percent_change else 0,
                'previous_period': float(rev.previous_period_value) if rev.previous_period_value else 0,
                'chart_data': []  # TODO: Add chart data from repository
            }

        # Sales metrics
        if snapshot.sales_metric:
            sales = snapshot.sales_metric
            response['orders'] = {
                'total': sales.total_orders,
                'completed': sales.completed_orders,
                'pending': sales.pending_orders,
                'cancelled': sales.cancelled_orders,
                'average_value': float(sales.average_order_value),
                'completion_rate': float(sales.calculate_completion_rate()),
                'cancellation_rate': float(sales.calculate_cancellation_rate()),
                'trend': 0  # TODO: Calculate trend from previous period
            }

        # Inventory metrics
        if snapshot.inventory_metric:
            inv = snapshot.inventory_metric
            response['inventory'] = {
                'total_products': inv.total_products,
                'in_stock': inv.in_stock_products,
                'low_stock': inv.low_stock_products,
                'out_of_stock': inv.out_of_stock_products,
                'total_quantity': float(inv.total_quantity),
                'total_value': float(inv.total_value),
                'stock_coverage_rate': float(inv.calculate_stock_coverage_rate()),
                'average_product_value': float(inv.calculate_average_product_value())
            }

        # Customer metrics
        if snapshot.customer_metric:
            cust = snapshot.customer_metric
            response['customers'] = {
                'total': cust.total_customers,
                'new': cust.new_customers,
                'returning': cust.returning_customers,
                'active': cust.active_customers,
                'average_value': float(cust.average_customer_value),
                'new_customer_rate': float(cust.calculate_new_customer_rate()),
                'active_rate': float(cust.calculate_active_rate()),
                'retention_rate': float(cust.retention_rate) if cust.retention_rate else None
            }

        return response

    # ========== Product Analytics Use Cases ==========

    async def get_product_analytics(
        self,
        store_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        period_days: int = 30,
        top_products_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get product performance analytics.

        Args:
            store_id: Optional store UUID
            tenant_id: Optional tenant UUID
            period_days: Number of days to analyze
            top_products_limit: Number of top products to return

        Returns:
            Dictionary with product analytics
        """
        try:
            period = DateRange(
                start_date=datetime.utcnow() - timedelta(days=period_days - 1),
                end_date=datetime.utcnow()
            )

            # Use store_id or create placeholder for aggregations
            target_store_id = store_id or UUID('00000000-0000-0000-0000-000000000000')

            # Get top performing products
            top_products = await self.analytics_repo.get_product_performance(
                store_id=target_store_id,
                period=period,
                limit=top_products_limit,
                tenant_id=tenant_id
            )

            # Get low stock products
            low_stock = await self.analytics_repo.get_low_stock_products(
                store_id=target_store_id,
                threshold=10,
                tenant_id=tenant_id
            )

            # Get category performance
            categories = await self.analytics_repo.get_category_performance(
                store_id=target_store_id,
                period=period,
                tenant_id=tenant_id
            )

            return {
                'period': {
                    'start': period.start_date.isoformat(),
                    'end': period.end_date.isoformat(),
                    'days': period.duration_days
                },
                'top_products': top_products,
                'low_stock_products': low_stock,
                'category_performance': categories,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Product analytics failed: {str(e)}", exc_info=True)
            raise AnalyticsCalculationError(
                message=f"Failed to get product analytics: {str(e)}",
                store_id=store_id,
                original_error=e
            )

    # ========== Sales Trends Use Cases ==========

    async def get_sales_trends(
        self,
        store_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        period_days: int = 30,
        granularity: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Get sales trend analytics.

        Args:
            store_id: Optional store UUID
            tenant_id: Optional tenant UUID
            period_days: Number of days to analyze
            granularity: Chart granularity ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            Dictionary with sales trends
        """
        try:
            period = DateRange(
                start_date=datetime.utcnow() - timedelta(days=period_days - 1),
                end_date=datetime.utcnow()
            )

            # Use store_id or create placeholder
            target_store_id = store_id or UUID('00000000-0000-0000-0000-000000000000')

            # Get revenue chart data
            chart_data = await self.analytics_repo.get_revenue_chart_data(
                store_id=target_store_id,
                period=period,
                granularity=granularity,
                tenant_id=tenant_id
            )

            # Get sales by hour
            sales_by_hour = await self.analytics_repo.get_sales_by_hour(
                store_id=target_store_id,
                period=period,
                tenant_id=tenant_id
            )

            # Get sales by day of week
            sales_by_day = await self.analytics_repo.get_sales_by_day_of_week(
                store_id=target_store_id,
                period=period,
                tenant_id=tenant_id
            )

            return {
                'period': {
                    'start': period.start_date.isoformat(),
                    'end': period.end_date.isoformat(),
                    'days': period.duration_days
                },
                'revenue_chart': [point.to_dict() for point in chart_data],
                'sales_by_hour': sales_by_hour,
                'sales_by_day_of_week': sales_by_day,
                'granularity': granularity,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Sales trends failed: {str(e)}", exc_info=True)
            raise AnalyticsCalculationError(
                message=f"Failed to get sales trends: {str(e)}",
                store_id=store_id,
                original_error=e
            )

    # ========== Alert & Threshold Use Cases ==========

    async def check_metric_thresholds(
        self,
        store_id: UUID,
        snapshot: DashboardSnapshot
    ) -> List[Dict[str, Any]]:
        """
        Check if any metrics exceed configured thresholds.

        This use case evaluates business rules and raises alerts.

        Args:
            store_id: Store UUID
            snapshot: Dashboard snapshot to evaluate

        Returns:
            List of threshold violations
        """
        violations = []

        # Check revenue drop threshold (>20% decline)
        if snapshot.revenue_metric and snapshot.revenue_metric.percent_change:
            if snapshot.revenue_metric.percent_change < Decimal('-20'):
                event = MetricThresholdExceeded(
                    store_id=store_id,
                    metric_name='revenue',
                    current_value=snapshot.revenue_metric.measured_value,
                    threshold_value=snapshot.revenue_metric.previous_period_value or Decimal('0'),
                    threshold_type='percentage_change',
                    severity='high',
                    alert_message=f"Revenue dropped by {abs(float(snapshot.revenue_metric.percent_change)):.1f}%"
                )
                violations.append(event.to_dict())
                self.logger.warning(f"Revenue threshold exceeded: {event.to_dict()}")

        # Check inventory low stock threshold
        if snapshot.inventory_metric:
            stock_coverage = snapshot.inventory_metric.calculate_stock_coverage_rate()
            if stock_coverage < Decimal('50'):  # Less than 50% coverage
                event = MetricThresholdExceeded(
                    store_id=store_id,
                    metric_name='stock_coverage',
                    current_value=stock_coverage,
                    threshold_value=Decimal('50'),
                    threshold_type='lower',
                    severity='medium',
                    alert_message=f"Stock coverage at {float(stock_coverage):.1f}%, below 50% threshold"
                )
                violations.append(event.to_dict())

        # Check cancellation rate threshold (>10%)
        if snapshot.sales_metric:
            cancel_rate = snapshot.sales_metric.calculate_cancellation_rate()
            if cancel_rate > Decimal('10'):
                event = MetricThresholdExceeded(
                    store_id=store_id,
                    metric_name='cancellation_rate',
                    current_value=cancel_rate,
                    threshold_value=Decimal('10'),
                    threshold_type='upper',
                    severity='medium',
                    alert_message=f"Order cancellation rate at {float(cancel_rate):.1f}%, above 10% threshold"
                )
                violations.append(event.to_dict())

        return violations

    # ========== Period Comparison Use Cases ==========

    async def compare_periods(
        self,
        store_id: UUID,
        current_period_days: int = 30,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Compare current period with previous period.

        Useful for trend analysis and period-over-period growth.

        Args:
            store_id: Store UUID
            current_period_days: Length of period to compare
            tenant_id: Optional tenant context

        Returns:
            Dictionary with period comparison
        """
        try:
            # Define periods
            current_end = datetime.utcnow()
            current_start = current_end - timedelta(days=current_period_days - 1)
            current_period = DateRange(start_date=current_start, end_date=current_end)

            previous_end = current_start - timedelta(days=1)
            previous_start = previous_end - timedelta(days=current_period_days - 1)
            previous_period = DateRange(start_date=previous_start, end_date=previous_end)

            # Get snapshots for both periods
            current_snapshot = await self.analytics_repo.get_dashboard_snapshot(
                store_id=store_id,
                period=current_period,
                tenant_id=tenant_id
            )

            previous_snapshot = await self.analytics_repo.get_dashboard_snapshot(
                store_id=store_id,
                period=previous_period,
                tenant_id=tenant_id
            )

            # Calculate comparisons
            comparison = {
                'current_period': {
                    'start': current_period.start_date.isoformat(),
                    'end': current_period.end_date.isoformat()
                },
                'previous_period': {
                    'start': previous_period.start_date.isoformat(),
                    'end': previous_period.end_date.isoformat()
                },
                'revenue': self._compare_metrics(
                    current_snapshot.revenue_metric.measured_value if current_snapshot.revenue_metric else Decimal('0'),
                    previous_snapshot.revenue_metric.measured_value if previous_snapshot.revenue_metric else Decimal('0')
                ),
                'orders': self._compare_metrics(
                    Decimal(current_snapshot.sales_metric.total_orders) if current_snapshot.sales_metric else Decimal('0'),
                    Decimal(previous_snapshot.sales_metric.total_orders) if previous_snapshot.sales_metric else Decimal('0')
                ),
                'customers': self._compare_metrics(
                    Decimal(current_snapshot.customer_metric.total_customers) if current_snapshot.customer_metric else Decimal('0'),
                    Decimal(previous_snapshot.customer_metric.total_customers) if previous_snapshot.customer_metric else Decimal('0')
                )
            }

            return comparison

        except Exception as e:
            self.logger.error(f"Period comparison failed: {str(e)}", exc_info=True)
            raise AnalyticsCalculationError(
                message=f"Failed to compare periods: {str(e)}",
                store_id=store_id,
                original_error=e
            )

    def _compare_metrics(
        self,
        current: Decimal,
        previous: Decimal
    ) -> Dict[str, Any]:
        """Helper to compare two metric values."""
        if previous > 0:
            change = ((current - previous) / previous) * Decimal('100')
            direction = 'up' if change > 0 else ('down' if change < 0 else 'stable')
        else:
            change = None
            direction = 'new'

        return {
            'current': float(current),
            'previous': float(previous),
            'absolute_change': float(current - previous),
            'percent_change': float(change) if change else None,
            'direction': direction
        }

    # ========== Refresh Use Cases ==========

    async def refresh_dashboard(
        self,
        store_id: UUID,
        triggered_by: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Manually refresh dashboard analytics.

        This triggers a recalculation and publishes refresh event.

        Args:
            store_id: Store UUID
            triggered_by: User who triggered refresh
            tenant_id: Optional tenant context

        Returns:
            Refreshed dashboard data
        """
        # Calculate fresh analytics
        dashboard_data = await self.get_dashboard_analytics(
            store_id=store_id,
            tenant_id=tenant_id
        )

        # Publish refresh event
        # TODO: Use actual snapshot_id from response
        from uuid import uuid4
        event = DashboardRefreshed(
            store_id=store_id,
            snapshot_id=uuid4(),
            refresh_type='manual',
            triggered_by=triggered_by
        )
        self.logger.info(f"Dashboard refreshed: {event.to_dict()}")

        return dashboard_data
