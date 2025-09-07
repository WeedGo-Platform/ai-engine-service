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
                          payment_method: str = "cash", delivery_address: Dict[str, Any] = None,
                          special_instructions: str = None) -> Dict[str, Any]:
        """Create a new order from cart session"""
        try:
            async with self.db.transaction():
                # Get cart session
                cart_query = """
                    SELECT 
                        id, items, subtotal, tax_amount, discount_amount,
                        delivery_fee, total_amount, user_profile_id
                    FROM cart_sessions
                    WHERE id = $1 AND status = 'active'
                """
                
                cart = await self.db.fetchrow(cart_query, cart_session_id)
                if not cart:
                    raise ValueError("Cart session not found or not active")
                
                # Generate order number
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
                
                # Create order
                order_query = """
                    INSERT INTO orders (
                        order_number, cart_session_id, user_id, user_profile_id,
                        items, subtotal, tax_amount, discount_amount, delivery_fee,
                        total_amount, payment_method, delivery_address, 
                        special_instructions, payment_status, delivery_status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'pending', 'pending')
                    RETURNING id, order_number, total_amount, created_at
                """
                
                order = await self.db.fetchrow(
                    order_query,
                    order_number, cart_session_id, user_id, cart['user_profile_id'],
                    cart['items'], cart['subtotal'], cart['tax_amount'],
                    cart['discount_amount'], cart['delivery_fee'], cart['total_amount'],
                    payment_method, json.dumps(delivery_address) if delivery_address else None,
                    special_instructions
                )
                
                # Update cart session status
                await self.db.execute(
                    "UPDATE cart_sessions SET status = 'converted' WHERE id = $1",
                    cart_session_id
                )
                
                # Deduct inventory for each item
                items = json.loads(cart['items']) if isinstance(cart['items'], str) else cart['items']
                for item in items:
                    if 'sku' in item:
                        inv_query = """
                            UPDATE inventory
                            SET quantity_available = quantity_available - $2,
                                quantity_reserved = quantity_reserved + $2
                            WHERE sku = $1 AND quantity_available >= $2
                        """
                        await self.db.execute(inv_query, item['sku'], item.get('quantity', 1))
                
                # Create order status history entry
                history_query = """
                    INSERT INTO order_status_history (order_id, status, notes)
                    VALUES ($1, 'pending', 'Order created')
                """
                await self.db.execute(history_query, order['id'])
                
                logger.info(f"Created order {order_number}")
                
                return {
                    "success": True,
                    "order_id": str(order['id']),
                    "order_number": order['order_number'],
                    "total_amount": float(order['total_amount']),
                    "created_at": order['created_at'].isoformat()
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
                return dict(result)
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
                    
                    # If order is completed, release reserved inventory
                    if delivery_status == 'delivered':
                        order_query = "SELECT items FROM orders WHERE id = $1"
                        order = await self.db.fetchrow(order_query, order_id)
                        
                        if order and order['items']:
                            items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                            for item in items:
                                if 'sku' in item:
                                    inv_query = """
                                        UPDATE inventory
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
                         o.created_at, o.updated_at, u.email
                ORDER BY o.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]
            
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