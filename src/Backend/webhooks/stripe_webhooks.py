"""
Stripe Webhook Handler
Processes Stripe events for subscription lifecycle management
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import Dict, Any
import asyncpg
import logging
import json
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from services.payment.stripe_provider import StripeProvider
from ddd_refactored.domain.tenant_management.entities.tenant_subscription import (
    TenantSubscription, SubscriptionStatus, PaymentStatus
)
from core.repositories.subscription_repository import SubscriptionRepository as TenantSubscriptionRepository
from core.database import get_db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ==========================================
# Dependency Injection
# ==========================================

async def get_stripe_provider(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> StripeProvider:
    """Get configured Stripe provider instance"""
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
# Webhook Endpoint
# ==========================================

@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: StripeProvider = Depends(get_stripe_provider),
    subscription_repo: TenantSubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Handle incoming Stripe webhook events.
    
    Stripe sends webhooks for various subscription lifecycle events.
    This endpoint validates the signature and processes the event.
    
    Important Events:
    - invoice.payment_succeeded: Payment successful, renew subscription
    - invoice.payment_failed: Payment failed, update status and notify
    - customer.subscription.deleted: Subscription cancelled
    - customer.subscription.updated: Subscription plan changed
    - customer.subscription.trial_will_end: Trial ending soon (3 days before)
    
    Returns:
        200 OK with event processing result
    """
    try:
        # Step 1: Get raw body and signature
        body = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            logger.error("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature"
            )
        
        # Step 2: Validate webhook signature
        is_valid = await stripe.validate_webhook(body, signature)
        
        if not is_valid:
            logger.error("Invalid Stripe webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Step 3: Parse event payload
        try:
            event = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        event_type = event.get('type')
        event_id = event.get('id')
        
        logger.info(f"Processing Stripe webhook: {event_type} (ID: {event_id})")
        
        # Step 4: Process event based on type
        result = await stripe.process_webhook(event_type, event)
        
        if not result.get('processed'):
            logger.info(f"Webhook event {event_type} not handled - no action required")
            return {"status": "ok", "message": "Event received but not processed"}
        
        # Step 5: Handle specific actions based on event type
        action = result.get('action')
        data = result.get('data', {})
        
        if action == 'payment_succeeded':
            await handle_payment_succeeded(data, subscription_repo)
        
        elif action == 'payment_failed':
            await handle_payment_failed(data, subscription_repo)
        
        elif action == 'subscription_cancelled':
            await handle_subscription_cancelled(data, subscription_repo)
        
        elif action == 'subscription_updated':
            await handle_subscription_updated(data, subscription_repo)
        
        elif action == 'trial_ending_soon':
            await handle_trial_ending_soon(data, subscription_repo)
        
        logger.info(f"Successfully processed Stripe webhook: {event_type}")
        
        return {
            "status": "ok",
            "event_type": event_type,
            "event_id": event_id,
            "action": action,
            "message": "Event processed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
        # Return 200 to Stripe even on errors to prevent retries
        # We log the error but acknowledge receipt
        return {
            "status": "error",
            "message": str(e)
        }


# ==========================================
# Event Handlers
# ==========================================

async def handle_payment_succeeded(
    data: Dict[str, Any],
    subscription_repo: TenantSubscriptionRepository
):
    """
    Handle successful payment event.
    
    Actions:
    1. Find subscription by Stripe subscription ID
    2. Record payment in domain model
    3. Renew subscription for next period
    4. Update next billing date
    5. Send payment confirmation email (future)
    
    Args:
        data: Payment data from webhook
        subscription_repo: Subscription repository
    """
    stripe_subscription_id = data.get('subscription_id')
    amount_paid = data.get('amount_paid', Decimal('0.00'))
    
    if not stripe_subscription_id:
        logger.warning("Payment succeeded webhook missing subscription_id")
        return
    
    # Find subscription by Stripe subscription ID
    subscription = await subscription_repo.find_by_stripe_subscription_id(stripe_subscription_id)
    
    if not subscription:
        logger.error(f"Subscription not found for Stripe subscription {stripe_subscription_id}")
        return
    
    logger.info(f"Recording successful payment for subscription {subscription.id}: ${amount_paid}")
    
    # Record payment using domain model
    subscription.record_payment(
        amount=amount_paid,
        payment_status=PaymentStatus.PAID,
        transaction_id=data.get('invoice_id')
    )
    
    # Renew subscription for next billing period
    subscription.renew()
    
    # Save changes
    await subscription_repo.save(subscription)
    
    logger.info(f"Subscription {subscription.id} renewed until {subscription.next_billing_date}")
    
    # TODO: Send payment confirmation email
    # await send_payment_confirmation_email(subscription)


async def handle_payment_failed(
    data: Dict[str, Any],
    subscription_repo: TenantSubscriptionRepository
):
    """
    Handle failed payment event.
    
    Actions:
    1. Find subscription by Stripe subscription ID
    2. Record failed payment in domain model
    3. Increment failed payment counter
    4. Update subscription status (PAST_DUE or SUSPENDED)
    5. Send payment failure notification email
    
    Args:
        data: Payment failure data from webhook
        subscription_repo: Subscription repository
    """
    stripe_subscription_id = data.get('subscription_id')
    amount_due = data.get('amount_due', Decimal('0.00'))
    attempt_count = data.get('attempt_count', 1)
    
    if not stripe_subscription_id:
        logger.warning("Payment failed webhook missing subscription_id")
        return
    
    # Find subscription
    subscription = await subscription_repo.find_by_stripe_subscription_id(stripe_subscription_id)
    
    if not subscription:
        logger.error(f"Subscription not found for Stripe subscription {stripe_subscription_id}")
        return
    
    logger.warning(f"Payment failed for subscription {subscription.id}: ${amount_due} (attempt {attempt_count})")
    
    # Record failed payment
    subscription.record_payment(
        amount=amount_due,
        payment_status=PaymentStatus.FAILED,
        transaction_id=data.get('invoice_id')
    )
    
    # Update status based on attempt count
    if attempt_count >= 3:
        # After 3 failed attempts, suspend subscription
        subscription.suspend(reason=f"Payment failed after {attempt_count} attempts")
        logger.warning(f"Subscription {subscription.id} suspended due to repeated payment failures")
    else:
        # Mark as past due
        subscription.status = SubscriptionStatus.PAST_DUE
        logger.info(f"Subscription {subscription.id} marked as PAST_DUE")
    
    # Save changes
    await subscription_repo.save(subscription)
    
    # TODO: Send payment failure notification email
    # await send_payment_failure_email(subscription, attempt_count)


async def handle_subscription_cancelled(
    data: Dict[str, Any],
    subscription_repo: TenantSubscriptionRepository
):
    """
    Handle subscription cancellation event.
    
    This occurs when:
    - Customer cancels via Stripe customer portal
    - Subscription is cancelled via API
    - Final payment attempt fails and Stripe auto-cancels
    
    Args:
        data: Cancellation data from webhook
        subscription_repo: Subscription repository
    """
    stripe_subscription_id = data.get('subscription_id')
    canceled_at = data.get('canceled_at')
    
    if not stripe_subscription_id:
        logger.warning("Subscription cancelled webhook missing subscription_id")
        return
    
    # Find subscription
    subscription = await subscription_repo.find_by_stripe_subscription_id(stripe_subscription_id)
    
    if not subscription:
        logger.error(f"Subscription not found for Stripe subscription {stripe_subscription_id}")
        return
    
    logger.info(f"Cancelling subscription {subscription.id} from Stripe webhook")
    
    # Cancel subscription using domain model
    subscription.cancel(
        immediate=True,
        reason="Cancelled via Stripe"
    )
    
    # Save changes
    await subscription_repo.save(subscription)
    
    logger.info(f"Subscription {subscription.id} cancelled at {canceled_at}")
    
    # TODO: Send cancellation confirmation email
    # await send_cancellation_email(subscription)


async def handle_subscription_updated(
    data: Dict[str, Any],
    subscription_repo: TenantSubscriptionRepository
):
    """
    Handle subscription update event.
    
    This occurs when:
    - Subscription plan is changed (upgrade/downgrade)
    - Billing frequency is changed
    - Subscription is reactivated
    
    Args:
        data: Update data from webhook
        subscription_repo: Subscription repository
    """
    stripe_subscription_id = data.get('subscription_id')
    new_status = data.get('status')
    current_period_end = data.get('current_period_end')
    
    if not stripe_subscription_id:
        logger.warning("Subscription updated webhook missing subscription_id")
        return
    
    # Find subscription
    subscription = await subscription_repo.find_by_stripe_subscription_id(stripe_subscription_id)
    
    if not subscription:
        logger.error(f"Subscription not found for Stripe subscription {stripe_subscription_id}")
        return
    
    logger.info(f"Updating subscription {subscription.id} from Stripe webhook")
    
    # Map Stripe status to our SubscriptionStatus
    status_map = {
        'active': SubscriptionStatus.ACTIVE,
        'trialing': SubscriptionStatus.TRIAL,
        'past_due': SubscriptionStatus.PAST_DUE,
        'canceled': SubscriptionStatus.CANCELLED,
        'unpaid': SubscriptionStatus.SUSPENDED
    }
    
    if new_status in status_map:
        subscription.status = status_map[new_status]
        logger.info(f"Updated subscription {subscription.id} status to {new_status}")
    
    # Update billing date if provided
    if current_period_end:
        subscription.next_billing_date = current_period_end.date() if isinstance(current_period_end, datetime) else current_period_end
    
    # Save changes
    await subscription_repo.save(subscription)


async def handle_trial_ending_soon(
    data: Dict[str, Any],
    subscription_repo: TenantSubscriptionRepository
):
    """
    Handle trial ending soon event (3 days before trial ends).
    
    Actions:
    1. Find subscription
    2. Send reminder email to customer
    3. Ensure payment method is attached
    
    Args:
        data: Trial ending data from webhook
        subscription_repo: Subscription repository
    """
    stripe_subscription_id = data.get('subscription_id')
    trial_end = data.get('trial_end')
    
    if not stripe_subscription_id:
        logger.warning("Trial ending webhook missing subscription_id")
        return
    
    # Find subscription
    subscription = await subscription_repo.find_by_stripe_subscription_id(stripe_subscription_id)
    
    if not subscription:
        logger.error(f"Subscription not found for Stripe subscription {stripe_subscription_id}")
        return
    
    logger.info(f"Trial ending soon for subscription {subscription.id} on {trial_end}")
    
    # TODO: Send trial ending reminder email
    # await send_trial_ending_email(subscription, trial_end)
    
    # TODO: Check if payment method is attached
    # If not, prompt customer to add payment method


# ==========================================
# Helper Functions
# ==========================================

async def send_payment_confirmation_email(subscription: TenantSubscription):
    """Send payment confirmation email to customer"""
    # TODO: Implement email sending
    logger.info(f"TODO: Send payment confirmation email for subscription {subscription.id}")


async def send_payment_failure_email(subscription: TenantSubscription, attempt_count: int):
    """Send payment failure notification email"""
    # TODO: Implement email sending
    logger.info(f"TODO: Send payment failure email for subscription {subscription.id} (attempt {attempt_count})")


async def send_cancellation_email(subscription: TenantSubscription):
    """Send subscription cancellation confirmation email"""
    # TODO: Implement email sending
    logger.info(f"TODO: Send cancellation email for subscription {subscription.id}")


async def send_trial_ending_email(subscription: TenantSubscription, trial_end: datetime):
    """Send trial ending reminder email"""
    # TODO: Implement email sending
    logger.info(f"TODO: Send trial ending email for subscription {subscription.id}")
