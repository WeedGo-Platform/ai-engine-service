"""
Customer Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
import logging
import asyncpg
import os

from services.customer_service import CustomerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/customers", tags=["customers"])

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
class CustomerAddress(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"


class CreateCustomerRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[CustomerAddress] = None
    tags: Optional[List[str]] = []
    notes: Optional[str] = None


class UpdateCustomerRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[CustomerAddress] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateLoyaltyPointsRequest(BaseModel):
    points: int = Field(..., description="Points to add (positive) or remove (negative)")


async def get_customer_service():
    """Get customer service instance"""
    pool = await get_db_pool()
    conn = await pool.acquire()
    try:
        yield CustomerService(conn)
    finally:
        await pool.release(conn)


@router.post("/", response_model=Dict[str, Any])
async def create_customer(
    request: CreateCustomerRequest,
    service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer"""
    try:
        customer_data = request.dict()
        if customer_data.get('address') and hasattr(customer_data['address'], 'dict'):
            customer_data['address'] = customer_data['address'].dict()
        elif customer_data.get('address') and isinstance(customer_data['address'], dict):
            # Address is already a dict, no conversion needed
            pass
        
        customer = await service.create_customer(customer_data)
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_customers(
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: CustomerService = Depends(get_customer_service)
):
    """List customers with optional filters"""
    try:
        customers = await service.list_customers(
            search=search,
            tenant_id=tenant_id,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return customers
    except asyncpg.UndefinedTableError:
        # Table doesn't exist yet - return empty result
        logger.warning("Customers table does not exist yet")
        return []
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        # Check if it's a database connection error
        if "connection" in str(e).lower() or "database" in str(e).lower():
            return []
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}", response_model=Dict[str, Any])
async def get_customer(
    customer_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer by ID"""
    try:
        customer = await service.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}", response_model=Dict[str, Any])
async def update_customer(
    customer_id: UUID,
    request: UpdateCustomerRequest,
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer information"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if update_data.get('address'):
            update_data['address'] = update_data['address'].dict()
        
        success = await service.update_customer(customer_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Return updated customer
        customer = await service.get_customer(customer_id)
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Soft delete a customer"""
    try:
        success = await service.delete_customer(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {"success": True, "message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/orders", response_model=List[Dict[str, Any]])
async def get_customer_orders(
    customer_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Get all orders for a customer"""
    try:
        orders = await service.get_customer_orders(customer_id)
        return orders
    except Exception as e:
        logger.error(f"Error getting customer orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{customer_id}/loyalty", response_model=Dict[str, Any])
async def update_loyalty_points(
    customer_id: UUID,
    request: UpdateLoyaltyPointsRequest,
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer loyalty points"""
    try:
        result = await service.update_loyalty_points(customer_id, request.points)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating loyalty points: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/stats", response_model=Dict[str, Any])
async def get_customer_stats(
    customer_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer statistics and summary"""
    try:
        stats = await service.get_customer_stats(customer_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Customer not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))