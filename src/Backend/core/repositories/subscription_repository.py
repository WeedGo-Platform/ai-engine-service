"""
Subscription Repository - Database access layer for subscriptions
"""

from typing import Optional, List
from uuid import UUID
import asyncpg
from core.domain.models import TenantSubscription
from core.repositories.interfaces import ISubscriptionRepository


class SubscriptionRepository(ISubscriptionRepository):
    """Repository for subscription management"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool

    async def create(self, subscription: TenantSubscription, conn=None) -> TenantSubscription:
        """Create a new subscription"""
        # For now, this is a simplified implementation
        # The subscription data is stored in the tenant record itself
        # This method exists for future expansion when subscriptions are separated
        return subscription

    async def get_by_tenant(self, tenant_id: UUID) -> Optional[TenantSubscription]:
        """Get subscription by tenant ID"""
        # Simplified implementation - would normally query database
        return None

    async def update(self, subscription: TenantSubscription) -> TenantSubscription:
        """Update subscription"""
        # Simplified implementation - would normally update database
        return subscription

    async def list_expiring(self, days_ahead: int = 7) -> List[TenantSubscription]:
        """List subscriptions expiring soon"""
        # Simplified implementation - would normally query database
        # for subscriptions expiring within the specified days
        return []
    
    async def get_by_id(self, subscription_id: UUID) -> Optional[TenantSubscription]:
        """Get subscription by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM tenant_subscriptions WHERE id = $1
                """,
                subscription_id
            )
            if not row:
                return None
            return self._row_to_entity(row)
    
    async def get_active_by_tenant(self, tenant_id: UUID) -> Optional[TenantSubscription]:
        """Get active subscription for a tenant"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM tenant_subscriptions 
                WHERE tenant_id = $1 AND status IN ('active', 'trial')
                ORDER BY created_at DESC LIMIT 1
                """,
                tenant_id
            )
            if not row:
                return None
            return self._row_to_entity(row)
    
    async def find_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[TenantSubscription]:
        """Find subscription by Stripe subscription ID stored in metadata"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM tenant_subscriptions 
                WHERE metadata->>'stripe_subscription_id' = $1
                LIMIT 1
                """,
                stripe_subscription_id
            )
            if not row:
                return None
            return self._row_to_entity(row)
    
    async def save(self, subscription: TenantSubscription) -> TenantSubscription:
        """Save (insert or update) subscription"""
        async with self.pool.acquire() as conn:
            # Check if exists
            existing = await conn.fetchval(
                "SELECT id FROM tenant_subscriptions WHERE id = $1",
                subscription.id
            )
            
            if existing:
                # Update
                await conn.execute(
                    """
                    UPDATE tenant_subscriptions SET
                        tier = $2, status = $3, billing_frequency = $4,
                        base_price = $5, discount_percentage = $6,
                        trial_end_date = $7, next_billing_date = $8,
                        payment_status = $9, failed_payment_count = $10,
                        last_payment_date = $11, payment_method_id = $12,
                        auto_renew = $13, metadata = $14, updated_at = $15
                    WHERE id = $1
                    """,
                    subscription.id, subscription.tier, subscription.status.value,
                    subscription.billing_frequency.value, subscription.base_price,
                    subscription.discount_percentage, subscription.trial_end_date,
                    subscription.next_billing_date, subscription.payment_status.value,
                    subscription.failed_payment_count, subscription.last_payment_date,
                    subscription.payment_method_id, subscription.auto_renew,
                    subscription.metadata, subscription.updated_at
                )
            else:
                # Insert
                await conn.execute(
                    """
                    INSERT INTO tenant_subscriptions (
                        id, tenant_id, tier, status, billing_frequency,
                        base_price, discount_percentage, trial_end_date,
                        next_billing_date, payment_status, failed_payment_count,
                        last_payment_date, payment_method_id, auto_renew,
                        metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """,
                    subscription.id, subscription.tenant_id, subscription.tier,
                    subscription.status.value, subscription.billing_frequency.value,
                    subscription.base_price, subscription.discount_percentage,
                    subscription.trial_end_date, subscription.next_billing_date,
                    subscription.payment_status.value, subscription.failed_payment_count,
                    subscription.last_payment_date, subscription.payment_method_id,
                    subscription.auto_renew, subscription.metadata,
                    subscription.created_at, subscription.updated_at
                )
            
            return subscription
    
    def _row_to_entity(self, row: asyncpg.Record) -> TenantSubscription:
        """Convert database row to TenantSubscription entity"""
        from ddd_refactored.domain.tenant_management.entities.tenant_subscription import (
            TenantSubscription, SubscriptionStatus, BillingFrequency, PaymentStatus
        )
        
        # Reconstruct entity from database row
        subscription = TenantSubscription(
            id=row['id'],
            tenant_id=row['tenant_id'],
            tier=row['tier'],
            status=SubscriptionStatus(row['status']),
            billing_frequency=BillingFrequency(row['billing_frequency']),
            base_price=row['base_price'],
            discount_percentage=row.get('discount_percentage', 0),
            trial_end_date=row.get('trial_end_date'),
            next_billing_date=row.get('next_billing_date'),
            payment_status=PaymentStatus(row['payment_status']),
            failed_payment_count=row.get('failed_payment_count', 0),
            last_payment_date=row.get('last_payment_date'),
            payment_method_id=row.get('payment_method_id'),
            auto_renew=row.get('auto_renew', True),
            metadata=row.get('metadata', {}),
            created_at=row['created_at'],
            updated_at=row.get('updated_at', row['created_at'])
        )
        
        return subscription