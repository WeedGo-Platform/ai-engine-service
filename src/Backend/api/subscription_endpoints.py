"""
Subscription Management API Endpoints
Handles tenant subscription billing with Stripe integration
"""

from fastapi import APIRouter, HTTPException, Depends, status, Body, Header
from typing import Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
import asyncpg
import logging
from decimal import Decimal

from services.tenant_service import TenantService
from services.payment.provider_factory import PaymentProviderFactory, ProviderType
from services.payment.stripe_provider import StripeProvider
from services.security.credential_manager import CredentialManager
from ddd_refactored.domain.tenant_management.entities.tenant_subscription import (
    TenantSubscription, SubscriptionStatus, BillingFrequency
)
from core.repositories.subscription_repository import SubscriptionRepository as TenantSubscriptionRepository
from core.database import get_db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


# ==========================================
# Pydantic Models for API
# ==========================================

class CreateSubscriptionRequest(BaseModel):
    """Request model for creating a new subscription"""
    tenant_id: UUID
    plan_tier: str = Field(..., description="Subscription tier: community, professional, enterprise")
    billing_frequency: str = Field(..., description="Billing frequency: monthly, quarterly, annual")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID (pm_...)")
    customer_email: EmailStr = Field(..., description="Customer email for Stripe customer creation")
    customer_name: Optional[str] = Field(None, description="Customer name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class UpdateSubscriptionRequest(BaseModel):
    """Request model for updating/upgrading a subscription"""
    new_tier: Optional[str] = Field(None, description="New subscription tier")
    new_billing_frequency: Optional[str] = Field(None, description="New billing frequency")
    payment_method_id: Optional[str] = Field(None, description="New payment method ID")


class CancelSubscriptionRequest(BaseModel):
    """Request model for cancelling a subscription"""
    cancel_immediately: bool = Field(False, description="Cancel now or at period end")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class SubscriptionResponse(BaseModel):
    """Response model for subscription details"""
    subscription_id: str
    tenant_id: UUID
    tier: str
    status: str
    billing_frequency: str
    base_price: Decimal
    next_billing_date: Optional[datetime]
    stripe_subscription_id: Optional[str]
    stripe_customer_id: Optional[str]
    payment_status: str
    auto_renew: bool
    created_at: datetime


# ==========================================
# Pricing Configuration
# ==========================================

SUBSCRIPTION_PRICING = {
    "community": {
        "monthly": Decimal("0.00"),  # Free tier
        "quarterly": Decimal("0.00"),
        "annual": Decimal("0.00"),
        "stripe_price_id": None,  # No Stripe price for free tier
        "max_stores": 1,
        "max_users": 3,
        "max_products": 100
    },
    "professional": {
        "monthly": Decimal("199.00"),
        "quarterly": Decimal("537.00"),  # 10% discount
        "annual": Decimal("1990.00"),  # ~17% discount
        "stripe_price_id": {
            "monthly": "price_professional_monthly_cad",  # Replace with actual Stripe price IDs
            "quarterly": "price_professional_quarterly_cad",
            "annual": "price_professional_annual_cad"
        },
        "max_stores": 5,
        "max_users": 25,
        "max_products": 10000
    },
    "enterprise": {
        "monthly": Decimal("499.00"),
        "quarterly": Decimal("1347.00"),  # 10% discount
        "annual": Decimal("4990.00"),  # ~17% discount
        "stripe_price_id": {
            "monthly": "price_enterprise_monthly_cad",
            "quarterly": "price_enterprise_quarterly_cad",
            "annual": "price_enterprise_annual_cad"
        },
        "max_stores": 999,  # Unlimited
        "max_users": 999,
        "max_products": 999999
    }
}


# ==========================================
# Dependency Injection
# ==========================================

async def get_stripe_provider(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> StripeProvider:
    """Get configured Stripe provider instance"""
    credential_manager = CredentialManager(db_pool)
    
    # Load Stripe credentials from secure storage
    # In production, these should be stored in credential_manager
    # For now, using environment variables as fallback
    import os
    
    stripe_config = {
        'api_key': os.getenv('STRIPE_SECRET_KEY'),
        'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET'),
        'environment': os.getenv('STRIPE_ENVIRONMENT', 'test')
    }
    
    if not stripe_config['api_key']:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe payment provider not configured"
        )
    
    return StripeProvider(stripe_config)


async def get_subscription_repository(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> TenantSubscriptionRepository:
    """Get subscription repository instance"""
    return TenantSubscriptionRepository(db_pool)


# ==========================================
# API Endpoints
# ==========================================

@router.post("/create", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: StripeProvider = Depends(get_stripe_provider),
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Create a new subscription with Stripe integration.
    
    Workflow:
    1. Validate pricing tier and billing frequency
    2. Create Stripe customer
    3. Attach payment method (if provided)
    4. Create Stripe subscription with trial period
    5. Create TenantSubscription domain entity
    6. Save to database
    
    Returns:
        Subscription details with Stripe subscription ID
    """
    try:
        # Validate tier and billing frequency
        if request.plan_tier.lower() not in SUBSCRIPTION_PRICING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan tier: {request.plan_tier}"
            )
        
        billing_freq = request.billing_frequency.lower()
        if billing_freq not in ["monthly", "quarterly", "annual"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid billing frequency: {billing_freq}"
            )
        
        pricing = SUBSCRIPTION_PRICING[request.plan_tier.lower()]
        base_price = pricing[billing_freq]
        stripe_price_id = pricing.get("stripe_price_id", {}).get(billing_freq) if isinstance(pricing.get("stripe_price_id"), dict) else None
        
        # Free tier doesn't require Stripe
        stripe_customer_id = None
        stripe_subscription_id = None
        
        if base_price > 0 and stripe_price_id:
            # Only create Stripe resources for paid plans
            if not request.payment_method_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment method required for paid plans"
                )
            
            # Step 1: Create Stripe customer
            customer_metadata = {
                'tenant_id': str(request.tenant_id),
                'plan_tier': request.plan_tier,
                'billing_frequency': billing_freq
            }
            customer_metadata.update(request.metadata)
            
            customer_response = await stripe.create_customer(
                email=request.customer_email,
                name=request.customer_name,
                metadata=customer_metadata,
                payment_method_id=request.payment_method_id
            )
            stripe_customer_id = customer_response['customer_id']
            logger.info(f"Created Stripe customer: {stripe_customer_id} for tenant {request.tenant_id}")
            
            # Step 2: Attach payment method
            await stripe.attach_payment_method_to_customer(
                payment_method_id=request.payment_method_id,
                customer_id=stripe_customer_id
            )
            logger.info(f"Attached payment method {request.payment_method_id} to customer {stripe_customer_id}")
            
            # Step 3: Create Stripe subscription (no trial)
            subscription_metadata = {
                'tenant_id': str(request.tenant_id),
                'plan_tier': request.plan_tier
            }
            
            stripe_sub_response = await stripe.create_subscription(
                customer_id=stripe_customer_id,
                price_id=stripe_price_id,
                trial_period_days=None,
                metadata=subscription_metadata,
                payment_method_id=request.payment_method_id
            )
            stripe_subscription_id = stripe_sub_response['subscription_id']
            logger.info(f"Created Stripe subscription: {stripe_subscription_id}")
        
        # Step 4: Create TenantSubscription domain entity
        # Map billing frequency to enum
        frequency_map = {
            'monthly': BillingFrequency.MONTHLY,
            'quarterly': BillingFrequency.QUARTERLY,
            'annual': BillingFrequency.ANNUAL
        }
        
        subscription = TenantSubscription.create(
            tenant_id=request.tenant_id,
            tier=request.plan_tier.lower(),
            billing_frequency=frequency_map[billing_freq],
            base_price=base_price,
            max_stores=pricing.get('max_stores', 1),
            max_users=pricing.get('max_users', 3),
            max_products=pricing.get('max_products', 100)
        )
        
        # Store Stripe IDs in metadata
        if stripe_customer_id:
            subscription.metadata['stripe_customer_id'] = stripe_customer_id
        if stripe_subscription_id:
            subscription.metadata['stripe_subscription_id'] = stripe_subscription_id
        
        # Step 5: Save to database
        saved_subscription = await subscription_repo.save(subscription)
        
        logger.info(f"Created subscription {saved_subscription.id} for tenant {request.tenant_id}")
        
        return SubscriptionResponse(
            subscription_id=str(saved_subscription.id),
            tenant_id=saved_subscription.tenant_id,
            tier=saved_subscription.tier,
            status=saved_subscription.status.value,
            billing_frequency=saved_subscription.billing_frequency.value,
            base_price=saved_subscription.base_price,
            next_billing_date=saved_subscription.next_billing_date,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            payment_status=saved_subscription.payment_status.value,
            auto_renew=saved_subscription.auto_renew,
            created_at=saved_subscription.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.get("/{tenant_id}", response_model=SubscriptionResponse)
async def get_subscription(
    tenant_id: UUID,
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Get active subscription for a tenant.
    
    Args:
        tenant_id: Tenant UUID
    
    Returns:
        Active subscription details
    """
    try:
        subscription = await subscription_repo.get_active_by_tenant(tenant_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active subscription found for tenant {tenant_id}"
            )
        
        return SubscriptionResponse(
            subscription_id=str(subscription.id),
            tenant_id=subscription.tenant_id,
            tier=subscription.tier,
            status=subscription.status.value,
            billing_frequency=subscription.billing_frequency.value,
            base_price=subscription.base_price,
            next_billing_date=subscription.next_billing_date,
            stripe_subscription_id=subscription.metadata.get('stripe_subscription_id'),
            stripe_customer_id=subscription.metadata.get('stripe_customer_id'),
            payment_status=subscription.payment_status.value,
            auto_renew=subscription.auto_renew,
            created_at=subscription.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription: {str(e)}"
        )


@router.patch("/{subscription_id}/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    subscription_id: UUID,
    request: UpdateSubscriptionRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: StripeProvider = Depends(get_stripe_provider),
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Upgrade/downgrade subscription plan.
    
    Workflow:
    1. Load existing subscription
    2. Calculate new pricing
    3. Update Stripe subscription (if paid plan)
    4. Update domain entity
    5. Save changes
    
    Returns:
        Updated subscription details
    """
    try:
        # Load existing subscription
        subscription = await subscription_repo.get_by_id(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {subscription_id} not found"
            )
        
        # Validate new tier if provided
        if request.new_tier:
            if request.new_tier.lower() not in SUBSCRIPTION_PRICING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid plan tier: {request.new_tier}"
                )
            
            new_tier = request.new_tier.lower()
            billing_freq = request.new_billing_frequency or subscription.billing_frequency.value
            
            # Get new pricing
            pricing = SUBSCRIPTION_PRICING[new_tier]
            new_price = pricing[billing_freq]
            new_stripe_price_id = pricing.get("stripe_price_id", {}).get(billing_freq) if isinstance(pricing.get("stripe_price_id"), dict) else None
            
            # Update Stripe subscription if it exists
            stripe_subscription_id = subscription.metadata.get('stripe_subscription_id')
            if stripe_subscription_id and new_stripe_price_id:
                await stripe.update_subscription(
                    subscription_id=stripe_subscription_id,
                    new_price_id=new_stripe_price_id
                )
                logger.info(f"Updated Stripe subscription {stripe_subscription_id} to price {new_stripe_price_id}")
            
            # Update domain entity
            subscription.tier = new_tier
            subscription.base_price = new_price
            subscription.max_stores = pricing.get('max_stores', 1)
            subscription.max_users = pricing.get('max_users', 3)
            subscription.max_products = pricing.get('max_products', 100)
        
        # Update payment method if provided
        if request.payment_method_id:
            stripe_customer_id = subscription.metadata.get('stripe_customer_id')
            if stripe_customer_id:
                await stripe.attach_payment_method_to_customer(
                    payment_method_id=request.payment_method_id,
                    customer_id=stripe_customer_id
                )
                subscription.payment_method_id = request.payment_method_id
        
        # Save changes
        updated_subscription = await subscription_repo.save(subscription)
        
        logger.info(f"Updated subscription {subscription_id}")
        
        return SubscriptionResponse(
            subscription_id=str(updated_subscription.id),
            tenant_id=updated_subscription.tenant_id,
            tier=updated_subscription.tier,
            status=updated_subscription.status.value,
            billing_frequency=updated_subscription.billing_frequency.value,
            base_price=updated_subscription.base_price,
            next_billing_date=updated_subscription.next_billing_date,
            trial_end_date=updated_subscription.trial_end_date,
            stripe_subscription_id=updated_subscription.metadata.get('stripe_subscription_id'),
            stripe_customer_id=updated_subscription.metadata.get('stripe_customer_id'),
            payment_status=updated_subscription.payment_status.value,
            auto_renew=updated_subscription.auto_renew,
            created_at=updated_subscription.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.delete("/{subscription_id}/cancel", response_model=Dict[str, Any])
async def cancel_subscription(
    subscription_id: UUID,
    request: CancelSubscriptionRequest = Body(...),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: StripeProvider = Depends(get_stripe_provider),
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Cancel a subscription.
    
    Args:
        subscription_id: Subscription UUID
        request: Cancellation request with immediate flag and reason
    
    Returns:
        Cancellation confirmation
    """
    try:
        # Load subscription
        subscription = await subscription_repo.get_by_id(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {subscription_id} not found"
            )
        
        # Cancel in Stripe if it exists
        stripe_subscription_id = subscription.metadata.get('stripe_subscription_id')
        if stripe_subscription_id:
            await stripe.cancel_subscription(
                subscription_id=stripe_subscription_id,
                cancel_immediately=request.cancel_immediately
            )
            logger.info(f"Cancelled Stripe subscription {stripe_subscription_id}")
        
        # Cancel domain entity
        cancellation_reason = request.reason or "Customer requested cancellation"
        subscription.cancel(immediate=request.cancel_immediately, reason=cancellation_reason)
        
        # Save changes
        await subscription_repo.save(subscription)
        
        logger.info(f"Cancelled subscription {subscription_id}")
        
        return {
            "subscription_id": str(subscription_id),
            "status": "cancelled" if request.cancel_immediately else "cancelling_at_period_end",
            "cancelled_at": datetime.utcnow(),
            "effective_date": datetime.utcnow() if request.cancel_immediately else subscription.next_billing_date,
            "message": "Subscription cancelled successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/{subscription_id}/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    subscription_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: StripeProvider = Depends(get_stripe_provider),
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Reactivate a subscription that was set to cancel at period end.
    
    Args:
        subscription_id: Subscription UUID
    
    Returns:
        Reactivated subscription details
    """
    try:
        # Load subscription
        subscription = await subscription_repo.get_by_id(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {subscription_id} not found"
            )
        
        # Reactivate in Stripe
        stripe_subscription_id = subscription.metadata.get('stripe_subscription_id')
        if stripe_subscription_id:
            await stripe.reactivate_subscription(stripe_subscription_id)
            logger.info(f"Reactivated Stripe subscription {stripe_subscription_id}")
        
        # Update domain entity
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.auto_renew = True
        
        # Save changes
        updated_subscription = await subscription_repo.save(subscription)
        
        logger.info(f"Reactivated subscription {subscription_id}")
        
        return SubscriptionResponse(
            subscription_id=str(updated_subscription.id),
            tenant_id=updated_subscription.tenant_id,
            tier=updated_subscription.tier,
            status=updated_subscription.status.value,
            billing_frequency=updated_subscription.billing_frequency.value,
            base_price=updated_subscription.base_price,
            next_billing_date=updated_subscription.next_billing_date,
            trial_end_date=updated_subscription.trial_end_date,
            stripe_subscription_id=updated_subscription.metadata.get('stripe_subscription_id'),
            stripe_customer_id=updated_subscription.metadata.get('stripe_customer_id'),
            payment_status=updated_subscription.payment_status.value,
            auto_renew=updated_subscription.auto_renew,
            created_at=updated_subscription.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reactivate subscription: {str(e)}"
        )
