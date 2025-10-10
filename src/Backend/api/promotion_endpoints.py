"""
Promotion and Pricing API Endpoints (V1 - Legacy)

⚠️ MIGRATION NOTICE:
This is the V1 Promotion & Pricing API. A new V2 API is available with improved DDD architecture.

**V2 Features:**
- Full Domain-Driven Design implementation
- Advanced pricing strategies (cost-plus, competitive, dynamic, tiered)
- Bulk/volume discounts with multi-tier configuration
- Time-based pricing schedules (happy hour, weekend specials)
- Promotional campaigns with BOGO support
- Discount code generation and tracking
- Customer segmentation and targeting
- Promotion stacking controls
- Usage limits and analytics
- Domain events for audit trails

**Migration Path:**
1. V1 endpoints remain functional for backward compatibility
2. New features will only be added to V2
3. V2 API available at `/api/v2/pricing-promotions/*`
4. Recommended to migrate to V2 for new integrations

**V2 Endpoints:**

Pricing Rules:
- POST /api/v2/pricing-promotions/pricing-rules - Create pricing rule
- GET /api/v2/pricing-promotions/pricing-rules/{id} - Get pricing rule
- POST /api/v2/pricing-promotions/pricing-rules/{id}/products - Add product price
- PUT /api/v2/pricing-promotions/pricing-rules/{id}/products/{sku} - Update product price
- POST /api/v2/pricing-promotions/pricing-rules/{id}/products/{sku}/bulk-discount - Add bulk discount
- POST /api/v2/pricing-promotions/pricing-rules/{id}/products/{sku}/schedule - Add price schedule

Promotions:
- POST /api/v2/pricing-promotions/promotions - Create promotion
- GET /api/v2/pricing-promotions/promotions/{id} - Get promotion
- POST /api/v2/pricing-promotions/promotions/{id}/status - Update promotion status
- POST /api/v2/pricing-promotions/promotions/{id}/discount-codes - Generate discount code
- POST /api/v2/pricing-promotions/promotions/{id}/apply-code - Apply discount code
- POST /api/v2/pricing-promotions/promotions/{id}/calculate - Calculate discount

For details, see: /docs (search for "Pricing & Promotions V2")
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
import logging
import asyncpg
import os

from services.promotion_service import PromotionService
from services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/promotions", tags=["promotions"])

# Database connection pool
db_pool = None


async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_promotion_service():
    """Get promotion service instance"""
    pool = await get_db_pool()
    return PromotionService(pool)


async def get_recommendation_service():
    """Get recommendation service instance"""
    pool = await get_db_pool()
    return RecommendationService(pool)


# Request/Response Models
class PromotionCreate(BaseModel):
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str  # 'percentage', 'fixed_amount', 'bogo', 'bundle', 'tiered'
    discount_type: str  # 'percentage' or 'amount'
    discount_value: float
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    usage_limit_per_customer: Optional[int] = None
    total_usage_limit: Optional[int] = None
    applies_to: str = 'all'  # 'all', 'category', 'brand', 'products'
    category_ids: List[str] = []
    brand_ids: List[str] = []
    product_ids: List[str] = []
    stackable: bool = False
    priority: int = 0
    start_date: datetime
    end_date: Optional[datetime] = None
    active: bool = True
    day_of_week: Optional[List[int]] = None
    hour_of_day: Optional[List[int]] = None
    first_time_customer_only: bool = False

    # NEW FIELDS - Enhanced Promotion System
    store_id: Optional[UUID] = Field(None, description="Limit promotion to specific store")
    tenant_id: Optional[UUID] = Field(None, description="Limit promotion to specific tenant")
    is_continuous: bool = Field(False, description="If true, promotion runs indefinitely")
    recurrence_type: str = Field('none', description="Recurrence pattern: none, daily, weekly")
    time_start: Optional[str] = Field(None, description="Daily start time (HH:MM:SS format)")
    time_end: Optional[str] = Field(None, description="Daily end time (HH:MM:SS format)")
    timezone: str = Field('America/Toronto', description="IANA timezone for time windows")


class ValidateCodeRequest(BaseModel):
    code: str
    tenant_id: Optional[UUID] = None


class PriceCalculationRequest(BaseModel):
    product_id: str
    quantity: int
    tenant_id: Optional[UUID] = None


class CartDiscountRequest(BaseModel):
    items: List[Dict[str, Any]]
    tenant_id: Optional[UUID] = None
    discount_codes: Optional[List[str]] = None


class TierAssignmentRequest(BaseModel):
    tenant_id: UUID
    tier_id: UUID
    custom_markup_percentage: Optional[float] = None
    volume_discounts: Optional[Dict[str, float]] = None


# PROMOTION ENDPOINTS

@router.get("/active")
async def get_active_promotions(
    category: Optional[str] = None,
    service: PromotionService = Depends(get_promotion_service)
):
    """Get all currently active promotions"""
    try:
        promotions = await service.get_applicable_promotions(
            categories=[category] if category else None
        )
        return {"promotions": promotions}
    except Exception as e:
        logger.error(f"Error getting active promotions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_promotion(
    promotion: PromotionCreate,
    created_by_user_id: Optional[UUID] = None,
    user_role: Optional[str] = Query(None, description="User role: platform_admin, tenant_admin, store_manager"),
    service: PromotionService = Depends(get_promotion_service)
):
    """
    Create a new promotion with enhanced fields.

    **Permission Levels:**
    - `platform_admin`: Can create any type of promotion
    - `tenant_admin`: Must specify tenant_id
    - `store_manager`: Must specify store_id, cannot specify tenant_id

    **New Features:**
    - Continuous promotions (no end date)
    - Recurring schedules (daily/weekly with time windows)
    - Store/tenant scoping
    - Timezone support
    """
    try:
        result = await service.create_promotion(
            promotion_data=promotion.dict(),
            created_by_user_id=created_by_user_id,
            user_role=user_role
        )
        return {"success": True, "promotion": result}
    except ValueError as e:
        logger.warning(f"Validation error creating promotion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission error creating promotion: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating promotion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-code")
async def validate_discount_code(
    request: ValidateCodeRequest,
    service: PromotionService = Depends(get_promotion_service)
):
    """Validate a discount code"""
    try:
        result = await service.validate_discount_code(
            request.code,
            request.tenant_id
        )
        return result
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-price")
async def calculate_product_price(
    request: PriceCalculationRequest,
    service: PromotionService = Depends(get_promotion_service)
):
    """Calculate final price for a product with all discounts"""
    try:
        result = await service.calculate_product_price(
            request.product_id,
            request.quantity,
            request.tenant_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cart-discounts")
async def calculate_cart_discounts(
    request: CartDiscountRequest,
    service: PromotionService = Depends(get_promotion_service)
):
    """Calculate all discounts for a shopping cart"""
    try:
        result = await service.calculate_cart_discounts(
            request.items,
            request.tenant_id,
            request.discount_codes
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating cart discounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bundles")
async def get_bundle_deals(
    active_only: bool = True,
    service: PromotionService = Depends(get_promotion_service)
):
    """Get available bundle deals"""
    try:
        bundles = await service.get_bundle_deals(active_only)
        return {"bundles": bundles}
    except Exception as e:
        logger.error(f"Error getting bundles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers")
async def get_price_tiers(
    service: PromotionService = Depends(get_promotion_service)
):
    """Get all price tiers"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            tiers = await conn.fetch("""
                SELECT * FROM price_tiers 
                WHERE active = true 
                ORDER BY priority
            """)
            return {"tiers": [dict(t) for t in tiers]}
    except Exception as e:
        logger.error(f"Error getting price tiers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer-tier/{tenant_id}")
async def get_customer_tier(
    tenant_id: UUID,
    service: PromotionService = Depends(get_promotion_service)
):
    """Get customer's current price tier"""
    try:
        tier = await service.get_customer_tier(tenant_id)
        return {"tier": tier}
    except Exception as e:
        logger.error(f"Error getting customer tier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-tier")
async def assign_price_tier(
    request: TierAssignmentRequest,
    service: PromotionService = Depends(get_promotion_service)
):
    """Assign a price tier to a customer"""
    try:
        await service.update_price_tier_assignment(
            request.tenant_id,
            request.tier_id,
            {
                'custom_markup_percentage': request.custom_markup_percentage,
                'volume_discounts': request.volume_discounts
            }
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Error assigning tier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_all_promotions(
    tenant_id: Optional[UUID] = Query(None),
    store_id: Optional[UUID] = Query(None),
    active_only: bool = Query(False),
    service: PromotionService = Depends(get_promotion_service)
):
    """List all promotions with optional filtering by tenant/store"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM promotions WHERE 1=1"
            params = []

            if active_only:
                query += " AND active = $" + str(len(params) + 1)
                params.append(True)

            if tenant_id:
                query += " AND tenant_id = $" + str(len(params) + 1)
                params.append(tenant_id)

            if store_id:
                query += " AND store_id = $" + str(len(params) + 1)
                params.append(store_id)

            query += " ORDER BY created_at DESC"

            promotions = await conn.fetch(query, *params)
            return {"promotions": [dict(p) for p in promotions]}
    except Exception as e:
        logger.error(f"Error listing promotions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_promotion_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: PromotionService = Depends(get_promotion_service)
):
    """Get analytics on promotion performance"""
    try:
        analytics = await service.get_promotion_analytics(start_date, end_date)
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{promotion_id}")
async def get_promotion(
    promotion_id: UUID,
    service: PromotionService = Depends(get_promotion_service)
):
    """Get a single promotion by ID"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            promo = await conn.fetchrow(
                "SELECT * FROM promotions WHERE id = $1",
                promotion_id
            )
            if not promo:
                raise HTTPException(status_code=404, detail="Promotion not found")
            return {"promotion": dict(promo)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting promotion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{promotion_id}")
async def update_promotion(
    promotion_id: UUID,
    promotion: PromotionCreate,
    user_role: Optional[str] = Query(None),
    service: PromotionService = Depends(get_promotion_service)
):
    """Update an existing promotion"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if promotion exists
            existing = await conn.fetchrow(
                "SELECT * FROM promotions WHERE id = $1",
                promotion_id
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Promotion not found")

            # Parse and convert dates/times (same logic as create)
            from datetime import time as time_type

            start_date = promotion.start_date
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if start_date.tzinfo is not None:
                    start_date = start_date.replace(tzinfo=None)

            end_date = promotion.end_date
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if end_date.tzinfo is not None:
                        end_date = end_date.replace(tzinfo=None)

            time_start = promotion.time_start
            if time_start and isinstance(time_start, str):
                parts = time_start.split(':')
                time_start = time_type(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

            time_end = promotion.time_end
            if time_end and isinstance(time_end, str):
                parts = time_end.split(':')
                time_end = time_type(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

            # Update promotion
            updated = await conn.fetchrow("""
                UPDATE promotions SET
                    code = $1, name = $2, description = $3, type = $4,
                    discount_type = $5, discount_value = $6,
                    min_purchase_amount = $7, max_discount_amount = $8,
                    usage_limit_per_customer = $9, total_usage_limit = $10,
                    applies_to = $11, category_ids = $12, brand_ids = $13,
                    product_ids = $14, stackable = $15, priority = $16,
                    start_date = $17, end_date = $18, active = $19,
                    day_of_week = $20, hour_of_day = $21,
                    first_time_customer_only = $22, store_id = $23,
                    tenant_id = $24, is_continuous = $25,
                    recurrence_type = $26, time_start = $27, time_end = $28,
                    timezone = $29, updated_at = NOW()
                WHERE id = $30
                RETURNING *
            """,
                promotion.code, promotion.name, promotion.description, promotion.type,
                promotion.discount_type, promotion.discount_value,
                promotion.min_purchase_amount, promotion.max_discount_amount,
                promotion.usage_limit_per_customer, promotion.total_usage_limit,
                promotion.applies_to, promotion.category_ids, promotion.brand_ids,
                promotion.product_ids, promotion.stackable, promotion.priority,
                start_date, end_date, promotion.active,
                promotion.day_of_week, promotion.hour_of_day,
                promotion.first_time_customer_only, promotion.store_id,
                promotion.tenant_id, promotion.is_continuous,
                promotion.recurrence_type, time_start, time_end,
                promotion.timezone, promotion_id
            )

            return {"success": True, "promotion": dict(updated)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating promotion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{promotion_id}")
async def delete_promotion(
    promotion_id: UUID,
    service: PromotionService = Depends(get_promotion_service)
):
    """Delete a promotion"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM promotions WHERE id = $1",
                promotion_id
            )
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Promotion not found")
            return {"success": True, "message": "Promotion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting promotion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# RECOMMENDATION ENDPOINTS

@router.get("/recommendations/similar/{product_id}")
async def get_similar_products(
    product_id: str,
    store_id: str = Query(..., description="Store ID to check inventory"),
    limit: int = Query(5, ge=1, le=20),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get products similar to the given product that are in stock at the specified store"""
    try:
        products = await service.get_similar_products(product_id, store_id, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting similar products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/complementary/{product_id}")
async def get_complementary_products(
    product_id: str,
    store_id: str = Query(..., description="Store ID to check inventory"),
    limit: int = Query(5, ge=1, le=20),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get products that complement the given product and are in stock at the specified store"""
    try:
        products = await service.get_complementary_products(product_id, store_id, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting complementary products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/trending")
async def get_trending_products(
    store_id: str = Query(..., description="Store ID to check inventory"),
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get trending products that are in stock at the specified store"""
    try:
        products = await service.get_trending_products(store_id, category, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting trending products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/personalized/{tenant_id}")
async def get_personalized_recommendations(
    tenant_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get personalized recommendations for a customer"""
    try:
        products = await service.get_personalized_recommendations(tenant_id, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/upsell/{product_id}")
async def get_upsell_products(
    product_id: str,
    store_id: str = Query(..., description="Store ID to check inventory"),
    limit: int = Query(3, ge=1, le=10),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get upsell recommendations for a product that are in stock at the specified store"""
    try:
        products = await service.get_upsell_products(product_id, store_id, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting upsell products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/frequently-bought/{product_id}")
async def get_frequently_bought_together(
    product_id: str,
    store_id: str = Query(..., description="Store ID to check inventory"),
    limit: int = Query(3, ge=1, le=10),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get products frequently bought with the given product that are in stock at the specified store"""
    try:
        products = await service.get_frequently_bought_together(product_id, store_id, limit)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting frequently bought products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/analytics")
async def get_recommendation_analytics(
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Get analytics on recommendation performance"""
    try:
        analytics = await service.get_recommendation_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting recommendation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))