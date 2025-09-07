"""
Order Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from services.order_service import OrderService
from services.database_connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])

# Get database connection
db_manager = DatabaseConnectionManager()


# Pydantic Models
class DeliveryAddress(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    instructions: Optional[str] = None


class CreateOrderRequest(BaseModel):
    cart_session_id: UUID
    payment_method: str = Field(default="cash", pattern="^(cash|credit|debit|etransfer)$")
    delivery_address: DeliveryAddress
    special_instructions: Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    payment_status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed|cancelled)$")
    delivery_status: Optional[str] = Field(None, pattern="^(pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled)$")
    notes: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: str


async def get_order_service():
    """Get order service instance"""
    conn = await db_manager.get_connection()
    return OrderService(conn)


async def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> Optional[UUID]:
    """Extract user ID from authorization header (simplified)"""
    # In production, would validate JWT token and extract user ID
    return None


@router.post("/create")
async def create_order(
    request: CreateOrderRequest,
    user_id: Optional[UUID] = Depends(get_user_id_from_header),
    service: OrderService = Depends(get_order_service)
):
    """Create a new order from cart"""
    try:
        result = await service.create_order(
            cart_session_id=request.cart_session_id,
            user_id=user_id,
            payment_method=request.payment_method,
            delivery_address=request.delivery_address.dict(),
            special_instructions=request.special_instructions
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    service: OrderService = Depends(get_order_service)
):
    """Get order details by ID"""
    try:
        order = await service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-number/{order_number}")
async def get_order_by_number(
    order_number: str,
    service: OrderService = Depends(get_order_service)
):
    """Get order details by order number"""
    try:
        order = await service.get_order_by_number(order_number)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        logger.error(f"Error getting order by number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    request: UpdateOrderStatusRequest,
    service: OrderService = Depends(get_order_service)
):
    """Update order status"""
    try:
        success = await service.update_order_status(
            order_id=order_id,
            payment_status=request.payment_status,
            delivery_status=request.delivery_status,
            notes=request.notes
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update order status")
        
        return {"success": True, "message": "Order status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    request: CancelOrderRequest,
    service: OrderService = Depends(get_order_service)
):
    """Cancel an order"""
    try:
        success = await service.cancel_order(order_id, request.reason)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Cannot cancel order - may be already delivered or cancelled"
            )
        
        return {"success": True, "message": "Order cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_orders(
    user_id: Optional[UUID] = Query(None),
    payment_status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed|cancelled)$"),
    delivery_status: Optional[str] = Query(None, pattern="^(pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: OrderService = Depends(get_order_service)
):
    """List orders with filters"""
    try:
        orders = await service.list_orders(
            user_id=user_id,
            payment_status=payment_status,
            delivery_status=delivery_status,
            limit=limit,
            offset=offset
        )
        
        return {
            "count": len(orders),
            "orders": orders
        }
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/history")
async def get_order_history(
    order_id: UUID,
    service: OrderService = Depends(get_order_service)
):
    """Get order status change history"""
    try:
        history = await service.get_order_status_history(order_id)
        
        return {
            "order_id": str(order_id),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting order history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_order_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: OrderService = Depends(get_order_service)
):
    """Get order analytics and statistics"""
    try:
        analytics = await service.get_order_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting order analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/payment")
async def payment_webhook(
    payload: Dict[str, Any],
    service: OrderService = Depends(get_order_service)
):
    """Webhook endpoint for payment updates"""
    try:
        # Process payment webhook (simplified)
        order_id = payload.get('order_id')
        payment_status = payload.get('status')
        
        if not order_id or not payment_status:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        await service.update_order_status(
            order_id=UUID(order_id),
            payment_status=payment_status,
            notes=f"Payment webhook: {payment_status}"
        )
        
        return {"success": True, "message": "Webhook processed"}
    except Exception as e:
        logger.error(f"Error processing payment webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))