"""
Order Management Service
Handles order creation, processing, tracking, and updates
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing customer orders"""
    
    def __init__(self, db_connection):
        """Initialize order service with database connection"""
        self.db = db_connection
    
    async def create_order(self, cart_session_id: UUID, user_id: Optional[UUID] = None,
                          store_id: Optional[UUID] = None, payment_method: str = "cash",
                          delivery_type: str = "delivery", delivery_address: Dict[str, Any] = None,
                          pickup_time: Optional[str] = None, tip_amount: float = 0,
                          special_instructions: str = None, promo_code: Optional[str] = None,
                          calculated_pricing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new order from cart session

        Args:
            cart_session_id: Cart session UUID
            user_id: User UUID (optional for guest)
            store_id: Store UUID
            payment_method: Payment method type (validated from user's profile)
            delivery_type: 'delivery' or 'pickup'
            delivery_address: Delivery address dict (required for delivery)
            pickup_time: Pickup time string (required for pickup)
            tip_amount: Tip amount
            special_instructions: Order notes
            promo_code: Promo code applied
            calculated_pricing: SERVER-CALCULATED pricing (from OrderPricingService)
        """
        try:
            async with self.db.transaction():
                # Get cart session
                # Query by session_id (VARCHAR) not id (UUID primary key)
                cart_query = """
                    SELECT
                        id, items, user_profile_id, store_id
                    FROM cart_sessions
                    WHERE session_id = $1 AND status = 'active'
                """

                cart = await self.db.fetchrow(cart_query, str(cart_session_id))
                if not cart:
                    raise ValueError("Cart session not found or not active")

                # Use server-calculated pricing (CRITICAL SECURITY)
                if calculated_pricing:
                    # Server-side recalculated prices (trusted)
                    items_with_prices = calculated_pricing['items']
                    subtotal = Decimal(str(calculated_pricing['subtotal']))
                    tax_amount = Decimal(str(calculated_pricing['tax']))
                    discount_amount = Decimal(str(calculated_pricing['discount']))
                    delivery_fee = Decimal(str(calculated_pricing['delivery_fee']))
                    total_amount = Decimal(str(calculated_pricing['total']))
                else:
                    # Fallback to cart values (legacy support)
                    items_with_prices = cart['items']
                    subtotal = Decimal(str(cart.get('subtotal', 0)))
                    tax_amount = Decimal(str(cart.get('tax_amount', 0)))
                    discount_amount = Decimal(str(cart.get('discount_amount', 0)))
                    delivery_fee = Decimal(str(cart.get('delivery_fee', 0)))
                    total_amount = Decimal(str(cart.get('total_amount', 0)))

                # Add tip to total
                tip_amount_decimal = Decimal(str(tip_amount))
                total_amount_with_tip = total_amount + tip_amount_decimal

                # Generate order number
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"

                # Use store_id from parameter or cart
                final_store_id = store_id or cart.get('store_id')

                # Create order
                order_query = """
                    INSERT INTO orders (
                        order_number, cart_session_id, user_id, user_profile_id, store_id,
                        items, subtotal, tax_amount, discount_amount, delivery_fee, tip_amount,
                        total_amount, payment_method, delivery_type, delivery_address, pickup_time,
                        special_instructions, promo_code, payment_status, delivery_status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, 'pending', 'pending')
                    RETURNING id, order_number, total_amount, created_at
                """

                # Use cart['id'] (UUID primary key) for foreign key constraint, not cart_session_id parameter
                order = await self.db.fetchrow(
                    order_query,
                    order_number, cart['id'], user_id, cart['user_profile_id'], final_store_id,
                    json.dumps(items_with_prices), subtotal, tax_amount,
                    discount_amount, delivery_fee, tip_amount_decimal, total_amount_with_tip,
                    payment_method, delivery_type, json.dumps(delivery_address) if delivery_address else None,
                    pickup_time, special_instructions, promo_code
                )
                
                # Update cart session status using the cart's actual UUID primary key
                await self.db.execute(
                    "UPDATE cart_sessions SET status = 'converted' WHERE id = $1",
                    cart['id']
                )

                # NOTE: Inventory reservation is handled by InventoryValidator BEFORE order creation
                # This follows DRY principle and prevents double-reservation

                # Create order status history entry
                history_query = """
                    INSERT INTO order_status_history (order_id, status, notes)
                    VALUES ($1, 'pending', 'Order created')
                """
                await self.db.execute(history_query, order['id'])
                
                logger.info(f"Created order {order_number}")

                # Create delivery for delivery-type orders
                delivery_id = None
                if delivery_type == 'delivery' and delivery_address:
                    try:
                        from services.delivery.delivery_service import DeliveryService

                        delivery_service = DeliveryService(self.db)
                        delivery = await delivery_service.create_delivery_from_order(
                            order_id=order['id'],
                            store_id=final_store_id,
                            customer_data={
                                'user_id': str(user_id) if user_id else None,
                                'name': delivery_address.get('recipient_name', 'Customer'),
                                'phone': delivery_address.get('phone', ''),
                                'email': delivery_address.get('email', '')
                            },
                            delivery_address=delivery_address,
                            delivery_fee=delivery_fee
                        )
                        delivery_id = str(delivery.id)
                        logger.info(f"Created delivery {delivery_id} for order {order_number}")
                    except Exception as delivery_error:
                        logger.error(f"Failed to create delivery for order {order_number}: {str(delivery_error)}")
                        # Don't fail the order creation if delivery creation fails
                        # The delivery can be created later

                return {
                    "success": True,
                    "id": str(order['id']),  # Frontend expects 'id'
                    "order_id": str(order['id']),  # Keep for backward compatibility
                    "order_number": order['order_number'],
                    "total_amount": float(order['total_amount']),
                    "created_at": order['created_at'].isoformat(),
                    "delivery_id": delivery_id  # Include delivery_id for tracking
                }
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise
    
    async def get_order(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """Get order details by ID"""
        try:
            query = """
                SELECT 
                    o.*,
                    u.email as user_email,
                    u.phone as user_phone
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.id = $1
            """
            
            result = await self.db.fetchrow(query, order_id)
            if result:
                order_dict = dict(result)
                # Parse JSON fields
                if order_dict.get('items'):
                    order_dict['items'] = json.loads(order_dict['items']) if isinstance(order_dict['items'], str) else order_dict['items']
                if order_dict.get('delivery_address'):
                    order_dict['delivery_address'] = json.loads(order_dict['delivery_address']) if isinstance(order_dict['delivery_address'], str) else order_dict['delivery_address']
                return order_dict
            return None
            
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise
    
    async def get_order_by_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        """Get order details by order number"""
        try:
            query = """
                SELECT 
                    o.*,
                    u.email as user_email,
                    u.phone as user_phone
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.order_number = $1
            """
            
            result = await self.db.fetchrow(query, order_number)
            if result:
                order = dict(result)
                # Parse JSON fields
                if order.get('items'):
                    order['items'] = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                    # Add total field to each item
                    for item in order['items']:
                        if 'subtotal' in item and 'total' not in item:
                            item['total'] = item['subtotal']
                if order.get('delivery_address'):
                    order['delivery_address'] = json.loads(order['delivery_address']) if isinstance(order['delivery_address'], str) else order['delivery_address']
                # Map delivery_status to status for frontend compatibility
                order['status'] = order.get('delivery_status', 'pending')
                # Map snake_case to camelCase for frontend
                order['total'] = float(order.get('total_amount', 0))
                order['subtotal'] = float(order.get('subtotal', 0))
                order['tax'] = float(order.get('tax_amount', 0))
                order['discount'] = float(order.get('discount_amount', 0))
                order['deliveryFee'] = float(order.get('delivery_fee', 0))
                order['paymentStatus'] = order.get('payment_status', 'pending')
                order['paymentMethod'] = order.get('payment_method', 'cash')
                order['customerEmail'] = order.get('user_email', '')
                order['customerPhone'] = order.get('user_phone', '')
                order['customerName'] = order.get('user_email', '').split('@')[0].title() if order.get('user_email') else 'Customer'
                order['orderNumber'] = order.get('order_number')
                order['notes'] = order.get('special_instructions')
                order['shippingAddress'] = order.get('delivery_address')
                order['fulfillmentMethod'] = 'delivery' if order.get('delivery_address') else 'pickup'
                return order
            return None
            
        except Exception as e:
            logger.error(f"Error getting order by number: {str(e)}")
            raise
    
    async def update_order_status(self, order_id: UUID, payment_status: str = None,
                                 delivery_status: str = None, notes: str = None) -> bool:
        """Update order payment or delivery status"""
        try:
            async with self.db.transaction():
                updates = []
                params = []
                param_count = 0
                
                if payment_status:
                    param_count += 1
                    updates.append(f"payment_status = ${param_count}")
                    params.append(payment_status)
                
                if delivery_status:
                    param_count += 1
                    updates.append(f"delivery_status = ${param_count}")
                    params.append(delivery_status)
                
                if not updates:
                    return False
                
                param_count += 1
                query = f"""
                    UPDATE orders
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ${param_count}
                    RETURNING id
                """
                params.append(order_id)
                
                result = await self.db.fetchval(query, *params)
                
                if result:
                    # Add to status history
                    status = payment_status or delivery_status
                    history_query = """
                        INSERT INTO order_status_history (order_id, status, notes)
                        VALUES ($1, $2, $3)
                    """
                    await self.db.execute(history_query, order_id, status, notes)

                    # Broadcast status update to mobile clients via WebSocket
                    if delivery_status:
                        try:
                            from api.order_websocket import broadcast_order_status_update

                            # Create status message
                            status_messages = {
                                'confirmed': 'Your order has been confirmed',
                                'preparing': 'Your order is being prepared',
                                'ready': 'Your order is ready for pickup/delivery',
                                'out_for_delivery': 'Your order is on its way',
                                'delivered': 'Your order has been delivered',
                                'cancelled': 'Your order has been cancelled'
                            }

                            message = status_messages.get(delivery_status, f'Order status: {delivery_status}')

                            # Broadcast to all clients watching this order
                            await broadcast_order_status_update(
                                order_id=str(order_id),
                                status=delivery_status,
                                message=message
                            )
                            logger.info(f"Broadcasted status update for order {order_id}: {delivery_status}")
                        except Exception as ws_error:
                            # Don't fail the status update if WebSocket broadcast fails
                            logger.error(f"Failed to broadcast order status update: {ws_error}")

                    # If order is completed, release reserved inventory
                    if delivery_status == 'delivered':
                        order_query = "SELECT items FROM orders WHERE id = $1"
                        order = await self.db.fetchrow(order_query, order_id)
                        
                        if order and order['items']:
                            items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                            for item in items:
                                if 'sku' in item:
                                    inv_query = """
                                        UPDATE ocs_inventory
                                        SET quantity_reserved = quantity_reserved - $2,
                                            quantity_on_hand = quantity_on_hand - $2
                                        WHERE sku = $1
                                    """
                                    await self.db.execute(inv_query, item['sku'], item.get('quantity', 1))
                    
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            raise
    
    async def list_orders(self, user_id: Optional[UUID] = None,
                         payment_status: Optional[str] = None,
                         delivery_status: Optional[str] = None,
                         limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List orders with filters"""
        try:
            query = """
                SELECT
                    o.id, o.order_number, o.total_amount,
                    o.payment_status, o.delivery_status,
                    o.created_at, o.updated_at,
                    o.items, o.subtotal, o.tax_amount, o.discount_amount,
                    o.delivery_fee, o.payment_method, o.delivery_address,
                    o.special_instructions,
                    u.email as user_email,
                    COUNT(osh.id) as status_updates
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                LEFT JOIN order_status_history osh ON o.id = osh.order_id
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            if user_id:
                param_count += 1
                query += f" AND o.user_id = ${param_count}"
                params.append(user_id)
            
            if payment_status:
                param_count += 1
                query += f" AND o.payment_status = ${param_count}"
                params.append(payment_status)
            
            if delivery_status:
                param_count += 1
                query += f" AND o.delivery_status = ${param_count}"
                params.append(delivery_status)
            
            query += f"""
                GROUP BY o.id, o.order_number, o.total_amount,
                         o.payment_status, o.delivery_status,
                         o.created_at, o.updated_at, o.items, o.subtotal,
                         o.tax_amount, o.discount_amount, o.delivery_fee,
                         o.payment_method, o.delivery_address, o.special_instructions,
                         u.email
                ORDER BY o.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            results = await self.db.fetch(query, *params)
            orders = []
            for row in results:
                order = dict(row)
                # Parse JSON fields
                if order.get('items'):
                    order['items'] = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                if order.get('delivery_address'):
                    order['delivery_address'] = json.loads(order['delivery_address']) if isinstance(order['delivery_address'], str) else order['delivery_address']
                # Map delivery_status to status for frontend compatibility
                order['status'] = order.get('delivery_status', 'pending')
                # Map payment_method to fulfillmentMethod for compatibility
                if order.get('delivery_address'):
                    order['fulfillmentMethod'] = 'delivery'
                else:
                    order['fulfillmentMethod'] = 'pickup'
                # Map total_amount to total for frontend
                order['total'] = float(order.get('total_amount', 0))
                # Add paymentStatus field
                order['paymentStatus'] = order.get('payment_status', 'pending')
                # Add paymentMethod field
                order['paymentMethod'] = order.get('payment_method', 'cash')
                # Add orderNumber field (already exists but ensure it's there)
                order['orderNumber'] = order.get('order_number')
                # Add createdAt field
                if order.get('created_at'):
                    order['createdAt'] = order['created_at'].isoformat() if hasattr(order['created_at'], 'isoformat') else str(order['created_at'])
                # Map delivery_address to deliveryAddress
                if order.get('delivery_address'):
                    order['deliveryAddress'] = order['delivery_address']
                orders.append(order)
            return orders
            
        except Exception as e:
            logger.error(f"Error listing orders: {str(e)}")
            raise
    
    async def get_order_status_history(self, order_id: UUID) -> List[Dict[str, Any]]:
        """Get order status change history"""
        try:
            query = """
                SELECT 
                    status, notes, changed_at
                FROM order_status_history
                WHERE order_id = $1
                ORDER BY changed_at DESC
            """
            
            results = await self.db.fetch(query, order_id)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting order status history: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: UUID, reason: str = None) -> bool:
        """Cancel an order and restore inventory"""
        try:
            async with self.db.transaction():
                # Get order details
                order_query = """
                    SELECT items, payment_status, delivery_status
                    FROM orders
                    WHERE id = $1
                """
                
                order = await self.db.fetchrow(order_query, order_id)
                if not order:
                    return False
                
                # Check if order can be cancelled
                if order['delivery_status'] in ['delivered', 'cancelled']:
                    return False
                
                # Update order status
                update_query = """
                    UPDATE orders
                    SET payment_status = 'cancelled',
                        delivery_status = 'cancelled',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """
                await self.db.execute(update_query, order_id)
                
                # Restore inventory
                if order['items']:
                    items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                    for item in items:
                        if 'sku' in item:
                            inv_query = """
                                UPDATE inventory
                                SET quantity_available = quantity_available + $2,
                                    quantity_reserved = quantity_reserved - $2
                                WHERE sku = $1
                            """
                            await self.db.execute(inv_query, item['sku'], item.get('quantity', 1))
                
                # Add to status history
                history_query = """
                    INSERT INTO order_status_history (order_id, status, notes)
                    VALUES ($1, 'cancelled', $2)
                """
                await self.db.execute(history_query, order_id, reason or 'Order cancelled')
                
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise
    
    async def get_order_analytics(self, start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """Get order analytics and statistics"""
        try:
            # Base query for analytics
            base_conditions = "WHERE 1=1"
            params = []
            param_count = 0
            
            if start_date:
                param_count += 1
                base_conditions += f" AND created_at >= ${param_count}"
                params.append(start_date)
            
            if end_date:
                param_count += 1
                base_conditions += f" AND created_at <= ${param_count}"
                params.append(end_date)
            
            # Total orders and revenue
            summary_query = f"""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(DISTINCT user_id) as unique_customers,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value,
                    SUM(CASE WHEN payment_status = 'completed' THEN total_amount ELSE 0 END) as paid_revenue
                FROM orders
                {base_conditions}
            """
            
            summary = await self.db.fetchrow(summary_query, *params)
            
            # Orders by status
            status_query = f"""
                SELECT 
                    delivery_status,
                    COUNT(*) as count,
                    SUM(total_amount) as total_value
                FROM orders
                {base_conditions}
                GROUP BY delivery_status
            """
            
            status_results = await self.db.fetch(status_query, *params)
            
            # Top products
            products_query = f"""
                SELECT 
                    item->>'sku' as sku,
                    item->>'name' as product_name,
                    SUM((item->>'quantity')::int) as total_quantity,
                    COUNT(*) as order_count
                FROM orders o,
                     jsonb_array_elements(o.items) as item
                {base_conditions}
                GROUP BY item->>'sku', item->>'name'
                ORDER BY total_quantity DESC
                LIMIT 10
            """
            
            top_products = await self.db.fetch(products_query, *params)
            
            return {
                'summary': dict(summary),
                'by_status': [dict(row) for row in status_results],
                'top_products': [dict(row) for row in top_products]
            }
            
        except Exception as e:
            logger.error(f"Error getting order analytics: {str(e)}")
            raise