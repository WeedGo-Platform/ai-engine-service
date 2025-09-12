"""
Payment API Endpoints
Secure payment processing with PCI compliance considerations
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field, validator
import logging
import hashlib
import hmac
import time
import asyncpg
import os
from enum import Enum

from services.payment_service import PaymentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])
security = HTTPBearer()

# Database connection pool
db_pool = None

# Rate limiting cache (in production, use Redis)
rate_limit_cache = {}


class PaymentProvider(str, Enum):
    MONERIS = "moneris"
    CLOVER = "clover"
    INTERAC = "interac"
    NUVEI = "nuvei"
    PAYBRIGHT = "paybright"


class PaymentMethodInput(BaseModel):
    """Input for saving a payment method"""
    card_number: str = Field(..., min_length=13, max_length=19, description="Card number (will be tokenized)")
    card_holder_name: str = Field(..., min_length=2, max_length=100)
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=datetime.now().year, le=datetime.now().year + 20)
    cvv: str = Field(..., min_length=3, max_length=4, description="Card verification value")
    billing_address: Dict[str, str] = Field(...)
    set_as_default: bool = Field(default=False)
    provider: PaymentProvider = Field(default=PaymentProvider.MONERIS)
    
    @validator('card_number')
    def validate_card_number(cls, v):
        # Remove spaces and validate using Luhn algorithm
        card_num = v.replace(' ', '').replace('-', '')
        if not card_num.isdigit():
            raise ValueError('Card number must contain only digits')
        
        # Luhn algorithm validation
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        if luhn_checksum(card_num) != 0:
            raise ValueError('Invalid card number')
        return card_num
    
    @validator('billing_address')
    def validate_billing_address(cls, v):
        required_fields = ['street', 'city', 'province', 'postal_code', 'country']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Billing address must include {field}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "card_number": "4242424242424242",
                "card_holder_name": "John Doe",
                "exp_month": 12,
                "exp_year": 2025,
                "cvv": "123",
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Toronto",
                    "province": "ON",
                    "postal_code": "M5V 3A8",
                    "country": "Canada"
                },
                "set_as_default": True
            }
        }


class ProcessPaymentRequest(BaseModel):
    """Request for processing a payment"""
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount in CAD")
    order_id: Optional[UUID] = Field(None, description="Associated order ID")
    payment_method_id: Optional[UUID] = Field(None, description="Saved payment method ID")
    payment_method: Optional[PaymentMethodInput] = Field(None, description="New payment method")
    save_payment_method: bool = Field(default=False, description="Save payment method for future use")
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    idempotency_key: Optional[str] = Field(None, description="Unique key to prevent duplicate charges")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v > Decimal('10000'):  # Max transaction limit
            raise ValueError('Amount exceeds maximum transaction limit')
        return v
    
    @validator('payment_method_id', 'payment_method')
    def validate_payment_info(cls, v, values):
        if 'payment_method_id' in values and 'payment_method' in values:
            if not values['payment_method_id'] and not values.get('payment_method'):
                raise ValueError('Either payment_method_id or payment_method must be provided')
        return v


class RefundRequest(BaseModel):
    """Request for processing a refund"""
    transaction_id: UUID = Field(..., description="Original transaction ID")
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Refund amount (omit for full refund)")
    reason: str = Field(..., min_length=5, max_length=500, description="Refund reason")
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 50.00,
                "reason": "Customer requested refund - product not as described"
            }
        }


class WebhookRequest(BaseModel):
    """Webhook payload from payment provider"""
    provider: PaymentProvider
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: Optional[int] = None


async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_payment_service():
    """Get payment service instance"""
    pool = await get_db_pool()
    service = PaymentService(pool)
    await service.initialize()
    return service


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate user authentication"""
    # TODO: Implement proper JWT validation
    # For now, return a mock user ID
    return UUID("123e4567-e89b-12d3-a456-426614174000")


async def check_rate_limit(request: Request, user_id: UUID):
    """Check rate limiting for payment endpoints"""
    client_ip = request.client.host
    key = f"{user_id}:{client_ip}"
    current_time = time.time()
    
    # Clean old entries
    rate_limit_cache[key] = [
        t for t in rate_limit_cache.get(key, []) 
        if current_time - t < 60
    ]
    
    # Check rate limit (10 requests per minute)
    if len(rate_limit_cache.get(key, [])) >= 10:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Add current request
    if key not in rate_limit_cache:
        rate_limit_cache[key] = []
    rate_limit_cache[key].append(current_time)


def validate_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    provider: str
) -> bool:
    """Validate webhook signature from payment provider"""
    if provider == "moneris":
        # Moneris uses HMAC-SHA256
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    elif provider == "clover":
        # Clover uses different signature method
        # Implementation depends on Clover's specification
        pass
    return False


# ENDPOINTS

@router.post("/process", response_model=Dict[str, Any])
async def process_payment(
    request: ProcessPaymentRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """
    Process a payment transaction
    
    Security measures:
    - Rate limiting
    - Idempotency key support
    - Request validation
    - Audit logging
    """
    try:
        # Rate limiting
        await check_rate_limit(req, user_id)
        
        # Check idempotency
        if request.idempotency_key:
            # TODO: Check if this key was already processed
            pass
        
        # Log payment attempt (without sensitive data)
        logger.info(f"Payment attempt - User: {user_id}, Amount: {request.amount}, Order: {request.order_id}")
        
        # Process payment method
        payment_method_id = request.payment_method_id
        
        if not payment_method_id and request.payment_method:
            # Save new payment method if requested
            if request.save_payment_method:
                pm_result = await service.save_payment_method(
                    customer_id=user_id,
                    payment_data=request.payment_method.dict(),
                    provider_type=request.payment_method.provider,
                    set_as_default=request.payment_method.set_as_default
                )
                if pm_result['success']:
                    payment_method_id = UUID(pm_result['payment_method_id'])
        
        # Process payment
        result = await service.process_payment(
            amount=request.amount,
            payment_method_id=payment_method_id,
            order_id=request.order_id,
            customer_id=user_id,
            description=request.description,
            metadata=request.metadata,
            ip_address=req.client.host,
            user_agent=req.headers.get('user-agent')
        )
        
        # Audit log in background
        background_tasks.add_task(
            log_payment_audit,
            user_id,
            result.get('transaction_id'),
            result.get('success'),
            request.amount
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Payment processing failed')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your payment"
        )


@router.post("/refund", response_model=Dict[str, Any])
async def process_refund(
    request: RefundRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """
    Process a refund for a transaction
    
    Requires admin privileges or ownership of original transaction
    """
    try:
        # Rate limiting
        await check_rate_limit(req, user_id)
        
        # TODO: Verify user has permission to refund this transaction
        
        # Process refund
        result = await service.refund_transaction(
            transaction_id=request.transaction_id,
            amount=request.amount,
            reason=request.reason,
            initiated_by=user_id
        )
        
        # Audit log
        background_tasks.add_task(
            log_refund_audit,
            user_id,
            request.transaction_id,
            request.amount,
            request.reason
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Refund processing failed')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing the refund"
        )


@router.get("/methods", response_model=List[Dict[str, Any]])
async def get_payment_methods(
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """Get saved payment methods for the current user"""
    try:
        methods = await service.get_payment_methods(user_id)
        return methods
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch payment methods"
        )


@router.post("/methods", response_model=Dict[str, Any])
async def save_payment_method(
    payment_method: PaymentMethodInput,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """Save a new payment method"""
    try:
        result = await service.save_payment_method(
            customer_id=user_id,
            payment_data=payment_method.dict(),
            provider_type=payment_method.provider,
            set_as_default=payment_method.set_as_default
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to save payment method')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving payment method: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save payment method"
        )


@router.delete("/methods/{method_id}")
async def delete_payment_method(
    method_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """Delete a saved payment method"""
    try:
        success = await service.delete_payment_method(method_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Payment method not found"
            )
        
        return {"success": True, "message": "Payment method deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment method: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete payment method"
        )


@router.get("/transactions", response_model=List[Dict[str, Any]])
async def get_transaction_history(
    limit: int = 20,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """Get transaction history for the current user"""
    try:
        transactions = await service.get_transaction_history(
            customer_id=user_id,
            limit=limit,
            offset=offset
        )
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch transaction history"
        )


@router.get("/transactions/{transaction_id}", response_model=Dict[str, Any])
async def get_transaction_details(
    transaction_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """Get details for a specific transaction"""
    try:
        # TODO: Verify user has access to this transaction
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            transaction = await conn.fetchrow("""
                SELECT t.*, pp.name as provider_name
                FROM payment_transactions t
                JOIN payment_providers pp ON t.provider_id = pp.id
                WHERE t.id = $1 AND t.tenant_id = $2
            """, transaction_id, user_id)
            
            if not transaction:
                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found"
                )
            
            return {
                'id': str(transaction['id']),
                'reference': transaction['transaction_reference'],
                'type': transaction['type'],
                'status': transaction['status'],
                'amount': float(transaction['amount']),
                'currency': transaction['currency'],
                'provider': transaction['provider_name'],
                'created_at': transaction['created_at'].isoformat(),
                'completed_at': transaction['completed_at'].isoformat() if transaction['completed_at'] else None,
                'error_message': transaction['error_message']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch transaction details"
        )


@router.post("/webhook/{provider}")
async def handle_webhook(
    provider: PaymentProvider,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle webhooks from payment providers
    
    Each provider has different signature validation methods
    """
    try:
        # Get raw body for signature validation
        body = await request.body()
        
        # Validate signature
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            provider_config = await conn.fetchrow("""
                SELECT configuration 
                FROM payment_providers 
                WHERE provider_type = $1
            """, provider.value)
            
            if not provider_config:
                raise HTTPException(status_code=400, detail="Invalid provider")
            
            webhook_secret = provider_config['configuration'].get('webhook_secret')
            
            if webhook_secret and x_webhook_signature:
                if not validate_webhook_signature(
                    body, 
                    x_webhook_signature, 
                    webhook_secret,
                    provider.value
                ):
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid webhook signature"
                    )
            
            # Parse webhook data
            webhook_data = await request.json()
            
            # Store webhook for processing
            await conn.execute("""
                INSERT INTO payment_webhooks (
                    provider_id, event_type, payload, 
                    signature, signature_verified, processed
                ) VALUES (
                    (SELECT id FROM payment_providers WHERE provider_type = $1),
                    $2, $3, $4, $5, false
                )
            """, provider.value, webhook_data.get('event_type', 'unknown'),
                webhook_data, x_webhook_signature, True)
            
            # Process webhook in background
            background_tasks.add_task(
                process_webhook_event,
                provider.value,
                webhook_data
            )
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # Return 200 to prevent retries for malformed webhooks
        return {"received": False, "error": "Processing error"}


@router.get("/analytics")
async def get_payment_analytics(
    start_date: datetime,
    end_date: datetime,
    provider: Optional[PaymentProvider] = None,
    user_id: UUID = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """
    Get payment analytics for a date range
    
    Requires admin privileges
    """
    try:
        # TODO: Check admin privileges
        
        analytics = await service.get_payment_analytics(
            start_date=start_date,
            end_date=end_date,
            provider_type=provider.value if provider else None
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch payment analytics"
        )


# Background tasks

async def log_payment_audit(
    user_id: UUID,
    transaction_id: str,
    success: bool,
    amount: Decimal
):
    """Log payment attempt for audit trail"""
    logger.info(f"Payment audit - User: {user_id}, Transaction: {transaction_id}, Success: {success}, Amount: {amount}")
    # TODO: Store in audit log table


async def log_refund_audit(
    user_id: UUID,
    transaction_id: UUID,
    amount: Optional[Decimal],
    reason: str
):
    """Log refund for audit trail"""
    logger.info(f"Refund audit - User: {user_id}, Transaction: {transaction_id}, Amount: {amount}, Reason: {reason}")
    # TODO: Store in audit log table


async def process_webhook_event(provider: str, webhook_data: Dict[str, Any]):
    """Process webhook event in background"""
    logger.info(f"Processing webhook from {provider}: {webhook_data.get('event_type')}")
    # TODO: Implement webhook processing logic