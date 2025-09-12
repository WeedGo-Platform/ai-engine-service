"""
Store Repository Implementation
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg
import logging
import json

from core.domain.models import (
    Store, StoreStatus, Address, GeoLocation
)
from core.repositories.interfaces import IStoreRepository

logger = logging.getLogger(__name__)


class StoreRepository(IStoreRepository):
    """PostgreSQL implementation of Store repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
    
    async def create(self, store: Store) -> Store:
        """Create a new store"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO stores (
                        id, tenant_id, province_territory_id, store_code, name,
                        address, phone, email, hours, timezone,
                        license_number, license_expiry, tax_rate, delivery_radius_km,
                        delivery_enabled, pickup_enabled, kiosk_enabled, pos_enabled,
                        ecommerce_enabled, status, settings, pos_integration,
                        seo_config, latitude, longitude, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, $25, $26, $27
                    )
                    RETURNING *
                """
                
                address_json = store.address.to_dict() if store.address else None
                latitude = float(store.location.latitude) if store.location else None
                longitude = float(store.location.longitude) if store.location else None
                
                row = await conn.fetchrow(
                    query,
                    store.id,
                    store.tenant_id,
                    store.province_territory_id,
                    store.store_code,
                    store.name,
                    json.dumps(address_json) if address_json else None,
                    store.phone,
                    store.email,
                    json.dumps(store.hours),
                    store.timezone,
                    store.license_number,
                    store.license_expiry,
                    store.tax_rate,
                    store.delivery_radius_km,
                    store.delivery_enabled,
                    store.pickup_enabled,
                    store.kiosk_enabled,
                    store.pos_enabled,
                    store.ecommerce_enabled,
                    store.status.value,
                    json.dumps(store.settings),
                    json.dumps(store.pos_integration),
                    json.dumps(store.seo_config),
                    latitude,
                    longitude,
                    store.created_at,
                    store.updated_at
                )
                
                return self._row_to_store(row)
                
            except asyncpg.UniqueViolationError as e:
                logger.error(f"Store with code {store.store_code} already exists for tenant: {e}")
                raise ValueError(f"Store with code {store.store_code} already exists")
            except Exception as e:
                logger.error(f"Error creating store: {e}")
                raise
    
    async def get_by_id(self, store_id: UUID) -> Optional[Store]:
        """Get store by ID"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM stores WHERE id = $1"
                row = await conn.fetchrow(query, store_id)
                
                if row:
                    return self._row_to_store(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting store {store_id}: {e}")
                raise
    
    async def get_by_code(self, tenant_id: UUID, store_code: str) -> Optional[Store]:
        """Get store by tenant and store code"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM stores 
                    WHERE tenant_id = $1 AND store_code = $2
                """
                row = await conn.fetchrow(query, tenant_id, store_code)
                
                if row:
                    return self._row_to_store(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting store by code {store_code}: {e}")
                raise
    
    async def update(self, store: Store) -> Store:
        """Update store information"""
        async with self.pool.acquire() as conn:
            try:
                store.updated_at = datetime.utcnow()
                
                query = """
                    UPDATE stores SET
                        name = $2, address = $3, phone = $4, email = $5,
                        hours = $6, timezone = $7, license_number = $8,
                        license_expiry = $9, tax_rate = $10, delivery_radius_km = $11,
                        delivery_enabled = $12, pickup_enabled = $13, kiosk_enabled = $14,
                        pos_enabled = $15, ecommerce_enabled = $16, status = $17,
                        settings = $18, pos_integration = $19, seo_config = $20,
                        latitude = $21, longitude = $22, updated_at = $23
                    WHERE id = $1
                    RETURNING *
                """
                
                address_json = store.address.to_dict() if store.address else None
                latitude = float(store.location.latitude) if store.location else None
                longitude = float(store.location.longitude) if store.location else None
                
                row = await conn.fetchrow(
                    query,
                    store.id,
                    store.name,
                    json.dumps(address_json) if address_json else None,
                    store.phone,
                    store.email,
                    json.dumps(store.hours),
                    store.timezone,
                    store.license_number,
                    store.license_expiry,
                    store.tax_rate,
                    store.delivery_radius_km,
                    store.delivery_enabled,
                    store.pickup_enabled,
                    store.kiosk_enabled,
                    store.pos_enabled,
                    store.ecommerce_enabled,
                    store.status.value,
                    json.dumps(store.settings),
                    json.dumps(store.pos_integration),
                    json.dumps(store.seo_config),
                    latitude,
                    longitude,
                    store.updated_at
                )
                
                return self._row_to_store(row)
                
            except Exception as e:
                logger.error(f"Error updating store {store.id}: {e}")
                raise
    
    async def delete(self, store_id: UUID) -> bool:
        """Soft delete a store"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE stores 
                    SET status = $2, updated_at = $3
                    WHERE id = $1
                """
                
                await conn.execute(
                    query,
                    store_id,
                    StoreStatus.INACTIVE.value,
                    datetime.utcnow()
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Error deleting store {store_id}: {e}")
                raise
    
    async def list_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Store]:
        """List stores for a tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM stores WHERE tenant_id = $1"
                params = [tenant_id]
                param_count = 2
                
                if status:
                    query += f" AND status = ${param_count}"
                    params.append(status.value)
                    param_count += 1
                
                query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [self._row_to_store(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Error listing stores for tenant {tenant_id}: {e}")
                raise
    
    async def list_by_province(
        self, 
        province_territory_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Store]:
        """List stores in a province/territory"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM stores WHERE province_territory_id = $1"
                params = [province_territory_id]
                param_count = 2
                
                if status:
                    query += f" AND status = ${param_count}"
                    params.append(status.value)
                    param_count += 1
                
                query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [self._row_to_store(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Error listing stores for province {province_territory_id}: {e}")
                raise
    
    def _row_to_store(self, row: asyncpg.Record) -> Store:
        """Convert database row to Store domain model"""
        address = None
        if row['address']:
            address_data = json.loads(row['address']) if isinstance(row['address'], str) else row['address']
            address = Address.from_dict(address_data)
        
        location = None
        if row['latitude'] is not None and row['longitude'] is not None:
            location = GeoLocation(
                latitude=Decimal(str(row['latitude'])),
                longitude=Decimal(str(row['longitude']))
            )
        
        return Store(
            id=row['id'],
            tenant_id=row['tenant_id'],
            province_territory_id=row['province_territory_id'],
            store_code=row['store_code'],
            name=row['name'],
            address=address,
            phone=row['phone'],
            email=row['email'],
            hours=json.loads(row['hours']) if isinstance(row['hours'], str) else row['hours'],
            timezone=row['timezone'],
            license_number=row['license_number'],
            license_expiry=row['license_expiry'],
            tax_rate=row['tax_rate'],
            delivery_radius_km=row['delivery_radius_km'],
            delivery_enabled=row['delivery_enabled'],
            pickup_enabled=row['pickup_enabled'],
            kiosk_enabled=row['kiosk_enabled'],
            pos_enabled=row['pos_enabled'],
            ecommerce_enabled=row['ecommerce_enabled'],
            status=StoreStatus(row['status']),
            settings=json.loads(row['settings']) if isinstance(row['settings'], str) else row['settings'],
            pos_integration=json.loads(row['pos_integration']) if isinstance(row['pos_integration'], str) else row['pos_integration'],
            seo_config=json.loads(row['seo_config']) if isinstance(row['seo_config'], str) else row['seo_config'],
            location=location,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )