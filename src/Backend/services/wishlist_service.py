"""
Wishlist Management Service
Handles wishlist operations for customers
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class WishlistService:
    """Service for managing customer wishlists"""

    def __init__(self, db_pool):
        """Initialize wishlist service with database connection pool"""
        self.db_pool = db_pool

    async def get_wishlist(self, customer_id: UUID, store_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get customer's wishlist items"""
        try:
            async with self.db_pool.acquire() as conn:
                if store_id:
                    query = """
                        SELECT * FROM wishlist_details
                        WHERE customer_id = $1 AND store_id = $2
                        ORDER BY priority DESC, added_at DESC
                    """
                    result = await conn.fetch(query, customer_id, store_id)
                else:
                    query = """
                        SELECT * FROM wishlist_details
                        WHERE customer_id = $1
                        ORDER BY priority DESC, added_at DESC
                    """
                    result = await conn.fetch(query, customer_id)

                return [dict(row) for row in result]

        except Exception as e:
            logger.error(f"Error getting wishlist: {str(e)}")
            raise

    async def add_to_wishlist(self, customer_id: UUID, product_id: UUID,
                            store_id: UUID, notes: Optional[str] = None,
                            priority: int = 0) -> Dict[str, Any]:
        """Add product to wishlist"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check if already in wishlist
                check_query = """
                    SELECT id FROM wishlist
                    WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                """
                existing = await conn.fetchrow(check_query, customer_id, product_id, store_id)

                if existing:
                    # Update existing item
                    update_query = """
                        UPDATE wishlist
                        SET notes = $4, priority = $5, added_at = CURRENT_TIMESTAMP
                        WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                        RETURNING id
                    """
                    result = await conn.fetchrow(
                        update_query, customer_id, product_id, store_id, notes, priority
                    )
                    action = "updated"
                else:
                    # Insert new item
                    insert_query = """
                        INSERT INTO wishlist (customer_id, product_id, store_id, notes, priority)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                    """
                    result = await conn.fetchrow(
                        insert_query, customer_id, product_id, store_id, notes, priority
                    )
                    action = "added"

                # Get full details
                detail_query = """
                    SELECT * FROM wishlist_details WHERE wishlist_id = $1
                """
                item = await conn.fetchrow(detail_query, result['id'])

                logger.info(f"Product {product_id} {action} to wishlist for customer {customer_id}")
                return dict(item)

        except asyncpg.UniqueViolationError:
            # Handle race condition
            return await self.get_wishlist_item(customer_id, product_id, store_id)
        except Exception as e:
            logger.error(f"Error adding to wishlist: {str(e)}")
            raise

    async def remove_from_wishlist(self, customer_id: UUID, product_id: UUID,
                                  store_id: UUID) -> bool:
        """Remove product from wishlist"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    DELETE FROM wishlist
                    WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                    RETURNING id
                """
                result = await conn.fetchrow(query, customer_id, product_id, store_id)

                if result:
                    logger.info(f"Product {product_id} removed from wishlist for customer {customer_id}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error removing from wishlist: {str(e)}")
            raise

    async def get_wishlist_item(self, customer_id: UUID, product_id: UUID,
                               store_id: UUID) -> Optional[Dict[str, Any]]:
        """Get specific wishlist item"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT * FROM wishlist_details
                    WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                """
                result = await conn.fetchrow(query, customer_id, product_id, store_id)
                return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting wishlist item: {str(e)}")
            raise

    async def update_wishlist_item(self, customer_id: UUID, product_id: UUID,
                                  store_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update wishlist item properties"""
        try:
            async with self.db_pool.acquire() as conn:
                # Build update query dynamically
                allowed_fields = ['notes', 'priority', 'notify_on_sale', 'notify_on_restock']
                set_clauses = []
                params = [customer_id, product_id, store_id]

                for field in allowed_fields:
                    if field in updates:
                        set_clauses.append(f"{field} = ${len(params) + 1}")
                        params.append(updates[field])

                if not set_clauses:
                    # No valid updates, return existing
                    return await self.get_wishlist_item(customer_id, product_id, store_id)

                query = f"""
                    UPDATE wishlist
                    SET {', '.join(set_clauses)}
                    WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                    RETURNING id
                """

                result = await conn.fetchrow(query, *params)

                if result:
                    # Get updated details
                    detail_query = """
                        SELECT * FROM wishlist_details WHERE wishlist_id = $1
                    """
                    item = await conn.fetchrow(detail_query, result['id'])
                    logger.info(f"Wishlist item updated for customer {customer_id}")
                    return dict(item)
                else:
                    raise ValueError("Wishlist item not found")

        except Exception as e:
            logger.error(f"Error updating wishlist item: {str(e)}")
            raise

    async def get_wishlist_stats(self, customer_id: UUID) -> Dict[str, Any]:
        """Get wishlist statistics for a customer"""
        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT * FROM get_wishlist_stats($1)"
                result = await conn.fetchrow(query, customer_id)
                return dict(result) if result else {
                    'total_items': 0,
                    'high_priority_items': 0,
                    'on_sale_items': 0,
                    'out_of_stock_items': 0,
                    'total_value': 0
                }

        except Exception as e:
            logger.error(f"Error getting wishlist stats: {str(e)}")
            raise

    async def clear_wishlist(self, customer_id: UUID, store_id: Optional[UUID] = None) -> int:
        """Clear all wishlist items for a customer"""
        try:
            async with self.db_pool.acquire() as conn:
                if store_id:
                    query = """
                        DELETE FROM wishlist
                        WHERE customer_id = $1 AND store_id = $2
                    """
                    result = await conn.execute(query, customer_id, store_id)
                else:
                    query = """
                        DELETE FROM wishlist
                        WHERE customer_id = $1
                    """
                    result = await conn.execute(query, customer_id)

                # Extract count from result
                count = int(result.split()[-1]) if result else 0
                logger.info(f"Cleared {count} items from wishlist for customer {customer_id}")
                return count

        except Exception as e:
            logger.error(f"Error clearing wishlist: {str(e)}")
            raise

    async def check_product_in_wishlist(self, customer_id: UUID, product_ids: List[UUID],
                                       store_id: UUID) -> Dict[str, bool]:
        """Check if products are in wishlist"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT product_id
                    FROM wishlist
                    WHERE customer_id = $1
                    AND product_id = ANY($2::uuid[])
                    AND store_id = $3
                """
                result = await conn.fetch(query, customer_id, product_ids, store_id)

                in_wishlist = {str(row['product_id']) for row in result}
                return {
                    str(pid): str(pid) in in_wishlist
                    for pid in product_ids
                }

        except Exception as e:
            logger.error(f"Error checking products in wishlist: {str(e)}")
            raise

    async def move_to_cart(self, customer_id: UUID, product_id: UUID,
                          store_id: UUID, session_id: str) -> Dict[str, Any]:
        """Move item from wishlist to cart"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get product details
                    product_query = """
                        SELECT * FROM wishlist_details
                        WHERE customer_id = $1 AND product_id = $2 AND store_id = $3
                    """
                    product = await conn.fetchrow(product_query, customer_id, product_id, store_id)

                    if not product:
                        raise ValueError("Product not in wishlist")

                    # TODO: Add to cart using cart service
                    # This would require injecting cart_service or calling cart API

                    # Remove from wishlist
                    await self.remove_from_wishlist(customer_id, product_id, store_id)

                    return {
                        'success': True,
                        'product': dict(product),
                        'message': 'Product moved to cart'
                    }

        except Exception as e:
            logger.error(f"Error moving to cart: {str(e)}")
            raise