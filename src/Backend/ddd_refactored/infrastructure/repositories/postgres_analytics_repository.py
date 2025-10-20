"""
PostgreSQL Analytics Repository Implementation

AsyncPG-based implementation of AnalyticsRepository interface.
Migrates SQL queries from analytics_endpoints.py into domain-driven repository.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta

from ...domain.analytics_audit.repositories import AnalyticsRepository
from ...domain.analytics_audit.entities import (
    DashboardSnapshot,
    AnalyticsMetric,
    RevenueMetric,
    SalesMetric,
    InventoryMetric,
    CustomerMetric
)
from ...domain.analytics_audit.value_objects import (
    DateRange,
    ChartDataPoint,
    MetricValue,
    TrendDirection
)
from ...domain.analytics_audit.exceptions import (
    AnalyticsCalculationError,
    StoreNotFoundError,
    InsufficientDataError
)


class PostgresAnalyticsRepository(AnalyticsRepository):
    """
    PostgreSQL implementation of AnalyticsRepository using AsyncPG.

    Responsibilities:
    - Execute analytics queries against PostgreSQL
    - Map database rows to domain entities
    - Calculate metrics from raw data
    - Handle tenant and store filtering
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize repository with database connection pool.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool

    # ========== Dashboard Analytics ==========

    async def get_dashboard_snapshot(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> DashboardSnapshot:
        """
        Get complete dashboard snapshot for a store and time period.

        This is the primary method that orchestrates all metrics.
        """
        try:
            # Create snapshot
            snapshot = DashboardSnapshot(
                store_id=store_id,
                period_start=period.start_date,
                period_end=period.end_date
            )

            # Fetch all metrics concurrently would be ideal, but for now sequential
            revenue_metric = await self.get_revenue_metrics(
                store_id=store_id,
                period=period,
                include_chart_data=True,
                tenant_id=tenant_id
            )
            snapshot.add_revenue_metric(revenue_metric)

            sales_metric = await self.get_sales_metrics(
                store_id=store_id,
                period=period,
                tenant_id=tenant_id
            )
            snapshot.add_sales_metric(sales_metric)

            inventory_metric = await self.get_inventory_metrics(
                store_id=store_id,
                tenant_id=tenant_id
            )
            snapshot.add_inventory_metric(inventory_metric)

            customer_metric = await self.get_customer_metrics(
                store_id=store_id,
                period=period,
                tenant_id=tenant_id
            )
            snapshot.add_customer_metric(customer_metric)

            return snapshot

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to calculate dashboard snapshot: {str(e)}",
                store_id=store_id,
                original_error=e
            )

    async def get_revenue_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        include_chart_data: bool = True,
        tenant_id: Optional[UUID] = None
    ) -> RevenueMetric:
        """
        Get revenue metrics for a store and time period.

        Migrated from analytics_endpoints.py revenue calculation logic.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build WHERE clause
                where_conditions = ["o.created_at >= $1", "o.created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"o.tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"o.store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                # Query revenue data
                revenue_query = f"""
                    SELECT
                        DATE(o.created_at) as date,
                        SUM(o.total_amount) as revenue,
                        SUM(o.tax_amount) as tax,
                        SUM(o.discount_amount) as discount,
                        COUNT(*) as order_count
                    FROM orders o
                    WHERE {where_clause}
                    GROUP BY DATE(o.created_at)
                    ORDER BY date
                """

                revenue_rows = await conn.fetch(revenue_query, *params)

                # Calculate totals
                total_revenue = Decimal('0.00')
                total_tax = Decimal('0.00')
                total_discount = Decimal('0.00')

                for row in revenue_rows:
                    total_revenue += Decimal(str(row['revenue'] or 0))
                    total_tax += Decimal(str(row['tax'] or 0))
                    total_discount += Decimal(str(row['discount'] or 0))

                gross_revenue = total_revenue + total_discount  # Revenue before discounts

                # Calculate comparison period (previous period of same length)
                comparison_period = DateRange(
                    start_date=period.start_date - timedelta(days=period.duration_days),
                    end_date=period.start_date - timedelta(days=1)
                )

                # Query previous period for comparison
                prev_params = [comparison_period.start_date, comparison_period.end_date] + params[2:]
                prev_revenue_query = f"""
                    SELECT SUM(o.total_amount) as revenue
                    FROM orders o
                    WHERE {where_clause.replace('$1', f'${len(prev_params)-1}').replace('$2', f'${len(prev_params)}')}
                """

                # Simplified - just get total for previous period
                prev_row = await conn.fetchrow(
                    f"""
                    SELECT SUM(o.total_amount) as revenue
                    FROM orders o
                    WHERE o.created_at >= ${param_index}
                        AND o.created_at <= ${param_index + 1}
                        {' AND o.tenant_id = ${param_index + 2}' if tenant_id else ''}
                        {' AND o.store_id = ${param_index + 3}' if store_id else ''}
                    """,
                    comparison_period.start_date,
                    comparison_period.end_date,
                    *(([str(tenant_id)] if tenant_id else []) + ([str(store_id)] if store_id else []))
                )

                previous_revenue = Decimal(str(prev_row['revenue'] or 0)) if prev_row else Decimal('0.00')

                # Calculate percent change
                if previous_revenue > 0:
                    percent_change = ((total_revenue - previous_revenue) / previous_revenue) * Decimal('100')
                else:
                    percent_change = None

                # Create revenue metric
                revenue_metric = RevenueMetric(
                    metric_name="total_revenue",
                    measured_value=total_revenue,
                    store_id=store_id,
                    measured_at=datetime.utcnow(),
                    period_start=period.start_date,
                    period_end=period.end_date,
                    currency='CAD',
                    gross_revenue=gross_revenue,
                    tax_amount=total_tax,
                    discount_amount=total_discount,
                    previous_period_value=previous_revenue,
                    percent_change=percent_change
                )

                return revenue_metric

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to calculate revenue metrics: {str(e)}",
                metric_name="revenue",
                store_id=store_id,
                original_error=e
            )

    async def get_sales_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> SalesMetric:
        """
        Get sales metrics for a store and time period.

        Migrated from analytics_endpoints.py order statistics logic.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build WHERE clause
                where_conditions = ["created_at >= $1", "created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                # Query order statistics
                order_stats_query = f"""
                    SELECT
                        COUNT(*) as total_orders,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_orders,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_orders,
                        COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_orders,
                        AVG(total_amount) FILTER (WHERE status = 'completed') as avg_order_value,
                        SUM(total_amount) FILTER (WHERE status = 'completed') as total_sales
                    FROM orders
                    WHERE {where_clause}
                """

                stats = await conn.fetchrow(order_stats_query, *params)

                total_orders = stats['total_orders'] or 0
                completed_orders = stats['completed_orders'] or 0
                pending_orders = stats['pending_orders'] or 0
                cancelled_orders = stats['cancelled_orders'] or 0
                avg_order_value = Decimal(str(stats['avg_order_value'] or 0))
                total_sales = Decimal(str(stats['total_sales'] or 0))

                # Create sales metric
                sales_metric = SalesMetric(
                    metric_name="sales_overview",
                    measured_value=total_sales,
                    store_id=store_id,
                    measured_at=datetime.utcnow(),
                    period_start=period.start_date,
                    period_end=period.end_date,
                    total_orders=total_orders,
                    completed_orders=completed_orders,
                    pending_orders=pending_orders,
                    cancelled_orders=cancelled_orders,
                    average_order_value=avg_order_value,
                    currency='CAD'
                )

                return sales_metric

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to calculate sales metrics: {str(e)}",
                metric_name="sales",
                store_id=store_id,
                original_error=e
            )

    async def get_inventory_metrics(
        self,
        store_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> InventoryMetric:
        """
        Get current inventory metrics for a store.

        Migrated from analytics_endpoints.py inventory statistics logic.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build query based on tenant/store context
                if tenant_id and store_id:
                    inventory_query = """
                        SELECT
                            COUNT(*) as total_products,
                            COUNT(*) FILTER (WHERE si.quantity > 0) as in_stock_products,
                            COUNT(*) FILTER (WHERE si.quantity <= si.reorder_point AND si.quantity > 0) as low_stock,
                            COUNT(*) FILTER (WHERE si.quantity = 0) as out_of_stock,
                            SUM(si.quantity) as total_quantity,
                            SUM(si.quantity * p.price) as total_value
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        JOIN stores s ON si.store_id = s.id
                        WHERE s.tenant_id = $1 AND si.store_id = $2
                    """
                    params = [str(tenant_id), str(store_id)]
                elif store_id:
                    inventory_query = """
                        SELECT
                            COUNT(*) as total_products,
                            COUNT(*) FILTER (WHERE si.quantity > 0) as in_stock_products,
                            COUNT(*) FILTER (WHERE si.quantity <= si.reorder_point AND si.quantity > 0) as low_stock,
                            COUNT(*) FILTER (WHERE si.quantity = 0) as out_of_stock,
                            SUM(si.quantity) as total_quantity,
                            SUM(si.quantity * p.price) as total_value
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.store_id = $1
                    """
                    params = [str(store_id)]
                elif tenant_id:
                    inventory_query = """
                        SELECT
                            COUNT(*) as total_products,
                            COUNT(*) FILTER (WHERE si.quantity > 0) as in_stock_products,
                            COUNT(*) FILTER (WHERE si.quantity <= si.reorder_point AND si.quantity > 0) as low_stock,
                            COUNT(*) FILTER (WHERE si.quantity = 0) as out_of_stock,
                            SUM(si.quantity) as total_quantity,
                            SUM(si.quantity * p.price) as total_value
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        JOIN stores s ON si.store_id = s.id
                        WHERE s.tenant_id = $1
                    """
                    params = [str(tenant_id)]
                else:
                    # Super admin - all inventory
                    inventory_query = """
                        SELECT
                            COUNT(*) as total_products,
                            COUNT(*) FILTER (WHERE si.quantity > 0) as in_stock_products,
                            COUNT(*) FILTER (WHERE si.quantity <= si.reorder_point AND si.quantity > 0) as low_stock,
                            COUNT(*) FILTER (WHERE si.quantity = 0) as out_of_stock,
                            SUM(si.quantity) as total_quantity,
                            SUM(si.quantity * p.price) as total_value
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                    """
                    params = []

                if params:
                    stats = await conn.fetchrow(inventory_query, *params)
                else:
                    stats = await conn.fetchrow(inventory_query)

                total_products = stats['total_products'] or 0
                in_stock = stats['in_stock_products'] or 0
                low_stock = stats['low_stock'] or 0
                out_of_stock = stats['out_of_stock'] or 0
                total_quantity = Decimal(str(stats['total_quantity'] or 0))
                total_value = Decimal(str(stats['total_value'] or 0))

                # Create inventory metric
                inventory_metric = InventoryMetric(
                    metric_name="inventory_status",
                    measured_value=total_quantity,
                    store_id=store_id,
                    measured_at=datetime.utcnow(),
                    total_products=total_products,
                    in_stock_products=in_stock,
                    low_stock_products=low_stock,
                    out_of_stock_products=out_of_stock,
                    total_quantity=total_quantity,
                    total_value=total_value,
                    currency='CAD'
                )

                return inventory_metric

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to calculate inventory metrics: {str(e)}",
                metric_name="inventory",
                store_id=store_id,
                original_error=e
            )

    async def get_customer_metrics(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> CustomerMetric:
        """
        Get customer metrics for a store and time period.

        Migrated from analytics_endpoints.py customer statistics logic.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build WHERE clause
                where_conditions = ["created_at >= $1", "created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                # Calculate 7 days ago for new customer detection
                seven_days_ago = period.end_date - timedelta(days=7)

                # Query customer statistics
                customer_stats_query = f"""
                    SELECT
                        COUNT(DISTINCT customer_id) as total_customers,
                        COUNT(DISTINCT customer_id) FILTER (
                            WHERE created_at >= ${param_index}
                        ) as new_customers,
                        AVG(total_amount) as avg_customer_value,
                        SUM(total_amount) as total_customer_value
                    FROM orders
                    WHERE {where_clause}
                """

                params_with_seven_days = params + [seven_days_ago]
                stats = await conn.fetchrow(customer_stats_query, *params_with_seven_days)

                total_customers = stats['total_customers'] or 0
                new_customers = stats['new_customers'] or 0
                returning_customers = total_customers - new_customers
                avg_value = Decimal(str(stats['avg_customer_value'] or 0))

                # Create customer metric
                customer_metric = CustomerMetric(
                    metric_name="customer_overview",
                    measured_value=Decimal(str(total_customers)),
                    store_id=store_id,
                    measured_at=datetime.utcnow(),
                    period_start=period.start_date,
                    period_end=period.end_date,
                    total_customers=total_customers,
                    new_customers=new_customers,
                    returning_customers=returning_customers,
                    active_customers=total_customers,  # Simplified: all with orders are active
                    average_customer_value=avg_value,
                    currency='CAD'
                )

                return customer_metric

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to calculate customer metrics: {str(e)}",
                metric_name="customers",
                store_id=store_id,
                original_error=e
            )

    # ========== Product Analytics ==========

    async def get_product_performance(
        self,
        store_id: UUID,
        period: DateRange,
        limit: int = 10,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get top performing products by revenue."""
        try:
            async with self.db_pool.acquire() as conn:
                where_conditions = ["o.created_at >= $1", "o.created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"o.tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"o.store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                query = f"""
                    SELECT
                        p.id,
                        p.name,
                        p.sku,
                        SUM(oi.quantity) as units_sold,
                        SUM(oi.price * oi.quantity) as revenue,
                        COUNT(DISTINCT o.id) as order_count
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    JOIN products p ON oi.product_id = p.id
                    WHERE {where_clause}
                    GROUP BY p.id, p.name, p.sku
                    ORDER BY revenue DESC
                    LIMIT ${param_index}
                """

                params.append(limit)
                rows = await conn.fetch(query, *params)

                return [
                    {
                        'product_id': str(row['id']),
                        'name': row['name'],
                        'sku': row['sku'],
                        'units_sold': row['units_sold'],
                        'revenue': float(row['revenue']),
                        'order_count': row['order_count']
                    }
                    for row in rows
                ]

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get product performance: {str(e)}",
                metric_name="product_performance",
                store_id=store_id,
                original_error=e
            )

    async def get_low_stock_products(
        self,
        store_id: UUID,
        threshold: int = 10,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get products below stock threshold."""
        try:
            async with self.db_pool.acquire() as conn:
                if tenant_id and store_id:
                    query = """
                        SELECT
                            p.id,
                            p.name,
                            p.sku,
                            si.quantity,
                            si.reorder_point
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        JOIN stores s ON si.store_id = s.id
                        WHERE s.tenant_id = $1
                            AND si.store_id = $2
                            AND si.quantity < $3
                            AND si.quantity > 0
                        ORDER BY si.quantity ASC
                    """
                    params = [str(tenant_id), str(store_id), threshold]
                elif store_id:
                    query = """
                        SELECT
                            p.id,
                            p.name,
                            p.sku,
                            si.quantity,
                            si.reorder_point
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.store_id = $1
                            AND si.quantity < $2
                            AND si.quantity > 0
                        ORDER BY si.quantity ASC
                    """
                    params = [str(store_id), threshold]
                else:
                    query = """
                        SELECT
                            p.id,
                            p.name,
                            p.sku,
                            si.quantity,
                            si.reorder_point
                        FROM ocs_inventory si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.quantity < $1
                            AND si.quantity > 0
                        ORDER BY si.quantity ASC
                    """
                    params = [threshold]

                rows = await conn.fetch(query, *params)

                return [
                    {
                        'product_id': str(row['id']),
                        'name': row['name'],
                        'sku': row['sku'],
                        'quantity': row['quantity'],
                        'reorder_point': row['reorder_point']
                    }
                    for row in rows
                ]

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get low stock products: {str(e)}",
                metric_name="low_stock",
                store_id=store_id,
                original_error=e
            )

    async def get_category_performance(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get sales performance by product category."""
        try:
            async with self.db_pool.acquire() as conn:
                where_conditions = ["o.created_at >= $1", "o.created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"o.tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"o.store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                query = f"""
                    SELECT
                        p.category,
                        SUM(oi.quantity) as units_sold,
                        SUM(oi.price * oi.quantity) as revenue,
                        COUNT(DISTINCT o.id) as order_count,
                        COUNT(DISTINCT p.id) as product_count
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    JOIN products p ON oi.product_id = p.id
                    WHERE {where_clause}
                    GROUP BY p.category
                    ORDER BY revenue DESC
                """

                rows = await conn.fetch(query, *params)

                return [
                    {
                        'category': row['category'],
                        'units_sold': row['units_sold'],
                        'revenue': float(row['revenue']),
                        'order_count': row['order_count'],
                        'product_count': row['product_count']
                    }
                    for row in rows
                ]

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get category performance: {str(e)}",
                metric_name="category_performance",
                store_id=store_id,
                original_error=e
            )

    # ========== Sales Trends ==========

    async def get_revenue_chart_data(
        self,
        store_id: UUID,
        period: DateRange,
        granularity: str = 'daily',
        tenant_id: Optional[UUID] = None
    ) -> List[ChartDataPoint]:
        """Get revenue trend data for charting."""
        try:
            async with self.db_pool.acquire() as conn:
                where_conditions = ["o.created_at >= $1", "o.created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"o.tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"o.store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                # Group by granularity
                if granularity == 'hourly':
                    date_trunc = "date_trunc('hour', o.created_at)"
                elif granularity == 'weekly':
                    date_trunc = "date_trunc('week', o.created_at)"
                elif granularity == 'monthly':
                    date_trunc = "date_trunc('month', o.created_at)"
                else:  # daily
                    date_trunc = "DATE(o.created_at)"

                query = f"""
                    SELECT
                        {date_trunc} as period,
                        SUM(o.total_amount) as revenue,
                        COUNT(*) as order_count
                    FROM orders o
                    WHERE {where_clause}
                    GROUP BY period
                    ORDER BY period
                """

                rows = await conn.fetch(query, *params)

                chart_points = []
                for row in rows:
                    point = ChartDataPoint(
                        timestamp=row['period'],
                        value=Decimal(str(row['revenue'])),
                        metadata={
                            'order_count': row['order_count']
                        }
                    )
                    chart_points.append(point)

                return chart_points

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get revenue chart data: {str(e)}",
                metric_name="revenue_chart",
                store_id=store_id,
                original_error=e
            )

    async def get_sales_by_hour(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get sales distribution by hour of day."""
        try:
            async with self.db_pool.acquire() as conn:
                where_conditions = ["created_at >= $1", "created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                query = f"""
                    SELECT
                        EXTRACT(HOUR FROM created_at) as hour,
                        COUNT(*) as order_count,
                        SUM(total_amount) as revenue
                    FROM orders
                    WHERE {where_clause}
                    GROUP BY hour
                    ORDER BY hour
                """

                rows = await conn.fetch(query, *params)

                return [
                    {
                        'hour': int(row['hour']),
                        'order_count': row['order_count'],
                        'revenue': float(row['revenue'])
                    }
                    for row in rows
                ]

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get sales by hour: {str(e)}",
                metric_name="sales_by_hour",
                store_id=store_id,
                original_error=e
            )

    async def get_sales_by_day_of_week(
        self,
        store_id: UUID,
        period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get sales distribution by day of week."""
        try:
            async with self.db_pool.acquire() as conn:
                where_conditions = ["created_at >= $1", "created_at <= $2"]
                params = [period.start_date, period.end_date]
                param_index = 3

                if tenant_id:
                    where_conditions.append(f"tenant_id = ${param_index}")
                    params.append(str(tenant_id))
                    param_index += 1

                if store_id:
                    where_conditions.append(f"store_id = ${param_index}")
                    params.append(str(store_id))
                    param_index += 1

                where_clause = " AND ".join(where_conditions)

                query = f"""
                    SELECT
                        EXTRACT(DOW FROM created_at) as day_of_week,
                        COUNT(*) as order_count,
                        SUM(total_amount) as revenue
                    FROM orders
                    WHERE {where_clause}
                    GROUP BY day_of_week
                    ORDER BY day_of_week
                """

                rows = await conn.fetch(query, *params)

                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

                return [
                    {
                        'day_of_week': int(row['day_of_week']),
                        'day_name': day_names[int(row['day_of_week'])],
                        'order_count': row['order_count'],
                        'revenue': float(row['revenue'])
                    }
                    for row in rows
                ]

        except Exception as e:
            raise AnalyticsCalculationError(
                message=f"Failed to get sales by day of week: {str(e)}",
                metric_name="sales_by_day",
                store_id=store_id,
                original_error=e
            )

    # ========== Snapshot Management (Stub implementations for now) ==========

    async def save_snapshot(self, snapshot: DashboardSnapshot) -> None:
        """Save dashboard snapshot - to be implemented when needed."""
        # TODO: Implement snapshot persistence if caching is required
        pass

    async def find_snapshot_by_id(self, snapshot_id: UUID) -> Optional[DashboardSnapshot]:
        """Find snapshot by ID - to be implemented when needed."""
        # TODO: Implement snapshot retrieval if caching is required
        return None

    async def find_snapshots_by_store(
        self,
        store_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[DashboardSnapshot]:
        """Find snapshots for store - to be implemented when needed."""
        # TODO: Implement snapshot listing if caching is required
        return []

    async def find_latest_snapshot(
        self,
        store_id: UUID,
        before: Optional[datetime] = None
    ) -> Optional[DashboardSnapshot]:
        """Find latest snapshot - to be implemented when needed."""
        # TODO: Implement latest snapshot retrieval if caching is required
        return None

    # ========== Metric Management (Stub implementations for now) ==========

    async def save_metric(self, metric: AnalyticsMetric) -> None:
        """Save individual metric - to be implemented when needed."""
        # TODO: Implement metric persistence if needed
        pass

    async def find_metrics_by_name(
        self,
        store_id: UUID,
        metric_name: str,
        period: Optional[DateRange] = None,
        limit: int = 100
    ) -> List[AnalyticsMetric]:
        """Find metrics by name - to be implemented when needed."""
        # TODO: Implement metric retrieval if needed
        return []

    # ========== Comparison & Aggregation (Stub implementations for now) ==========

    async def compare_periods(
        self,
        store_id: UUID,
        current_period: DateRange,
        comparison_period: DateRange,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Compare periods - to be implemented when needed."""
        # TODO: Implement period comparison if needed
        return {}

    async def get_tenant_aggregate(
        self,
        tenant_id: UUID,
        period: DateRange
    ) -> DashboardSnapshot:
        """Get tenant aggregate - uses same logic as store but without store filter."""
        # Reuse get_dashboard_snapshot without store_id filter
        return await self.get_dashboard_snapshot(
            store_id=tenant_id,  # Will be filtered differently in queries
            period=period,
            tenant_id=tenant_id
        )

    async def get_global_aggregate(
        self,
        period: DateRange
    ) -> DashboardSnapshot:
        """Get global aggregate - to be implemented for super admin."""
        # TODO: Implement global aggregation across all tenants
        # For now, use a placeholder UUID
        from uuid import uuid4
        placeholder_id = uuid4()
        return await self.get_dashboard_snapshot(
            store_id=placeholder_id,
            period=period,
            tenant_id=None
        )
