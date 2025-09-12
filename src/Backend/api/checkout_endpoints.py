"""
Checkout Flow API Endpoints
Handles the complete checkout process including session management,
tax calculation, delivery fees, discounts, and payment processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg
import uuid
import json
from enum import Enum

# Initialize router
router = APIRouter(prefix="/api/checkout", tags=["checkout"])

# Database connection
from database.connection import get_db_pool

# Auth dependencies
from .customer_auth import get_current_user, get_optional_user

# Payment service
from services.payments.payment_service_v2 import PaymentServiceV2

# Enums
class FulfillmentType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"
    SHIPPING = "shipping"

class CheckoutStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"

# Request/Response Models
class DeliveryAddress(BaseModel):
    street_address: str
    unit_number: Optional[str] = None
    city: str
    province_state: str
    postal_code: str
    country: str = "CA"
    delivery_instructions: Optional[str] = None

class CheckoutInitRequest(BaseModel):
    cart_session_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: str
    store_id: str
    fulfillment_type: FulfillmentType = FulfillmentType.DELIVERY

class GuestInfo(BaseModel):
    email: EmailStr
    phone: str
    first_name: str
    last_name: str
    
    @validator('phone')
    def validate_phone(cls, v):
        # Basic phone validation
        clean_phone = ''.join(filter(str.isdigit, v))
        if len(clean_phone) < 10:
            raise ValueError('Invalid phone number')
        return v

class UpdateCheckoutRequest(BaseModel):
    guest_info: Optional[GuestInfo] = None
    delivery_address: Optional[DeliveryAddress] = None
    pickup_store_id: Optional[str] = None
    pickup_datetime: Optional[datetime] = None
    delivery_datetime: Optional[datetime] = None
    delivery_instructions: Optional[str] = None
    tip_amount: Optional[Decimal] = Field(default=0, ge=0)

class ApplyDiscountRequest(BaseModel):
    code: str

class CompleteCheckoutRequest(BaseModel):
    payment_method: str
    payment_intent_id: Optional[str] = None
    age_verified: bool = False
    age_verification_method: Optional[str] = None
    id_verification_token: Optional[str] = None
    medical_card_number: Optional[str] = None

class CheckoutSessionResponse(BaseModel):
    id: str
    session_id: str
    status: CheckoutStatus
    fulfillment_type: FulfillmentType
    
    # Pricing
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    service_fee: Decimal
    tip_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    
    # Applied discounts
    coupon_code: Optional[str] = None
    discount_details: Optional[Dict] = None
    
    # Customer info
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Delivery/pickup info
    delivery_address: Optional[Dict] = None
    pickup_store: Optional[Dict] = None
    pickup_datetime: Optional[datetime] = None
    delivery_datetime: Optional[datetime] = None
    
    # Cart items
    items: List[Dict] = []
    
    # Compliance
    age_verified: bool = False
    medical_card_verified: bool = False
    
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

# Helper Functions
async def calculate_taxes(
    db_pool: asyncpg.Pool,
    province_id: str,
    subtotal: Decimal
) -> Dict[str, Decimal]:
    """Calculate taxes based on province"""
    async with db_pool.acquire() as conn:
        # Get tax rates for province
        tax_rates = await conn.fetchrow("""
            SELECT 
                COALESCE(federal_tax_rate, 0.05) as federal_rate,
                COALESCE(provincial_tax_rate, 0.08) as provincial_rate,
                COALESCE(cannabis_excise_duty, 0.10) as excise_rate,
                excise_calculation_method
            FROM tax_rates
            WHERE province_territory_id = $1
                AND is_active = TRUE
                AND CURRENT_DATE BETWEEN effective_from 
                AND COALESCE(effective_to, CURRENT_DATE + INTERVAL '1 day')
            ORDER BY created_at DESC
            LIMIT 1
        """, uuid.UUID(province_id) if province_id else None)
        
        if not tax_rates:
            # Default rates if not configured
            federal_tax = float(subtotal) * 0.05
            provincial_tax = float(subtotal) * 0.08
            excise_duty = float(subtotal) * 0.10
        else:
            federal_tax = float(subtotal) * float(tax_rates['federal_rate'])
            provincial_tax = float(subtotal) * float(tax_rates['provincial_rate'])
            
            if tax_rates['excise_calculation_method'] == 'percentage':
                excise_duty = float(subtotal) * float(tax_rates['excise_rate'])
            else:
                # Would need weight-based calculation
                excise_duty = float(tax_rates['excise_rate'])
        
        return {
            'federal_tax': Decimal(str(round(federal_tax, 2))),
            'provincial_tax': Decimal(str(round(provincial_tax, 2))),
            'excise_duty': Decimal(str(round(excise_duty, 2))),
            'total_tax': Decimal(str(round(federal_tax + provincial_tax + excise_duty, 2)))
        }

async def calculate_delivery_fee(
    db_pool: asyncpg.Pool,
    store_id: str,
    delivery_address: Dict,
    subtotal: Decimal
) -> Decimal:
    """Calculate delivery fee based on zone and order amount"""
    async with db_pool.acquire() as conn:
        # Simple delivery fee calculation
        # In production, would check delivery zones and postal codes
        base_fee = Decimal("5.00")
        
        # Free delivery for orders over $50
        if subtotal >= Decimal("50.00"):
            return Decimal("0.00")
        
        return base_fee

async def reserve_inventory(
    db_pool: asyncpg.Pool,
    checkout_session_id: str,
    items: List[Dict],
    duration_minutes: int = 30
) -> bool:
    """Reserve inventory for checkout session"""
    async with db_pool.acquire() as conn:
        try:
            async with conn.transaction():
                reserved_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
                
                for item in items:
                    # Check available inventory
                    available = await conn.fetchval("""
                        SELECT quantity_on_hand - COALESCE(
                            (SELECT SUM(quantity) 
                             FROM inventory_reservations 
                             WHERE product_id = $1 
                               AND released = FALSE 
                               AND reserved_until > CURRENT_TIMESTAMP), 0
                        ) as available
                        FROM products
                        WHERE id = $1
                    """, uuid.UUID(item['product_id']))
                    
                    if available is None or available < item['quantity']:
                        raise Exception(f"Insufficient inventory for product {item['product_id']}")
                    
                    # Create reservation
                    await conn.execute("""
                        INSERT INTO inventory_reservations (
                            checkout_session_id, product_id, quantity, reserved_until
                        ) VALUES ($1, $2, $3, $4)
                    """, uuid.UUID(checkout_session_id), 
                        uuid.UUID(item['product_id']), 
                        item['quantity'], 
                        reserved_until)
            
            return True
        except Exception as e:
            print(f"Inventory reservation failed: {e}")
            return False

async def release_inventory(
    db_pool: asyncpg.Pool,
    checkout_session_id: str
):
    """Release inventory reservations"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE inventory_reservations
            SET released = TRUE
            WHERE checkout_session_id = $1 AND released = FALSE
        """, uuid.UUID(checkout_session_id))

# API Endpoints

@router.post("/initiate", response_model=CheckoutSessionResponse)
async def initiate_checkout(
    request: CheckoutInitRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_optional_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Initialize a new checkout session"""
    
    async with db_pool.acquire() as conn:
        # Get cart session
        cart = None
        if request.cart_session_id:
            cart = await conn.fetchrow("""
                SELECT * FROM cart_sessions
                WHERE id = $1 OR session_id = $1
            """, request.cart_session_id)
        elif request.session_id:
            cart = await conn.fetchrow("""
                SELECT * FROM cart_sessions
                WHERE session_id = $1
            """, request.session_id)
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        if not cart['items'] or len(json.loads(cart['items'])) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Create checkout session
        checkout_id = uuid.uuid4()
        session_id = f"checkout_{checkout_id.hex[:8]}_{uuid.uuid4().hex[:8]}"
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # Get store info for tax calculation
        store = await conn.fetchrow("""
            SELECT province_territory_id 
            FROM stores 
            WHERE id = $1
        """, uuid.UUID(request.store_id))
        
        # Calculate initial taxes
        tax_info = await calculate_taxes(
            db_pool,
            str(store['province_territory_id']) if store else None,
            cart['subtotal']
        )
        
        # Create checkout session
        checkout = await conn.fetchrow("""
            INSERT INTO checkout_sessions (
                id, session_id, cart_session_id, user_id, 
                tenant_id, store_id, fulfillment_type,
                subtotal, tax_amount, total_amount,
                status, expires_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            ) RETURNING *
        """, checkout_id, session_id, cart['id'],
            uuid.UUID(current_user['id']) if current_user else None,
            uuid.UUID(request.tenant_id), uuid.UUID(request.store_id),
            request.fulfillment_type.value,
            cart['subtotal'], tax_info['total_tax'],
            cart['subtotal'] + tax_info['total_tax'],
            CheckoutStatus.DRAFT.value, expires_at)
        
        # Reserve inventory in background
        items = json.loads(cart['items'])
        background_tasks.add_task(
            reserve_inventory,
            db_pool,
            str(checkout_id),
            items
        )
        
        return CheckoutSessionResponse(
            id=str(checkout['id']),
            session_id=checkout['session_id'],
            status=checkout['status'],
            fulfillment_type=checkout['fulfillment_type'],
            subtotal=checkout['subtotal'],
            tax_amount=checkout['tax_amount'],
            delivery_fee=checkout['delivery_fee'],
            service_fee=checkout['service_fee'],
            tip_amount=checkout['tip_amount'],
            discount_amount=checkout['discount_amount'],
            total_amount=checkout['total_amount'],
            items=items,
            expires_at=checkout['expires_at'],
            created_at=checkout['created_at'],
            updated_at=checkout['updated_at']
        )

@router.get("/session/{session_id}", response_model=CheckoutSessionResponse)
async def get_checkout_session(
    session_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get checkout session details"""
    
    async with db_pool.acquire() as conn:
        checkout = await conn.fetchrow("""
            SELECT c.*, cs.items
            FROM checkout_sessions c
            LEFT JOIN cart_sessions cs ON c.cart_session_id = cs.id
            WHERE c.session_id = $1 OR c.id::text = $1
        """, session_id)
        
        if not checkout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session not found"
            )
        
        # Check if expired
        if checkout['status'] == 'draft' and checkout['expires_at'] < datetime.utcnow():
            # Mark as expired
            await conn.execute("""
                UPDATE checkout_sessions
                SET status = 'expired'
                WHERE id = $1
            """, checkout['id'])
            
            # Release inventory
            await release_inventory(db_pool, str(checkout['id']))
            
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Checkout session has expired"
            )
        
        # Get pickup store info if applicable
        pickup_store = None
        if checkout['pickup_store_id']:
            pickup_store = await conn.fetchrow("""
                SELECT id, name, address, phone
                FROM stores
                WHERE id = $1
            """, checkout['pickup_store_id'])
            if pickup_store:
                pickup_store = dict(pickup_store)
                pickup_store['id'] = str(pickup_store['id'])
        
        return CheckoutSessionResponse(
            id=str(checkout['id']),
            session_id=checkout['session_id'],
            status=checkout['status'],
            fulfillment_type=checkout['fulfillment_type'],
            subtotal=checkout['subtotal'],
            tax_amount=checkout['tax_amount'],
            delivery_fee=checkout['delivery_fee'],
            service_fee=checkout['service_fee'],
            tip_amount=checkout['tip_amount'],
            discount_amount=checkout['discount_amount'],
            total_amount=checkout['total_amount'],
            coupon_code=checkout['coupon_code'],
            customer_email=checkout['customer_email'],
            customer_phone=checkout['customer_phone'],
            delivery_address=json.loads(checkout['delivery_address']) if checkout['delivery_address'] else None,
            pickup_store=pickup_store,
            pickup_datetime=checkout['pickup_datetime'],
            delivery_datetime=checkout['delivery_datetime'],
            items=json.loads(checkout['items']) if checkout['items'] else [],
            age_verified=checkout['age_verified'],
            medical_card_verified=checkout['medical_card_verified'],
            expires_at=checkout['expires_at'],
            created_at=checkout['created_at'],
            updated_at=checkout['updated_at']
        )

@router.put("/session/{session_id}", response_model=CheckoutSessionResponse)
async def update_checkout_session(
    session_id: str,
    request: UpdateCheckoutRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update checkout session with customer info and delivery details"""
    
    async with db_pool.acquire() as conn:
        # Get current session
        checkout = await conn.fetchrow("""
            SELECT * FROM checkout_sessions
            WHERE session_id = $1 AND status = 'draft'
        """, session_id)
        
        if not checkout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session not found or not editable"
            )
        
        # Build update query
        updates = []
        params = [session_id]
        param_count = 1
        
        if request.guest_info:
            param_count += 4
            updates.extend([
                f"customer_email = ${param_count - 3}",
                f"customer_phone = ${param_count - 2}",
                f"customer_first_name = ${param_count - 1}",
                f"customer_last_name = ${param_count}"
            ])
            params.extend([
                request.guest_info.email,
                request.guest_info.phone,
                request.guest_info.first_name,
                request.guest_info.last_name
            ])
        
        if request.delivery_address:
            param_count += 1
            updates.append(f"delivery_address = ${param_count}::jsonb")
            params.append(json.dumps(request.delivery_address.dict()))
            
            # Calculate delivery fee
            delivery_fee = await calculate_delivery_fee(
                db_pool,
                str(checkout['store_id']),
                request.delivery_address.dict(),
                checkout['subtotal']
            )
            param_count += 1
            updates.append(f"delivery_fee = ${param_count}")
            params.append(delivery_fee)
        
        if request.pickup_store_id:
            param_count += 1
            updates.append(f"pickup_store_id = ${param_count}")
            params.append(uuid.UUID(request.pickup_store_id))
            updates.append("delivery_fee = 0")  # No delivery fee for pickup
        
        if request.pickup_datetime:
            param_count += 1
            updates.append(f"pickup_datetime = ${param_count}")
            params.append(request.pickup_datetime)
        
        if request.delivery_datetime:
            param_count += 1
            updates.append(f"delivery_datetime = ${param_count}")
            params.append(request.delivery_datetime)
        
        if request.delivery_instructions is not None:
            param_count += 1
            updates.append(f"delivery_instructions = ${param_count}")
            params.append(request.delivery_instructions)
        
        if request.tip_amount is not None:
            param_count += 1
            updates.append(f"tip_amount = ${param_count}")
            params.append(request.tip_amount)
        
        if updates:
            # Recalculate total
            updates.append("""
                total_amount = subtotal + tax_amount + delivery_fee + 
                               service_fee + tip_amount - discount_amount
            """)
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE checkout_sessions
                SET {', '.join(updates)}
                WHERE session_id = $1
                RETURNING *
            """
            
            checkout = await conn.fetchrow(query, *params)
        
        # Get cart items
        cart = await conn.fetchrow("""
            SELECT items FROM cart_sessions
            WHERE id = $1
        """, checkout['cart_session_id'])
        
        return CheckoutSessionResponse(
            id=str(checkout['id']),
            session_id=checkout['session_id'],
            status=checkout['status'],
            fulfillment_type=checkout['fulfillment_type'],
            subtotal=checkout['subtotal'],
            tax_amount=checkout['tax_amount'],
            delivery_fee=checkout['delivery_fee'],
            service_fee=checkout['service_fee'],
            tip_amount=checkout['tip_amount'],
            discount_amount=checkout['discount_amount'],
            total_amount=checkout['total_amount'],
            customer_email=checkout['customer_email'],
            customer_phone=checkout['customer_phone'],
            delivery_address=json.loads(checkout['delivery_address']) if checkout['delivery_address'] else None,
            pickup_datetime=checkout['pickup_datetime'],
            delivery_datetime=checkout['delivery_datetime'],
            items=json.loads(cart['items']) if cart and cart['items'] else [],
            expires_at=checkout['expires_at'],
            created_at=checkout['created_at'],
            updated_at=checkout['updated_at']
        )

@router.post("/session/{session_id}/apply-discount")
async def apply_discount_code(
    session_id: str,
    request: ApplyDiscountRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Apply a discount code to checkout session"""
    
    async with db_pool.acquire() as conn:
        # Get checkout session
        checkout = await conn.fetchrow("""
            SELECT * FROM checkout_sessions
            WHERE session_id = $1 AND status = 'draft'
        """, session_id)
        
        if not checkout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session not found"
            )
        
        # Check discount code
        discount = await conn.fetchrow("""
            SELECT dc.*, p.discount_type, p.discount_value
            FROM discount_codes dc
            LEFT JOIN promotions p ON dc.promotion_id = p.id
            WHERE UPPER(dc.code) = UPPER($1)
                AND (dc.tenant_id = $2 OR dc.tenant_id IS NULL)
                AND dc.used = FALSE
                AND CURRENT_TIMESTAMP BETWEEN dc.valid_from 
                AND COALESCE(dc.valid_until, CURRENT_TIMESTAMP + INTERVAL '1 day')
        """, request.code, checkout['tenant_id'])
        
        if not discount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired discount code"
            )
        
        # Calculate discount amount
        discount_amount = Decimal("0")
        if discount['discount_type'] == 'percentage':
            discount_amount = checkout['subtotal'] * (discount['discount_value'] / 100)
        elif discount['discount_type'] == 'fixed':
            discount_amount = min(discount['discount_value'], checkout['subtotal'])
        elif discount['discount_type'] == 'free_delivery':
            discount_amount = checkout['delivery_fee']
        
        # Update checkout session
        await conn.execute("""
            UPDATE checkout_sessions
            SET coupon_code = $1,
                discount_id = $2,
                discount_amount = $3,
                total_amount = subtotal + tax_amount + delivery_fee + 
                              service_fee + tip_amount - $3,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $4
        """, request.code, discount['id'], discount_amount, checkout['id'])
        
        return {
            "success": True,
            "discount_amount": float(discount_amount),
            "message": f"Discount applied: {discount['discount_type']}"
        }

@router.post("/session/{session_id}/calculate-taxes")
async def recalculate_taxes(
    session_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Recalculate taxes for checkout session"""
    
    async with db_pool.acquire() as conn:
        checkout = await conn.fetchrow("""
            SELECT * FROM checkout_sessions
            WHERE session_id = $1
        """, session_id)
        
        if not checkout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session not found"
            )
        
        # Determine province for tax calculation
        province_id = None
        if checkout['pickup_store_id']:
            store = await conn.fetchrow("""
                SELECT province_territory_id 
                FROM stores 
                WHERE id = $1
            """, checkout['pickup_store_id'])
            province_id = str(store['province_territory_id']) if store else None
        elif checkout['delivery_address']:
            # Could look up province from address
            pass
        else:
            store = await conn.fetchrow("""
                SELECT province_territory_id 
                FROM stores 
                WHERE id = $1
            """, checkout['store_id'])
            province_id = str(store['province_territory_id']) if store else None
        
        # Calculate taxes
        tax_info = await calculate_taxes(db_pool, province_id, checkout['subtotal'])
        
        # Update checkout
        await conn.execute("""
            UPDATE checkout_sessions
            SET tax_amount = $1,
                total_amount = subtotal + $1 + delivery_fee + 
                              service_fee + tip_amount - discount_amount,
                metadata = metadata || $2::jsonb,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $3
        """, tax_info['total_tax'], 
            json.dumps({'tax_breakdown': {
                'federal_tax': float(tax_info['federal_tax']),
                'provincial_tax': float(tax_info['provincial_tax']),
                'excise_duty': float(tax_info['excise_duty'])
            }}),
            checkout['id'])
        
        return {
            "success": True,
            "tax_breakdown": tax_info,
            "total_tax": float(tax_info['total_tax'])
        }

@router.post("/session/{session_id}/complete")
async def complete_checkout(
    session_id: str,
    request: CompleteCheckoutRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_optional_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Complete checkout and create order"""
    
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Get checkout session with lock
            checkout = await conn.fetchrow("""
                SELECT * FROM checkout_sessions
                WHERE session_id = $1 AND status = 'draft'
                FOR UPDATE
            """, session_id)
            
            if not checkout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Checkout session not found or already completed"
                )
            
            # Validate required fields
            if checkout['fulfillment_type'] == 'delivery' and not checkout['delivery_address']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Delivery address is required"
                )
            
            if checkout['fulfillment_type'] == 'pickup' and not checkout['pickup_store_id']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pickup store is required"
                )
            
            if not checkout['customer_email'] and not current_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer email is required"
                )
            
            # Verify age and compliance
            if not request.age_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Age verification is required"
                )
            
            # Update checkout with compliance info
            await conn.execute("""
                UPDATE checkout_sessions
                SET age_verified = $1,
                    age_verification_method = $2,
                    id_verification_token = $3,
                    medical_card_verified = $4,
                    medical_card_number = $5,
                    payment_method = $6,
                    payment_intent_id = $7,
                    status = 'processing',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $8
            """, request.age_verified, request.age_verification_method,
                request.id_verification_token, 
                request.medical_card_number is not None,
                request.medical_card_number,
                request.payment_method, request.payment_intent_id,
                checkout['id'])
            
            # Process payment
            try:
                payment_service = PaymentServiceV2(db_pool)
                
                # Create payment request
                payment_result = await payment_service.process_payment(
                    tenant_id=str(checkout['tenant_id']),
                    amount=float(checkout['total_amount']),
                    currency="CAD",
                    payment_method=request.payment_method,
                    metadata={
                        'checkout_session_id': str(checkout['id']),
                        'order_type': checkout['fulfillment_type']
                    }
                )
                
                if not payment_result['success']:
                    raise Exception(payment_result.get('error', 'Payment failed'))
                
                # Update checkout with payment success
                await conn.execute("""
                    UPDATE checkout_sessions
                    SET payment_status = 'completed',
                        status = 'completed',
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, checkout['id'])
                
            except Exception as e:
                # Payment failed
                await conn.execute("""
                    UPDATE checkout_sessions
                    SET payment_status = 'failed',
                        status = 'failed',
                        metadata = metadata || $1::jsonb
                    WHERE id = $2
                """, json.dumps({'payment_error': str(e)}), checkout['id'])
                
                # Release inventory
                await release_inventory(db_pool, str(checkout['id']))
                
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Payment failed: {str(e)}"
                )
            
            # Create order from checkout
            order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Get cart items
            cart = await conn.fetchrow("""
                SELECT items FROM cart_sessions
                WHERE id = $1
            """, checkout['cart_session_id'])
            
            order = await conn.fetchrow("""
                INSERT INTO orders (
                    order_number, user_id, cart_session_id,
                    subtotal, tax_amount, delivery_fee, tip_amount,
                    discount_amount, total_amount,
                    delivery_address, delivery_instructions,
                    status, payment_status, payment_method,
                    tenant_id, store_id, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    'pending', 'paid', $12, $13, $14, CURRENT_TIMESTAMP
                ) RETURNING id
            """, order_number, 
                checkout['user_id'] or current_user['id'] if current_user else None,
                checkout['cart_session_id'],
                checkout['subtotal'], checkout['tax_amount'],
                checkout['delivery_fee'], checkout['tip_amount'],
                checkout['discount_amount'], checkout['total_amount'],
                checkout['delivery_address'], checkout['delivery_instructions'],
                checkout['payment_method'], checkout['tenant_id'], checkout['store_id'])
            
            # Mark discount code as used if applicable
            if checkout['discount_id']:
                await conn.execute("""
                    UPDATE discount_codes
                    SET used = TRUE,
                        used_at = CURRENT_TIMESTAMP,
                        order_id = $1
                    WHERE id = $2
                """, order['id'], checkout['discount_id'])
                
                # Track discount usage
                await conn.execute("""
                    INSERT INTO discount_usage (
                        discount_code_id, user_id, order_id, 
                        checkout_session_id, discount_amount
                    ) VALUES ($1, $2, $3, $4, $5)
                """, checkout['discount_id'], checkout['user_id'],
                    order['id'], checkout['id'], checkout['discount_amount'])
            
            # Clear cart
            await conn.execute("""
                UPDATE cart_sessions
                SET status = 'completed'
                WHERE id = $1
            """, checkout['cart_session_id'])
            
            # TODO: Send order confirmation email in background
            # background_tasks.add_task(send_order_confirmation, ...)
            
            return {
                "success": True,
                "order_id": str(order['id']),
                "order_number": order_number,
                "message": "Order placed successfully"
            }

@router.delete("/session/{session_id}")
async def cancel_checkout(
    session_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Cancel checkout session and release inventory"""
    
    async with db_pool.acquire() as conn:
        checkout = await conn.fetchrow("""
            UPDATE checkout_sessions
            SET status = 'abandoned',
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $1 AND status = 'draft'
            RETURNING id
        """, session_id)
        
        if not checkout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session not found or already completed"
            )
        
        # Release inventory reservations
        await release_inventory(db_pool, str(checkout['id']))
        
        return {"success": True, "message": "Checkout cancelled"}

# Cleanup expired sessions (should be run periodically)
@router.post("/cleanup-expired")
async def cleanup_expired_sessions(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Clean up expired checkout sessions"""
    
    async with db_pool.acquire() as conn:
        # Get expired sessions
        expired = await conn.fetch("""
            UPDATE checkout_sessions
            SET status = 'expired'
            WHERE status = 'draft' 
                AND expires_at < CURRENT_TIMESTAMP
            RETURNING id
        """)
        
        # Release inventory for each expired session
        for session in expired:
            await release_inventory(db_pool, str(session['id']))
        
        return {
            "success": True,
            "expired_count": len(expired),
            "message": f"Cleaned up {len(expired)} expired sessions"
        }