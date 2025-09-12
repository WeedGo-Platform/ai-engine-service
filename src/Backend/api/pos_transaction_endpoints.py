"""
Simplified POS Transaction API Endpoints
Using a dedicated transactions table for POS
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
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
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


async def ensure_pos_transactions_table():
    """Ensure POS transactions table exists"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pos_transactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                store_id TEXT NOT NULL,
                cashier_id TEXT NOT NULL,
                customer_id UUID,
                transaction_data JSONB NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                total_amount DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pos_transactions_store 
            ON pos_transactions(store_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pos_transactions_status 
            ON pos_transactions(status)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pos_transactions_created 
            ON pos_transactions(created_at DESC)
        """)


@router.post("/pos/transactions")
async def create_pos_transaction(transaction: POSTransactionCreate):
    """Create a new POS transaction"""
    try:
        # Ensure table exists
        await ensure_pos_transactions_table()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Prepare transaction data
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
            
            # Parse customer_id if provided
            customer_uuid = None
            if transaction.customer_id and transaction.customer_id != 'anonymous':
                try:
                    customer_uuid = uuid.UUID(transaction.customer_id)
                except:
                    pass
            
            query = """
                INSERT INTO pos_transactions (
                    store_id, cashier_id, customer_id,
                    transaction_data, status, total_amount
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id::text as id, created_at as timestamp
            """
            
            row = await conn.fetchrow(
                query,
                transaction.store_id,
                transaction.cashier_id,
                customer_uuid,
                json.dumps(transaction_data),
                transaction.status,
                Decimal(str(transaction.total))
            )
            
            result = transaction_data.copy()
            result['id'] = row['id']
            result['timestamp'] = row['timestamp'].isoformat()
            
            # Update customer loyalty points if applicable
            if customer_uuid:
                try:
                    points_earned = int(transaction.total)  # 1 point per dollar
                    await conn.execute(
                        "UPDATE customers SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE id = $2",
                        points_earned,
                        customer_uuid
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
    status: Optional[str] = Query(None),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get POS transactions for a store"""
    try:
        await ensure_pos_transactions_table()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conditions = ["store_id = $1"]
            params = [store_id]
            param_num = 2
            
            if status:
                conditions.append(f"status = ${param_num}")
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
                    transaction_data,
                    created_at as timestamp
                FROM pos_transactions
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_num}
            """
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            transactions = []
            for row in rows:
                trans = json.loads(row['transaction_data']) if row['transaction_data'] else {}
                trans['id'] = row['id']
                trans['timestamp'] = row['timestamp'].isoformat()
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
    """Resume a parked transaction"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT transaction_data 
                FROM pos_transactions 
                WHERE id = $1::uuid AND status = 'parked'
            """
            
            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Parked transaction not found")
            
            # Mark as resumed
            await conn.execute(
                "UPDATE pos_transactions SET status = 'resumed' WHERE id = $1::uuid",
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


@router.post("/pos/transactions/{transaction_id}/refund")
async def refund_pos_transaction(transaction_id: str):
    """Process a refund for a POS transaction"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get original transaction
            query = """
                SELECT transaction_data, customer_id
                FROM pos_transactions 
                WHERE id = $1::uuid AND status = 'completed'
            """
            
            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            original = json.loads(row['transaction_data'])
            customer_id = row['customer_id']
            
            # Update status to refunded
            await conn.execute(
                "UPDATE pos_transactions SET status = 'refunded', updated_at = NOW() WHERE id = $1::uuid",
                transaction_id
            )
            
            # Restore inventory
            for item in original.get('items', []):
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
            if customer_id:
                try:
                    points_to_deduct = int(original.get('total', 0))
                    await conn.execute(
                        "UPDATE customers SET loyalty_points = GREATEST(0, loyalty_points - $1) WHERE id = $2",
                        points_to_deduct,
                        customer_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to deduct loyalty points: {e}")
            
            return {"success": True, "message": f"Transaction {transaction_id} refunded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))