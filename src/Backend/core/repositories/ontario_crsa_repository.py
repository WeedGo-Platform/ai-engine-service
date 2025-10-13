"""
Ontario CRSA Repository Implementation
Handles data access for Ontario Cannabis Retail Store Authorization records
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
import logging
import json

from core.domain.models import OntarioCRSA, CRSAVerificationStatus
from core.repositories.interfaces import IOntarioCRSARepository

logger = logging.getLogger(__name__)


class OntarioCRSARepository(IOntarioCRSARepository):
    """PostgreSQL implementation of Ontario CRSA repository"""

    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool

    async def get_by_id(self, crsa_id: UUID) -> Optional[OntarioCRSA]:
        """Get CRSA record by ID"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM ontario_crsa_status WHERE id = $1"
                row = await conn.fetchrow(query, crsa_id)

                if row:
                    return self._row_to_crsa(row)
                return None

            except Exception as e:
                logger.error(f"Error getting CRSA record {crsa_id}: {e}")
                raise

    async def get_by_license(self, license_number: str) -> Optional[OntarioCRSA]:
        """Get CRSA record by license number"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM ontario_crsa_status WHERE license_number = $1"
                row = await conn.fetchrow(query, license_number)

                if row:
                    return self._row_to_crsa(row)
                return None

            except Exception as e:
                logger.error(f"Error getting CRSA record by license {license_number}: {e}")
                raise

    async def search_stores(
        self,
        query: str,
        limit: int = 10,
        authorized_only: bool = True
    ) -> List[OntarioCRSA]:
        """
        Search CRSA stores by name or address using fuzzy matching
        Uses the search_crsa_stores function created in the migration
        """
        async with self.pool.acquire() as conn:
            try:
                sql = """
                    SELECT * FROM search_crsa_stores($1, $2)
                """

                rows = await conn.fetch(sql, query, limit)

                results = []
                for row in rows:
                    # Fetch full record by ID
                    full_row = await conn.fetchrow(
                        "SELECT * FROM ontario_crsa_status WHERE id = $1",
                        row['id']
                    )
                    if full_row:
                        crsa = self._row_to_crsa(full_row)
                        # Filter authorized only if requested
                        if not authorized_only or crsa.is_authorized():
                            results.append(crsa)

                return results

            except Exception as e:
                logger.error(f"Error searching CRSA stores: {e}")
                raise

    async def list_authorized(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List all authorized stores"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM ontario_crsa_status
                    WHERE store_application_status = 'Authorized to Open'
                      AND is_active = TRUE
                    ORDER BY store_name
                    LIMIT $1 OFFSET $2
                """

                rows = await conn.fetch(query, limit, offset)
                return [self._row_to_crsa(row) for row in rows]

            except Exception as e:
                logger.error(f"Error listing authorized stores: {e}")
                raise

    async def list_available_for_signup(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List authorized stores not yet linked to a tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM ontario_crsa_status
                    WHERE store_application_status = 'Authorized to Open'
                      AND is_active = TRUE
                      AND linked_tenant_id IS NULL
                    ORDER BY store_name
                    LIMIT $1 OFFSET $2
                """

                rows = await conn.fetch(query, limit, offset)
                return [self._row_to_crsa(row) for row in rows]

            except Exception as e:
                logger.error(f"Error listing available stores: {e}")
                raise

    async def get_statistics(self) -> Dict[str, Any]:
        """Get CRSA database statistics"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT
                        COUNT(*) as total_stores,
                        COUNT(*) FILTER (WHERE store_application_status = 'Authorized to Open') as authorized_count,
                        COUNT(*) FILTER (WHERE store_application_status LIKE 'Public Notice%') as pending_count,
                        COUNT(*) FILTER (WHERE store_application_status = 'Cancelled') as cancelled_count,
                        COUNT(*) FILTER (WHERE linked_tenant_id IS NOT NULL) as signed_up_count,
                        COUNT(*) FILTER (WHERE store_application_status = 'Authorized to Open' AND linked_tenant_id IS NULL) as available_for_signup,
                        MAX(last_synced_at) as last_sync_time,
                        COUNT(DISTINCT municipality) as municipality_count
                    FROM ontario_crsa_status
                    WHERE is_active = TRUE
                """

                row = await conn.fetchrow(query)

                return {
                    'total_stores': row['total_stores'],
                    'authorized_count': row['authorized_count'],
                    'pending_count': row['pending_count'],
                    'cancelled_count': row['cancelled_count'],
                    'signed_up_count': row['signed_up_count'],
                    'available_for_signup': row['available_for_signup'],
                    'last_sync_time': row['last_sync_time'].isoformat() if row['last_sync_time'] else None,
                    'municipality_count': row['municipality_count']
                }

            except Exception as e:
                logger.error(f"Error getting CRSA statistics: {e}")
                raise

    async def mark_linked(self, license_number: str, tenant_id: UUID) -> OntarioCRSA:
        """Link a CRSA record to a tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE ontario_crsa_status
                    SET linked_tenant_id = $2,
                        updated_at = NOW()
                    WHERE license_number = $1
                    RETURNING *
                """

                row = await conn.fetchrow(query, license_number, tenant_id)

                if not row:
                    raise ValueError(f"CRSA record with license {license_number} not found")

                return self._row_to_crsa(row)

            except Exception as e:
                logger.error(f"Error linking CRSA record {license_number} to tenant {tenant_id}: {e}")
                raise

    async def mark_unlinked(self, license_number: str) -> OntarioCRSA:
        """Unlink a CRSA record from tenant"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE ontario_crsa_status
                    SET linked_tenant_id = NULL,
                        updated_at = NOW()
                    WHERE license_number = $1
                    RETURNING *
                """

                row = await conn.fetchrow(query, license_number)

                if not row:
                    raise ValueError(f"CRSA record with license {license_number} not found")

                return self._row_to_crsa(row)

            except Exception as e:
                logger.error(f"Error unlinking CRSA record {license_number}: {e}")
                raise

    async def verify_license(
        self,
        license_number: str,
        verified_by_user_id: UUID
    ) -> OntarioCRSA:
        """Mark a license as verified"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE ontario_crsa_status
                    SET verification_status = $2,
                        verification_date = NOW(),
                        verified_by = $3,
                        updated_at = NOW()
                    WHERE license_number = $1
                    RETURNING *
                """

                row = await conn.fetchrow(
                    query,
                    license_number,
                    CRSAVerificationStatus.VERIFIED.value,
                    verified_by_user_id
                )

                if not row:
                    raise ValueError(f"CRSA record with license {license_number} not found")

                return self._row_to_crsa(row)

            except Exception as e:
                logger.error(f"Error verifying license {license_number}: {e}")
                raise

    async def list_by_municipality(
        self,
        municipality: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List stores in a specific municipality"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM ontario_crsa_status
                    WHERE LOWER(municipality) = LOWER($1)
                      AND is_active = TRUE
                    ORDER BY store_name
                    LIMIT $2 OFFSET $3
                """

                rows = await conn.fetch(query, municipality, limit, offset)
                return [self._row_to_crsa(row) for row in rows]

            except Exception as e:
                logger.error(f"Error listing stores in municipality {municipality}: {e}")
                raise

    def _row_to_crsa(self, row: asyncpg.Record) -> OntarioCRSA:
        """Convert database row to OntarioCRSA domain model"""
        return OntarioCRSA(
            id=row['id'],
            license_number=row['license_number'],
            municipality=row['municipality'],
            first_nation=row['first_nation'],
            store_name=row['store_name'],
            address=row['address'],
            store_application_status=row['store_application_status'],
            website=row['website'],
            linked_tenant_id=row['linked_tenant_id'],
            verification_status=CRSAVerificationStatus(row['verification_status']) if row['verification_status'] else CRSAVerificationStatus.UNVERIFIED,
            verification_date=row['verification_date'],
            verified_by=row['verified_by'],
            notes=row['notes'],
            admin_notes=row['admin_notes'],
            data_source=row['data_source'] or 'agco_csv',
            first_seen_at=row['first_seen_at'],
            last_synced_at=row['last_synced_at'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
