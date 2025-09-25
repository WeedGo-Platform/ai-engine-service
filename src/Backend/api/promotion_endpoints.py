"""
Promotion and Pricing API Endpoints
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
    service: PromotionService = Depends(get_promotion_service)
):
    """Create a new promotion"""
    try:
        result = await service.create_promotion(promotion.dict())
        return {"success": True, "promotion": result}
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