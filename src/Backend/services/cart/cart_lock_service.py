"""
Cart Locking Service
SRP: Manages cart locks during checkout to prevent concurrent modifications
Uses PostgreSQL advisory locks for distributed locking
"""

from typing import Optional
from uuid import UUID
import logging
import hashlib

logger = logging.getLogger(__name__)


class CartLockService:
    """
    Manages cart locks using PostgreSQL advisory locks
    SRP: ONLY handles cart locking/unlocking
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def acquire_lock(self, cart_session_id: UUID, timeout_seconds: int = 10) -> bool:
        """
        Acquire an exclusive lock on a cart session

        Args:
            cart_session_id: Cart session UUID
            timeout_seconds: Maximum time to wait for lock

        Returns:
            True if lock acquired, False if timeout

        Note:
            Uses PostgreSQL advisory locks which are automatically released when:
            - Connection is closed
            - Transaction is committed/rolled back
            - Explicitly released via release_lock()
        """
        # Convert UUID to integer for advisory lock
        lock_id = self._uuid_to_lock_id(cart_session_id)

        logger.debug(f"Attempting to acquire lock for cart {cart_session_id} (lock_id: {lock_id})")

        try:
            # Try to acquire lock with timeout
            # pg_try_advisory_lock returns immediately (no waiting)
            # To implement timeout, we use a loop with short delays
            import asyncio
            start_time = asyncio.get_event_loop().time()

            while True:
                result = await self.db.fetchval(
                    "SELECT pg_try_advisory_lock($1)",
                    lock_id
                )

                if result:
                    logger.info(f"Lock acquired for cart {cart_session_id}")
                    return True

                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout_seconds:
                    logger.warning(
                        f"Lock timeout for cart {cart_session_id} "
                        f"after {timeout_seconds}s"
                    )
                    return False

                # Wait a bit before retrying
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error acquiring lock for cart {cart_session_id}: {str(e)}")
            return False

    async def release_lock(self, cart_session_id: UUID) -> bool:
        """
        Release the lock on a cart session

        Args:
            cart_session_id: Cart session UUID

        Returns:
            True if lock released, False if lock wasn't held
        """
        lock_id = self._uuid_to_lock_id(cart_session_id)

        try:
            result = await self.db.fetchval(
                "SELECT pg_advisory_unlock($1)",
                lock_id
            )

            if result:
                logger.info(f"Lock released for cart {cart_session_id}")
            else:
                logger.warning(f"Lock not held for cart {cart_session_id}")

            return result

        except Exception as e:
            logger.error(f"Error releasing lock for cart {cart_session_id}: {str(e)}")
            return False

    async def is_locked(self, cart_session_id: UUID) -> bool:
        """
        Check if a cart is currently locked

        Args:
            cart_session_id: Cart session UUID

        Returns:
            True if cart is locked by any session
        """
        lock_id = self._uuid_to_lock_id(cart_session_id)

        try:
            # Query pg_locks to see if advisory lock is held
            result = await self.db.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_locks
                    WHERE locktype = 'advisory'
                    AND objid = $1
                )
                """,
                lock_id
            )

            return result

        except Exception as e:
            logger.error(f"Error checking lock status for cart {cart_session_id}: {str(e)}")
            return False

    def _uuid_to_lock_id(self, uuid: UUID) -> int:
        """
        Convert UUID to 32-bit integer for PostgreSQL advisory lock

        PostgreSQL advisory locks use bigint (64-bit), but for simplicity
        we use a hash of the UUID to generate a 32-bit positive integer.

        Args:
            uuid: UUID to convert

        Returns:
            32-bit positive integer
        """
        # Hash UUID string and take first 8 hex chars
        hash_hex = hashlib.md5(str(uuid).encode()).hexdigest()[:8]
        # Convert to integer (max 32-bit)
        lock_id = int(hash_hex, 16) & 0x7FFFFFFF  # Keep positive
        return lock_id


class CartLockContext:
    """
    Context manager for cart locks
    Automatically acquires lock on entry and releases on exit
    """

    def __init__(self, lock_service: CartLockService, cart_session_id: UUID, timeout: int = 10):
        self.lock_service = lock_service
        self.cart_session_id = cart_session_id
        self.timeout = timeout
        self.lock_acquired = False

    async def __aenter__(self):
        """Acquire lock when entering context"""
        self.lock_acquired = await self.lock_service.acquire_lock(
            self.cart_session_id,
            self.timeout
        )

        if not self.lock_acquired:
            raise TimeoutError(
                f"Could not acquire lock for cart {self.cart_session_id} "
                f"within {self.timeout} seconds"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock when exiting context"""
        if self.lock_acquired:
            await self.lock_service.release_lock(self.cart_session_id)

        return False  # Don't suppress exceptions
