"""
OCS Product Catalog Synchronization Service
Syncs the 67-column ocs_product_catalog (the bible) to RAG knowledge base
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncpg
from services.rag.rag_service import get_rag_service
from services.rag.document_chunker import DocumentChunker

logger = logging.getLogger(__name__)


class OCSProductSyncService:
    """
    Synchronizes OCS product catalog to RAG knowledge base
    ocs_product_catalog is the "bible" for all cannabis information
    """
    
    # Important fields for overview chunks
    OVERVIEW_FIELDS = [
        "product_name",
        "strain_type",
        "thc_min",
        "thc_max",
        "cbd_min",
        "cbd_max",
        "producer",
        "brand",
        "category"
    ]
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize sync service
        
        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self.rag_service = None
        self.chunker = DocumentChunker(
            chunk_size=512,
            chunk_overlap=100
        )
    
    async def initialize(self):
        """Initialize RAG service"""
        self.rag_service = await get_rag_service()
        await self.rag_service.initialize()
        logger.info("OCS Product Sync Service initialized")
    
    async def sync_tenant_products(
        self,
        tenant_id: str,
        store_id: Optional[str] = None,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync OCS products for a tenant to RAG knowledge base
        
        Args:
            tenant_id: Tenant ID
            store_id: Optional store ID (None = all stores)
            force_full_sync: Force full sync even if recently synced
            
        Returns:
            Sync status with counts
        """
        start_time = datetime.now()
        
        try:
            # Check if sync needed
            if not force_full_sync:
                should_sync = await self._should_sync(tenant_id, store_id)
                if not should_sync:
                    logger.info(f"Skipping sync for tenant {tenant_id} - recently synced")
                    return {"status": "skipped", "reason": "recently_synced"}
            
            # Mark sync as in progress
            await self._update_sync_status(
                tenant_id,
                store_id,
                status="in_progress"
            )
            
            # Fetch products from OCS catalog
            products = await self._fetch_ocs_products(tenant_id, store_id)
            
            if not products:
                logger.warning(f"No products found for tenant {tenant_id}")
                await self._update_sync_status(
                    tenant_id,
                    store_id,
                    status="success",
                    count=0
                )
                return {"status": "success", "count": 0}
            
            # Sync each product
            synced_count = 0
            errors = []
            
            for product in products:
                try:
                    await self._sync_product(product, tenant_id, store_id)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Error syncing product {product.get('id')}: {e}")
                    errors.append(str(e))
            
            # Update sync status
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_sync_status(
                tenant_id,
                store_id,
                status="success" if not errors else "failed",
                count=synced_count,
                error_message="; ".join(errors[:5]) if errors else None
            )
            
            logger.info(
                f"Synced {synced_count}/{len(products)} products for tenant {tenant_id} "
                f"in {elapsed_ms:.2f}ms"
            )
            
            return {
                "status": "success" if not errors else "partial",
                "total": len(products),
                "synced": synced_count,
                "errors": len(errors),
                "elapsed_ms": elapsed_ms
            }
            
        except Exception as e:
            logger.error(f"Error during OCS product sync: {e}")
            await self._update_sync_status(
                tenant_id,
                store_id,
                status="failed",
                error_message=str(e)
            )
            raise
    
    async def _sync_product(
        self,
        product: Dict[str, Any],
        tenant_id: str,
        store_id: Optional[str]
    ):
        """
        Sync a single product to RAG knowledge base
        
        Args:
            product: Product data from ocs_product_catalog
            tenant_id: Tenant ID
            store_id: Optional store ID
        """
        product_id = product.get("id") or product.get("product_id")
        product_name = product.get("product_name") or product.get("name", "Unknown Product")
        
        # Build document metadata
        document_metadata = {
            "source": "ocs_product_catalog",
            "product_id": product_id,
            "product_name": product_name,
            "tenant_id": tenant_id,
            "store_id": store_id,
            "synced_at": datetime.now().isoformat()
        }
        
        # Create structured chunks for product
        chunks = self.chunker.chunk_structured_data(
            data=product,
            title=product_name,
            important_fields=self.OVERVIEW_FIELDS
        )
        
        # Add each chunk to RAG
        for i, chunk in enumerate(chunks):
            # Combine metadata
            chunk_metadata = {
                **document_metadata,
                **chunk.get("metadata", {}),
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            # Add to RAG service
            await self.rag_service.add_document(
                text=chunk["text"],
                metadata=chunk_metadata,
                document_type="ocs_product",
                tenant_id=tenant_id,
                store_id=store_id,
                source_table="ocs_product_catalog",
                source_id=str(product_id),
                access_level="customer"  # Products visible to customer-facing agents
            )
    
    async def _fetch_ocs_products(
        self,
        tenant_id: str,
        store_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch products from OCS catalog
        
        Args:
            tenant_id: Tenant ID
            store_id: Optional store ID
            
        Returns:
            List of product dictionaries
        """
        query = """
            SELECT *
            FROM ocs_product_catalog
            WHERE tenant_id = $1
                AND is_active = TRUE
        """
        params = [tenant_id]
        
        if store_id:
            query += " AND store_id = $2"
            params.append(store_id)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            products = [dict(row) for row in rows]
        
        return products
    
    async def _should_sync(
        self,
        tenant_id: str,
        store_id: Optional[str]
    ) -> bool:
        """
        Check if sync is needed based on last sync time
        
        Args:
            tenant_id: Tenant ID
            store_id: Optional store ID
            
        Returns:
            True if sync should run
        """
        query = """
            SELECT 
                last_sync_at,
                sync_frequency_minutes
            FROM knowledge_sync_status
            WHERE source_table = 'ocs_product_catalog'
                AND tenant_id = $1
                AND ($2::UUID IS NULL OR store_id = $2)
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id, store_id)
        
        if not row:
            return True  # Never synced
        
        last_sync = row["last_sync_at"]
        frequency_minutes = row["sync_frequency_minutes"] or 60
        
        if not last_sync:
            return True
        
        next_sync = last_sync + timedelta(minutes=frequency_minutes)
        return datetime.now() > next_sync
    
    async def _update_sync_status(
        self,
        tenant_id: str,
        store_id: Optional[str],
        status: str,
        count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Update sync status in database
        
        Args:
            tenant_id: Tenant ID
            store_id: Optional store ID
            status: Sync status
            count: Number of records synced
            error_message: Optional error message
        """
        query = """
            INSERT INTO knowledge_sync_status (
                source_table,
                tenant_id,
                store_id,
                last_sync_at,
                last_sync_count,
                last_sync_status,
                error_message,
                next_sync_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (source_table, tenant_id)
            DO UPDATE SET
                last_sync_at = EXCLUDED.last_sync_at,
                last_sync_count = EXCLUDED.last_sync_count,
                last_sync_status = EXCLUDED.last_sync_status,
                error_message = EXCLUDED.error_message,
                next_sync_at = EXCLUDED.next_sync_at,
                updated_at = EXCLUDED.updated_at
        """
        
        now = datetime.now()
        next_sync = now + timedelta(hours=1)  # Default: 1 hour
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                "ocs_product_catalog",
                tenant_id,
                store_id,
                now if status != "in_progress" else None,
                count,
                status,
                error_message,
                next_sync if status == "success" else None,
                now
            )
    
    async def schedule_periodic_sync(
        self,
        tenant_id: str,
        interval_hours: int = 1
    ):
        """
        Schedule periodic background sync
        
        Args:
            tenant_id: Tenant ID
            interval_hours: Sync interval in hours
        """
        while True:
            try:
                await self.sync_tenant_products(tenant_id)
            except Exception as e:
                logger.error(f"Error in periodic sync for tenant {tenant_id}: {e}")
            
            await asyncio.sleep(interval_hours * 3600)


# Singleton instance
_sync_service: Optional[OCSProductSyncService] = None


async def get_ocs_sync_service(
    db_pool: Optional[asyncpg.Pool] = None
) -> OCSProductSyncService:
    """
    Get singleton OCS sync service instance
    
    Args:
        db_pool: PostgreSQL connection pool (required for first call)
        
    Returns:
        OCSProductSyncService instance
    """
    global _sync_service
    
    if _sync_service is None:
        if db_pool is None:
            raise ValueError("db_pool required for first initialization")
        
        _sync_service = OCSProductSyncService(db_pool)
        await _sync_service.initialize()
    
    return _sync_service
