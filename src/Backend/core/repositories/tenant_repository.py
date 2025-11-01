"""
Tenant Repository Implementation
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
import logging
import json

from core.domain.models import (
    Tenant, TenantStatus, SubscriptionTier, Address
)
from core.repositories.interfaces import ITenantRepository

logger = logging.getLogger(__name__)


class TenantRepository(ITenantRepository):
    """PostgreSQL implementation of Tenant repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
    
    async def create(self, tenant: Tenant, conn=None) -> Tenant:
        """Create a new tenant
        
        Args:
            tenant: Tenant entity to create
            conn: Optional database connection for transaction control.
                  If provided, uses this connection; otherwise acquires new one.
        """
        async def _create(connection):
            try:
                query = """
                    INSERT INTO tenants (
                        id, name, code, company_name, business_number,
                        gst_hst_number, address, contact_email, contact_phone,
                        website, logo_url, status, subscription_tier,
                        max_stores, billing_info, currency, settings, metadata,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                    )
                    RETURNING *
                """
                
                address_json = tenant.address.to_dict() if tenant.address else None
                
                row = await connection.fetchrow(
                    query,
                    tenant.id,
                    tenant.name,
                    tenant.code,
                    tenant.company_name,
                    tenant.business_number,
                    tenant.gst_hst_number,
                    json.dumps(address_json) if address_json else None,
                    tenant.contact_email,
                    tenant.contact_phone,
                    tenant.website,
                    tenant.logo_url,
                    tenant.status.value,
                    tenant.subscription_tier.value,
                    tenant.max_stores,
                    json.dumps(tenant.billing_info),
                    tenant.currency,
                    json.dumps(tenant.settings),
                    json.dumps(tenant.metadata),
                    tenant.created_at,
                    tenant.updated_at
                )
                
                return self._row_to_tenant(row)
                
            except asyncpg.UniqueViolationError as e:
                logger.error(f"Tenant with code {tenant.code} already exists: {e}")
                raise ValueError(f"Tenant with code {tenant.code} already exists")
            except Exception as e:
                logger.error(f"Error creating tenant: {e}")
                raise
        
        # Use provided connection or acquire new one
        if conn is not None:
            return await _create(conn)
        else:
            async with self.pool.acquire() as connection:
                return await _create(connection)
    
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM tenants WHERE id = $1"
                row = await conn.fetchrow(query, tenant_id)
                
                if row:
                    return self._row_to_tenant(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting tenant {tenant_id}: {e}")
                raise
    
    async def get_by_code(self, code: str) -> Optional[Tenant]:
        """Get tenant by unique code"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM tenants WHERE code = $1"
                row = await conn.fetchrow(query, code)
                
                if row:
                    return self._row_to_tenant(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting tenant by code {code}: {e}")
                raise
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant information"""
        async with self.pool.acquire() as conn:
            try:
                tenant.updated_at = datetime.utcnow()
                
                query = """
                    UPDATE tenants SET
                        name = $2, company_name = $3, business_number = $4,
                        gst_hst_number = $5, address = $6, contact_email = $7,
                        contact_phone = $8, website = $9, logo_url = $10,
                        status = $11, subscription_tier = $12, max_stores = $13,
                        billing_info = $14, currency = $15, settings = $16,
                        metadata = $17, updated_at = $18
                    WHERE id = $1
                    RETURNING *
                """
                
                address_json = tenant.address.to_dict() if tenant.address else None
                
                row = await conn.fetchrow(
                    query,
                    tenant.id,
                    tenant.name,
                    tenant.company_name,
                    tenant.business_number,
                    tenant.gst_hst_number,
                    json.dumps(address_json) if address_json else None,
                    tenant.contact_email,
                    tenant.contact_phone,
                    tenant.website,
                    tenant.logo_url,
                    tenant.status.value,
                    tenant.subscription_tier.value,
                    tenant.max_stores,
                    json.dumps(tenant.billing_info),
                    tenant.currency,
                    json.dumps(tenant.settings),
                    json.dumps(tenant.metadata),
                    tenant.updated_at
                )
                
                return self._row_to_tenant(row)
                
            except Exception as e:
                logger.error(f"Error updating tenant {tenant.id}: {e}")
                raise
    
    async def delete(self, tenant_id: UUID) -> bool:
        """Soft delete a tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE tenants 
                    SET status = $2, updated_at = $3
                    WHERE id = $1
                """
                
                await conn.execute(
                    query,
                    tenant_id,
                    TenantStatus.CANCELLED.value,
                    datetime.utcnow()
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Error deleting tenant {tenant_id}: {e}")
                raise
    
    async def list(
        self, 
        status: Optional[TenantStatus] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filters"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM tenants WHERE 1=1"
                params = []
                param_count = 1
                
                if status:
                    query += f" AND status = ${param_count}"
                    params.append(status.value)
                    param_count += 1
                
                if subscription_tier:
                    query += f" AND subscription_tier = ${param_count}"
                    params.append(subscription_tier.value)
                    param_count += 1
                
                query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [self._row_to_tenant(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Error listing tenants: {e}")
                raise
    
    async def count_stores(self, tenant_id: UUID) -> int:
        """Count stores for a tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT COUNT(*) FROM stores 
                    WHERE tenant_id = $1 AND status != 'inactive'
                """
                
                count = await conn.fetchval(query, tenant_id)
                return count or 0
                
            except Exception as e:
                logger.error(f"Error counting stores for tenant {tenant_id}: {e}")
                raise
    
    def _row_to_tenant(self, row: asyncpg.Record) -> Tenant:
        """Convert database row to Tenant domain model"""
        address = None
        if row['address']:
            address_data = json.loads(row['address']) if isinstance(row['address'], str) else row['address']
            address = Address.from_dict(address_data)
        
        return Tenant(
            id=row['id'],
            name=row['name'],
            code=row['code'],
            company_name=row['company_name'],
            business_number=row['business_number'],
            gst_hst_number=row['gst_hst_number'],
            address=address,
            contact_email=row['contact_email'],
            contact_phone=row['contact_phone'],
            website=row['website'],
            logo_url=row['logo_url'],
            status=TenantStatus(row['status']),
            subscription_tier=SubscriptionTier(row['subscription_tier']),
            max_stores=row['max_stores'],
            billing_info=json.loads(row['billing_info']) if isinstance(row['billing_info'], str) else row['billing_info'],
            currency=row['currency'],
            settings=json.loads(row['settings']) if isinstance(row['settings'], str) else row['settings'],
            metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )