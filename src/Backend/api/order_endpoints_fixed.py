"""
Order Management API Endpoints - Fixed Version
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field
import logging
import asyncpg
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])

# Pydantic Models
class DeliveryAddress(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    instructions: Optional[str] = None


class CreateOrderRequest(BaseModel):
    cart_session_id: UUID
    payment_method: str = Field(default="cash", pattern="^(cash|credit|debit|etransfer)$")
    delivery_address: DeliveryAddress
    special_instructions: Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    payment_status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed|cancelled)$")
    delivery_status: Optional[str] = Field(None, pattern="^(pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled)$")
    notes: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: str


async def get_db_connection():
    """Get async database connection"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


@router.get("/")
async def list_orders(
    user_id: Optional[UUID] = Query(None),
    payment_status: Optional[str] = Query(None),
    delivery_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List orders with optional filters"""
    conn = None
    try:
        conn = await get_db_connection()
        if not conn:
            # Return empty list if no connection
            return {"orders": [], "total": 0}
        
        # Check if orders table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            )
        """)
        
        if not table_exists:
            # Return empty list if table doesn't exist
            return {"orders": [], "total": 0}
        
        # Build query
        where_clauses = []
        params = []
        param_count = 1
        
        if user_id:
            where_clauses.append(f"user_id = ${param_count}")
            params.append(user_id)
            param_count += 1
        
        if payment_status:
            where_clauses.append(f"payment_status = ${param_count}")
            params.append(payment_status)
            param_count += 1
        
        if delivery_status:
            where_clauses.append(f"delivery_status = ${param_count}")
            params.append(delivery_status)
            param_count += 1
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM orders{where_clause}"
        total = await conn.fetchval(count_query, *params)
        
        # Get orders
        params.extend([limit, offset])
        query = f"""
            SELECT 
                id, order_number, cart_session_id, user_id,
                total_amount, payment_method, payment_status,
                delivery_status, created_at, updated_at
            FROM orders
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        rows = await conn.fetch(query, *params)
        
        orders = []
        for row in rows:
            order = dict(row)
            # Convert UUID and datetime to strings for JSON serialization
            order['id'] = str(order['id'])
            if order['cart_session_id']:
                order['cart_session_id'] = str(order['cart_session_id'])
            if order['user_id']:
                order['user_id'] = str(order['user_id'])
            if order['created_at']:
                order['created_at'] = order['created_at'].isoformat()
            if order['updated_at']:
                order['updated_at'] = order['updated_at'].isoformat()
            order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
            orders.append(order)
        
        return {"orders": orders, "total": total}
        
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        # Return empty list on error
        return {"orders": [], "total": 0}
    finally:
        if conn:
            await conn.close()


@router.get("/{order_id}")
async def get_order(order_id: UUID):
    """Get order details by ID"""
    conn = None
    try:
        conn = await get_db_connection()
        if not conn:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        query = """
            SELECT * FROM orders WHERE id = $1
        """
        
        row = await conn.fetchrow(query, order_id)
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = dict(row)
        # Convert for JSON serialization
        order['id'] = str(order['id'])
        if order['cart_session_id']:
            order['cart_session_id'] = str(order['cart_session_id'])
        if order['user_id']:
            order['user_id'] = str(order['user_id'])
        if order['created_at']:
            order['created_at'] = order['created_at'].isoformat()
        if order['updated_at']:
            order['updated_at'] = order['updated_at'].isoformat()
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.post("/create")
async def create_order(request: CreateOrderRequest):
    """Create a new order from cart"""
    conn = None
    try:
        conn = await get_db_connection()
        if not conn:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(UUID())[0:8].upper()}"
        
        # Create order (simplified)
        query = """
            INSERT INTO orders (
                order_number, cart_session_id, 
                payment_method, payment_status, delivery_status,
                total_amount, created_at
            ) VALUES ($1, $2, $3, 'pending', 'pending', 0, $4)
            RETURNING id, order_number, created_at
        """
        
        row = await conn.fetchrow(
            query,
            order_number,
            request.cart_session_id,
            request.payment_method,
            datetime.now()
        )
        
        return {
            "success": True,
            "order_id": str(row['id']),
            "order_number": row['order_number'],
            "created_at": row['created_at'].isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/track")
async def track_order(
    order_number: str = Query(..., description="Order number"),
    email: str = Query(..., description="Customer email")
):
    """Track order without authentication"""
    conn = None
    try:
        conn = await get_db_connection()
        if not conn:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Query order by number and email
        query = """
            SELECT 
                o.id,
                o.order_number,
                o.payment_status,
                o.delivery_status,
                o.total_amount,
                o.created_at,
                o.updated_at,
                c.email,
                c.first_name,
                c.last_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.order_number = $1 
            AND (c.email = $2 OR o.customer_email = $2)
        """
        
        row = await conn.fetchrow(query, order_number, email)
        
        if not row:
            raise HTTPException(
                status_code=404, 
                detail="Order not found. Please check your order number and email."
            )
        
        return {
            "id": str(row['id']),
            "order_number": row['order_number'],
            "status": row['delivery_status'],
            "payment_status": row['payment_status'],
            "total": float(row['total_amount']) if row['total_amount'] else 0,
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
            "customer": {
                "email": row['email'],
                "first_name": row['first_name'],
                "last_name": row['last_name']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()