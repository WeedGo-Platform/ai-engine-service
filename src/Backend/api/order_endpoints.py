"""
Order Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
import logging
import asyncpg

from services.order_service import OrderService
from services.delivery.delivery_service import DeliveryService
from services.delivery.repository import DeliveryRepository
from services.delivery.tracking_service import TrackingService
from services.delivery.assignment_service import AssignmentService
from services.delivery.eta_service import ETAService
from database.connection import get_db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])


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


async def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> Optional[UUID]:
    """Extract user ID from authorization header (simplified)"""
    # In production, would validate JWT token and extract user ID
    return None


@router.post("/create")
async def create_order(
    request: CreateOrderRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a new order from cart"""
    try:
        user_id = await get_user_id_from_header(authorization)
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
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
async def get_order(order_id: UUID):
    """Get order details by ID"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            order = await service.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-number/{order_number}")
async def get_order_by_number(order_number: str):
    """Get order details by order number"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            order = await service.get_order_by_number(order_number)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order by number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    request: UpdateOrderStatusRequest
):
    """Update order status and create delivery if needed"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)

            # First, get the order details
            order = await service.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Update the order status
            success = await service.update_order_status(
                order_id=order_id,
                payment_status=request.payment_status,
                delivery_status=request.delivery_status,
                notes=request.notes
            )

            if not success:
                raise HTTPException(status_code=400, detail="Failed to update order status")

            # If status changed to out_for_delivery, create a delivery
            if request.delivery_status == "out_for_delivery":
                try:
                    # Initialize delivery services
                    repo = DeliveryRepository(conn)
                    tracking_service = TrackingService(conn)
                    assignment_service = AssignmentService(conn)
                    eta_service = ETAService()

                    delivery_service = DeliveryService(
                        repository=repo,
                        tracking_service=tracking_service,
                        assignment_service=assignment_service,
                        eta_service=eta_service
                    )

                    # Create delivery from order
                    delivery = await delivery_service.create_delivery(
                        order_id=str(order_id),
                        customer_name=f"{order.get('customer_first_name', 'Customer')} {order.get('customer_last_name', '')}".strip(),
                        customer_phone=order.get('customer_phone', ''),
                        delivery_address={
                            'street': order.get('delivery_street', ''),
                            'city': order.get('delivery_city', 'Toronto'),
                            'state': order.get('delivery_province', 'ON'),
                            'postal_code': order.get('delivery_postal_code', ''),
                            'location': {
                                'latitude': order.get('delivery_latitude', 43.6532),
                                'longitude': order.get('delivery_longitude', -79.3832)
                            }
                        },
                        items=[]  # Items can be added if needed
                    )

                    # Update order with delivery ID
                    await conn.execute(
                        """
                        UPDATE orders
                        SET delivery_id = $1, updated_at = NOW()
                        WHERE id = $2
                        """,
                        delivery.id,
                        order_id
                    )

                    logger.info(f"Created delivery {delivery.id} for order {order_id}")

                except Exception as e:
                    logger.error(f"Failed to create delivery for order {order_id}: {str(e)}")
                    # Don't fail the whole request if delivery creation fails
                    # The order status is already updated

            return {"success": True, "message": "Order status updated successfully", "delivery_created": request.delivery_status == "out_for_delivery"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    request: CancelOrderRequest
):
    """Cancel an order"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            success = await service.cancel_order(order_id, request.reason)

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot cancel order - may be already delivered or cancelled"
                )

            return {"success": True, "message": "Order cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_orders(
    user_id: Optional[UUID] = Query(None),
    payment_status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed|cancelled)$"),
    delivery_status: Optional[str] = Query(None, pattern="^(pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List orders with filters"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            orders = await service.list_orders(
                user_id=user_id,
                payment_status=payment_status,
                delivery_status=delivery_status,
                limit=limit,
                offset=offset
            )

            return {
                "count": len(orders),
                "orders": orders,
                "data": orders  # For compatibility with dashboard
            }
    except asyncpg.UndefinedTableError:
        # Table doesn't exist yet - return empty result
        logger.warning("Orders table does not exist yet")
        return {
            "count": 0,
            "orders": [],
            "data": []
        }
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        # Check if it's a database connection error
        if "connection" in str(e).lower() or "database" in str(e).lower():
            return {
                "count": 0,
                "orders": [],
                "data": [],
                "error": "Database connection issue"
            }
        # Return empty list with error for other issues
        return {
            "count": 0,
            "orders": [],
            "data": [],
            "error": str(e)
        }


@router.get("/{order_id}/history")
async def get_order_history(order_id: UUID):
    """Get order status change history"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
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
    end_date: Optional[datetime] = Query(None)
):
    """Get order analytics and statistics"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            analytics = await service.get_order_analytics(
                start_date=start_date,
                end_date=end_date
            )
            return analytics
    except Exception as e:
        logger.error(f"Error getting order analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/payment")
async def payment_webhook(payload: Dict[str, Any]):
    """Webhook endpoint for payment updates"""
    try:
        # Process payment webhook (simplified)
        order_id = payload.get('order_id')
        payment_status = payload.get('status')

        if not order_id or not payment_status:
            raise HTTPException(status_code=400, detail="Missing required fields")

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            await service.update_order_status(
                order_id=UUID(order_id),
                payment_status=payment_status,
                notes=f"Payment webhook: {payment_status}"
            )

        return {"success": True, "message": "Webhook processed"}
    except Exception as e:
        logger.error(f"Error processing payment webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))