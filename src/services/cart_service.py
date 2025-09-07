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
    
    def __init__(self, db_connection):
        """Initialize cart service with database connection"""
        self.db = db_connection
        # Get tax rate from environment or use 13% HST for Ontario
        self.tax_rate = Decimal(os.getenv('TAX_RATE', '0.13'))
        self.delivery_fee = Decimal(os.getenv('DEFAULT_DELIVERY_FEE', '10.00'))
    
    async def get_or_create_cart(self, session_id: str, 
                                user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get existing cart or create new one for session"""
        try:
            # Check for existing active cart
            query = """
                SELECT * FROM cart_sessions
                WHERE session_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cart = await self.db.fetchrow(query, session_id)
            
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
            
            new_cart = await self.db.fetchrow(
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
                      quantity: int = 1) -> Dict[str, Any]:
        """Add item to cart"""
        try:
            async with self.db.transaction():
                # Get or create cart
                cart = await self.get_or_create_cart(session_id)
                
                # Check inventory availability
                if 'sku' in product:
                    inv_query = """
                        SELECT quantity_available, retail_price
                        FROM inventory
                        WHERE sku = $1
                    """
                    inventory = await self.db.fetchrow(inv_query, product['sku'])
                    
                    if not inventory or inventory['quantity_available'] < quantity:
                        raise ValueError(f"Insufficient inventory for SKU {product['sku']}")
                    
                    # Use retail price from inventory
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
                
                updated_cart = await self.db.fetchrow(
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
            async with self.db.transaction():
                # Get cart
                cart = await self.get_or_create_cart(session_id)
                items = cart['items'] if isinstance(cart['items'], list) else []
                
                # Find and update item
                item_found = False
                for item in items:
                    if item.get('id') == item_id:
                        if quantity <= 0:
                            items.remove(item)
                        else:
                            # Check inventory
                            if 'sku' in item:
                                inv_query = "SELECT quantity_available FROM inventory WHERE sku = $1"
                                inventory = await self.db.fetchrow(inv_query, item['sku'])
                                
                                if not inventory or inventory['quantity_available'] < quantity:
                                    raise ValueError(f"Insufficient inventory for SKU {item['sku']}")
                            
                            item['quantity'] = quantity
                            item['subtotal'] = quantity * item['price']
                        item_found = True
                        break
                
                if not item_found:
                    raise ValueError(f"Item {item_id} not found in cart")
                
                # Recalculate totals
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
                
                updated_cart = await self.db.fetchrow(
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
                    "cart": cart_dict
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
            
            result = await self.db.fetchval(query, session_id)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            raise
    
    async def apply_discount(self, session_id: str, discount_code: str) -> Dict[str, Any]:
        """Apply discount code to cart"""
        try:
            async with self.db.transaction():
                # Get cart
                cart = await self.get_or_create_cart(session_id)
                
                # Validate discount code (simplified - would check discount table)
                discount_amount = Decimal('0')
                if discount_code.upper() == 'WELCOME10':
                    discount_amount = cart['subtotal'] * Decimal('0.10')  # 10% off
                elif discount_code.upper() == 'SAVE20':
                    discount_amount = cart['subtotal'] * Decimal('0.20')  # 20% off
                else:
                    raise ValueError("Invalid discount code")
                
                # Update cart with discount
                tax_amount = (cart['subtotal'] - discount_amount) * self.tax_rate
                total_amount = cart['subtotal'] - discount_amount + tax_amount + cart['delivery_fee']
                
                # Store discount code
                discount_codes = json.loads(cart['discount_codes']) if cart['discount_codes'] else []
                if discount_code not in discount_codes:
                    discount_codes.append(discount_code)
                
                update_query = """
                    UPDATE cart_sessions
                    SET discount_amount = $2,
                        tax_amount = $3,
                        total_amount = $4,
                        discount_codes = $5,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    RETURNING *
                """
                
                updated_cart = await self.db.fetchrow(
                    update_query,
                    cart['id'],
                    discount_amount,
                    tax_amount,
                    total_amount,
                    json.dumps(discount_codes)
                )
                
                cart_dict = dict(updated_cart)
                cart_dict['items'] = json.loads(cart['items']) if isinstance(cart['items'], str) else cart['items']
                
                return {
                    "success": True,
                    "cart": cart_dict,
                    "discount_applied": float(discount_amount),
                    "message": f"Discount code {discount_code} applied successfully"
                }
                
        except Exception as e:
            logger.error(f"Error applying discount: {str(e)}")
            raise
    
    async def update_delivery_address(self, session_id: str,
                                     delivery_address: Dict[str, Any]) -> bool:
        """Update delivery address for cart session"""
        try:
            # Calculate delivery fee based on address (simplified)
            delivery_fee = self.delivery_fee
            if delivery_address.get('city', '').lower() == 'toronto':
                delivery_fee = Decimal('5.00')  # Local delivery discount
            
            # Get cart to recalculate total
            cart = await self.get_or_create_cart(session_id)
            total_amount = cart['subtotal'] - cart['discount_amount'] + cart['tax_amount'] + delivery_fee
            
            query = """
                UPDATE cart_sessions
                SET delivery_fee = $2,
                    total_amount = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = $1 AND status = 'active'
                RETURNING id
            """
            
            result = await self.db.fetchval(query, session_id, delivery_fee, total_amount)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating delivery address: {str(e)}")
            raise
    
    async def get_cart_summary(self, session_id: str) -> Dict[str, Any]:
        """Get detailed cart summary with calculations"""
        try:
            cart = await self.get_or_create_cart(session_id)
            
            # Count unique items and total quantity
            items = cart['items'] if isinstance(cart['items'], list) else []
            unique_items = len(items)
            total_quantity = sum(item.get('quantity', 0) for item in items)
            
            # Check inventory for each item
            for item in items:
                if 'sku' in item:
                    inv_query = "SELECT quantity_available FROM inventory WHERE sku = $1"
                    inventory = await self.db.fetchrow(inv_query, item['sku'])
                    item['in_stock'] = inventory and inventory['quantity_available'] >= item['quantity']
                else:
                    item['in_stock'] = True
            
            return {
                "cart_id": str(cart['id']),
                "session_id": cart['session_id'],
                "status": cart['status'],
                "items": items,
                "unique_items": unique_items,
                "total_quantity": total_quantity,
                "subtotal": float(cart['subtotal']),
                "tax_amount": float(cart['tax_amount']),
                "tax_rate": float(self.tax_rate),
                "discount_amount": float(cart['discount_amount']),
                "delivery_fee": float(cart['delivery_fee']),
                "total_amount": float(cart['total_amount']),
                "discount_codes": json.loads(cart['discount_codes']) if cart['discount_codes'] else [],
                "created_at": cart['created_at'].isoformat(),
                "updated_at": cart['updated_at'].isoformat(),
                "expires_at": cart['expires_at'].isoformat() if cart['expires_at'] else None
            }
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {str(e)}")
            raise
    
    async def cleanup_expired_carts(self) -> int:
        """Clean up expired cart sessions"""
        try:
            query = """
                UPDATE cart_sessions
                SET status = 'expired'
                WHERE status = 'active' 
                AND expires_at < CURRENT_TIMESTAMP
                RETURNING id
            """
            
            results = await self.db.fetch(query)
            count = len(results)
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired carts")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired carts: {str(e)}")
            raise
    
    async def merge_carts(self, guest_session_id: str, user_id: UUID) -> Dict[str, Any]:
        """Merge guest cart with user cart when user logs in"""
        try:
            async with self.db.transaction():
                # Get guest cart
                guest_cart = await self.get_or_create_cart(guest_session_id)
                
                # Get or create user cart
                user_query = """
                    SELECT * FROM cart_sessions
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                user_cart = await self.db.fetchrow(user_query, user_id)
                
                if not user_cart:
                    # Just assign guest cart to user
                    update_query = """
                        UPDATE cart_sessions
                        SET user_id = $2
                        WHERE id = $1
                        RETURNING *
                    """
                    result = await self.db.fetchrow(update_query, guest_cart['id'], user_id)
                    return dict(result)
                
                # Merge items
                guest_items = json.loads(guest_cart['items']) if isinstance(guest_cart['items'], str) else guest_cart['items']
                user_items = json.loads(user_cart['items']) if isinstance(user_cart['items'], str) else user_cart['items']
                
                # Add guest items to user cart
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
                
                # Recalculate totals
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
                
                updated_cart = await self.db.fetchrow(
                    update_query,
                    user_cart['id'],
                    json.dumps(user_items),
                    subtotal,
                    tax_amount,
                    total_amount
                )
                
                # Mark guest cart as merged
                await self.db.execute(
                    "UPDATE cart_sessions SET status = 'merged' WHERE id = $1",
                    guest_cart['id']
                )
                
                cart_dict = dict(updated_cart)
                cart_dict['items'] = user_items
                
                return cart_dict
                
        except Exception as e:
            logger.error(f"Error merging carts: {str(e)}")
            raise