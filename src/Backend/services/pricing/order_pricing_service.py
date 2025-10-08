"""
Order Pricing Service
SRP: Calculates order totals, taxes, fees
KISS: Simple, clear calculation logic
DRY: Reusable across order creation and updates
"""

from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
import logging
import json

logger = logging.getLogger(__name__)


class PricingConfig:
    """Pricing configuration constants"""
    TAX_RATE = Decimal('0.13')  # 13% HST for Ontario
    MIN_ORDER_AMOUNT = Decimal('0.00')  # No minimum for now
    DELIVERY_BASE_FEE = Decimal('5.00')
    DELIVERY_PER_KM = Decimal('0.50')
    FREE_DELIVERY_THRESHOLD = Decimal('100.00')


class OrderPricingService:
    """
    Calculates order pricing components
    SRP: ONLY handles price calculations
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def calculate_order_totals(
        self,
        cart_session_id: UUID,
        delivery_type: str,
        delivery_address: Dict[str, Any] = None,
        promo_code: str = None
    ) -> Dict[str, Any]:
        """
        Calculate all order totals from cart

        Args:
            cart_session_id: Cart session UUID
            delivery_type: 'delivery' or 'pickup'
            delivery_address: Delivery address dict (for distance calculation)
            promo_code: Promotional code if any

        Returns:
            Dict with subtotal, tax, delivery_fee, discount, total
        """
        # 1. Get cart items and validate
        cart_items = await self._get_cart_items(cart_session_id)

        if not cart_items:
            raise ValueError("Cart is empty")

        # 2. Calculate subtotal from current product prices
        subtotal = await self._calculate_subtotal(cart_items)

        # 3. Calculate discount
        discount = await self._calculate_discount(subtotal, promo_code)

        # 4. Calculate delivery fee
        delivery_fee = Decimal('0.00')
        if delivery_type == 'delivery':
            delivery_fee = await self._calculate_delivery_fee(
                subtotal,
                delivery_address
            )

        # 5. Calculate tax (on subtotal - discount, NOT on delivery)
        taxable_amount = subtotal - discount
        tax = self._calculate_tax(taxable_amount)

        # 6. Calculate grand total
        total = subtotal - discount + tax + delivery_fee

        logger.info(
            f"Order totals calculated - Subtotal: ${subtotal}, "
            f"Tax: ${tax}, Delivery: ${delivery_fee}, "
            f"Discount: ${discount}, Total: ${total}"
        )

        return {
            'subtotal': float(subtotal),
            'tax': float(tax),
            'delivery_fee': float(delivery_fee),
            'discount': float(discount),
            'total': float(total),
            'items': cart_items  # Return items with current prices
        }

    async def _get_cart_items(self, cart_session_id: UUID) -> List[Dict[str, Any]]:
        """Get cart items with current prices from inventory"""
        # Query by session_id (VARCHAR) not id (UUID primary key)
        # The cart_session_id parameter is actually the session_id string from the frontend
        query = """
            SELECT items, store_id
            FROM cart_sessions
            WHERE session_id = $1 AND status = 'active'
        """

        result = await self.db.fetchrow(query, str(cart_session_id))

        if not result:
            raise ValueError("Cart session not found or not active")

        items = result['items']
        store_id = result['store_id']

        if isinstance(items, str):
            items = json.loads(items)

        # Get current prices for each item
        enriched_items = []
        for item in items:
            current_price = await self._get_current_price(item['sku'], store_id)
            quantity = Decimal(str(item.get('quantity', 1)))
            line_total = current_price * quantity

            enriched_items.append({
                **item,
                'current_price': float(current_price),
                'line_total': float(line_total)
            })

        return enriched_items

    async def _get_current_price(self, sku: str, store_id: UUID = None) -> Decimal:
        """Get current price from inventory"""
        # Use override_price if set, otherwise use retail_price
        query = """
            SELECT COALESCE(override_price, retail_price) as price
            FROM ocs_inventory
            WHERE LOWER(TRIM(sku)) = LOWER(TRIM($1))
            AND is_available = true
        """

        params = [sku]

        if store_id:
            query += " AND store_id = $2"
            params.append(store_id)

        query += " LIMIT 1"

        result = await self.db.fetchrow(query, *params)

        if not result:
            logger.warning(f"SKU {sku} not found in inventory")
            return Decimal('0.00')

        return Decimal(str(result['price']))

    async def _calculate_subtotal(self, items: List[Dict[str, Any]]) -> Decimal:
        """Calculate subtotal from line totals"""
        subtotal = sum(
            Decimal(str(item.get('line_total', 0)))
            for item in items
        )
        return subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_tax(self, taxable_amount: Decimal) -> Decimal:
        """Calculate tax on taxable amount"""
        tax = Decimal(str(taxable_amount)) * PricingConfig.TAX_RATE
        return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    async def _calculate_delivery_fee(
        self,
        subtotal: Decimal,
        delivery_address: Dict[str, Any]
    ) -> Decimal:
        """Calculate delivery fee based on distance and subtotal"""
        # Free delivery over threshold
        if subtotal >= PricingConfig.FREE_DELIVERY_THRESHOLD:
            return Decimal('0.00')

        # Get distance from store to address
        distance_km = await self._calculate_delivery_distance(delivery_address)

        # Base fee + per-km charge
        fee = PricingConfig.DELIVERY_BASE_FEE + (
            Decimal(str(distance_km)) * PricingConfig.DELIVERY_PER_KM
        )

        return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    async def _calculate_delivery_distance(
        self,
        delivery_address: Dict[str, Any]
    ) -> float:
        """Calculate distance from store to delivery address"""
        # Placeholder - would use geocoding API
        # For now, return flat rate distance
        return 5.0  # 5 km default

    async def _calculate_discount(
        self,
        subtotal: Decimal,
        promo_code: str = None
    ) -> Decimal:
        """Calculate discount from promo code"""
        if not promo_code:
            return Decimal('0.00')

        # Query promo code from database
        query = """
            SELECT discount_type, discount_value, min_order_amount
            FROM promo_codes
            WHERE code = $1
            AND is_active = true
            AND (expires_at IS NULL OR expires_at > NOW())
        """

        result = await self.db.fetchrow(query, promo_code.upper())

        if not result:
            logger.warning(f"Invalid or expired promo code: {promo_code}")
            return Decimal('0.00')

        # Check minimum order requirement
        min_amount = Decimal(str(result['min_order_amount'] or 0))
        if subtotal < min_amount:
            logger.info(
                f"Promo code {promo_code} requires minimum ${min_amount}, "
                f"current: ${subtotal}"
            )
            return Decimal('0.00')

        # Calculate discount
        discount_type = result['discount_type']
        discount_value = Decimal(str(result['discount_value']))

        if discount_type == 'percentage':
            discount = subtotal * (discount_value / Decimal('100'))
        else:  # fixed
            discount = discount_value

        # Don't exceed subtotal
        discount = min(discount, subtotal)

        return discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
