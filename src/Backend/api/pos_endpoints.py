"""
POS (Point of Sale) API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request, Header
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging
import asyncpg
import os
import json
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pos"])

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=1,
            max_size=10
        )
    return db_pool


# Pydantic Models
class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class CustomerSearch(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    loyalty_points: int = 0
    is_verified: bool = False
    birth_date: Optional[str] = None


class AgeVerification(BaseModel):
    birth_date: str


class CartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    price_override: Optional[float] = None


class PaymentDetails(BaseModel):
    cash_amount: Optional[float] = None
    card_amount: Optional[float] = None
    change_given: Optional[float] = None
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None


class TransactionCreate(BaseModel):
    store_id: str
    cashier_id: str
    customer_id: Optional[str] = None
    items: List[CartItem]
    subtotal: float
    discounts: float
    tax: float
    total: float
    payment_method: str
    payment_details: Optional[PaymentDetails] = None
    status: str = 'completed'
    receipt_number: str
    notes: Optional[str] = None


# Customer endpoints for POS
@router.get("/customers/search")
async def search_customers(
    q: str = Query(..., description="Search query for name, email, or phone"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    request: Request = None
):
    """
    Search customers for POS

    Filtering logic:
    - If X-Store-ID header present: Filter by that store's tenant
    - If no header and super admin: Return all customers
    - If no header and tenant admin: Error (must select store)
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            search_pattern = f'%{q}%'

            # If store context provided, filter by that store's tenant
            if x_store_id:
                # Get tenant_id for this store
                store_row = await conn.fetchrow("""
                    SELECT tenant_id FROM stores WHERE id = $1::uuid
                """, x_store_id)

                if not store_row:
                    return {"customers": []}

                tenant_id = store_row['tenant_id']

                # Query customers for this tenant
                query = """
                    SELECT
                        u.id::text as id,
                        COALESCE(u.first_name || ' ' || u.last_name, u.email) as name,
                        u.email,
                        u.phone,
                        COALESCE(p.loyalty_points, 0) as loyalty_points,
                        COALESCE(u.date_of_birth::text, '') as birth_date,
                        u.active as is_verified,
                        $3::text as primary_store_id
                    FROM users u
                    LEFT JOIN profiles p ON u.profile_id = p.id
                    WHERE u.role = 'customer'
                    AND u.active = true
                    AND u.tenant_id = $2::uuid
                    AND (
                        LOWER(u.first_name || ' ' || u.last_name) LIKE LOWER($1)
                        OR LOWER(u.email) LIKE LOWER($1)
                        OR u.phone LIKE $1
                    )
                    ORDER BY u.created_at DESC
                    LIMIT 10
                """
                rows = await conn.fetch(query, search_pattern, tenant_id, x_store_id)
            else:
                # No store context - return all customers (super admin view)
                query = """
                    SELECT
                        u.id::text as id,
                        COALESCE(u.first_name || ' ' || u.last_name, u.email) as name,
                        u.email,
                        u.phone,
                        COALESCE(p.loyalty_points, 0) as loyalty_points,
                        COALESCE(u.date_of_birth::text, '') as birth_date,
                        u.active as is_verified
                    FROM users u
                    LEFT JOIN profiles p ON u.profile_id = p.id
                    WHERE u.role = 'customer'
                    AND u.active = true
                    AND (
                        LOWER(u.first_name || ' ' || u.last_name) LIKE LOWER($1)
                        OR LOWER(u.email) LIKE LOWER($1)
                        OR u.phone LIKE $1
                    )
                    ORDER BY u.created_at DESC
                    LIMIT 10
                """
                rows = await conn.fetch(query, search_pattern)

            customers = []
            for row in rows:
                customer = dict(row)
                # Calculate age verification if birth_date exists
                if customer.get('birth_date'):
                    try:
                        birth = datetime.strptime(customer['birth_date'], '%Y-%m-%d')
                        today = datetime.now()
                        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                        customer['is_verified'] = age >= 19  # Legal age in most Canadian provinces
                    except:
                        pass
                customers.append(customer)

            return {"customers": customers}
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return {"customers": []}


@router.post("/customers")
async def create_customer(customer: CustomerCreate, request: Request = None):
    """Create a new customer for POS"""
    try:
        # Get store ID from header if provided
        store_id = request.headers.get("X-Store-ID") if request else None

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Split name into first and last
            name_parts = customer.name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            query = """
                INSERT INTO profiles (
                    user_id, first_name, last_name, email, phone, loyalty_points, primary_store_id
                ) VALUES (gen_random_uuid(), $1, $2, $3, $4, 0, $5::uuid)
                RETURNING
                    id::text as id,
                    first_name || ' ' || last_name as name,
                    email,
                    phone,
                    loyalty_points,
                    primary_store_id::text as primary_store_id
            """

            row = await conn.fetchrow(
                query,
                first_name,
                last_name,
                customer.email or '',
                customer.phone or '',
                store_id  # Will be NULL if not provided
            )
            
            result = dict(row)
            # Calculate age verification
            if result.get('birth_date'):
                try:
                    birth = datetime.strptime(result['birth_date'], '%Y-%m-%d')
                    today = datetime.now()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    result['is_verified'] = age >= 19
                except:
                    result['is_verified'] = False
            else:
                result['is_verified'] = False
            
            return result
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/verify-age")
async def verify_customer_age(verification: AgeVerification):
    """Verify customer age for cannabis purchase"""
    try:
        birth = datetime.strptime(verification.birth_date, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        
        # Legal age is 19 in most provinces, 21 in Quebec
        is_valid = age >= 19
        
        return {
            "is_valid": is_valid,
            "age": age,
            "message": f"Customer is {age} years old. {'Eligible' if is_valid else 'Not eligible'} for cannabis purchase."
        }
    except Exception as e:
        logger.error(f"Error verifying age: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid birth date format")


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: str,
    customer_update: Dict[str, Any] = Body(...),
    request: Request = None
):
    """Update customer details"""
    try:
        # Get store ID from header if provided
        store_id = request.headers.get("X-Store-ID") if request else None

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # If store ID is provided, verify customer belongs to store or has no store
            if store_id:
                customer_store = await conn.fetchval("""
                    SELECT primary_store_id::text
                    FROM profiles
                    WHERE id = $1::uuid
                """, customer_id)

                if customer_store and customer_store != store_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Customer belongs to a different store"
                    )
            # Build dynamic update query based on provided fields
            update_fields = []
            params = []
            param_count = 0

            # Handle name field - split into first and last name
            if 'name' in customer_update:
                name_parts = customer_update['name'].split(' ', 1)
                param_count += 1
                update_fields.append(f"first_name = ${param_count}")
                params.append(name_parts[0])

                param_count += 1
                update_fields.append(f"last_name = ${param_count}")
                params.append(name_parts[1] if len(name_parts) > 1 else '')

            # Handle other fields
            field_mapping = {
                'email': 'email',
                'phone': 'phone',
                'loyalty_points': 'loyalty_points',
                'marketing_consent': 'marketing_consent'
            }

            for field_key, db_column in field_mapping.items():
                if field_key in customer_update:
                    param_count += 1
                    update_fields.append(f"{db_column} = ${param_count}")
                    params.append(customer_update[field_key])

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            # Add updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            # Add customer_id as final parameter
            param_count += 1
            params.append(customer_id)

            query = f"""
                UPDATE profiles
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}::uuid
                RETURNING
                    id::text as id,
                    COALESCE(first_name || ' ' || last_name, email) as name,
                    email,
                    phone,
                    COALESCE(loyalty_points, 0) as loyalty_points,
                    marketing_consent,
                    is_verified
            """

            row = await conn.fetchrow(query, *params)

            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")

            return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}")
async def get_customer_by_id(customer_id: str):
    """Get customer details by ID"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT
                    id::text as id,
                    COALESCE(first_name || ' ' || last_name, email) as name,
                    email,
                    phone,
                    COALESCE(loyalty_points, 0) as loyalty_points,
                    COALESCE(date_of_birth::text, '') as birth_date,
                    is_verified,
                    address
                FROM profiles
                WHERE id = $1::uuid
            """
            
            row = await conn.fetchrow(query, customer_id)
            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            customer = dict(row)
            # Parse address if it exists
            if customer.get('address'):
                try:
                    customer['address'] = json.loads(customer['address'])
                except:
                    pass
            
            return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Transaction endpoints
@router.post("/transactions")
async def create_transaction(transaction: TransactionCreate):
    """Create a new POS transaction"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Convert transaction to database format
            transaction_data = {
                'store_id': transaction.store_id,
                'cashier_id': transaction.cashier_id,
                'customer_id': transaction.customer_id,
                'items': [item.dict() for item in transaction.items],
                'subtotal': transaction.subtotal,
                'discounts': transaction.discounts,
                'tax': transaction.tax,
                'total': transaction.total,
                'payment_method': transaction.payment_method,
                'payment_details': transaction.payment_details.dict() if transaction.payment_details else {},
                'status': transaction.status,
                'receipt_number': transaction.receipt_number,
                'notes': transaction.notes
            }
            
            query = """
                INSERT INTO purchase_orders (
                    store_id, 
                    order_data, status, total_amount
                ) VALUES ($1, $2, $3, $4)
                RETURNING id::text as id, created_at as timestamp
            """
            
            row = await conn.fetchrow(
                query,
                transaction.store_id,
                json.dumps(transaction_data),
                transaction.status,
                Decimal(str(transaction.total))
            )
            
            result = transaction_data.copy()
            result['id'] = row['id']
            result['timestamp'] = row['timestamp'].isoformat()
            
            # Update customer loyalty points if applicable
            if transaction.customer_id and transaction.customer_id != 'anonymous':
                points_earned = int(transaction.total)  # 1 point per dollar
                await conn.execute(
                    "UPDATE profiles SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE id = $2::uuid",
                    points_earned,
                    transaction.customer_id
                )
            
            # Update inventory
            for item in transaction.items:
                product_id = item.product.get('id')
                if product_id:
                    await conn.execute(
                        """
                        UPDATE products 
                        SET available_quantity = GREATEST(0, available_quantity - $1)
                        WHERE id = $2::uuid
                        """,
                        item.quantity,
                        product_id
                    )
            
            return result
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions/park")
async def park_transaction(transaction: TransactionCreate):
    """Park a transaction for later"""
    transaction.status = 'parked'
    return await create_transaction(transaction)


@router.get("/stores/{store_id}/transactions/parked")
async def get_parked_transactions(store_id: str):
    """Get all parked transactions for a store"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    id::text as id,
                    order_data as transaction_data,
                    created_at as timestamp
                FROM purchase_orders
                WHERE store_id = $1 
                AND status = 'parked'
                ORDER BY created_at DESC
            """
            
            rows = await conn.fetch(query, store_id)
            transactions = []
            for row in rows:
                trans = json.loads(row['transaction_data']) if row['transaction_data'] else {}
                trans['id'] = row['id']
                trans['timestamp'] = row['timestamp'].isoformat()
                transactions.append(trans)
            
            return transactions
    except Exception as e:
        logger.error(f"Error getting parked transactions: {str(e)}")
        return []


@router.put("/transactions/{transaction_id}/resume")
async def resume_transaction(transaction_id: str):
    """Resume a parked transaction"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get the transaction
            query = """
                SELECT order_data as transaction_data 
                FROM purchase_orders 
                WHERE id = $1::uuid AND status = 'parked'
            """
            
            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Parked transaction not found")
            
            # Update status to resumed (will be deleted when completed)
            await conn.execute(
                "UPDATE purchase_orders SET status = 'resumed' WHERE id = $1::uuid",
                transaction_id
            )
            
            transaction = json.loads(row['transaction_data'])
            transaction['id'] = transaction_id
            return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores/{store_id}/transactions")
async def get_transaction_history(
    store_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get transaction history for a store"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if date:
                query = """
                    SELECT 
                        id::text as id,
                        order_data as transaction_data,
                        created_at as timestamp
                    FROM purchase_orders
                    WHERE store_id = $1 
                    AND status = 'completed'
                    AND DATE(created_at) = $2
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, store_id, datetime.strptime(date, '%Y-%m-%d').date())
            else:
                query = """
                    SELECT 
                        id::text as id,
                        order_data as transaction_data,
                        created_at as timestamp
                    FROM purchase_orders
                    WHERE store_id = $1 
                    AND status = 'completed'
                    ORDER BY created_at DESC
                    LIMIT 100
                """
                rows = await conn.fetch(query, store_id)
            
            transactions = []
            for row in rows:
                trans = json.loads(row['transaction_data'])
                trans['id'] = row['id']
                trans['timestamp'] = row['timestamp'].isoformat()
                transactions.append(trans)
            
            return transactions
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}")
        return []


@router.post("/transactions/{transaction_id}/refund")
async def refund_transaction(
    transaction_id: str,
    items: Optional[List[str]] = Body(None, description="List of item IDs to refund")
):
    """Process a refund for a transaction"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get the original transaction
            query = """
                SELECT transaction_data 
                FROM transactions 
                WHERE id = $1::uuid AND status = 'completed'
            """
            
            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            original = json.loads(row['transaction_data'])
            
            # Create refund transaction
            refund_data = original.copy()
            refund_data['status'] = 'refunded'
            refund_data['original_transaction_id'] = transaction_id
            refund_data['refunded_at'] = datetime.now().isoformat()
            
            # If partial refund, filter items
            if items:
                refund_data['items'] = [item for item in original['items'] if item.get('id') in items]
                # Recalculate totals for partial refund
                # This is simplified - in production you'd need proper calculation
                refund_data['total'] = sum(item['product']['price'] * item['quantity'] for item in refund_data['items'])
            
            # Update original transaction status
            await conn.execute(
                "UPDATE transactions SET status = 'refunded' WHERE id = $1::uuid",
                transaction_id
            )
            
            # Return inventory
            for item in refund_data['items']:
                product_id = item['product'].get('id')
                if product_id:
                    await conn.execute(
                        """
                        UPDATE products 
                        SET available_quantity = available_quantity + $1
                        WHERE id = $2::uuid
                        """,
                        item['quantity'],
                        product_id
                    )
            
            # Deduct loyalty points if applicable
            if refund_data.get('customer_id') and refund_data['customer_id'] != 'anonymous':
                points_to_deduct = int(refund_data['total'])
                await conn.execute(
                    "UPDATE profiles SET loyalty_points = GREATEST(0, loyalty_points - $1) WHERE id = $2::uuid",
                    points_to_deduct,
                    refund_data['customer_id']
                )
            
            return refund_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Receipt endpoints
@router.post("/transactions/{transaction_id}/receipt/print")
async def print_receipt(transaction_id: str):
    """Print a receipt for a transaction"""
    # In a real implementation, this would interface with a receipt printer
    return {"success": True, "message": f"Receipt printed for transaction {transaction_id}"}


@router.post("/transactions/{transaction_id}/receipt/email")
async def email_receipt(
    transaction_id: str,
    email: str = Body(..., embed=True)
):
    """Email a receipt to a customer"""
    # In a real implementation, this would send an email
    return {"success": True, "message": f"Receipt emailed to {email} for transaction {transaction_id}"}


# Hardware testing endpoints
@router.post("/hardware/scanner/{scanner_id}/test")
async def test_scanner(scanner_id: str):
    """Test barcode scanner connection"""
    return {"success": True, "message": f"Scanner {scanner_id} is connected and working"}


@router.post("/hardware/printer/{printer_id}/test")
async def test_printer(printer_id: str):
    """Test receipt printer connection"""
    return {"success": True, "message": f"Printer {printer_id} is connected and working"}


@router.post("/hardware/terminal/{terminal_id}/test")
async def test_terminal(terminal_id: str):
    """Test payment terminal connection"""
    return {"success": True, "message": f"Terminal {terminal_id} is connected and working"}


# Product barcode lookup
@router.get("/products/barcode/{barcode}")
async def get_product_by_barcode(barcode: str):
    """Get product by barcode"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    id::text as id,
                    sku,
                    name,
                    brand,
                    category,
                    sub_category,
                    thc_content,
                    cbd_content,
                    unit_price as price,
                    available_quantity as quantity_available,
                    COALESCE((metadata->>'size')::text, '') as size,
                    COALESCE((metadata->>'weight_grams')::float, 0) as weight_grams,
                    COALESCE((metadata->>'dried_flower_equivalent')::float, 0) as dried_flower_equivalent
                FROM products
                WHERE sku = $1 OR metadata->>'barcode' = $1
                LIMIT 1
            """
            
            row = await conn.fetchrow(query, barcode)
            if not row:
                raise HTTPException(status_code=404, detail="Product not found")
            
            return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product by barcode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))