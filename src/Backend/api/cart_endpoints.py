"""
Cart Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from services.cart_service import CartService
from services.promotion_service import PromotionService
from services.recommendation_service import RecommendationService
import asyncpg
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cart", tags=["cart"])

# Database connection pool
db_pool = None


# Pydantic Models
class AddItemRequest(BaseModel):
    sku: str
    name: str
    category: str
    price: float = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    image_url: Optional[str] = None
    store_id: Optional[str] = None  # Store ID for inventory filtering and promotion validation


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(ge=0)


class ApplyDiscountRequest(BaseModel):
    discount_code: Optional[str] = None
    promo_code: Optional[str] = None  # Mobile app compatibility

    def get_code(self) -> str:
        """Get the code regardless of which field was used"""
        return self.promo_code or self.discount_code or ""

    def model_post_init(self, __context):
        """Validate that at least one code is provided"""
        if not self.discount_code and not self.promo_code:
            raise ValueError("Either discount_code or promo_code must be provided")


class DeliveryAddressRequest(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    instructions: Optional[str] = None


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


async def get_cart_service():
    """Get cart service instance"""
    pool = await get_db_pool()
    # Don't inject promotion_service here - we'll pass it at the endpoint level
    return CartService(pool)


async def get_recommendation_service():
    """Get recommendation service instance"""
    pool = await get_db_pool()
    return RecommendationService(pool)


async def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Extract session ID from header"""
    if not x_session_id:
        # Generate a new session ID if not provided
        import uuid
        return str(uuid.uuid4())
    return x_session_id


async def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> Optional[UUID]:
    """Extract user ID from authorization header (simplified)"""
    # In production, would validate JWT token and extract user ID
    return None


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any], include_in_schema=False)
async def get_cart(
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    service: CartService = Depends(get_cart_service)
):
    """Get current cart for session"""
    try:
        cart = await service.get_cart_summary(session_id)
        return cart
    except Exception as e:
        logger.error(f"Error getting cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items")
async def add_item_to_cart(
    request: AddItemRequest,
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    service: CartService = Depends(get_cart_service)
):
    """Add item to cart"""
    try:
        # Extract store_id from request if provided
        store_id = UUID(request.store_id) if request.store_id else None

        result = await service.add_item(
            session_id=session_id,
            product=request.dict(),
            quantity=request.quantity,
            store_id=store_id,
            tenant_id=user_id  # Use user_id as tenant_id
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{item_id}")
async def update_item_quantity(
    item_id: str,
    request: UpdateQuantityRequest,
    session_id: str = Depends(get_session_id),
    service: CartService = Depends(get_cart_service)
):
    """Update quantity of item in cart"""
    try:
        result = await service.update_item_quantity(
            session_id=session_id,
            item_id=item_id,
            quantity=request.quantity
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating item quantity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{item_id}")
async def remove_item_from_cart(
    item_id: str,
    session_id: str = Depends(get_session_id),
    service: CartService = Depends(get_cart_service)
):
    """Remove item from cart"""
    try:
        result = await service.remove_item(session_id, item_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def clear_cart(
    session_id: str = Depends(get_session_id),
    service: CartService = Depends(get_cart_service)
):
    """Clear all items from cart"""
    try:
        success = await service.clear_cart(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to clear cart")
        
        return {"success": True, "message": "Cart cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discount")
async def apply_discount(
    request: ApplyDiscountRequest,
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    cart_service: CartService = Depends(get_cart_service),
    promo_service: PromotionService = Depends(get_promotion_service)
):
    """Apply discount code to cart with promotion validation"""
    try:
        # Get the code from either field
        code = request.get_code()
        if not code:
            raise ValueError("Please enter a promo code")

        # Use tenant_id from header if user_id is not available (guest users)
        effective_tenant_id = user_id or (UUID(tenant_id) if tenant_id else None)

        # Debug logging
        logger.info(f"Applying promo code: {code}, session_id: {session_id}, store_id: {store_id}, user_id: {user_id}, tenant_id: {tenant_id}, effective_tenant_id: {effective_tenant_id}")

        # Inject promotion service into cart service for this request
        cart_service.promotion_service = promo_service

        # Update cart with store/tenant IDs if missing
        if store_id or effective_tenant_id:
            updated = await cart_service.update_cart_context(
                session_id=session_id,
                store_id=UUID(store_id) if store_id else None,
                tenant_id=effective_tenant_id
            )
            logger.info(f"Cart context updated: {updated}")

        # Apply the discount to the cart (cart service will handle validation)
        result = await cart_service.apply_discount(
            session_id=session_id,
            discount_code=code
        )

        return result
    except ValueError as e:
        # Return user-friendly error message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying discount: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to apply promo code. Please try again.")


@router.post("/promo")
async def apply_promo(
    request: ApplyDiscountRequest,
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    cart_service: CartService = Depends(get_cart_service),
    promo_service: PromotionService = Depends(get_promotion_service)
):
    """Apply promo code to cart (alias for /discount endpoint for mobile app compatibility)"""
    logger.info(f"/promo endpoint called - session_id: {session_id}, store_id: {store_id}, user_id: {user_id}, tenant_id: {tenant_id}")
    # Delegate to the discount endpoint
    return await apply_discount(request, session_id, user_id, store_id, tenant_id, cart_service, promo_service)


@router.delete("/promo")
async def remove_promo(
    session_id: str = Depends(get_session_id),
    cart_service: CartService = Depends(get_cart_service)
):
    """Remove promo code from cart"""
    try:
        logger.info(f"Removing promo code for session: {session_id}")
        # Remove discount from cart
        result = await cart_service.remove_discount(session_id)
        logger.info(f"Promo code removed successfully. New total: {result.get('total_amount')}")
        return {
            "success": True,
            "message": "Promo code removed successfully",
            "cart": result
        }
    except Exception as e:
        logger.error(f"Error removing promo code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discounts")
async def calculate_cart_discounts(
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    cart_service: CartService = Depends(get_cart_service),
    promo_service: PromotionService = Depends(get_promotion_service)
):
    """Calculate all applicable discounts for the current cart"""
    try:
        # Get current cart
        cart = await cart_service.get_cart_summary(session_id)

        if not cart['items']:
            return {
                "subtotal": 0,
                "total_discount": 0,
                "final_total": 0,
                "applied_promotions": []
            }

        # Calculate discounts using promotion service
        discount_details = await promo_service.calculate_cart_discounts(
            cart_items=cart['items'],
            tenant_id=user_id,
            discount_codes=cart.get('discount_codes', [])
        )

        return discount_details
    except Exception as e:
        logger.error(f"Error calculating cart discounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/delivery-address")
async def update_delivery_address(
    request: DeliveryAddressRequest,
    session_id: str = Depends(get_session_id),
    service: CartService = Depends(get_cart_service)
):
    """Update delivery address and recalculate delivery fee"""
    try:
        success = await service.update_delivery_address(
            session_id=session_id,
            delivery_address=request.dict()
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update delivery address")
        
        # Return updated cart
        cart = await service.get_cart_summary(session_id)
        return cart
    except Exception as e:
        logger.error(f"Error updating delivery address: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge")
async def merge_carts(
    guest_session_id: str,
    user_id: UUID,
    service: CartService = Depends(get_cart_service)
):
    """Merge guest cart with user cart when user logs in"""
    try:
        merged_cart = await service.merge_carts(
            guest_session_id=guest_session_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": "Carts merged successfully",
            "cart": merged_cart
        }
    except Exception as e:
        logger.error(f"Error merging carts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_cart(
    session_id: str = Depends(get_session_id),
    service: CartService = Depends(get_cart_service)
):
    """Validate cart items are in stock and prices are current"""
    try:
        cart = await service.get_cart_summary(session_id)
        
        # Check if all items are in stock
        all_in_stock = all(item.get('in_stock', True) for item in cart['items'])
        has_items = len(cart['items']) > 0
        
        validation = {
            "valid": all_in_stock and has_items,
            "has_items": has_items,
            "all_in_stock": all_in_stock,
            "total_amount": cart['total_amount'],
            "issues": []
        }
        
        if not has_items:
            validation['issues'].append("Cart is empty")
        
        for item in cart['items']:
            if not item.get('in_stock', True):
                validation['issues'].append(f"{item['name']} is out of stock")
        
        return validation
    except Exception as e:
        logger.error(f"Error validating cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_cart_recommendations(
    session_id: str = Depends(get_session_id),
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    cart_service: CartService = Depends(get_cart_service),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """Get product recommendations based on cart items"""
    try:
        # Get current cart
        cart = await cart_service.get_cart_summary(session_id)
        
        if not cart['items']:
            # If cart is empty, return trending products
            trending = await rec_service.get_trending_products(limit=6)
            return {
                "type": "trending",
                "products": trending
            }
        
        # Get recommendations based on cart items
        recommendations = {
            "complementary": [],
            "frequently_bought": [],
            "upsell": []
        }
        
        # Get complementary products for first few items
        for item in cart['items'][:2]:
            complementary = await rec_service.get_complementary_products(
                item['sku'], 
                limit=3
            )
            recommendations['complementary'].extend(complementary)
        
        # Get frequently bought together for most expensive item
        expensive_item = max(cart['items'], key=lambda x: x.get('price', 0))
        frequently = await rec_service.get_frequently_bought_together(
            expensive_item['sku'],
            limit=3
        )
        recommendations['frequently_bought'] = frequently
        
        # Get upsell products for cheapest item
        cheapest_item = min(cart['items'], key=lambda x: x.get('price', float('inf')))
        upsell = await rec_service.get_upsell_products(
            cheapest_item['sku'],
            limit=2
        )
        recommendations['upsell'] = upsell
        
        return recommendations
    except Exception as e:
        logger.error(f"Error getting cart recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_carts(
    service: CartService = Depends(get_cart_service)
):
    """Clean up expired cart sessions (admin endpoint)"""
    try:
        count = await service.cleanup_expired_carts()
        
        return {
            "success": True,
            "message": f"Cleaned up {count} expired carts"
        }
    except Exception as e:
        logger.error(f"Error cleaning up carts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))