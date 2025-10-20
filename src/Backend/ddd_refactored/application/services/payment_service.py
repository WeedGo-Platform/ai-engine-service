"""
Payment Application Service

Orchestrates payment use cases using domain entities and infrastructure.
"""

import asyncpg
import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from ...domain.payment_processing.entities import PaymentTransaction, PaymentRefund
from ...domain.payment_processing.repositories import PaymentRepository, PaymentRefundRepository
from ...domain.payment_processing.value_objects import Money, PaymentStatus
from ...domain.payment_processing.exceptions import (
    TransactionNotFoundError,
    InvalidTransactionStateError,
    RefundNotAllowedError,
    RefundAmountExceededError,
    StoreNotConfiguredError,
    DuplicateTransactionError,
    ProviderError
)
from services.payment.provider_factory import PaymentProviderFactory

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Application service for payment processing.

    Responsibilities:
    - Coordinate between domain entities, repositories, and providers
    - Orchestrate payment use cases (process payment, refund, etc.)
    - Load store provider configurations
    - Call external payment providers
    - Persist transactions and refunds
    - Publish domain events (future: event bus integration)

    This service follows the Application Service pattern from DDD,
    keeping business logic in domain entities while orchestrating
    the overall workflow.
    """

    def __init__(
        self,
        payment_repo: PaymentRepository,
        refund_repo: PaymentRefundRepository,
        provider_factory: PaymentProviderFactory,
        db_pool: asyncpg.Pool
    ):
        """
        Initialize payment service with dependencies.

        Args:
            payment_repo: Repository for payment transactions
            refund_repo: Repository for refunds
            provider_factory: Factory for creating payment provider instances
            db_pool: Database connection pool
        """
        self.payment_repo = payment_repo
        self.refund_repo = refund_repo
        self.provider_factory = provider_factory
        self.db_pool = db_pool
        self.logger = logger

    async def process_payment(
        self,
        store_id: UUID,
        amount: Money,
        payment_method_id: UUID,
        provider_type: str,  # 'clover', 'moneris', 'interac'
        order_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentTransaction:
        """
        Process a payment transaction.

        This is the main payment processing use case.

        Steps:
        1. Check idempotency key (prevent duplicates)
        2. Get store provider configuration
        3. Create PaymentTransaction entity (domain)
        4. Get payment provider from factory
        5. Call provider.charge()
        6. Update transaction (complete or fail)
        7. Save transaction
        8. Publish domain events
        9. Return transaction

        Args:
            store_id: Store UUID
            amount: Payment amount (Money value object)
            payment_method_id: Payment method UUID
            provider_type: Provider to use (clover/moneris/interac)
            order_id: Optional order reference
            idempotency_key: Optional key to prevent duplicates
            user_id: User making the payment
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            PaymentTransaction entity with status

        Raises:
            DuplicateTransactionError: If idempotency key already used
            StoreNotConfiguredError: If store has no active provider
            ProviderError: If provider call fails
        """
        self.logger.info(
            f"Processing payment for store {store_id}, "
            f"amount {amount}, provider {provider_type}"
        )

        # 1. Check for duplicate (idempotency)
        if idempotency_key:
            existing = await self.payment_repo.find_by_idempotency_key(idempotency_key)
            if existing:
                self.logger.info(
                    f"Idempotent request detected: {idempotency_key}, "
                    f"returning existing transaction {existing.id}"
                )
                return existing

        # 2. Get store provider config
        store_provider = await self._get_store_provider(store_id, provider_type)

        # Get payment method token
        payment_method_token = await self._get_payment_method_token(payment_method_id)

        # 3. Create domain entity
        transaction = PaymentTransaction(
            store_id=store_id,
            provider_id=store_provider['provider_id'],
            store_provider_id=store_provider['id'],
            order_id=order_id,
            user_id=user_id,
            payment_method_id=payment_method_id,
            transaction_type='charge',
            amount=amount,
            idempotency_key=idempotency_key,
            ip_address=ip_address,
            metadata=metadata or {}
        )

        # 4. Get payment provider
        try:
            provider = await self.provider_factory.get_provider(
                tenant_id=str(store_id),  # Note: Will be updated to store_id in factory refactor
                provider_type=provider_type
            )
        except Exception as e:
            self.logger.error(f"Failed to get provider for store {store_id}: {e}")
            raise StoreNotConfiguredError(store_id, provider_type)

        # 5. Begin processing
        transaction.begin_processing(provider_type)

        try:
            # Call external provider API
            self.logger.info(f"Calling {provider_type} provider for transaction {transaction.id}")

            provider_response = await provider.charge(
                amount=float(amount.amount),
                currency=amount.currency,
                payment_method_token=payment_method_token,
                metadata={
                    'transaction_id': str(transaction.id),
                    'transaction_reference': str(transaction.transaction_reference),
                    'order_id': str(order_id) if order_id else None,
                    **(metadata or {})
                }
            )

            # 6a. Mark as completed
            transaction.complete(
                provider_transaction_id=provider_response.get('transaction_id') or provider_response.get('id'),
                provider_response=provider_response
            )

            self.logger.info(
                f"Transaction {transaction.id} completed successfully: "
                f"{provider_response.get('transaction_id')}"
            )

        except Exception as e:
            # 6b. Mark as failed
            self.logger.error(f"Transaction {transaction.id} failed: {e}")

            transaction.fail(
                error_code=getattr(e, 'error_code', 'PROVIDER_ERROR'),
                error_message=str(e),
                provider_response=getattr(e, 'provider_response', None)
            )

        # 7. Save transaction
        await self.payment_repo.save(transaction)

        # 8. Publish domain events (TODO: implement event bus)
        # for event in transaction.domain_events:
        #     await self.event_bus.publish(event)

        # Clear events after publishing
        transaction.clear_events()

        # 9. Return
        return transaction

    async def refund_payment(
        self,
        transaction_id: UUID,
        refund_amount: Money,
        reason: str,
        requested_by: UUID,
        notes: Optional[str] = None
    ) -> PaymentRefund:
        """
        Process a refund for a payment transaction.

        Steps:
        1. Load original transaction
        2. Validate refund is allowed
        3. Create refund entity via transaction.request_refund()
        4. Get payment provider
        5. Call provider.refund()
        6. Update refund status
        7. Save refund
        8. If full refund, mark transaction as refunded
        9. Publish domain events

        Args:
            transaction_id: Original transaction UUID
            refund_amount: Amount to refund
            reason: Reason for refund
            requested_by: User requesting refund
            notes: Optional notes

        Returns:
            PaymentRefund entity

        Raises:
            TransactionNotFoundError: If transaction doesn't exist
            RefundNotAllowedError: If transaction can't be refunded
            RefundAmountExceededError: If refund exceeds transaction amount
            ProviderError: If provider call fails
        """
        self.logger.info(
            f"Processing refund for transaction {transaction_id}, "
            f"amount {refund_amount}, reason: {reason}"
        )

        # 1. Load transaction
        transaction = await self.payment_repo.find_by_id(transaction_id)
        if not transaction:
            raise TransactionNotFoundError(transaction_id=transaction_id)

        # 2 & 3. Validate and create refund entity
        refund = transaction.request_refund(
            refund_amount=refund_amount,
            reason=reason,
            requested_by=requested_by
        )

        if notes:
            refund.notes = notes

        # 4. Get provider
        try:
            provider = await self.provider_factory.get_provider(
                tenant_id=str(transaction.store_id),  # Will be updated
                provider_type=self._get_provider_type(transaction.provider_id)
            )
        except Exception as e:
            self.logger.error(f"Failed to get provider for refund: {e}")
            refund.fail(
                error_message=f"Failed to get payment provider: {str(e)}"
            )
            await self.refund_repo.save(refund)
            return refund

        # 5. Call provider
        refund.mark_as_processing()

        try:
            self.logger.info(
                f"Calling provider refund API for transaction "
                f"{transaction.provider_transaction_id}"
            )

            provider_response = await provider.refund(
                transaction_id=transaction.provider_transaction_id,
                amount=float(refund_amount.amount),
                currency=refund_amount.currency,
                reason=reason
            )

            refund.complete(
                provider_refund_id=provider_response.get('refund_id') or provider_response.get('id'),
                provider_response=provider_response
            )

            self.logger.info(
                f"Refund {refund.id} completed successfully: "
                f"{provider_response.get('refund_id')}"
            )

        except Exception as e:
            self.logger.error(f"Refund {refund.id} failed: {e}")

            refund.fail(
                error_message=str(e),
                provider_response=getattr(e, 'provider_response', None)
            )

        # 7. Save refund
        await self.refund_repo.save(refund)

        # 8. Check if full refund
        if refund.is_completed and refund.amount == transaction.amount:
            transaction.mark_as_refunded()
            await self.payment_repo.save(transaction)
            self.logger.info(f"Transaction {transaction.id} marked as fully refunded")

        # 9. Publish domain events (TODO: implement event bus)
        # for event in refund.domain_events:
        #     await self.event_bus.publish(event)

        refund.clear_events()

        return refund

    async def get_transaction(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by ID.

        Args:
            transaction_id: Transaction UUID

        Returns:
            PaymentTransaction if found, None otherwise
        """
        return await self.payment_repo.find_by_id(transaction_id)

    async def get_transaction_by_reference(
        self,
        transaction_reference: str
    ) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by reference.

        Args:
            transaction_reference: Transaction reference (e.g., TXN-20250118-ABC123)

        Returns:
            PaymentTransaction if found, None otherwise
        """
        from ...domain.payment_processing.value_objects import TransactionReference

        ref = TransactionReference.from_string(transaction_reference)
        return await self.payment_repo.find_by_reference(ref)

    async def list_store_transactions(
        self,
        store_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[PaymentTransaction]:
        """
        List payment transactions for a store.

        Args:
            store_id: Store UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of PaymentTransactions
        """
        return await self.payment_repo.find_by_store(store_id, limit, offset)

    async def list_order_transactions(
        self,
        order_id: UUID
    ) -> List[PaymentTransaction]:
        """
        List all payment transactions for an order.

        Args:
            order_id: Order UUID

        Returns:
            List of PaymentTransactions
        """
        return await self.payment_repo.find_by_order(order_id)

    async def list_transaction_refunds(
        self,
        transaction_id: UUID
    ) -> List[PaymentRefund]:
        """
        List all refunds for a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            List of PaymentRefunds
        """
        return await self.refund_repo.find_by_transaction(transaction_id)

    async def get_refund(self, refund_id: UUID) -> Optional[PaymentRefund]:
        """
        Get a refund by ID.

        Args:
            refund_id: Refund UUID

        Returns:
            PaymentRefund if found, None otherwise
        """
        return await self.refund_repo.find_by_id(refund_id)

    async def _get_store_provider(
        self,
        store_id: UUID,
        provider_type: str
    ) -> Dict[str, Any]:
        """
        Get store provider configuration from database.

        Args:
            store_id: Store UUID
            provider_type: Provider type (clover/moneris/interac)

        Returns:
            Store provider configuration dict

        Raises:
            StoreNotConfiguredError: If no active provider found
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT spp.*, pp.provider_type
                FROM store_payment_providers spp
                JOIN payment_providers pp ON spp.provider_id = pp.id
                WHERE spp.store_id = $1
                  AND pp.provider_type = $2
                  AND spp.is_active = true
                LIMIT 1
                """,
                store_id,
                provider_type
            )

            if not row:
                raise StoreNotConfiguredError(store_id, provider_type)

            return dict(row)

    async def _get_payment_method_token(self, payment_method_id: UUID) -> str:
        """
        Get payment method token from database.

        Args:
            payment_method_id: Payment method UUID

        Returns:
            Payment method token for provider

        Raises:
            ValueError: If payment method not found
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT provider_token
                FROM payment_methods
                WHERE id = $1 AND is_active = true
                """,
                payment_method_id
            )

            if not row or not row['provider_token']:
                raise ValueError(f"Payment method {payment_method_id} not found or inactive")

            return row['provider_token']

    def _get_provider_type(self, provider_id: UUID) -> str:
        """
        Get provider type from provider_id.

        Note: This is a temporary method until we refactor
        the provider factory to use store-level configs.

        Args:
            provider_id: Provider UUID

        Returns:
            Provider type string
        """
        # TODO: Query from database
        # For now, this is a placeholder
        return 'clover'  # Will be replaced with actual query
