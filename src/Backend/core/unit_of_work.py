"""
Unit of Work Pattern Implementation
Manages transactions across multiple repositories
Following SOLID principles and DDD patterns
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import psycopg2
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class IUnitOfWork(ABC):
    """
    Unit of Work interface
    Manages database transactions across multiple repositories
    """

    @abstractmethod
    async def __aenter__(self):
        """Begin a unit of work (start transaction)"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End unit of work (commit/rollback transaction)"""
        pass

    @abstractmethod
    async def commit(self):
        """Commit the current transaction"""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction"""
        pass

    @abstractmethod
    def get_repository(self, name: str):
        """Get a repository instance within this unit of work"""
        pass


class SqlUnitOfWork(IUnitOfWork):
    """
    SQL implementation of Unit of Work pattern
    Manages PostgreSQL transactions
    """

    def __init__(self, connection_manager):
        """
        Initialize SQL Unit of Work

        Args:
            connection_manager: Database connection manager
        """
        self.connection_manager = connection_manager
        self.connection: Optional[Any] = None
        self.repositories: Dict[str, Any] = {}
        self._is_active = False

    async def __aenter__(self):
        """
        Begin unit of work - start transaction
        """
        try:
            self.connection = self.connection_manager.get_connection()
            self.connection.autocommit = False  # Enable transaction mode
            self._is_active = True
            logger.debug("Unit of Work started - transaction begun")
            return self
        except Exception as e:
            logger.error(f"Failed to start Unit of Work: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        End unit of work - commit or rollback based on exceptions
        """
        if not self._is_active:
            return

        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
                logger.warning(f"Unit of Work rolled back due to exception: {exc_val}")
        finally:
            self._cleanup()

    async def commit(self):
        """
        Commit the current transaction
        """
        if not self._is_active:
            raise RuntimeError("Cannot commit: Unit of Work is not active")

        try:
            self.connection.commit()
            logger.debug("Unit of Work committed successfully")
        except Exception as e:
            logger.error(f"Failed to commit Unit of Work: {e}")
            await self.rollback()
            raise

    async def rollback(self):
        """
        Rollback the current transaction
        """
        if not self._is_active:
            return

        try:
            self.connection.rollback()
            logger.debug("Unit of Work rolled back")
        except Exception as e:
            logger.error(f"Failed to rollback Unit of Work: {e}")

    def get_repository(self, name: str):
        """
        Get or create a repository instance within this unit of work

        Args:
            name: Name of the repository

        Returns:
            Repository instance
        """
        if name not in self.repositories:
            self.repositories[name] = self._create_repository(name)
        return self.repositories[name]

    def _create_repository(self, name: str):
        """
        Factory method to create repository instances

        Args:
            name: Repository name

        Returns:
            Repository instance
        """
        # Import repositories dynamically to avoid circular imports
        repository_map = {
            'product': self._create_product_repository,
            'inventory': self._create_inventory_repository,
            'order': self._create_order_repository,
            'customer': self._create_customer_repository,
            'cart': self._create_cart_repository,
            'tenant': self._create_tenant_repository,
        }

        creator = repository_map.get(name)
        if not creator:
            raise ValueError(f"Unknown repository: {name}")

        return creator()

    def _create_product_repository(self):
        """Create ProductRepository instance"""
        from core.repositories.product_repository import ProductRepository
        # Create a special connection manager that uses our transaction connection
        txn_manager = TransactionConnectionManager(self.connection)
        return ProductRepository(txn_manager)

    def _create_inventory_repository(self):
        """Create InventoryRepository instance"""
        from core.repositories.inventory_repository import InventoryRepository
        txn_manager = TransactionConnectionManager(self.connection)
        return InventoryRepository(txn_manager)

    def _create_order_repository(self):
        """Create OrderRepository instance"""
        from core.repositories.order_repository import OrderRepository
        txn_manager = TransactionConnectionManager(self.connection)
        return OrderRepository(txn_manager)

    def _create_customer_repository(self):
        """Create CustomerRepository instance"""
        from core.repositories.customer_repository import CustomerRepository
        txn_manager = TransactionConnectionManager(self.connection)
        return CustomerRepository(txn_manager)

    def _create_cart_repository(self):
        """Create CartRepository instance"""
        from core.repositories.cart_repository import CartRepository
        txn_manager = TransactionConnectionManager(self.connection)
        return CartRepository(txn_manager)

    def _create_tenant_repository(self):
        """Create TenantRepository instance"""
        from core.repositories.tenant_repository import TenantRepository
        txn_manager = TransactionConnectionManager(self.connection)
        return TenantRepository(txn_manager)

    def _cleanup(self):
        """
        Cleanup resources
        """
        self._is_active = False
        self.repositories.clear()
        if self.connection:
            self.connection_manager.release_connection(self.connection)
            self.connection = None


class TransactionConnectionManager:
    """
    Special connection manager for use within a Unit of Work transaction
    Provides the same connection interface but uses the UoW's connection
    """

    def __init__(self, connection):
        """
        Initialize with the transaction connection

        Args:
            connection: The active transaction connection
        """
        self.connection = connection

    def get_connection(self):
        """
        Return the transaction connection
        Always returns the same connection within a transaction
        """
        return self.connection

    def release_connection(self, connection):
        """
        No-op for transaction connections
        Connection is managed by the Unit of Work
        """
        pass


class UnitOfWorkFactory:
    """
    Factory for creating Unit of Work instances
    Follows Factory Pattern
    """

    def __init__(self, connection_manager):
        """
        Initialize factory with connection manager

        Args:
            connection_manager: Database connection manager
        """
        self.connection_manager = connection_manager

    def create(self) -> IUnitOfWork:
        """
        Create a new Unit of Work instance

        Returns:
            Unit of Work instance
        """
        return SqlUnitOfWork(self.connection_manager)

    @contextmanager
    def create_sync(self):
        """
        Create a synchronous Unit of Work context manager

        Yields:
            Unit of Work instance
        """
        uow = SqlUnitOfWork(self.connection_manager)
        try:
            # Synchronous version of __aenter__
            uow.connection = self.connection_manager.get_connection()
            uow.connection.autocommit = False
            uow._is_active = True
            yield uow
            # Commit if no exception
            uow.connection.commit()
        except Exception as e:
            # Rollback on exception
            if uow.connection:
                uow.connection.rollback()
            raise
        finally:
            # Cleanup
            uow._cleanup()