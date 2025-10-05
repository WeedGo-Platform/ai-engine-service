"""
Cart Management Service
Handles shopping cart operations, item management, and calculations
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import asyncpg
import logging
import json
import os

logger = logging.getLogger(__name__)


class CartService:
    """Service for managing shopping carts"""

    def __init__(self, db_pool, promotion_service=None):
        """Initialize cart service with database connection pool and optional promotion service"""
        self.db_pool = db_pool
        self.promotion_service = promotion_service
        # Get tax rate from environment or use 13% HST for Ontario
        self.tax_rate = Decimal(os.getenv('TAX_RATE', '0.13'))
        self.delivery_fee = Decimal(os.getenv('DEFAULT_DELIVERY_FEE', '10.00'))

    def _extract_first_discount_code(self, discount_codes) -> Optional[str]:
        """Safely extract the first discount code from various input formats"""
        if not discount_codes:
            return None

        # Handle list type
        if isinstance(discount_codes, list):
            return discount_codes[0] if len(discount_codes) > 0 else None

        # Handle string representation of list (e.g., "[]" or '["CODE"]')
        if isinstance(discount_codes, str):
            try:
                codes_list = json.loads(discount_codes)
                return codes_list[0] if len(codes_list) > 0 else None
            except (json.JSONDecodeError, IndexError, TypeError):
                return None

        return None

    async def get_or_create_cart(self, session_id: str, 
                                user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get existing cart or create new one for session"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check for existing active cart
                query = """
                    SELECT * FROM cart_sessions
                    WHERE session_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                
                cart = await conn.fetchrow(query, session_id)
                
                if cart:
                    cart_dict = dict(cart)
                    cart_dict['items'] = json.loads(cart_dict['items']) if isinstance(cart_dict['items'], str) else cart_dict['items']
                    return cart_dict
                
                # Create new cart
                cart_id = uuid4()
                expires_at = datetime.now() + timedelta(hours=24)
                
                create_query = """
                    INSERT INTO cart_sessions (
                        id, session_id, user_id, items, subtotal, tax_amount,
                        discount_amount, delivery_fee, total_amount, status, expires_at
                    ) VALUES ($1, $2, $3, '[]'::jsonb, 0, 0, 0, $4, 0, 'active', $5)
                    RETURNING *
                """
                
                new_cart = await conn.fetchrow(
                    create_query,
                    cart_id, session_id, user_id, self.delivery_fee, expires_at
                )
                
                cart_dict = dict(new_cart)
                cart_dict['items'] = []
                
                logger.info(f"Created new cart for session {session_id}")
                return cart_dict
            
        except Exception as e:
            logger.error(f"Error getting/creating cart: {str(e)}")
            raise
    
    async def add_item(self, session_id: str, product: Dict[str, Any],
                      quantity: int = 1, store_id: UUID = None, tenant_id: UUID = None) -> Dict[str, Any]:
        """Add item to cart"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get or create cart
                    cart = await self.get_or_create_cart(session_id)

                    # Update cart with store_id and tenant_id if provided
                    if store_id and not cart.get('store_id'):
                        await conn.execute(
                            "UPDATE cart_sessions SET store_id = $1 WHERE id = $2",
                            store_id, cart['id']
                        )
                        cart['store_id'] = store_id

                    if tenant_id and not cart.get('tenant_id'):
                        await conn.execute(
                            "UPDATE cart_sessions SET tenant_id = $1 WHERE id = $2",
                            tenant_id, cart['id']
                        )
                        cart['tenant_id'] = tenant_id

                    # Check inventory availability
                    if 'sku' in product:
                        inv_query = """
                            SELECT quantity_available, retail_price, store_id
                            FROM ocs_inventory
                            WHERE sku = $1
                        """
                        # If store_id provided, filter by store
                        if store_id:
                            inv_query += " AND store_id = $2"
                            inventory = await conn.fetchrow(inv_query, product['sku'], store_id)
                        else:
                            inventory = await conn.fetchrow(inv_query, product['sku'])

                        if inventory and inventory['quantity_available'] < quantity:
                            raise ValueError(f"Insufficient inventory for SKU {product['sku']}")

                        # Use retail price from inventory if available
                        if inventory:
                            product['price'] = float(inventory['retail_price'])
                    
                    # Parse existing items
                    items = cart['items'] if isinstance(cart['items'], list) else []
                    
                    # Check if item already exists in cart
                    item_found = False
                    for item in items:
                        if item.get('sku') == product.get('sku'):
                            item['quantity'] += quantity
                            item['subtotal'] = item['quantity'] * item['price']
                            item_found = True
                            break
                    
                    if not item_found:
                        # Add new item
                        new_item = {
                            'id': str(uuid4()),
                            'sku': product.get('sku'),
                            'name': product.get('name'),
                            'category': product.get('category'),
                            'price': product.get('price', 0),
                            'quantity': quantity,
                            'subtotal': quantity * product.get('price', 0),
                            'image_url': product.get('image_url'),
                            'added_at': datetime.now().isoformat()
                        }
                        items.append(new_item)
                    
                    # Calculate totals
                    subtotal = sum(Decimal(str(item['subtotal'])) for item in items)
                    tax_amount = subtotal * self.tax_rate
                    total_amount = subtotal + tax_amount + cart['delivery_fee']
                    
                    # Update cart
                    update_query = """
                        UPDATE cart_sessions
                        SET items = $2,
                            subtotal = $3,
                            tax_amount = $4,
                            total_amount = $5,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING *
                    """
                    
                    updated_cart = await conn.fetchrow(
                        update_query,
                        cart['id'],
                        json.dumps(items),
                        subtotal,
                        tax_amount,
                        total_amount
                    )
                    
                    cart_dict = dict(updated_cart)
                    cart_dict['items'] = items
                    
                    return {
                        "success": True,
                        "cart": cart_dict,
                        "message": f"Added {quantity} x {product.get('name')} to cart"
                    }
                    
        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}")
            raise
    
    async def update_item_quantity(self, session_id: str, item_id: str,
                                  quantity: int) -> Dict[str, Any]:
        """Update quantity of item in cart"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get cart
                    cart = await self.get_or_create_cart(session_id)
                    items = cart['items'] if isinstance(cart['items'], list) else []
                    
                    # Find and update item
                    item_found = False
                    for item in items:
                        if item.get('id') == item_id:
                            if quantity > 0:
                                # Check inventory
                                if 'sku' in item:
                                    inv_query = """
                                        SELECT quantity_available
                                        FROM ocs_inventory
                                        WHERE sku = $1
                                    """
                                    inventory = await conn.fetchrow(inv_query, item['sku'])
                                    
                                    if inventory and inventory['quantity_available'] < quantity:
                                        raise ValueError(f"Insufficient inventory for SKU {item['sku']}")
                                
                                item['quantity'] = quantity
                                item['subtotal'] = quantity * item['price']
                            else:
                                # Remove item if quantity is 0
                                items.remove(item)
                            item_found = True
                            break
                    
                    if not item_found:
                        raise ValueError(f"Item {item_id} not found in cart")
                    
                    # Calculate totals
                    subtotal = sum(Decimal(str(item['subtotal'])) for item in items)
                    tax_amount = subtotal * self.tax_rate
                    total_amount = subtotal + tax_amount + cart['delivery_fee']
                    
                    # Update cart
                    update_query = """
                        UPDATE cart_sessions
                        SET items = $2,
                            subtotal = $3,
                            tax_amount = $4,
                            total_amount = $5,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING *
                    """
                    
                    updated_cart = await conn.fetchrow(
                        update_query,
                        cart['id'],
                        json.dumps(items),
                        subtotal,
                        tax_amount,
                        total_amount
                    )
                    
                    cart_dict = dict(updated_cart)
                    cart_dict['items'] = items
                    
                    return {
                        "success": True,
                        "cart": cart_dict,
                        "message": "Cart updated successfully"
                    }
                    
        except Exception as e:
            logger.error(f"Error updating item quantity: {str(e)}")
            raise
    
    async def remove_item(self, session_id: str, item_id: str) -> Dict[str, Any]:
        """Remove item from cart"""
        return await self.update_item_quantity(session_id, item_id, 0)
    
    async def clear_cart(self, session_id: str) -> bool:
        """Clear all items from cart"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE cart_sessions
                    SET items = '[]'::jsonb,
                        subtotal = 0,
                        tax_amount = 0,
                        total_amount = delivery_fee,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = $1 AND status = 'active'
                    RETURNING id
                """
                
                result = await conn.fetchval(query, session_id)
                return result is not None
                
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            raise
    
    async def update_cart_context(self, session_id: str, store_id: UUID = None, tenant_id: UUID = None) -> bool:
        """Update cart's store_id and tenant_id if they're not set"""
        try:
            async with self.db_pool.acquire() as conn:
                cart = await self.get_or_create_cart(session_id)

                logger.info(f"update_cart_context - Current cart: store_id={cart.get('store_id')}, tenant_id={cart.get('tenant_id')}")
                logger.info(f"update_cart_context - Params: store_id={store_id}, tenant_id={tenant_id}")

                updates = []
                params = []
                param_count = 1

                if store_id and not cart.get('store_id'):
                    updates.append(f"store_id = ${param_count}")
                    params.append(store_id)
                    param_count += 1
                    logger.info(f"Will update store_id to {store_id}")

                if tenant_id and not cart.get('tenant_id'):
                    updates.append(f"tenant_id = ${param_count}")
                    params.append(tenant_id)
                    param_count += 1
                    logger.info(f"Will update tenant_id to {tenant_id}")

                if updates:
                    query = f"""
                        UPDATE cart_sessions
                        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ${param_count}
                    """
                    params.append(cart['id'])
                    logger.info(f"Executing update query: {query} with params: {params}")
                    await conn.execute(query, *params)
                    return True

                logger.info("No updates needed - cart already has required IDs or params not provided")
                return False
        except Exception as e:
            logger.error(f"Error updating cart context: {str(e)}")
            return False

    async def apply_discount(self, session_id: str, discount_code: str) -> Dict[str, Any]:
        """Apply discount code to cart using promotion service"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get cart
                    cart = await self.get_or_create_cart(session_id)

                    # Validate discount code using promotion service
                    if not self.promotion_service:
                        raise ValueError("Promotion service not available")

                    # Validate discount code with store/tenant context
                    validation = await self.promotion_service.validate_discount_code(
                        discount_code,
                        tenant_id=cart.get('tenant_id'),
                        store_id=cart.get('store_id')
                    )

                    if not validation['valid']:
                        # Return user-friendly error message
                        error_msg = validation.get('error', 'This promo code is not valid')
                        raise ValueError(error_msg)

                    # Calculate discount based on promotion type
                    discount_type = validation['discount_type']
                    discount_value = Decimal(str(validation['discount_value']))

                    if discount_type == 'percentage':
                        discount_amount = cart['subtotal'] * (discount_value / 100)
                    else:  # fixed amount
                        discount_amount = discount_value

                    # Ensure discount doesn't exceed subtotal
                    discount_amount = min(discount_amount, cart['subtotal'])

                    # Recalculate totals with discount
                    # Tax is calculated on subtotal AFTER discount
                    taxable_amount = cart['subtotal'] - discount_amount
                    tax_amount = taxable_amount * self.tax_rate
                    total_amount = taxable_amount + tax_amount + cart['delivery_fee']

                    # Update cart
                    update_query = """
                        UPDATE cart_sessions
                        SET discount_codes = $2::jsonb,
                            discount_amount = $3,
                            tax_amount = $4,
                            total_amount = $5,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING *
                    """

                    updated_cart = await conn.fetchrow(
                        update_query,
                        cart['id'],
                        json.dumps([discount_code]),  # Store as JSONB array
                        discount_amount,
                        tax_amount,
                        total_amount
                    )

                    cart_dict = dict(updated_cart)
                    cart_dict['items'] = json.loads(cart_dict['items']) if isinstance(cart_dict['items'], str) else cart_dict['items']

                    return {
                        "success": True,
                        "cart": cart_dict,
                        "discount": float(discount_amount),
                        "discount_applied": float(discount_amount),  # Legacy compatibility
                        "message": f"Discount code {discount_code} applied successfully"
                    }

        except Exception as e:
            logger.error(f"Error applying discount: {str(e)}")
            raise

    async def remove_discount(self, session_id: str) -> Dict[str, Any]:
        """Remove discount code from cart and recalculate totals"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get cart
                    cart = await self.get_or_create_cart(session_id)

                    logger.info(f"Removing discount from cart. Current discount: {cart.get('discount_amount')}, codes: {cart.get('discount_codes')}")

                    # Recalculate totals without discount
                    tax_amount = cart['subtotal'] * self.tax_rate
                    total_amount = cart['subtotal'] + tax_amount + cart['delivery_fee']

                    logger.info(f"Recalculated totals - subtotal: {cart['subtotal']}, tax: {tax_amount}, total: {total_amount}")

                    # Update cart
                    update_query = """
                        UPDATE cart_sessions
                        SET discount_codes = '[]'::jsonb,
                            discount_amount = 0,
                            tax_amount = $2,
                            total_amount = $3,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING *
                    """

                    updated_cart = await conn.fetchrow(
                        update_query,
                        cart['id'],
                        tax_amount,
                        total_amount
                    )

                    cart_dict = dict(updated_cart)
                    cart_dict['items'] = json.loads(cart_dict['items']) if isinstance(cart_dict['items'], str) else cart_dict['items']

                    return cart_dict

        except Exception as e:
            logger.error(f"Error removing discount: {str(e)}")
            raise

    async def update_delivery_address(self, session_id: str, 
                                    delivery_address: Dict[str, Any]) -> bool:
        """Update delivery address and recalculate delivery fee"""
        try:
            async with self.db_pool.acquire() as conn:
                # Calculate delivery fee based on address (simplified)
                delivery_fee = self.delivery_fee
                postal_code = delivery_address.get('postal_code', '')
                
                # Example: Free delivery for certain postal codes
                if postal_code.startswith('M5'):  # Downtown Toronto
                    delivery_fee = Decimal('5.00')
                elif postal_code.startswith('M'):  # Greater Toronto Area
                    delivery_fee = Decimal('10.00')
                else:
                    delivery_fee = Decimal('15.00')
                
                # Get current cart totals
                cart = await self.get_or_create_cart(session_id)
                total_amount = cart['subtotal'] + cart['tax_amount'] - cart['discount_amount'] + delivery_fee
                
                # Update cart with delivery info
                query = """
                    UPDATE cart_sessions
                    SET delivery_address = $2,
                        delivery_fee = $3,
                        total_amount = $4,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = $1 AND status = 'active'
                    RETURNING id
                """
                
                result = await conn.fetchval(query, session_id, json.dumps(delivery_address), delivery_fee, total_amount)
                return result is not None
                
        except Exception as e:
            logger.error(f"Error updating delivery address: {str(e)}")
            raise
    
    async def get_cart_summary(self, session_id: str) -> Dict[str, Any]:
        """Get cart summary with calculated totals"""
        try:
            cart = await self.get_or_create_cart(session_id)
            
            # Parse items if needed
            items = cart['items'] if isinstance(cart['items'], list) else []
            
            # Calculate item count
            item_count = sum(item.get('quantity', 0) for item in items)
            
            return {
                'id': str(cart['id']),
                'session_id': session_id,
                'items': items,
                'item_count': item_count,
                'subtotal': float(cart['subtotal']),
                'tax_amount': float(cart['tax_amount']),
                'discount_amount': float(cart.get('discount_amount', 0)),
                'discount_code': self._extract_first_discount_code(cart.get('discount_codes')),
                'delivery_fee': float(cart['delivery_fee']),
                'total_amount': float(cart['total_amount']),
                'delivery_address': json.loads(cart['delivery_address']) if cart.get('delivery_address') and isinstance(cart['delivery_address'], str) else cart.get('delivery_address'),
                'status': cart['status'],
                'store_id': str(cart['store_id']) if cart.get('store_id') else None,
                'tenant_id': str(cart['tenant_id']) if cart.get('tenant_id') else None,
                'created_at': cart['created_at'].isoformat() if cart.get('created_at') else None,
                'updated_at': cart['updated_at'].isoformat() if cart.get('updated_at') else None
            }
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {str(e)}")
            # Return empty cart on error
            return {
                'id': '',
                'session_id': session_id,
                'items': [],
                'item_count': 0,
                'subtotal': 0,
                'tax_amount': 0,
                'discount_amount': 0,
                'delivery_fee': float(self.delivery_fee),
                'total_amount': 0,
                'status': 'active'
            }
    
    async def cleanup_expired_carts(self) -> int:
        """Clean up expired cart sessions"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE cart_sessions
                    SET status = 'expired'
                    WHERE status = 'active' 
                    AND expires_at < CURRENT_TIMESTAMP
                    RETURNING id
                """
                
                results = await conn.fetch(query)
                count = len(results)
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired carts")
                
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up carts: {str(e)}")
            raise
    
    async def merge_carts(self, guest_session_id: str, user_id: UUID) -> Dict[str, Any]:
        """Merge guest cart with user cart when user logs in"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get guest cart
                    guest_cart = await self.get_or_create_cart(guest_session_id)
                    
                    # Get user cart
                    user_query = """
                        SELECT * FROM cart_sessions
                        WHERE user_id = $1 AND status = 'active'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    
                    user_cart = await conn.fetchrow(user_query, user_id)
                    
                    if not user_cart:
                        # No user cart, just update guest cart with user_id
                        update_query = """
                            UPDATE cart_sessions
                            SET user_id = $2
                            WHERE id = $1
                            RETURNING *
                        """
                        
                        result = await conn.fetchrow(update_query, guest_cart['id'], user_id)
                        cart_dict = dict(result)
                        cart_dict['items'] = json.loads(cart_dict['items']) if isinstance(cart_dict['items'], str) else cart_dict['items']
                        return cart_dict
                    
                    # Merge items
                    guest_items = guest_cart['items'] if isinstance(guest_cart['items'], list) else []
                    user_items = json.loads(user_cart['items']) if isinstance(user_cart['items'], str) else user_cart['items']
                    
                    # Combine items, updating quantities for duplicates
                    for guest_item in guest_items:
                        found = False
                        for user_item in user_items:
                            if user_item.get('sku') == guest_item.get('sku'):
                                user_item['quantity'] += guest_item['quantity']
                                user_item['subtotal'] = user_item['quantity'] * user_item['price']
                                found = True
                                break
                        if not found:
                            user_items.append(guest_item)
                    
                    # Calculate new totals
                    subtotal = sum(Decimal(str(item['subtotal'])) for item in user_items)
                    tax_amount = subtotal * self.tax_rate
                    total_amount = subtotal + tax_amount + user_cart['delivery_fee']
                    
                    # Update user cart
                    update_query = """
                        UPDATE cart_sessions
                        SET items = $2,
                            subtotal = $3,
                            tax_amount = $4,
                            total_amount = $5,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING *
                    """
                    
                    updated_cart = await conn.fetchrow(
                        update_query,
                        user_cart['id'],
                        json.dumps(user_items),
                        subtotal,
                        tax_amount,
                        total_amount
                    )
                    
                    # Delete guest cart
                    await conn.execute(
                        "DELETE FROM cart_sessions WHERE id = $1",
                        guest_cart['id']
                    )
                    
                    cart_dict = dict(updated_cart)
                    cart_dict['items'] = user_items
                    
                    return cart_dict
                    
        except Exception as e:
            logger.error(f"Error merging carts: {str(e)}")
            raise