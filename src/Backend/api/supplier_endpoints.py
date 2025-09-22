"""
Supplier Management API Endpoints
Provides supplier management functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
import logging
import asyncpg
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])

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


async def get_db_connection():
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection


# Pydantic Models
class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
@router.get("/")
async def get_suppliers(
    search: Optional[str] = Query(None, description="Search in name or contact"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn = Depends(get_db_connection)
):
    """Get list of suppliers with optional filters"""
    try:
        query = """
            SELECT
                ps.id,
                ps.name,
                ps.contact_person,
                ps.email,
                ps.phone,
                ps.address,
                ps.payment_terms,
                ps.is_active,
                ps.provinces_territories_id,
                pt.code as province_code,
                pt.name as province_name,
                ps.is_provincial_supplier,
                ps.created_at,
                ps.updated_at
            FROM provincial_suppliers ps
            LEFT JOIN provinces_territories pt ON ps.provinces_territories_id = pt.id
            WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        if search:
            param_count += 1
            query += f""" AND (
                name ILIKE ${param_count} OR 
                contact_person ILIKE ${param_count} OR
                email ILIKE ${param_count}
            )"""
            params.append(f"%{search}%")
        
        if is_active is not None:
            param_count += 1
            query += f" AND is_active = ${param_count}"
            params.append(is_active)
        
        query += " ORDER BY name"
        
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        rows = await conn.fetch(query, *params)
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM provincial_suppliers WHERE 1=1"
        count_params = []
        count_param_count = 0
        
        if search:
            count_param_count += 1
            count_query += f""" AND (
                name ILIKE ${count_param_count} OR 
                contact_person ILIKE ${count_param_count} OR
                email ILIKE ${count_param_count}
            )"""
            count_params.append(f"%{search}%")
        
        if is_active is not None:
            count_param_count += 1
            count_query += f" AND is_active = ${count_param_count}"
            count_params.append(is_active)
        
        total_count = await conn.fetchval(count_query, *count_params)
        
        suppliers = [dict(row) for row in rows]
        
        return {
            "suppliers": suppliers,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "page": (offset // limit) + 1,
            "total_pages": ((total_count - 1) // limit) + 1 if total_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-province/{province_code}")
async def get_supplier_by_province(
    province_code: str,
    conn = Depends(get_db_connection)
):
    """Get provincial supplier for a specific province"""
    try:
        query = """
            SELECT
                ps.id,
                ps.name,
                ps.contact_person,
                ps.email,
                ps.phone,
                ps.address,
                ps.payment_terms,
                ps.is_active,
                ps.provinces_territories_id,
                pt.code as province_code,
                pt.name as province_name,
                ps.is_provincial_supplier,
                ps.created_at,
                ps.updated_at
            FROM provincial_suppliers ps
            INNER JOIN provinces_territories pt ON ps.provinces_territories_id = pt.id
            WHERE pt.code = $1
            AND ps.is_provincial_supplier = true
            AND ps.is_active = true
        """

        row = await conn.fetchrow(query, province_code.upper())

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No provincial supplier found for province {province_code}"
            )

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier by province: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-province-territory-id/{province_territory_id}")
async def get_supplier_by_province_territory_id(
    province_territory_id: UUID,
    conn = Depends(get_db_connection)
):
    """Get provincial supplier for a specific province/territory by ID"""
    try:
        query = """
            SELECT
                ps.id,
                ps.name,
                ps.contact_person,
                ps.email,
                ps.phone,
                ps.address,
                ps.payment_terms,
                ps.is_active,
                ps.provinces_territories_id,
                pt.code as province_code,
                pt.name as province_name,
                ps.is_provincial_supplier,
                ps.created_at,
                ps.updated_at
            FROM provincial_suppliers ps
            INNER JOIN provinces_territories pt ON ps.provinces_territories_id = pt.id
            WHERE ps.provinces_territories_id = $1
            AND ps.is_provincial_supplier = true
            AND ps.is_active = true
        """

        row = await conn.fetchrow(query, province_territory_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No provincial supplier found for province/territory ID {province_territory_id}"
            )

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier by province territory ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{supplier_id}")
async def get_supplier_by_id(
    supplier_id: UUID,
    conn = Depends(get_db_connection)
):
    """Get supplier by ID"""
    try:
        query = """
            SELECT
                ps.id,
                ps.name,
                ps.contact_person,
                ps.email,
                ps.phone,
                ps.address,
                ps.payment_terms,
                ps.is_active,
                ps.provinces_territories_id,
                pt.code as province_code,
                pt.name as province_name,
                ps.is_provincial_supplier,
                ps.created_at,
                ps.updated_at
            FROM provincial_suppliers ps
            LEFT JOIN provinces_territories pt ON ps.provinces_territories_id = pt.id
            WHERE ps.id = $1
        """
        
        row = await conn.fetchrow(query, supplier_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return dict(row)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@router.post("/")
async def create_supplier(
    supplier: SupplierCreate,
    conn = Depends(get_db_connection)
):
    """Create a new supplier"""
    try:
        query = """
            INSERT INTO provincial_suppliers (
                name, contact_person, email, phone,
                address, payment_terms
            ) VALUES (
                $1, $2, $3, $4, $5, $6
            )
            RETURNING id, created_at
        """
        
        result = await conn.fetchrow(
            query,
            supplier.name,
            supplier.contact_person,
            supplier.email,
            supplier.phone,
            supplier.address,
            supplier.payment_terms
        )
        
        return {
            "id": str(result['id']),
            "message": "Supplier created successfully",
            "created_at": result['created_at']
        }
        
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: UUID,
    supplier: SupplierUpdate,
    conn = Depends(get_db_connection)
):
    """Update supplier information"""
    try:
        # Build dynamic update query
        update_fields = []
        params = []
        param_count = 0
        
        if supplier.name is not None:
            param_count += 1
            update_fields.append(f"name = ${param_count}")
            params.append(supplier.name)
        
        if supplier.contact_person is not None:
            param_count += 1
            update_fields.append(f"contact_person = ${param_count}")
            params.append(supplier.contact_person)
        
        if supplier.email is not None:
            param_count += 1
            update_fields.append(f"email = ${param_count}")
            params.append(supplier.email)
        
        if supplier.phone is not None:
            param_count += 1
            update_fields.append(f"phone = ${param_count}")
            params.append(supplier.phone)
        
        if supplier.address is not None:
            param_count += 1
            update_fields.append(f"address = ${param_count}")
            params.append(supplier.address)
        
        if supplier.payment_terms is not None:
            param_count += 1
            update_fields.append(f"payment_terms = ${param_count}")
            params.append(supplier.payment_terms)
        
        if supplier.is_active is not None:
            param_count += 1
            update_fields.append(f"is_active = ${param_count}")
            params.append(supplier.is_active)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        
        param_count += 1
        params.append(supplier_id)
        
        query = f"""
            UPDATE provincial_suppliers
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING id, updated_at
        """
        
        result = await conn.fetchrow(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {
            "id": str(result['id']),
            "message": "Supplier updated successfully",
            "updated_at": result['updated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: UUID,
    conn = Depends(get_db_connection)
):
    """Delete a supplier (soft delete by setting is_active to false)"""
    try:
        query = """
            UPDATE provincial_suppliers
            SET is_active = false, updated_at = $1
            WHERE id = $2
            RETURNING id
        """
        
        result = await conn.fetchrow(query, datetime.utcnow(), supplier_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {
            "id": str(result['id']),
            "message": "Supplier deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))