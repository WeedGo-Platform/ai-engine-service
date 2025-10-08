"""
Order Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
import logging
import asyncpg

from services.order_service import OrderService
from services.delivery.delivery_service import DeliveryService
from services.delivery.repository import DeliveryRepository
from services.delivery.tracking_service import TrackingService
from services.delivery.assignment_service import AssignmentService
from services.delivery.eta_service import ETAService
from services.pricing.order_pricing_service import OrderPricingService
from services.inventory import InventoryValidator, InventoryValidationError
from services.cart import CartLockService, CartLockContext
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


class MobileCreateOrderRequest(BaseModel):
    """Order creation request from mobile app"""
    cart_session_id: UUID
    user_id: Optional[UUID] = None
    store_id: UUID
    delivery_type: str = Field(pattern="^(delivery|pickup)$")
    delivery_address: Optional[DeliveryAddress] = None
    pickup_time: Optional[str] = None
    payment_method_id: str  # ID of the payment method
    tip_amount: float = Field(default=0, ge=0)
    special_instructions: Optional[str] = None
    promo_code: Optional[str] = None


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


async def get_payment_method_type(payment_method_id: str, user_id: UUID, conn) -> str:
    """
    Get payment method type from user's profile payment methods (FIXED)

    Args:
        payment_method_id: UUID of the payment method
        user_id: UUID of the user (for ownership validation)
        conn: Database connection

    Returns:
        Payment method type (e.g., 'cash', 'card', 'etransfer')

    Raises:
        HTTPException: If payment method not found or doesn't belong to user
    """
    # Query profiles.payment_methods JSONB (FIXED - was querying wrong table)
    query = """
        SELECT method->>'type' as type
        FROM profiles,
        jsonb_array_elements(COALESCE(payment_methods, '[]'::jsonb)) as method
        WHERE user_id = $1
        AND method->>'id' = $2
        LIMIT 1
    """
    result = await conn.fetchrow(query, user_id, payment_method_id)

    if result and result['type']:
        logger.info(f"Payment method {payment_method_id} validated: {result['type']}")
        return result['type']

    # If not found, it's an error (no more silent fallback to cash)
    logger.error(f"Payment method {payment_method_id} not found for user {user_id}")
    raise HTTPException(
        status_code=400,
        detail=f"Payment method not found or does not belong to user"
    )


@router.post("/", include_in_schema=True)
@router.post("", include_in_schema=False)  # Also handle without trailing slash
async def create_order_mobile(
    request: MobileCreateOrderRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a new order from mobile app"""
    logger.info(f"[ORDER] Starting order creation for cart {request.cart_session_id}")
    try:
        user_id = request.user_id or await get_user_id_from_header(authorization)

        # Validate user_id is present
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required for order creation"
            )

        logger.info(f"[ORDER] User validated: {user_id}")
        pool = await get_db_pool()
        logger.info(f"[ORDER] DB pool acquired")

        async with pool.acquire() as conn:
            logger.info(f"[ORDER] DB connection acquired")
            # CART LOCKING (Prevents concurrent modifications during checkout)
            lock_service = CartLockService(conn)

            try:
                logger.info(f"[ORDER] Attempting to acquire cart lock for {request.cart_session_id}")
                async with CartLockContext(lock_service, request.cart_session_id, timeout=10):
                    logger.info(f"[ORDER] Cart {request.cart_session_id} locked for checkout")

                    # Get payment method type from ID (FIXED - now passes user_id for validation)
                    logger.info(f"[ORDER] Getting payment method type for {request.payment_method_id}")
                    payment_method_type = await get_payment_method_type(
                        request.payment_method_id,
                        user_id,
                        conn
                    )
                    logger.info(f"[ORDER] Payment method type: {payment_method_type}")

                    # SERVER-SIDE PRICE RECALCULATION (Security: prevent price manipulation)
                    logger.info(f"[ORDER] Calculating order totals")
                    pricing_service = OrderPricingService(conn)
                    calculated_pricing = await pricing_service.calculate_order_totals(
                        cart_session_id=request.cart_session_id,
                        delivery_type=request.delivery_type,
                        delivery_address=request.delivery_address.dict() if request.delivery_address else None,
                        promo_code=request.promo_code
                    )

                    logger.info(
                        f"[ORDER] Server-calculated pricing - Subtotal: ${calculated_pricing['subtotal']}, "
                        f"Tax: ${calculated_pricing['tax']}, "
                        f"Delivery: ${calculated_pricing['delivery_fee']}, "
                        f"Total: ${calculated_pricing['total']}"
                    )

                    # INVENTORY VALIDATION AND RESERVATION (Security: prevent overselling)
                    logger.info(f"[ORDER] Validating and reserving inventory")
                    inventory_validator = InventoryValidator(conn)
                    try:
                        validation_result = await inventory_validator.validate_and_reserve(
                            cart_session_id=request.cart_session_id,
                            store_id=request.store_id
                        )
                        logger.info(
                            f"Inventory validated and reserved - "
                            f"{validation_result['items_reserved']} items reserved"
                        )
                    except InventoryValidationError as e:
                        # Return detailed error with unavailable items
                        logger.warning(f"Inventory validation failed: {str(e)}")
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "message": str(e),
                                "unavailable_items": e.unavailable_items
                            }
                        )

                    # CREATE ORDER (with inventory reservation rollback on failure)
                    service = OrderService(conn)
                    try:
                        result = await service.create_order(
                            cart_session_id=request.cart_session_id,
                            user_id=user_id,
                            store_id=request.store_id,
                            payment_method=payment_method_type,
                            delivery_type=request.delivery_type,
                            delivery_address=request.delivery_address.dict() if request.delivery_address else None,
                            pickup_time=request.pickup_time,
                            tip_amount=request.tip_amount,
                            special_instructions=request.special_instructions,
                            promo_code=request.promo_code,
                            calculated_pricing=calculated_pricing  # Pass server-calculated prices
                        )

                        logger.info(
                            f"Order created successfully - Order: {result.get('order_number')}, "
                            f"Total: ${result.get('total_amount')}"
                        )
                        return result

                    except Exception as order_error:
                        # Order creation failed - release inventory reservation
                        logger.error(f"Order creation failed: {str(order_error)}")
                        logger.info("Releasing inventory reservation due to order creation failure")

                        await inventory_validator.release_reservation(
                            cart_session_id=request.cart_session_id,
                            store_id=request.store_id
                        )

                        raise  # Re-raise the original error

            except TimeoutError as e:
                # Cart lock timeout
                logger.warning(f"Cart lock timeout for {request.cart_session_id}: {str(e)}")
                raise HTTPException(
                    status_code=409,
                    detail="Another checkout is in progress for this cart. Please try again."
                )

    except InventoryValidationError:
        # Already handled above - don't catch here
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order from mobile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/{order_id}/status")
async def get_order_status(order_id: UUID):
    """Get order status for tracking"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            service = OrderService(conn)
            order = await service.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Return status info for mobile tracking
            return {
                "order_id": str(order['id']),
                "order_number": order['order_number'],
                "status": order['delivery_status'],
                "payment_status": order['payment_status'],
                "updated_at": order['updated_at'].isoformat() if order.get('updated_at') else None,
                "status_message": f"Order is {order['delivery_status']}",
                "estimated_delivery": order.get('estimated_time'),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order status: {str(e)}")
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
                    from services.delivery.delivery_service import DeliveryService

                    delivery_service = DeliveryService(conn)

                    # Create delivery from order
                    delivery = await delivery_service.create_delivery_from_order(
                        order_id=order_id,
                        store_id=UUID(order.get('store_id')),
                        customer_data={
                            'id': str(order.get('user_id')) if order.get('user_id') else None,
                            'name': f"{order.get('customer_first_name', 'Customer')} {order.get('customer_last_name', '')}".strip(),
                            'phone': order.get('customer_phone', ''),
                            'email': order.get('customer_email')
                        },
                        delivery_address={
                            'street': order.get('delivery_street') or order.get('delivery_address_line1', ''),
                            'city': order.get('delivery_city', 'Toronto'),
                            'state': order.get('delivery_province', 'ON'),
                            'postal_code': order.get('delivery_postal_code', ''),
                            'latitude': order.get('delivery_latitude', 43.6532),
                            'longitude': order.get('delivery_longitude', -79.3832)
                        },
                        delivery_fee=Decimal(str(order.get('delivery_fee', 5.00)))
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


@router.get("/", include_in_schema=True)
@router.get("", include_in_schema=False)  # Also handle without trailing slash
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