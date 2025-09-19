"""
Wishlist API Endpoints
Handles customer wishlist operations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
import logging
from services.wishlist_service import WishlistService
from database.connection import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


class AddToWishlistRequest(BaseModel):
    """Request model for adding item to wishlist"""
    product_id: UUID
    store_id: UUID
    notes: Optional[str] = None
    priority: int = 0  # 0: normal, 1: high
    notify_on_sale: bool = False
    notify_on_restock: bool = False


class UpdateWishlistItemRequest(BaseModel):
    """Request model for updating wishlist item"""
    notes: Optional[str] = None
    priority: Optional[int] = None
    notify_on_sale: Optional[bool] = None
    notify_on_restock: Optional[bool] = None


class CheckWishlistRequest(BaseModel):
    """Request model for checking products in wishlist"""
    product_ids: List[UUID]
    store_id: UUID


async def get_customer_id(x_customer_id: Optional[str] = Header(None)) -> UUID:
    """Extract customer ID from header"""
    if not x_customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer ID required in header"
        )
    try:
        return UUID(x_customer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID format"
        )


@router.get("/")
async def get_wishlist(
    store_id: Optional[UUID] = None,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Get customer's wishlist items

    Args:
        store_id: Optional store filter
        customer_id: Customer ID from header

    Returns:
        List of wishlist items with product details
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)
        items = await service.get_wishlist(customer_id, store_id)

        return {
            "success": True,
            "count": len(items),
            "items": items
        }

    except Exception as e:
        logger.error(f"Error getting wishlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wishlist: {str(e)}"
        )


@router.post("/add")
async def add_to_wishlist(
    request: AddToWishlistRequest,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Add product to wishlist

    Args:
        request: Product details to add
        customer_id: Customer ID from header

    Returns:
        Added wishlist item details
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        item = await service.add_to_wishlist(
            customer_id=customer_id,
            product_id=request.product_id,
            store_id=request.store_id,
            notes=request.notes,
            priority=request.priority
        )

        # Update notification preferences if provided
        if request.notify_on_sale or request.notify_on_restock:
            await service.update_wishlist_item(
                customer_id=customer_id,
                product_id=request.product_id,
                store_id=request.store_id,
                updates={
                    'notify_on_sale': request.notify_on_sale,
                    'notify_on_restock': request.notify_on_restock
                }
            )

        return {
            "success": True,
            "message": "Product added to wishlist",
            "item": item
        }

    except Exception as e:
        logger.error(f"Error adding to wishlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to wishlist: {str(e)}"
        )


@router.delete("/{product_id}")
async def remove_from_wishlist(
    product_id: UUID,
    store_id: UUID,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Remove product from wishlist

    Args:
        product_id: Product ID to remove
        store_id: Store ID
        customer_id: Customer ID from header

    Returns:
        Success status
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        removed = await service.remove_from_wishlist(
            customer_id=customer_id,
            product_id=product_id,
            store_id=store_id
        )

        if removed:
            return {
                "success": True,
                "message": "Product removed from wishlist"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in wishlist"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from wishlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from wishlist: {str(e)}"
        )


@router.put("/{product_id}")
async def update_wishlist_item(
    product_id: UUID,
    store_id: UUID,
    request: UpdateWishlistItemRequest,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Update wishlist item properties

    Args:
        product_id: Product ID to update
        store_id: Store ID
        request: Update details
        customer_id: Customer ID from header

    Returns:
        Updated wishlist item
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        updates = {k: v for k, v in request.dict().items() if v is not None}

        item = await service.update_wishlist_item(
            customer_id=customer_id,
            product_id=product_id,
            store_id=store_id,
            updates=updates
        )

        return {
            "success": True,
            "message": "Wishlist item updated",
            "item": item
        }

    except Exception as e:
        logger.error(f"Error updating wishlist item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update wishlist item: {str(e)}"
        )


@router.get("/stats")
async def get_wishlist_stats(
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Get wishlist statistics

    Args:
        customer_id: Customer ID from header

    Returns:
        Wishlist statistics including counts and total value
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        stats = await service.get_wishlist_stats(customer_id)

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting wishlist stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wishlist stats: {str(e)}"
        )


@router.post("/check")
async def check_products_in_wishlist(
    request: CheckWishlistRequest,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Check if products are in wishlist

    Args:
        request: Product IDs to check
        customer_id: Customer ID from header

    Returns:
        Dictionary of product IDs and their wishlist status
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        result = await service.check_product_in_wishlist(
            customer_id=customer_id,
            product_ids=request.product_ids,
            store_id=request.store_id
        )

        return {
            "success": True,
            "products": result
        }

    except Exception as e:
        logger.error(f"Error checking wishlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check wishlist: {str(e)}"
        )


@router.delete("/clear/all")
async def clear_wishlist(
    store_id: Optional[UUID] = None,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Clear all wishlist items

    Args:
        store_id: Optional store filter
        customer_id: Customer ID from header

    Returns:
        Number of items cleared
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        count = await service.clear_wishlist(customer_id, store_id)

        return {
            "success": True,
            "message": f"Cleared {count} items from wishlist",
            "count": count
        }

    except Exception as e:
        logger.error(f"Error clearing wishlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear wishlist: {str(e)}"
        )


@router.post("/move-to-cart/{product_id}")
async def move_to_cart(
    product_id: UUID,
    store_id: UUID,
    session_id: str,
    customer_id: UUID = Depends(get_customer_id)
):
    """
    Move item from wishlist to cart

    Args:
        product_id: Product to move
        store_id: Store ID
        session_id: Cart session ID
        customer_id: Customer ID from header

    Returns:
        Success status
    """
    try:
        db_pool = await get_db_pool()
        service = WishlistService(db_pool)

        result = await service.move_to_cart(
            customer_id=customer_id,
            product_id=product_id,
            store_id=store_id,
            session_id=session_id
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error moving to cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move to cart: {str(e)}"
        )