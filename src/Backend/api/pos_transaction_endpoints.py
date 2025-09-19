"""
POS Transaction API Endpoints
Uses unified orders system - all POS transactions create orders with order_source='pos'
No separate pos_transactions table needed
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import asyncpg
import os
import json
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pos-transactions"])

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
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


# Pydantic Models for POS
class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None


class POSPaymentDetails(BaseModel):
    cash_amount: Optional[float] = None
    card_amount: Optional[float] = None
    change_given: Optional[float] = None
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None


class POSTransactionCreate(BaseModel):
    store_id: str
    cashier_id: str
    customer_id: Optional[str] = None
    items: List[POSCartItem]
    subtotal: float
    discounts: float
    tax: float
    total: float
    payment_method: str
    payment_details: Optional[POSPaymentDetails] = None
    status: str = 'completed'
    receipt_number: str
    notes: Optional[str] = None



@router.post("/pos/transactions")
async def create_pos_transaction(transaction: POSTransactionCreate):
    """Create a new POS transaction (now creates an order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Parse store_id and customer_id as UUIDs
            store_uuid = None
            try:
                store_uuid = uuid.UUID(transaction.store_id)
            except:
                logger.warning(f"Invalid store UUID: {transaction.store_id}")

            customer_uuid = None
            if transaction.customer_id and transaction.customer_id not in ['anonymous', 'anon']:
                try:
                    customer_uuid = uuid.UUID(transaction.customer_id)
                except:
                    pass

            # Get user_id from customer if exists
            user_id = None
            if customer_uuid:
                user_row = await conn.fetchrow(
                    "SELECT user_id FROM profiles WHERE id = $1",
                    customer_uuid
                )
                if user_row:
                    user_id = user_row['user_id']

            # Prepare items in the format expected by orders table
            order_items = [item.dict() for item in transaction.items]

            # Create order using the unified system
            order_number = transaction.receipt_number or f"POS-{int(datetime.now().timestamp())}"

            query = """
                INSERT INTO orders (
                    order_number,
                    user_id,
                    customer_id,
                    store_id,
                    items,
                    subtotal,
                    tax_amount,
                    discount_amount,
                    total_amount,
                    payment_status,
                    payment_method,
                    payment_details,
                    order_source,
                    order_status,
                    is_pos_transaction,
                    receipt_number,
                    pos_metadata
                ) VALUES (
                    $1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12::jsonb,
                    'pos', $13, TRUE, $14, $15::jsonb
                )
                RETURNING id::text as id, created_at as timestamp
            """

            pos_metadata = {
                'cashier_id': transaction.cashier_id,
                'store_id_text': transaction.store_id,
                'notes': transaction.notes,
                'created_via': 'pos_terminal'
            }

            payment_status = 'paid' if transaction.status == 'completed' else 'pending'

            row = await conn.fetchrow(
                query,
                order_number,  # 1
                user_id,  # 2
                customer_uuid,  # 3
                store_uuid,  # 4
                json.dumps(order_items),  # 5
                Decimal(str(transaction.subtotal)),  # 6
                Decimal(str(transaction.tax)),  # 7
                Decimal(str(transaction.discounts)),  # 8
                Decimal(str(transaction.total)),  # 9
                payment_status,  # 10
                transaction.payment_method,  # 11
                json.dumps(transaction.payment_details.dict() if transaction.payment_details else {}),  # 12
                transaction.status,  # 13
                transaction.receipt_number,  # 14
                json.dumps(pos_metadata)  # 15
            )
            
            result = transaction_data.copy()
            result['id'] = row['id']
            result['timestamp'] = row['timestamp'].isoformat()
            
            # Update customer loyalty points if applicable
            if user_id:
                try:
                    points_earned = int(transaction.total)  # 1 point per dollar
                    await conn.execute(
                        "UPDATE profiles SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE user_id = $2",
                        points_earned,
                        user_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to update loyalty points: {e}")
            
            # Update inventory for each item
            for item in transaction.items:
                product_id = item.product.get('id')
                if product_id:
                    try:
                        await conn.execute(
                            """
                            UPDATE products 
                            SET available_quantity = GREATEST(0, available_quantity - $1)
                            WHERE id = $2::uuid
                            """,
                            item.quantity,
                            product_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update inventory for product {product_id}: {e}")
            
            return result
    except Exception as e:
        logger.error(f"Error creating POS transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pos/transactions")
async def get_pos_transactions(
    store_id: str,
    status: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 100
):
    """Get POS transactions (orders) for a store"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conditions = ["order_source = 'pos'"]
            params = []
            param_num = 1

            # Handle store_id - could be UUID or text stored in metadata
            try:
                store_uuid = uuid.UUID(store_id)
                conditions.append(f"store_id = ${param_num}")
                params.append(store_uuid)
                param_num += 1
            except:
                conditions.append(f"pos_metadata->>'store_id_text' = ${param_num}")
                params.append(store_id)
                param_num += 1

            if status:
                conditions.append(f"order_status = ${param_num}")
                params.append(status)
                param_num += 1

            if date:
                conditions.append(f"DATE(created_at) = ${param_num}")
                params.append(datetime.strptime(date, '%Y-%m-%d').date())
                param_num += 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT
                    id::text as id,
                    order_number,
                    items,
                    subtotal,
                    tax_amount as tax,
                    discount_amount as discounts,
                    total_amount as total,
                    payment_method,
                    payment_details,
                    order_status as status,
                    receipt_number,
                    pos_metadata,
                    created_at as timestamp
                FROM orders
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_num}
            """
            params.append(limit)

            rows = await conn.fetch(query, *params)
            
            transactions = []
            for row in rows:
                pos_metadata = json.loads(row['pos_metadata']) if row['pos_metadata'] else {}
                trans = {
                    'id': row['id'],
                    'store_id': store_id,
                    'cashier_id': pos_metadata.get('cashier_id', 'unknown'),
                    'items': json.loads(row['items']) if row['items'] else [],
                    'subtotal': float(row['subtotal']),
                    'tax': float(row['tax']),
                    'discounts': float(row['discounts']),
                    'total': float(row['total']),
                    'payment_method': row['payment_method'],
                    'payment_details': json.loads(row['payment_details']) if row['payment_details'] else {},
                    'status': row['status'],
                    'receipt_number': row['receipt_number'],
                    'notes': pos_metadata.get('notes'),
                    'timestamp': row['timestamp'].isoformat()
                }
                transactions.append(trans)
            
            return transactions
    except Exception as e:
        logger.error(f"Error getting POS transactions: {str(e)}")
        return []


@router.post("/pos/transactions/park")
async def park_pos_transaction(transaction: POSTransactionCreate):
    """Park a POS transaction for later"""
    transaction.status = 'parked'
    return await create_pos_transaction(transaction)


@router.get("/pos/transactions/parked")
async def get_parked_transactions(store_id: str):
    """Get all parked transactions for a store"""
    return await get_pos_transactions(store_id, status='parked')


@router.put("/pos/transactions/{transaction_id}/resume")
async def resume_pos_transaction(transaction_id: str):
    """Resume a parked transaction (order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT
                    id::text as id,
                    items,
                    subtotal,
                    tax_amount as tax,
                    discount_amount as discounts,
                    total_amount as total,
                    payment_method,
                    payment_details,
                    receipt_number,
                    pos_metadata
                FROM orders
                WHERE id = $1::uuid AND order_status = 'parked' AND order_source = 'pos'
            """

            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Parked transaction not found")

            # Mark as resumed
            await conn.execute(
                "UPDATE orders SET order_status = 'resumed' WHERE id = $1::uuid",
                transaction_id
            )

            pos_metadata = json.loads(row['pos_metadata']) if row['pos_metadata'] else {}
            transaction = {
                'id': transaction_id,
                'store_id': pos_metadata.get('store_id_text'),
                'cashier_id': pos_metadata.get('cashier_id'),
                'items': json.loads(row['items']) if row['items'] else [],
                'subtotal': float(row['subtotal']),
                'tax': float(row['tax']),
                'discounts': float(row['discounts']),
                'total': float(row['total']),
                'payment_method': row['payment_method'],
                'payment_details': json.loads(row['payment_details']) if row['payment_details'] else {},
                'receipt_number': row['receipt_number'],
                'notes': pos_metadata.get('notes')
            }
            return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pos/transactions/{transaction_id}/refund")
async def refund_pos_transaction(transaction_id: str):
    """Process a refund for a POS transaction (order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get original order
            query = """
                SELECT items, total_amount, user_id, customer_id
                FROM orders
                WHERE id = $1::uuid AND order_status = 'completed' AND order_source = 'pos'
            """

            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Transaction not found")

            items = json.loads(row['items']) if row['items'] else []
            total_amount = row['total_amount']
            user_id = row['user_id']

            # Update status to refunded
            await conn.execute(
                "UPDATE orders SET order_status = 'refunded', payment_status = 'refunded', updated_at = NOW() WHERE id = $1::uuid",
                transaction_id
            )
            
            # Restore inventory
            for item in items:
                product_id = item.get('product', {}).get('id')
                if product_id:
                    try:
                        await conn.execute(
                            """
                            UPDATE products
                            SET available_quantity = available_quantity + $1
                            WHERE id = $2::uuid
                            """,
                            item.get('quantity', 0),
                            product_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to restore inventory for product {product_id}: {e}")

            # Deduct loyalty points if applicable
            if user_id:
                try:
                    points_to_deduct = int(total_amount)
                    await conn.execute(
                        "UPDATE profiles SET loyalty_points = GREATEST(0, loyalty_points - $1) WHERE user_id = $2",
                        points_to_deduct,
                        user_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to deduct loyalty points: {e}")
            
            return {"success": True, "message": f"Transaction {transaction_id} refunded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))