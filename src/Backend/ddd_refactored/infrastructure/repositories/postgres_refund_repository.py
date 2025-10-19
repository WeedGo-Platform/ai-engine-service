"""
PostgreSQL Refund Repository Implementation

AsyncPG-based implementation of PaymentRefundRepository interface.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from ...domain.payment_processing.repositories import PaymentRefundRepository
from ...domain.payment_processing.entities import PaymentRefund
from ...domain.payment_processing.value_objects import Money
from ...domain.payment_processing.exceptions import DuplicateTransactionError


class PostgresRefundRepository(PaymentRefundRepository):
    """
    PostgreSQL implementation of PaymentRefundRepository using AsyncPG.

    Responsibilities:
    - Map refund entities to/from database rows
    - Execute SQL queries asynchronously
    - Handle domain events (publish after save)
    - Manage database transactions
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize repository with database connection pool.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool

    async def save(self, refund: PaymentRefund) -> None:
        """
        Save payment refund (insert or update).

        Args:
            refund: PaymentRefund entity to save

        Raises:
            DuplicateTransactionError: If refund reference already exists
        """
        async with self.db_pool.acquire() as conn:
            # Check for existing refund
            existing = await conn.fetchrow(
                "SELECT id FROM payment_refunds WHERE id = $1",
                refund.id
            )

            if existing:
                # Update existing
                await self._update_refund(conn, refund)
            else:
                # Insert new
                await self._insert_refund(conn, refund)

    async def _insert_refund(
        self,
        conn: asyncpg.Connection,
        refund: PaymentRefund
    ) -> None:
        """Insert new refund into database."""
        try:
            await conn.execute(
                """
                INSERT INTO payment_refunds (
                    id, refund_reference, transaction_id, amount, currency,
                    reason, status, provider_refund_id, provider_response,
                    error_message, created_by, notes,
                    created_at, processed_at, completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15
                )
                """,
                refund.id,
                refund.refund_reference,
                refund.transaction_id,
                refund.amount.amount,
                refund.amount.currency,
                refund.reason,
                refund.status,
                refund.provider_refund_id,
                refund.provider_response,
                refund.error_message,
                refund.created_by,
                refund.notes,
                refund.created_at,
                refund.processed_at,
                refund.completed_at
            )
        except asyncpg.UniqueViolationError as e:
            if 'refund_reference' in str(e):
                raise DuplicateTransactionError(
                    idempotency_key=refund.refund_reference,
                    existing_transaction_id=refund.id
                )
            raise

    async def _update_refund(
        self,
        conn: asyncpg.Connection,
        refund: PaymentRefund
    ) -> None:
        """Update existing refund in database."""
        await conn.execute(
            """
            UPDATE payment_refunds SET
                status = $2,
                provider_refund_id = $3,
                provider_response = $4,
                error_message = $5,
                notes = $6,
                processed_at = $7,
                completed_at = $8
            WHERE id = $1
            """,
            refund.id,
            refund.status,
            refund.provider_refund_id,
            refund.provider_response,
            refund.error_message,
            refund.notes,
            refund.processed_at,
            refund.completed_at
        )

    async def find_by_id(self, refund_id: UUID) -> Optional[PaymentRefund]:
        """
        Find refund by ID.

        Args:
            refund_id: Refund UUID

        Returns:
            PaymentRefund if found, None otherwise
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM payment_refunds WHERE id = $1",
                refund_id
            )
            return self._map_row_to_entity(row) if row else None

    async def find_by_transaction(
        self,
        transaction_id: UUID
    ) -> List[PaymentRefund]:
        """
        Find all refunds for a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            List of PaymentRefunds (may be empty)
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM payment_refunds
                WHERE transaction_id = $1
                ORDER BY created_at DESC
                """,
                transaction_id
            )
            return [self._map_row_to_entity(row) for row in rows]

    async def find_by_reference(
        self,
        refund_reference: str
    ) -> Optional[PaymentRefund]:
        """
        Find refund by refund reference.

        Args:
            refund_reference: Refund reference (e.g., REF-A3F9B2C1)

        Returns:
            PaymentRefund if found, None otherwise
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM payment_refunds WHERE refund_reference = $1",
                refund_reference
            )
            return self._map_row_to_entity(row) if row else None

    async def find_by_store(
        self,
        store_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[PaymentRefund]:
        """
        Find refunds for a store with pagination.

        This joins with payment_transactions to filter by store.

        Args:
            store_id: Store UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of PaymentRefunds (may be empty)
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT pr.* FROM payment_refunds pr
                JOIN payment_transactions pt ON pr.transaction_id = pt.id
                WHERE pt.store_id = $1
                ORDER BY pr.created_at DESC
                LIMIT $2 OFFSET $3
                """,
                store_id,
                limit,
                offset
            )
            return [self._map_row_to_entity(row) for row in rows]

    async def count_by_transaction(self, transaction_id: UUID) -> int:
        """
        Count total refunds for a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Count of refunds
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM payment_refunds WHERE transaction_id = $1",
                transaction_id
            )
            return result or 0

    async def sum_refunds_for_transaction(self, transaction_id: UUID) -> Decimal:
        """
        Calculate total refunded amount for a transaction.

        Useful for determining remaining refundable amount.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Total refunded amount as Decimal
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM payment_refunds
                WHERE transaction_id = $1
                  AND status = 'completed'
                """,
                transaction_id
            )
            return Decimal(str(result)) if result else Decimal('0.00')

    def _map_row_to_entity(self, row: asyncpg.Record) -> PaymentRefund:
        """
        Map database row to PaymentRefund entity.

        Args:
            row: AsyncPG record from database

        Returns:
            PaymentRefund domain entity
        """
        # Create Money value object
        amount = Money(
            amount=Decimal(str(row['amount'])),
            currency=row['currency']
        )

        # Create entity (bypassing __post_init__ validation)
        refund = object.__new__(PaymentRefund)

        # Set attributes directly
        refund.id = row['id']
        refund.refund_reference = row['refund_reference']
        refund.transaction_id = row['transaction_id']
        refund.amount = amount
        refund.reason = row['reason']
        refund.status = row['status']
        refund.provider_refund_id = row['provider_refund_id']
        refund.provider_response = row['provider_response']
        refund.error_message = row['error_message']
        refund.created_by = row['created_by']
        refund.notes = row['notes']
        refund.created_at = row['created_at']
        refund.processed_at = row['processed_at']
        refund.completed_at = row['completed_at']

        # Initialize domain events list
        refund._domain_events = []

        return refund
