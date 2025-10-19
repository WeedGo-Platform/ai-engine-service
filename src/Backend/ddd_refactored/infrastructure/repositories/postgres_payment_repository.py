"""
PostgreSQL Payment Repository Implementation

AsyncPG-based implementation of PaymentRepository interface.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from ...domain.payment_processing.repositories import PaymentRepository
from ...domain.payment_processing.entities import PaymentTransaction
from ...domain.payment_processing.value_objects import (
    Money,
    PaymentStatus,
    TransactionReference
)
from ...domain.payment_processing.exceptions import (
    DuplicateTransactionError,
    TransactionNotFoundError
)


class PostgresPaymentRepository(PaymentRepository):
    """
    PostgreSQL implementation of PaymentRepository using AsyncPG.

    Responsibilities:
    - Map domain entities to/from database rows
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

    async def save(self, transaction: PaymentTransaction) -> None:
        """
        Save payment transaction (insert or update).

        Args:
            transaction: PaymentTransaction aggregate to save

        Raises:
            DuplicateTransactionError: If transaction reference already exists
        """
        async with self.db_pool.acquire() as conn:
            # Check for existing transaction
            existing = await conn.fetchrow(
                "SELECT id FROM payment_transactions WHERE id = $1",
                transaction.id
            )

            if existing:
                # Update existing
                await self._update_transaction(conn, transaction)
            else:
                # Insert new
                await self._insert_transaction(conn, transaction)

    async def _insert_transaction(
        self,
        conn: asyncpg.Connection,
        transaction: PaymentTransaction
    ) -> None:
        """Insert new transaction into database."""
        try:
            await conn.execute(
                """
                INSERT INTO payment_transactions (
                    id, transaction_reference, store_id, provider_id,
                    store_provider_id, order_id, user_id, payment_method_id,
                    transaction_type, amount, currency, status,
                    provider_transaction_id, provider_response,
                    error_code, error_message, idempotency_key, ip_address,
                    metadata, created_at, updated_at, completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                )
                """,
                transaction.id,
                str(transaction.transaction_reference),
                transaction.store_id,
                transaction.provider_id,
                transaction.store_provider_id,
                transaction.order_id,
                transaction.user_id,
                transaction.payment_method_id,
                transaction.transaction_type,
                transaction.amount.amount,
                transaction.amount.currency,
                transaction.status.value,
                transaction.provider_transaction_id,
                transaction.provider_response,
                transaction.error_code,
                transaction.error_message,
                transaction.idempotency_key,
                str(transaction.ip_address) if transaction.ip_address else None,
                transaction.metadata,
                transaction.created_at,
                transaction.updated_at,
                transaction.completed_at
            )
        except asyncpg.UniqueViolationError as e:
            if 'transaction_reference' in str(e):
                raise DuplicateTransactionError(
                    idempotency_key=transaction.idempotency_key or str(transaction.transaction_reference),
                    existing_transaction_id=transaction.id
                )
            raise

    async def _update_transaction(
        self,
        conn: asyncpg.Connection,
        transaction: PaymentTransaction
    ) -> None:
        """Update existing transaction in database."""
        await conn.execute(
            """
            UPDATE payment_transactions SET
                status = $2,
                provider_transaction_id = $3,
                provider_response = $4,
                error_code = $5,
                error_message = $6,
                metadata = $7,
                updated_at = $8,
                completed_at = $9
            WHERE id = $1
            """,
            transaction.id,
            transaction.status.value,
            transaction.provider_transaction_id,
            transaction.provider_response,
            transaction.error_code,
            transaction.error_message,
            transaction.metadata,
            transaction.updated_at,
            transaction.completed_at
        )

    async def find_by_id(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """Find transaction by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM payment_transactions WHERE id = $1",
                transaction_id
            )
            return self._map_row_to_entity(row) if row else None

    async def find_by_reference(
        self,
        reference: TransactionReference
    ) -> Optional[PaymentTransaction]:
        """Find transaction by transaction reference."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM payment_transactions WHERE transaction_reference = $1",
                str(reference)
            )
            return self._map_row_to_entity(row) if row else None

    async def find_by_order(self, order_id: UUID) -> List[PaymentTransaction]:
        """Find all transactions for an order."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM payment_transactions
                WHERE order_id = $1
                ORDER BY created_at DESC
                """,
                order_id
            )
            return [self._map_row_to_entity(row) for row in rows]

    async def find_by_store(
        self,
        store_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[PaymentTransaction]:
        """Find transactions for a store with pagination."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM payment_transactions
                WHERE store_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                store_id,
                limit,
                offset
            )
            return [self._map_row_to_entity(row) for row in rows]

    async def find_by_idempotency_key(self, key: str) -> Optional[PaymentTransaction]:
        """Find transaction by idempotency key."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM payment_transactions WHERE idempotency_key = $1",
                key
            )
            return self._map_row_to_entity(row) if row else None

    async def find_by_provider_transaction_id(
        self,
        provider_transaction_id: str,
        provider_id: UUID
    ) -> Optional[PaymentTransaction]:
        """Find transaction by provider's transaction ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM payment_transactions
                WHERE provider_transaction_id = $1 AND provider_id = $2
                """,
                provider_transaction_id,
                provider_id
            )
            return self._map_row_to_entity(row) if row else None

    async def count_by_store(self, store_id: UUID) -> int:
        """Count total transactions for a store."""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM payment_transactions WHERE store_id = $1",
                store_id
            )
            return result or 0

    def _map_row_to_entity(self, row: asyncpg.Record) -> PaymentTransaction:
        """
        Map database row to PaymentTransaction entity.

        Args:
            row: AsyncPG record from database

        Returns:
            PaymentTransaction domain entity
        """
        # Create Money value object
        amount = Money(
            amount=Decimal(str(row['amount'])),
            currency=row['currency']
        )

        # Create TransactionReference value object
        reference = TransactionReference.from_string(row['transaction_reference'])

        # Create PaymentStatus enum
        status = PaymentStatus.from_string(row['status'])

        # Create entity (bypassing __post_init__ validation)
        transaction = object.__new__(PaymentTransaction)

        # Set attributes directly
        transaction.id = row['id']
        transaction.transaction_reference = reference
        transaction.store_id = row['store_id']
        transaction.provider_id = row['provider_id']
        transaction.store_provider_id = row['store_provider_id']
        transaction.order_id = row['order_id']
        transaction.user_id = row['user_id']
        transaction.payment_method_id = row['payment_method_id']
        transaction.transaction_type = row['transaction_type']
        transaction.amount = amount
        transaction.status = status
        transaction.provider_transaction_id = row['provider_transaction_id']
        transaction.provider_response = row['provider_response']
        transaction.error_code = row['error_code']
        transaction.error_message = row['error_message']
        transaction.idempotency_key = row['idempotency_key']
        transaction.ip_address = row['ip_address']
        transaction.metadata = row['metadata'] or {}
        transaction.created_at = row['created_at']
        transaction.updated_at = row['updated_at']
        transaction.completed_at = row['completed_at']

        # Initialize domain events list
        transaction._domain_events = []

        return transaction
