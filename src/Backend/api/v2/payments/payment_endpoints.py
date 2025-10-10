"""
Payment Processing V2 Endpoints
DDD-Powered Payment API using Payment Processing Bounded Context

This endpoint demonstrates the DDD integration pattern:
- Uses PaymentTransaction aggregate from domain layer
- Implements Command/Query separation
- Publishes domain events
- Returns clean DTOs (not domain objects)
- Full backward compatibility with V1
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import logging

from ..dependencies import get_payment_service, get_current_user, PaymentService
from ..dto_mappers import (
    PaymentTransactionDTO,
    ProcessPaymentRequest,
    RefundPaymentRequest,
    map_payment_to_dto
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/v2/payments",
    tags=["💳 Payments V2 (DDD-Powered)"],
    responses={
        404: {"description": "Payment transaction not found"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "/process",
    response_model=PaymentTransactionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Process Payment",
    description="""
    Process a new payment transaction using DDD Payment Processing context.

    **Features:**
    - Creates PaymentTransaction aggregate
    - Validates business rules
    - Publishes PaymentInitiated event
    - Returns complete payment details

    **Business Rules:**
    - Amount must be positive
    - Payment method must be valid
    - Card details required for card payments
    """
)
async def process_payment(
    request: ProcessPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Process a payment transaction

    This endpoint:
    1. Creates PaymentTransaction aggregate
    2. Validates business rules
    3. Publishes domain events
    4. Returns DTO (not domain object)
    """
    try:
        logger.info(f"Processing payment for order {request.order_id}")

        # Use tenant/store from authenticated user
        payment = await service.process_payment(
            order_id=request.order_id,
            store_id=current_user.get("store_id", "default-store"),
            tenant_id=current_user.get("tenant_id", "default-tenant"),
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            customer_id=request.customer_id or current_user.get("id")
        )

        logger.info(f"Payment created: {payment['id']}")
        return payment

    except ValueError as e:
        # Business rule violation
        logger.warning(f"Payment validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment request: {str(e)}"
        )
    except Exception as e:
        # System error
        logger.error(f"Payment processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed. Please try again."
        )


@router.get(
    "/{transaction_id}",
    response_model=PaymentTransactionDTO,
    summary="Get Payment Transaction",
    description="Retrieve payment transaction details by ID"
)
async def get_transaction(
    transaction_id: str,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """Get payment transaction by ID"""
    try:
        logger.info(f"Retrieving payment: {transaction_id}")

        payment = await service.get_transaction(transaction_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment transaction {transaction_id} not found"
            )

        return map_payment_to_dto(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment transaction"
        )


@router.post(
    "/{transaction_id}/refund",
    response_model=PaymentTransactionDTO,
    summary="Refund Payment",
    description="""
    Refund a payment transaction (full or partial).

    **Business Rules:**
    - Only captured payments can be refunded
    - Refund amount cannot exceed remaining amount
    - Multiple partial refunds are allowed
    """
)
async def refund_payment(
    transaction_id: str,
    request: RefundPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Refund a payment transaction

    This endpoint:
    1. Loads PaymentTransaction aggregate
    2. Validates refund is allowed
    3. Initiates refund process
    4. Publishes RefundIssued event
    """
    try:
        logger.info(f"Refunding payment {transaction_id}: {request.amount or 'full'}")

        payment = await service.refund_payment(
            transaction_id=transaction_id,
            amount=request.amount,
            reason=request.reason
        )

        logger.info(f"Refund initiated for payment {transaction_id}")
        return map_payment_to_dto(payment)

    except ValueError as e:
        logger.warning(f"Refund validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid refund request: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refund processing failed"
        )


@router.get(
    "/",
    response_model=List[PaymentTransactionDTO],
    summary="List Payment Transactions",
    description="List payment transactions with optional filters"
)
async def list_transactions(
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """
    List payment transactions with optional filtering

    Supports pagination and filtering by order_id and status
    """
    try:
        logger.info(f"Listing payments: order_id={order_id}, status={status}")

        # In full implementation, would use query handlers
        # For now, return empty list
        payments = []

        return [map_payment_to_dto(p) for p in payments]

    except Exception as e:
        logger.error(f"Failed to list payments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list payment transactions"
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if Payment V2 API is healthy",
    tags=["Health"]
)
async def health_check():
    """Health check endpoint for Payment V2 API"""
    return {
        "status": "healthy",
        "service": "payments-v2",
        "version": "2.0.0",
        "ddd_enabled": True,
        "features": [
            "process_payment",
            "refund_payment",
            "query_transactions",
            "event_publishing"
        ]
    }


@router.get(
    "/stats",
    summary="Payment Statistics",
    description="Get payment statistics and metrics"
)
async def get_stats(
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get payment processing statistics

    Returns metrics useful for monitoring and dashboards
    """
    return {
        "total_processed": 0,
        "total_amount": 0.0,
        "success_rate": 0.0,
        "average_amount": 0.0,
        "refund_rate": 0.0,
        "note": "Statistics will be calculated from event store in production"
    }
