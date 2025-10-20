"""
Analytics API Endpoints V2 - DDD Architecture

Clean implementation using Domain-Driven Design:
- Domain entities for business logic
- Repository pattern for data access
- Application services for use case orchestration
- Thin API layer for HTTP concerns only

This replaces analytics_endpoints.py with proper architecture.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional, Any
from uuid import UUID
import asyncpg
from database.connection import get_db_pool

# DDD imports
from ddd_refactored.infrastructure.repositories import PostgresAnalyticsRepository
from ddd_refactored.application.services import AnalyticsManagementService
from ddd_refactored.domain.analytics_audit.exceptions import (
    AnalyticsCalculationError,
    StoreNotFoundError,
    InvalidDateRangeError
)

router = APIRouter(prefix="/api/v2/analytics", tags=["Analytics V2"])


# ========== Dependency Injection ==========

async def get_analytics_service(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> AnalyticsManagementService:
    """
    Dependency injection for AnalyticsManagementService.

    Creates the full dependency chain:
    DB Pool → Repository → Service
    """
    repository = PostgresAnalyticsRepository(db_pool)
    service = AnalyticsManagementService(
        analytics_repo=repository,
        db_pool=db_pool
    )
    return service


# ========== API Endpoints ==========

@router.get("/dashboard")
async def get_dashboard_analytics_v2(
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific stats"),
    store_id: Optional[str] = Query(None, description="Store ID for store-specific stats"),
    period_days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    """
    Get comprehensive dashboard analytics for e-commerce operations.

    **V2 - DDD Architecture:**
    - Uses domain entities (DashboardSnapshot, RevenueMetric, etc.)
    - Repository pattern for data access
    - Application service for orchestration
    - Clean separation of concerns

    **Access levels:**
    - No tenant_id, no store_id: Super admin - all stores across all tenants
    - tenant_id, no store_id: Tenant admin - all stores for that tenant
    - tenant_id and store_id: Store manager - specific store only

    **Returns:**
    - revenue: Total revenue, trends, breakdown
    - orders: Order counts, status distribution, trends
    - inventory: Stock levels, low stock alerts
    - customers: Customer counts, acquisition, retention
    """
    try:
        # Convert string IDs to UUIDs if provided
        store_uuid = UUID(store_id) if store_id else None
        tenant_uuid = UUID(tenant_id) if tenant_id else None

        # Call application service (orchestrates use case)
        dashboard_data = await service.get_dashboard_analytics(
            store_id=store_uuid,
            tenant_id=tenant_uuid,
            period_days=period_days
        )

        return dashboard_data

    except ValueError as e:
        # Invalid UUID format
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except StoreNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AnalyticsCalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics calculation failed: {str(e)}"
        )
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/products")
async def get_product_analytics_v2(
    tenant_id: Optional[str] = Query(None, description="Tenant ID for filtering"),
    store_id: Optional[str] = Query(None, description="Store ID for filtering"),
    period_days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    top_limit: int = Query(10, description="Number of top products to return", ge=1, le=100),
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    """
    Get product performance analytics.

    **Returns:**
    - top_products: Best selling products by revenue
    - low_stock_products: Products below reorder threshold
    - category_performance: Sales by product category
    """
    try:
        store_uuid = UUID(store_id) if store_id else None
        tenant_uuid = UUID(tenant_id) if tenant_id else None

        product_data = await service.get_product_analytics(
            store_id=store_uuid,
            tenant_id=tenant_uuid,
            period_days=period_days,
            top_products_limit=top_limit
        )

        return product_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except AnalyticsCalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product analytics failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/sales-trends")
async def get_sales_trends_v2(
    tenant_id: Optional[str] = Query(None, description="Tenant ID for filtering"),
    store_id: Optional[str] = Query(None, description="Store ID for filtering"),
    period_days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    granularity: str = Query('daily', description="Chart granularity", regex="^(hourly|daily|weekly|monthly)$"),
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    """
    Get sales trend analytics with time-series data.

    **Returns:**
    - revenue_chart: Time-series revenue data
    - sales_by_hour: Hourly distribution (0-23)
    - sales_by_day_of_week: Weekly pattern (Mon-Sun)
    """
    try:
        store_uuid = UUID(store_id) if store_id else None
        tenant_uuid = UUID(tenant_id) if tenant_id else None

        trends_data = await service.get_sales_trends(
            store_id=store_uuid,
            tenant_id=tenant_uuid,
            period_days=period_days,
            granularity=granularity
        )

        return trends_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AnalyticsCalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sales trends failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/dashboard/refresh")
async def refresh_dashboard_v2(
    store_id: str = Query(..., description="Store ID to refresh"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID for context"),
    triggered_by: Optional[str] = Query(None, description="User ID who triggered refresh"),
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    """
    Manually refresh dashboard analytics.

    Forces recalculation of all metrics and publishes refresh event.
    Useful for:
    - Manual cache invalidation
    - Real-time updates after bulk changes
    - Testing/debugging analytics

    **Returns:**
    - Fresh dashboard data
    - Refresh metadata (timestamp, triggered_by, etc.)
    """
    try:
        store_uuid = UUID(store_id)
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        user_uuid = UUID(triggered_by) if triggered_by else None

        refreshed_data = await service.refresh_dashboard(
            store_id=store_uuid,
            triggered_by=user_uuid,
            tenant_id=tenant_uuid
        )

        return {
            'status': 'success',
            'message': 'Dashboard refreshed successfully',
            'data': refreshed_data
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except AnalyticsCalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/comparison")
async def compare_periods_v2(
    store_id: str = Query(..., description="Store ID"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID for context"),
    period_days: int = Query(30, description="Length of periods to compare", ge=1, le=365),
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    """
    Compare current period with previous period.

    **Returns:**
    - current_period: Metrics for current period
    - previous_period: Metrics for comparison period
    - Changes: Absolute and percentage changes
    - Trends: Direction indicators (up/down/stable)

    Useful for:
    - Period-over-period growth analysis
    - Trend identification
    - Performance tracking
    """
    try:
        store_uuid = UUID(store_id)
        tenant_uuid = UUID(tenant_id) if tenant_id else None

        comparison_data = await service.compare_periods(
            store_id=store_uuid,
            current_period_days=period_days,
            tenant_id=tenant_uuid
        )

        return comparison_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except AnalyticsCalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/health")
async def analytics_health_check():
    """
    Health check endpoint for analytics service.

    Returns service status and version information.
    """
    return {
        'status': 'healthy',
        'service': 'analytics-v2',
        'architecture': 'domain-driven-design',
        'version': '2.0.0',
        'features': [
            'dashboard_analytics',
            'product_analytics',
            'sales_trends',
            'period_comparison',
            'manual_refresh'
        ]
    }
