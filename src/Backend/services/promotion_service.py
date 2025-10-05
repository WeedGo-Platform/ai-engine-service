"""
Promotion and Pricing Service
Handles all pricing calculations, promotions, discounts, and recommendations
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
import asyncpg
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)


class PromotionType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo"
    BUNDLE = "bundle"
    TIERED = "tiered"


class DiscountType(Enum):
    PERCENTAGE = "percentage"
    AMOUNT = "amount"


class PromotionService:
    """Service for managing promotions and pricing"""
    
    def __init__(self, db_pool):
        """Initialize promotion service with database connection pool"""
        self.db_pool = db_pool
    
    async def get_customer_tier(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get customer's price tier"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT pt.*, cpr.custom_markup_percentage, cpr.volume_discounts
                FROM customer_pricing_rules cpr
                JOIN price_tiers pt ON cpr.price_tier_id = pt.id
                WHERE cpr.tenant_id = $1 AND cpr.active = true
                ORDER BY pt.priority DESC
                LIMIT 1
            """
            tier = await conn.fetchrow(query, tenant_id)
            
            if not tier:
                # Get default retail tier
                tier = await conn.fetchrow(
                    "SELECT * FROM price_tiers WHERE customer_type = 'retail' AND name = 'Retail'"
                )
            
            return dict(tier) if tier else None
    
    async def get_applicable_promotions(
        self,
        product_ids: List[str] = None,
        categories: List[str] = None,
        tenant_id: UUID = None,
        store_id: UUID = None,
        order_total: Decimal = Decimal('0')
    ) -> List[Dict[str, Any]]:
        """
        Get all applicable promotions for given criteria.
        Enhanced to support store/tenant scoping, continuous promotions, and time windows.
        """
        async with self.db_pool.acquire() as conn:
            current_time = datetime.now()  # Use naive datetime for PostgreSQL compatibility
            current_hour = current_time.hour
            current_day = current_time.weekday()  # 0=Monday
            current_time_only = current_time.time()

            query = """
                SELECT * FROM promotions
                WHERE active = true
                  -- Date range check
                  AND start_date <= $1
                  AND (
                      -- Continuous promotions (no end date)
                      (is_continuous = true AND end_date IS NULL)
                      OR
                      -- Time-limited promotions
                      (is_continuous = false AND (end_date IS NULL OR end_date >= $1))
                  )
                  -- Minimum purchase check
                  AND (min_purchase_amount IS NULL OR min_purchase_amount <= $2)
                  -- Product/category applicability
                  AND (
                      applies_to = 'all'
                      OR ($3::text[] && product_ids)
                      OR ($4::text[] && category_ids)
                  )
                  -- Store/Tenant scoping
                  AND (
                      -- Global promotions
                      (store_id IS NULL AND tenant_id IS NULL)
                      OR
                      -- Store-specific promotions
                      (store_id = $7 AND tenant_id IS NULL)
                      OR
                      -- Tenant-specific promotions
                      (tenant_id = $8 AND store_id IS NULL)
                      OR
                      -- Tenant+Store specific
                      (store_id = $7 AND tenant_id = $8)
                  )
                  -- Day of week check
                  AND (day_of_week IS NULL OR $5 = ANY(day_of_week))
                  -- Time window check (new - uses time_start/time_end)
                  AND (
                      (time_start IS NULL AND time_end IS NULL)
                      OR
                      ($6 >= time_start AND $6 <= time_end)
                  )
                ORDER BY priority DESC, discount_value DESC
            """

            promotions = await conn.fetch(
                query,
                current_time,
                order_total,
                product_ids or [],
                categories or [],
                current_day,
                current_time_only,
                store_id,
                tenant_id
            )

            return [dict(p) for p in promotions]
    
    async def validate_discount_code(self, code: str, tenant_id: UUID = None, store_id: UUID = None) -> Dict[str, Any]:
        """
        Validate a discount code with store/tenant restrictions.
        A promo code is valid if:
        - It's active and not expired
        - It's either global (no store/tenant), or matches the cart's store/tenant
        """
        async with self.db_pool.acquire() as conn:
            # Check if code exists and is valid
            query = """
                SELECT dc.*, p.*
                FROM discount_codes dc
                LEFT JOIN promotions p ON dc.promotion_id = p.id
                WHERE dc.code = $1
                AND dc.used = false
                AND (dc.valid_until IS NULL OR dc.valid_until > CURRENT_TIMESTAMP)
                AND (dc.tenant_id IS NULL OR dc.tenant_id = $2)
            """

            result = await conn.fetchrow(query, code.upper(), tenant_id)

            if not result:
                # Check if it's a general promotion code with store/tenant validation
                query = """
                    SELECT * FROM promotions
                    WHERE code = $1
                    AND active = true
                    AND CURRENT_TIMESTAMP BETWEEN start_date AND COALESCE(end_date, CURRENT_TIMESTAMP + INTERVAL '1 day')
                    AND (
                        -- Global promotions (no store/tenant restrictions)
                        (store_id IS NULL AND tenant_id IS NULL)
                        OR
                        -- Store-specific promotions
                        (store_id = $2 AND tenant_id IS NULL)
                        OR
                        -- Tenant-specific promotions
                        (tenant_id = $3 AND store_id IS NULL)
                        OR
                        -- Tenant+Store specific
                        (store_id = $2 AND tenant_id = $3)
                    )
                """
                result = await conn.fetchrow(query, code.upper(), store_id, tenant_id)

            if result:
                return {
                    'valid': True,
                    'code': code.upper(),
                    'discount_type': result['discount_type'],
                    'discount_value': float(result['discount_value']),
                    'promotion_name': result.get('name'),
                    'promotion_id': str(result.get('id')) if result.get('id') else None,
                    'store_id': str(result.get('store_id')) if result.get('store_id') else None,
                    'tenant_id': str(result.get('tenant_id')) if result.get('tenant_id') else None
                }

            return {'valid': False, 'code': code.upper(), 'error': 'This promo code is not valid or has expired'}
    
    async def calculate_product_price(
        self,
        product_id: str,
        quantity: int,
        tenant_id: UUID = None
    ) -> Dict[str, Any]:
        """Calculate final price for a product with all applicable discounts"""
        async with self.db_pool.acquire() as conn:
            # Get base price
            product = await conn.fetchrow(
                "SELECT unit_price, category FROM product_catalog WHERE ocs_variant_number = $1",
                product_id
            )
            
            if not product:
                return None
            
            base_price = Decimal(str(product['unit_price'])) * quantity
            
            # Get customer tier discount
            tier = await self.get_customer_tier(tenant_id) if tenant_id else None
            tier_discount = Decimal('0')
            if tier:
                tier_discount = base_price * Decimal(str(tier['discount_percentage'])) / 100
            
            # Get volume discount
            volume_discount = self._calculate_volume_discount(base_price, quantity)
            
            # Get applicable promotions
            promotions = await self.get_applicable_promotions(
                product_ids=[product_id],
                categories=[product['category']],
                tenant_id=tenant_id,
                order_total=base_price
            )
            
            promo_discount = Decimal('0')
            applied_promotions = []
            
            for promo in promotions:
                if promo['discount_type'] == 'percentage':
                    discount = base_price * Decimal(str(promo['discount_value'])) / 100
                else:
                    discount = Decimal(str(promo['discount_value']))
                
                # Check if stackable or if it's the first promotion
                if not applied_promotions or promo.get('stackable', False):
                    promo_discount += discount
                    applied_promotions.append({
                        'name': promo['name'],
                        'discount': float(discount)
                    })
            
            # Calculate final price
            total_discount = tier_discount + volume_discount + promo_discount
            final_price = base_price - total_discount
            
            return {
                'product_id': product_id,
                'quantity': quantity,
                'base_price': float(base_price),
                'tier_discount': float(tier_discount),
                'volume_discount': float(volume_discount),
                'promo_discount': float(promo_discount),
                'total_discount': float(total_discount),
                'final_price': float(max(final_price, Decimal('0'))),
                'applied_promotions': applied_promotions,
                'savings_percentage': float((total_discount / base_price * 100)) if base_price > 0 else 0
            }
    
    def _calculate_volume_discount(self, base_price: Decimal, quantity: int) -> Decimal:
        """Calculate volume-based discount"""
        if quantity >= 100:
            return base_price * Decimal('0.10')  # 10% off
        elif quantity >= 50:
            return base_price * Decimal('0.07')  # 7% off
        elif quantity >= 20:
            return base_price * Decimal('0.05')  # 5% off
        elif quantity >= 10:
            return base_price * Decimal('0.03')  # 3% off
        return Decimal('0')
    
    async def get_bundle_deals(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get available bundle deals"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM bundle_deals
                WHERE ($1 = false OR active = true)
                AND (start_date IS NULL OR start_date <= CURRENT_TIMESTAMP)
                AND (end_date IS NULL OR end_date >= CURRENT_TIMESTAMP)
                ORDER BY savings_amount DESC
            """
            
            bundles = await conn.fetch(query, active_only)
            return [dict(b) for b in bundles]
    
    async def create_promotion(
        self,
        promotion_data: Dict[str, Any],
        created_by_user_id: UUID = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Create a new promotion with enhanced fields and permission validation.

        Args:
            promotion_data: Promotion details
            created_by_user_id: ID of user creating the promotion
            user_role: Role of user (platform_admin, tenant_admin, store_manager)

        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks permission
        """
        # Validate continuous promotion
        if promotion_data.get('is_continuous') and promotion_data.get('end_date'):
            raise ValueError("Continuous promotions cannot have an end_date")

        # Validate time windows
        time_start = promotion_data.get('time_start')
        time_end = promotion_data.get('time_end')
        if time_start and time_end:
            if time_start >= time_end:
                raise ValueError("time_start must be before time_end")
        elif (time_start and not time_end) or (time_end and not time_start):
            raise ValueError("Both time_start and time_end must be provided together")

        # Validate recurrence logic
        recurrence_type = promotion_data.get('recurrence_type', 'none')
        if recurrence_type == 'weekly' and not promotion_data.get('day_of_week'):
            raise ValueError("Weekly recurrence requires day_of_week to be specified")

        # Permission validation
        if user_role == 'store_manager':
            if not promotion_data.get('store_id'):
                raise PermissionError("Store managers must specify a store_id")
            if promotion_data.get('tenant_id'):
                raise PermissionError("Store managers cannot create tenant-specific promotions")
        elif user_role == 'tenant_admin':
            if not promotion_data.get('tenant_id'):
                raise PermissionError("Tenant admins must specify tenant_id")
            # Tenant admins can optionally restrict to specific stores they own
        # platform_admin has no restrictions

        async with self.db_pool.acquire() as conn:
            # Parse dates and ensure they're naive (PostgreSQL TIMESTAMP without timezone)
            start_date = promotion_data['start_date']
            if isinstance(start_date, str):
                # Parse ISO format and remove timezone info for PostgreSQL
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if start_date.tzinfo is not None:
                    start_date = start_date.replace(tzinfo=None)
            elif start_date.tzinfo is not None:
                # Remove timezone info if datetime object is timezone-aware
                start_date = start_date.replace(tzinfo=None)

            end_date = promotion_data.get('end_date')
            if end_date:
                if isinstance(end_date, str):
                    # Parse ISO format and remove timezone info for PostgreSQL
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if end_date.tzinfo is not None:
                        end_date = end_date.replace(tzinfo=None)
                elif end_date.tzinfo is not None:
                    # Remove timezone info if datetime object is timezone-aware
                    end_date = end_date.replace(tzinfo=None)

            # Parse time_start and time_end strings to time objects for PostgreSQL TIME columns
            from datetime import time as time_type
            time_start = promotion_data.get('time_start')
            if time_start and isinstance(time_start, str):
                # Parse "HH:MM" or "HH:MM:SS" format to time object
                time_parts = time_start.split(':')
                time_start = time_type(
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]),
                    second=int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            time_end = promotion_data.get('time_end')
            if time_end and isinstance(time_end, str):
                # Parse "HH:MM" or "HH:MM:SS" format to time object
                time_parts = time_end.split(':')
                time_end = time_type(
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]),
                    second=int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            query = """
                INSERT INTO promotions (
                    code, name, description, type, discount_type, discount_value,
                    min_purchase_amount, max_discount_amount, usage_limit_per_customer,
                    total_usage_limit, applies_to, category_ids, brand_ids, product_ids,
                    stackable, priority, start_date, end_date, active,
                    day_of_week, hour_of_day, first_time_customer_only,
                    store_id, tenant_id, created_by_user_id,
                    is_continuous, recurrence_type, time_start, time_end, timezone
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                    $15, $16, $17, $18, $19, $20, $21, $22,
                    $23, $24, $25,
                    $26, $27, $28, $29, $30
                ) RETURNING *
            """

            result = await conn.fetchrow(
                query,
                promotion_data.get('code'),
                promotion_data['name'],
                promotion_data.get('description'),
                promotion_data['type'],
                promotion_data['discount_type'],
                promotion_data['discount_value'],
                promotion_data.get('min_purchase_amount'),
                promotion_data.get('max_discount_amount'),
                promotion_data.get('usage_limit_per_customer'),
                promotion_data.get('total_usage_limit'),
                promotion_data.get('applies_to', 'all'),
                promotion_data.get('category_ids', []),
                promotion_data.get('brand_ids', []),
                promotion_data.get('product_ids', []),
                promotion_data.get('stackable', False),
                promotion_data.get('priority', 0),
                start_date,
                end_date,
                promotion_data.get('active', True),
                promotion_data.get('day_of_week'),
                promotion_data.get('hour_of_day'),
                promotion_data.get('first_time_customer_only', False),
                # New fields
                promotion_data.get('store_id'),
                promotion_data.get('tenant_id'),
                created_by_user_id,
                promotion_data.get('is_continuous', False),
                promotion_data.get('recurrence_type', 'none'),
                time_start,  # Use parsed time object
                time_end,    # Use parsed time object
                promotion_data.get('timezone', 'America/Toronto')
            )

            logger.info(f"Created promotion: {result['name']} (ID: {result['id']})")
            return dict(result)
    
    async def track_promotion_usage(
        self,
        promotion_id: UUID,
        tenant_id: UUID,
        order_id: UUID,
        discount_amount: Decimal,
        order_total: Decimal
    ):
        """Track when a promotion is used"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO promotion_usage (
                    promotion_id, tenant_id, order_id, discount_amount, order_total
                ) VALUES ($1, $2, $3, $4, $5)
            """, promotion_id, tenant_id, order_id, discount_amount, order_total)
            
            # Update promotion usage count
            await conn.execute("""
                UPDATE promotions 
                SET times_used = times_used + 1 
                WHERE id = $1
            """, promotion_id)
    
    async def get_promotion_analytics(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get analytics on promotion performance"""
        async with self.db_pool.acquire() as conn:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get promotion usage stats
            query = """
                SELECT 
                    p.name,
                    p.code,
                    p.discount_type,
                    p.discount_value,
                    COUNT(pu.id) as times_used,
                    SUM(pu.discount_amount) as total_discount_given,
                    SUM(pu.order_total) as total_revenue,
                    AVG(pu.discount_amount) as avg_discount,
                    AVG(pu.order_total) as avg_order_value
                FROM promotions p
                LEFT JOIN promotion_usage pu ON p.id = pu.promotion_id
                WHERE pu.used_at BETWEEN $1 AND $2
                GROUP BY p.id, p.name, p.code, p.discount_type, p.discount_value
                ORDER BY times_used DESC
            """
            
            stats = await conn.fetch(query, start_date, end_date)
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'promotions': [dict(s) for s in stats]
            }
    
    async def update_price_tier_assignment(
        self,
        tenant_id: UUID,
        tier_id: UUID,
        custom_rules: Dict[str, Any] = None
    ):
        """Update customer's price tier assignment"""
        async with self.db_pool.acquire() as conn:
            # Check if customer pricing rule exists
            existing = await conn.fetchrow(
                "SELECT id FROM customer_pricing_rules WHERE tenant_id = $1",
                tenant_id
            )
            
            if existing:
                # Update existing
                await conn.execute("""
                    UPDATE customer_pricing_rules
                    SET price_tier_id = $1,
                        custom_markup_percentage = $2,
                        volume_discounts = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = $4
                """, tier_id, 
                    custom_rules.get('custom_markup_percentage') if custom_rules else None,
                    json.dumps(custom_rules.get('volume_discounts')) if custom_rules else None,
                    tenant_id)
            else:
                # Create new
                await conn.execute("""
                    INSERT INTO customer_pricing_rules (
                        tenant_id, price_tier_id, custom_markup_percentage, volume_discounts
                    ) VALUES ($1, $2, $3, $4)
                """, tenant_id, tier_id,
                    custom_rules.get('custom_markup_percentage') if custom_rules else None,
                    json.dumps(custom_rules.get('volume_discounts')) if custom_rules else None)
    
    async def calculate_cart_discounts(
        self,
        cart_items: List[Dict[str, Any]],
        tenant_id: UUID = None,
        discount_codes: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate all discounts for a shopping cart"""
        subtotal = Decimal('0')
        total_discount = Decimal('0')
        item_discounts = []
        
        # Get customer tier
        tier = await self.get_customer_tier(tenant_id) if tenant_id else None
        
        # Process each item
        for item in cart_items:
            price_calc = await self.calculate_product_price(
                item['sku'],
                item['quantity'],
                tenant_id
            )
            
            if price_calc:
                subtotal += Decimal(str(price_calc['base_price']))
                total_discount += Decimal(str(price_calc['total_discount']))
                item_discounts.append(price_calc)
        
        # Apply discount codes
        code_discounts = Decimal('0')
        applied_codes = []
        
        if discount_codes:
            for code in discount_codes:
                validation = await self.validate_discount_code(code, tenant_id)
                if validation['valid']:
                    if validation['discount_type'] == 'percentage':
                        discount = subtotal * Decimal(str(validation['discount_value'])) / 100
                    else:
                        discount = Decimal(str(validation['discount_value']))
                    
                    code_discounts += discount
                    applied_codes.append({
                        'code': code,
                        'discount': float(discount),
                        'name': validation.get('promotion_name')
                    })
        
        total_discount += code_discounts
        final_total = subtotal - total_discount
        
        return {
            'subtotal': float(subtotal),
            'tier_name': tier['name'] if tier else 'Retail',
            'tier_discount': float(tier['discount_percentage']) if tier else 0,
            'total_discount': float(total_discount),
            'code_discounts': float(code_discounts),
            'final_total': float(max(final_total, Decimal('0'))),
            'savings_percentage': float((total_discount / subtotal * 100)) if subtotal > 0 else 0,
            'item_discounts': item_discounts,
            'applied_codes': applied_codes
        }