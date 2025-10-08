"""
Inventory Validation and Reservation Service
SRP: Validates inventory availability and reserves stock for orders
KISS: Simple validation with clear error messages
DRY: Reusable validation logic
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)


class InventoryValidationError(Exception):
    """Raised when inventory validation fails"""
    def __init__(self, message: str, unavailable_items: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.unavailable_items = unavailable_items or []


class InventoryValidator:
    """
    Validates and reserves inventory for orders
    SRP: ONLY handles inventory validation and reservation
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def validate_and_reserve(
        self,
        cart_session_id: UUID,
        store_id: UUID
    ) -> Dict[str, Any]:
        """
        Validate all cart items are in stock and reserve them

        Args:
            cart_session_id: Cart session UUID
            store_id: Store UUID to check inventory at

        Returns:
            Dict with validation results and reserved items

        Raises:
            InventoryValidationError: If any items are out of stock
        """
        # 1. Get cart items
        cart_items = await self._get_cart_items(cart_session_id)

        if not cart_items:
            raise InventoryValidationError("Cart is empty")

        # 2. Validate each item's availability
        validation_results = []
        unavailable_items = []

        for item in cart_items:
            sku = item.get('sku')
            requested_qty = int(item.get('quantity', 1))

            # Check inventory
            inventory = await self._get_inventory_item(sku, store_id)

            if not inventory:
                unavailable_items.append({
                    'sku': sku,
                    'name': item.get('name', 'Unknown'),
                    'reason': 'Product not found in inventory',
                    'requested': requested_qty,
                    'available': 0
                })
                continue

            if not inventory['is_available']:
                unavailable_items.append({
                    'sku': sku,
                    'name': inventory['product_name'],
                    'reason': 'Product is not available for sale',
                    'requested': requested_qty,
                    'available': 0
                })
                continue

            available_qty = inventory['quantity_available']

            if available_qty < requested_qty:
                unavailable_items.append({
                    'sku': sku,
                    'name': inventory['product_name'],
                    'reason': 'Insufficient stock',
                    'requested': requested_qty,
                    'available': available_qty
                })
                continue

            # Item is valid
            validation_results.append({
                'sku': sku,
                'name': inventory['product_name'],
                'requested': requested_qty,
                'available': available_qty,
                'price': float(inventory['price']),
                'valid': True
            })

        # 3. If any items unavailable, raise error
        if unavailable_items:
            logger.warning(
                f"Inventory validation failed for cart {cart_session_id}: "
                f"{len(unavailable_items)} items unavailable"
            )
            raise InventoryValidationError(
                f"{len(unavailable_items)} item(s) are unavailable or out of stock",
                unavailable_items=unavailable_items
            )

        # 4. Reserve inventory for all valid items
        try:
            reserved_items = await self._reserve_inventory(validation_results, store_id)
            logger.info(
                f"Successfully reserved {len(reserved_items)} items for cart {cart_session_id}"
            )
        except Exception as e:
            logger.error(f"Failed to reserve inventory: {str(e)}")
            raise InventoryValidationError(f"Failed to reserve inventory: {str(e)}")

        return {
            'valid': True,
            'items_validated': len(validation_results),
            'items_reserved': len(reserved_items),
            'items': validation_results
        }

    async def release_reservation(
        self,
        cart_session_id: UUID,
        store_id: UUID
    ) -> bool:
        """
        Release inventory reservation (e.g., when order fails or is cancelled)

        Args:
            cart_session_id: Cart session UUID
            store_id: Store UUID

        Returns:
            True if successful
        """
        try:
            cart_items = await self._get_cart_items(cart_session_id)

            for item in cart_items:
                sku = item.get('sku')
                quantity = int(item.get('quantity', 1))

                # Restore quantity_available
                await self.db.execute(
                    """
                    UPDATE ocs_inventory
                    SET quantity_available = quantity_available + $1,
                        quantity_reserved = GREATEST(quantity_reserved - $1, 0)
                    WHERE LOWER(TRIM(sku)) = LOWER(TRIM($2))
                    AND store_id = $3
                    """,
                    quantity, sku, store_id
                )

            logger.info(f"Released inventory reservation for cart {cart_session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to release reservation: {str(e)}")
            return False

    async def _get_cart_items(self, cart_session_id: UUID) -> List[Dict[str, Any]]:
        """Get cart items"""
        # Query by session_id (VARCHAR), not id (UUID primary key)
        # The cart_session_id parameter is the session_id from the client
        query = """
            SELECT items
            FROM cart_sessions
            WHERE session_id = $1 AND status = 'active'
        """

        result = await self.db.fetchrow(query, str(cart_session_id))

        if not result:
            return []

        items = result['items']
        if isinstance(items, str):
            items = json.loads(items)

        return items

    async def _get_inventory_item(
        self,
        sku: str,
        store_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get inventory item details"""
        query = """
            SELECT
                sku,
                product_name,
                COALESCE(override_price, retail_price) as price,
                quantity_available,
                quantity_reserved,
                is_available
            FROM ocs_inventory
            WHERE LOWER(TRIM(sku)) = LOWER(TRIM($1))
            AND store_id = $2
            LIMIT 1
        """

        result = await self.db.fetchrow(query, sku, store_id)

        if result:
            return dict(result)

        return None

    async def _reserve_inventory(
        self,
        items: List[Dict[str, Any]],
        store_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Reserve inventory by decrementing quantity_available and incrementing quantity_reserved

        Args:
            items: List of validated items to reserve
            store_id: Store UUID

        Returns:
            List of successfully reserved items
        """
        reserved_items = []

        for item in items:
            sku = item['sku']
            quantity = item['requested']

            # Atomic update with optimistic locking
            result = await self.db.execute(
                """
                UPDATE ocs_inventory
                SET quantity_available = quantity_available - $1,
                    quantity_reserved = quantity_reserved + $1,
                    updated_at = NOW()
                WHERE LOWER(TRIM(sku)) = LOWER(TRIM($2))
                AND store_id = $3
                AND quantity_available >= $1
                RETURNING sku
                """,
                quantity, sku, store_id
            )

            # Check if update succeeded (optimistic lock check)
            if result == "UPDATE 1":
                reserved_items.append(item)
                logger.debug(f"Reserved {quantity}x {sku}")
            else:
                # Inventory changed between validation and reservation
                logger.error(
                    f"Failed to reserve {sku}: "
                    "inventory changed between validation and reservation"
                )
                # Rollback previous reservations
                await self._rollback_reservations(reserved_items, store_id)
                raise InventoryValidationError(
                    f"Inventory changed during checkout. Please try again."
                )

        return reserved_items

    async def _rollback_reservations(
        self,
        reserved_items: List[Dict[str, Any]],
        store_id: UUID
    ) -> None:
        """Rollback inventory reservations"""
        for item in reserved_items:
            sku = item['sku']
            quantity = item['requested']

            await self.db.execute(
                """
                UPDATE ocs_inventory
                SET quantity_available = quantity_available + $1,
                    quantity_reserved = quantity_reserved - $1
                WHERE LOWER(TRIM(sku)) = LOWER(TRIM($2))
                AND store_id = $3
                """,
                quantity, sku, store_id
            )

        logger.info(f"Rolled back {len(reserved_items)} inventory reservations")
