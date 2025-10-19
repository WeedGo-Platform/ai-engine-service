"""
Payment Repository Interface

Defines the contract for payment transaction persistence.
Follows the Repository pattern from DDD.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities import PaymentTransaction, PaymentRefund
from ..value_objects import TransactionReference


class PaymentRepository(ABC):
    """
    Repository interface for payment transactions.

    This defines the contract that infrastructure implementations must follow.
    The repository is responsible for:
    - Persisting aggregates
    - Retrieving aggregates by various criteria
    - Managing aggregate lifecycle
    """

    @abstractmethod
    async def save(self, transaction: PaymentTransaction) -> None:
        """
        Save a payment transaction (insert or update).

        Args:
            transaction: PaymentTransaction aggregate to save

        Raises:
            DuplicateTransactionError: If transaction reference already exists
            ProviderError: If database operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """
        Find transaction by ID.

        Args:
            transaction_id: Transaction UUID

        Returns:
            PaymentTransaction if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_reference(
        self,
        reference: TransactionReference
    ) -> Optional[PaymentTransaction]:
        """
        Find transaction by transaction reference.

        Args:
            reference: Transaction reference (e.g., TXN-20250118-A3F9B2C1)

        Returns:
            PaymentTransaction if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_order(self, order_id: UUID) -> List[PaymentTransaction]:
        """
        Find all transactions for an order.

        Args:
            order_id: Order UUID

        Returns:
            List of PaymentTransactions (may be empty)
        """
        pass

    @abstractmethod
    async def find_by_store(
        self,
        store_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[PaymentTransaction]:
        """
        Find transactions for a store with pagination.

        Args:
            store_id: Store UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of PaymentTransactions (may be empty)
        """
        pass

    @abstractmethod
    async def find_by_idempotency_key(self, key: str) -> Optional[PaymentTransaction]:
        """
        Find transaction by idempotency key.

        Used to prevent duplicate transactions.

        Args:
            key: Idempotency key

        Returns:
            PaymentTransaction if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_provider_transaction_id(
        self,
        provider_transaction_id: str,
        provider_id: UUID
    ) -> Optional[PaymentTransaction]:
        """
        Find transaction by provider's transaction ID.

        Useful for webhook processing.

        Args:
            provider_transaction_id: Provider's transaction identifier
            provider_id: Payment provider UUID

        Returns:
            PaymentTransaction if found, None otherwise
        """
        pass

    @abstractmethod
    async def count_by_store(self, store_id: UUID) -> int:
        """
        Count total transactions for a store.

        Args:
            store_id: Store UUID

        Returns:
            Count of transactions
        """
        pass


class PaymentRefundRepository(ABC):
    """
    Repository interface for payment refunds.

    Manages refund entity persistence separate from transactions.
    """

    @abstractmethod
    async def save(self, refund: PaymentRefund) -> None:
        """
        Save a payment refund (insert or update).

        Args:
            refund: PaymentRefund entity to save
        """
        pass

    @abstractmethod
    async def find_by_id(self, refund_id: UUID) -> Optional[PaymentRefund]:
        """
        Find refund by ID.

        Args:
            refund_id: Refund UUID

        Returns:
            PaymentRefund if found, None otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def find_by_reference(self, refund_reference: str) -> Optional[PaymentRefund]:
        """
        Find refund by refund reference.

        Args:
            refund_reference: Refund reference (e.g., REF-A3F9B2C1)

        Returns:
            PaymentRefund if found, None otherwise
        """
        pass
