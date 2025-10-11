"""
Promotion Repository Interface and Implementation
Following Repository Pattern from DDD Architecture
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg

from ..entities.promotion import Promotion, PromotionStatus, DiscountType, ApplicableProducts, CustomerSegment, DiscountCode


class IPromotionRepository(ABC):
    """Repository interface for Promotion aggregate"""

    @abstractmethod
    async def save(self, promotion: Promotion) -> Promotion:
        """Save or update a promotion"""
        pass

    @abstractmethod
    async def get_by_id(self, promotion_id: UUID) -> Optional[Promotion]:
        """Get promotion by ID"""
        pass

    @abstractmethod
    async def list_all(
        self,
        store_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        status: Optional[PromotionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Promotion]:
        """List promotions with optional filters"""
        pass

    @abstractmethod
    async def get_active_promotions(
        self,
        store_id: UUID,
        current_time: Optional[datetime] = None
    ) -> List[Promotion]:
        """Get currently active promotions for a store"""
        pass

    @abstractmethod
    async def delete(self, promotion_id: UUID) -> bool:
        """Delete a promotion"""
        pass

    @abstractmethod
    async def get_statistics(
        self,
        store_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get promotion statistics"""
        pass


class AsyncPGPromotionRepository(IPromotionRepository):
    """AsyncPG implementation of promotion repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def save(self, promotion: Promotion) -> Promotion:
        """Save or update promotion"""
        async with self.db_pool.acquire() as conn:
            # Check if exists
            existing = await conn.fetchrow(
                "SELECT id FROM promotions WHERE id = $1",
                promotion.id
            )

            if existing:
                # Update
                await conn.execute("""
                    UPDATE promotions SET
                        store_id = $2,
                        code = $3,
                        name = $4,
                        description = $5,
                        type = $6,
                        value = $7,
                        min_purchase = $8,
                        max_discount = $9,
                        start_date = $10,
                        end_date = $11,
                        usage_limit = $12,
                        times_used = $13,
                        is_active = $14,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """,
                    promotion.id,
                    promotion.store_id,
                    promotion.discount_codes[0].code if promotion.discount_codes else None,
                    promotion.promotion_name,
                    promotion.description,
                    promotion.discount_type.value,
                    float(promotion.discount_value),
                    None,  # min_purchase
                    None,  # max_discount
                    promotion.valid_from,
                    promotion.valid_until,
                    promotion.max_total_uses,
                    promotion.current_total_uses,
                    promotion.status == PromotionStatus.ACTIVE
                )
            else:
                # Insert
                await conn.execute("""
                    INSERT INTO promotions (
                        id, store_id, code, name, description, type, value,
                        start_date, end_date, usage_limit, times_used, is_active,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """,
                    promotion.id,
                    promotion.store_id,
                    promotion.discount_codes[0].code if promotion.discount_codes else None,
                    promotion.promotion_name,
                    promotion.description,
                    promotion.discount_type.value,
                    float(promotion.discount_value),
                    promotion.valid_from,
                    promotion.valid_until,
                    promotion.max_total_uses,
                    promotion.current_total_uses,
                    promotion.status == PromotionStatus.ACTIVE
                )

            return promotion

    async def get_by_id(self, promotion_id: UUID) -> Optional[Promotion]:
        """Get promotion by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM promotions WHERE id = $1",
                promotion_id
            )

            if not row:
                return None

            return self._map_row_to_promotion(row)

    async def list_all(
        self,
        store_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        status: Optional[PromotionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Promotion]:
        """List promotions with filters"""
        async with self.db_pool.acquire() as conn:
            query = "SELECT * FROM promotions WHERE 1=1"
            params = []
            param_idx = 1

            if store_id:
                query += f" AND store_id = ${param_idx}"
                params.append(store_id)
                param_idx += 1

            if status:
                is_active = (status == PromotionStatus.ACTIVE)
                query += f" AND is_active = ${param_idx}"
                params.append(is_active)
                param_idx += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, skip])

            rows = await conn.fetch(query, *params)
            return [self._map_row_to_promotion(row) for row in rows]

    async def get_active_promotions(
        self,
        store_id: UUID,
        current_time: Optional[datetime] = None
    ) -> List[Promotion]:
        """Get currently active promotions"""
        if not current_time:
            current_time = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM promotions
                WHERE store_id = $1
                  AND is_active = true
                  AND start_date <= $2
                  AND (end_date IS NULL OR end_date >= $2)
                ORDER BY created_at DESC
            """, store_id, current_time)

            return [self._map_row_to_promotion(row) for row in rows]

    async def delete(self, promotion_id: UUID) -> bool:
        """Delete promotion"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM promotions WHERE id = $1",
                promotion_id
            )
            return result != "DELETE 0"

    async def get_statistics(
        self,
        store_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive promotion statistics"""
        async with self.db_pool.acquire() as conn:
            # Count promotions by status
            status_query = """
                SELECT
                    COUNT(*) FILTER (WHERE is_active = true) as active,
                    COUNT(*) FILTER (WHERE is_active = false) as inactive,
                    COUNT(*) as total
                FROM promotions
                WHERE 1=1
            """
            params = []
            if store_id:
                status_query += " AND store_id = $1"
                params.append(store_id)

            status_stats = await conn.fetchrow(status_query, *params)

            # Get usage statistics
            usage_query = """
                SELECT
                    COUNT(DISTINCT pu.id) as total_uses,
                    COALESCE(SUM(pu.discount_amount), 0) as total_discount_amount,
                    COALESCE(AVG(pu.discount_amount), 0) as avg_discount_amount,
                    COUNT(DISTINCT p.code) FILTER (WHERE p.code IS NOT NULL) as total_codes
                FROM promotions p
                LEFT JOIN promotion_usage pu ON p.id = pu.promotion_id
                WHERE 1=1
            """
            usage_params = []
            param_idx = 1

            if store_id:
                usage_query += f" AND p.store_id = ${param_idx}"
                usage_params.append(store_id)
                param_idx += 1

            if start_date:
                usage_query += f" AND pu.used_at >= ${param_idx}"
                usage_params.append(start_date)
                param_idx += 1

            if end_date:
                usage_query += f" AND pu.used_at <= ${param_idx}"
                usage_params.append(end_date)

            usage_stats = await conn.fetchrow(usage_query, *usage_params)

            return {
                "pricing_rules": {
                    "total": 0,  # Not implemented yet
                    "active": 0,
                    "inactive": 0
                },
                "promotions": {
                    "total": status_stats['total'],
                    "active": status_stats['active'],
                    "scheduled": 0,  # Would need more complex query
                    "expired": 0,  # Would need date-based query
                    "cancelled": status_stats['inactive']
                },
                "discount_codes": {
                    "total": usage_stats['total_codes'] or 0,
                    "active": status_stats['active'],  # Approximation
                    "total_uses": usage_stats['total_uses'] or 0
                },
                "totals": {
                    "total_discount_amount": float(usage_stats['total_discount_amount'] or 0),
                    "average_discount_percentage": float(usage_stats['avg_discount_amount'] or 0)
                }
            }

    def _map_row_to_promotion(self, row: asyncpg.Record) -> Promotion:
        """Map database row to Promotion aggregate"""
        # Map discount type
        try:
            discount_type = DiscountType(row['type'])
        except (ValueError, KeyError):
            discount_type = DiscountType.PERCENTAGE

        # Create promotion
        promotion = Promotion(
            id=row['id'],
            store_id=row['store_id'],
            tenant_id=row['store_id'],  # Using store_id as fallback for tenant_id
            promotion_name=row['name'],
            description=row['description'],
            status=PromotionStatus.ACTIVE if row['is_active'] else PromotionStatus.PAUSED,
            discount_type=discount_type,
            discount_value=Decimal(str(row['value'])),
            valid_from=row['start_date'],
            valid_until=row['end_date'],
            max_total_uses=row['usage_limit'],
            current_total_uses=row['times_used'] or 0,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

        # Add discount code if exists
        if row.get('code'):
            discount_code = DiscountCode(
                code=row['code'],
                max_uses=row.get('usage_limit'),
                current_uses=row.get('times_used', 0),
                is_active=row['is_active']
            )
            promotion.discount_codes = [discount_code]
            promotion.requires_code = True

        return promotion
