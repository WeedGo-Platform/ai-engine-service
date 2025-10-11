"""
Dependency Injection for V2 API
Provides instances of repositories and application services
"""

import asyncpg
import os
from typing import Optional
from fastapi import Depends, HTTPException, Header

# Database connection
async def get_db_connection() -> asyncpg.Connection:
    """
    Get database connection from environment

    In production, this should use a connection pool
    """
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "weedgo"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "ai_engine")
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


# Repository dependencies
class PaymentRepository:
    """
    Payment transaction repository (placeholder for now)
    In full DDD implementation, this would be in infrastructure layer
    """
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def get_by_id(self, payment_id: str):
        """Get payment by ID"""
        result = await self.db.fetchrow(
            "SELECT * FROM payment_transactions WHERE id = $1",
            payment_id
        )
        return result

    async def save(self, payment_data: dict):
        """Save payment transaction"""
        # Simplified save - in real implementation would map domain object to DB
        await self.db.execute(
            """
            INSERT INTO payment_transactions
            (id, order_id, amount, currency, status, payment_method, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            payment_data["id"],
            payment_data["order_id"],
            payment_data["amount"],
            payment_data["currency"],
            payment_data["status"],
            payment_data["payment_method"]
        )

    async def list_by_order(self, order_id: str):
        """List payments for an order"""
        results = await self.db.fetch(
            "SELECT * FROM payment_transactions WHERE order_id = $1",
            order_id
        )
        return results


async def get_payment_repository(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> PaymentRepository:
    """Get payment repository instance"""
    return PaymentRepository(db)


# Application Service dependencies
class PaymentService:
    """
    Payment application service
    Orchestrates payment operations using DDD domain models
    """
    def __init__(self, repository: PaymentRepository):
        self.repository = repository

    async def process_payment(
        self,
        order_id: str,
        store_id: str,
        tenant_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        customer_id: Optional[str] = None
    ) -> dict:
        """
        Process a payment transaction

        In full DDD implementation, this would:
        1. Create PaymentTransaction aggregate
        2. Execute authorize/capture commands
        3. Publish domain events
        4. Save via repository
        """
        from uuid import UUID, uuid4
        from decimal import Decimal
        from ddd_refactored.domain.payment_processing.entities.payment_transaction import PaymentTransaction
        from ddd_refactored.domain.payment_processing.value_objects.payment_types import (
            Money,
            PaymentMethod as PMEnum,
            PaymentProvider,
            PaymentMethodDetails
        )

        # Create domain objects
        payment_amount = Money(
            amount=Decimal(str(amount)),
            currency=currency
        )

        payment_method_enum = PMEnum(payment_method.lower())

        payment_method_details = PaymentMethodDetails(
            payment_method=payment_method_enum,
            provider=PaymentProvider.STRIPE  # Default to Stripe for now
        )

        # Create payment transaction using DDD aggregate
        payment = PaymentTransaction.create(
            order_id=UUID(order_id) if isinstance(order_id, str) else order_id,
            store_id=UUID(store_id) if isinstance(store_id, str) else store_id,
            tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            payment_amount=payment_amount,
            payment_method_details=payment_method_details,
            customer_id=UUID(customer_id) if customer_id else None
        )

        # In real implementation, would save via repository
        # For now, return the created payment
        return {
            "id": str(payment.id),
            "order_id": str(payment.order_id),
            "amount": float(payment.payment_amount.amount),
            "currency": payment.payment_amount.currency,
            "status": payment.payment_status.value,
            "payment_method": payment.payment_method_details.payment_method.value,
            "provider": payment.payment_provider.value,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "events": [type(event).__name__ for event in payment.domain_events]
        }

    async def get_transaction(self, transaction_id: str) -> Optional[dict]:
        """Get payment transaction by ID"""
        result = await self.repository.get_by_id(transaction_id)
        return dict(result) if result else None

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[float],
        reason: str
    ) -> dict:
        """Refund a payment transaction"""
        # Placeholder - would load aggregate, call refund method, save
        return {
            "id": transaction_id,
            "status": "refund_pending",
            "refund_amount": amount,
            "refund_reason": reason
        }


async def get_payment_service(
    repository: PaymentRepository = Depends(get_payment_repository)
) -> PaymentService:
    """Get payment application service"""
    return PaymentService(repository)


# Database Pool Management (for promotions)
_db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5434")),
            user=os.getenv("DB_USER", "weedgo"),
            password=os.getenv("DB_PASSWORD", "your_password_here"),
            database=os.getenv("DB_NAME", "ai_engine"),
            min_size=1,
            max_size=10
        )
    return _db_pool


# Promotion Repository Dependencies
from ddd_refactored.domain.pricing_promotions.repositories import (
    IPromotionRepository,
    AsyncPGPromotionRepository
)

async def get_promotion_repository() -> IPromotionRepository:
    """Get promotion repository instance"""
    pool = await get_db_pool()
    return AsyncPGPromotionRepository(pool)


# Authentication dependencies
async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Get current authenticated user

    In production, this would validate JWT token and return user info
    For now, returns a mock user for testing
    """
    if not authorization:
        # For development, return mock user
        return {
            "id": "mock-user-id",
            "tenant_id": "mock-tenant-id",
            "store_id": "mock-store-id",
            "role": "admin"
        }

    # TODO: Implement JWT validation
    return {
        "id": "authenticated-user-id",
        "tenant_id": "tenant-id",
        "store-id": "store-id",
        "role": "admin"
    }
