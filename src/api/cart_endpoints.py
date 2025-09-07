"""
Cart Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from services.cart_service import CartService
from services.database_connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cart", tags=["cart"])

# Get database connection
db_manager = DatabaseConnectionManager()


# Pydantic Models
class AddItemRequest(BaseModel):
    sku: str
    name: str
    category: str
    price: float = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    image_url: Optional[str] = None


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(ge=0)


class ApplyDiscountRequest(BaseModel):
    discount_code: str


class DeliveryAddressRequest(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    instructions: Optional[str] = None


async def get_cart_service():
    """Get cart service instance"""
    conn = await db_manager.get_connection()
    return CartService(conn)


async def get_session_id(x_session_id: str = Header(...)) -> str:
    """Extract session ID from header"""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    return x_session_id


async def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> Optional[UUID]:
    """Extract user ID from authorization header (simplified)"""
    # In production, would validate JWT token and extract user ID
    return None


@router.get("/")
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
    service: CartService = Depends(get_cart_service)
):
    """Add item to cart"""
    try:
        result = await service.add_item(
            session_id=session_id,
            product=request.dict(),
            quantity=request.quantity
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
    service: CartService = Depends(get_cart_service)
):
    """Apply discount code to cart"""
    try:
        result = await service.apply_discount(
            session_id=session_id,
            discount_code=request.discount_code
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying discount: {str(e)}")
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