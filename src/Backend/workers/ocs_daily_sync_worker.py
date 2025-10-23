"""
OCS Daily Sync Worker

Runs daily at 1 AM Eastern to submit inventory position snapshots to OCS.
Uses APScheduler for scheduling and asyncpg for database operations.
"""

import os
import logging
import asyncio
import asyncpg
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from services.ocs_auth_service import OCSAuthService
from services.ocs_inventory_position_service import OCSInventoryPositionService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCSDailySyncWorker:
    """
    OCS Daily Position Sync Worker
    
    Runs at 1 AM Eastern timezone daily to submit inventory snapshots
    for all stores configured for OCS compliance.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_pool = None
        self.auth_service = None
        self.position_service = None
        self.eastern = pytz.timezone('America/New_York')
        
    async def initialize(self):
        """Initialize database pool and services"""
        try:
            # Create database pool
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5434)),
                database=os.getenv('DB_NAME', 'ai_engine'),
                user=os.getenv('DB_USER', 'weedgo'),
                password=os.getenv('DB_PASSWORD', 'weedgo123'),
                min_size=2,
                max_size=10
            )
            
            # Initialize services
            self.auth_service = OCSAuthService(self.db_pool)
            self.position_service = OCSInventoryPositionService(
                self.db_pool,
                self.auth_service
            )
            
            logger.info("OCS Daily Sync Worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise
    
    async def get_ocs_enabled_stores(self):
        """Get all stores configured for OCS"""
        try:
            async with self.db_pool.acquire() as conn:
                stores = await conn.fetch("""
                    SELECT 
                        s.id as store_id,
                        s.tenant_id,
                        s.name as store_name,
                        s.ocs_key,
                        s.license_number
                    FROM stores s
                    WHERE s.ocs_key IS NOT NULL
                    AND s.license_number IS NOT NULL
                    ORDER BY s.tenant_id, s.name
                """)
                
                return [dict(store) for store in stores]
                
        except Exception as e:
            logger.error(f"Error getting OCS-enabled stores: {e}")
            return []
    
    async def sync_store_position(self, store: dict):
        """Sync inventory position for a single store"""
        store_id = store['store_id']
        tenant_id = store['tenant_id']
        store_name = store['store_name']
        
        try:
            logger.info(f"Starting position sync for store: {store_name} ({store_id})")
            
            result = await self.position_service.submit_daily_position(
                tenant_id=tenant_id,
                store_id=store_id
            )
            
            if result['success']:
                logger.info(
                    f"✅ Successfully synced {result.get('items_count', 0)} items "
                    f"for store {store_name}"
                )
            else:
                logger.error(
                    f"❌ Failed to sync store {store_name}: {result.get('error', 'Unknown error')}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Exception syncing store {store_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'store_id': store_id
            }
    
    async def run_daily_sync(self):
        """Run daily inventory position sync for all stores"""
        logger.info("=" * 60)
        logger.info("Starting OCS Daily Position Sync")
        logger.info(f"Timestamp: {datetime.now(self.eastern).isoformat()}")
        logger.info("=" * 60)
        
        try:
            # Get all OCS-enabled stores
            stores = await self.get_ocs_enabled_stores()
            
            if not stores:
                logger.warning("No OCS-enabled stores found")
                return
            
            logger.info(f"Found {len(stores)} OCS-enabled stores")
            
            # Sync each store
            results = {
                'total': len(stores),
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for store in stores:
                result = await self.sync_store_position(store)
                
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'store_id': store['store_id'],
                        'store_name': store['store_name'],
                        'error': result.get('error')
                    })
                
                # Small delay between stores to avoid overwhelming the API
                await asyncio.sleep(2)
            
            # Log summary
            logger.info("=" * 60)
            logger.info("OCS Daily Sync Complete")
            logger.info(f"Total stores: {results['total']}")
            logger.info(f"Successful: {results['success']}")
            logger.info(f"Failed: {results['failed']}")
            
            if results['errors']:
                logger.error("Failed stores:")
                for error in results['errors']:
                    logger.error(f"  - {error['store_name']}: {error['error']}")
            
            logger.info("=" * 60)
            
            # Log to audit table
            await self._log_sync_run(results)
            
        except Exception as e:
            logger.error(f"Error in daily sync job: {e}")
            import traceback
            traceback.print_exc()
    
    async def _log_sync_run(self, results: dict):
        """Log sync run to audit table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ocs_audit_log (
                        operation,
                        status,
                        details,
                        created_at
                    ) VALUES ($1, $2, $3, NOW())
                """,
                    'daily_position_sync',
                    'success' if results['failed'] == 0 else 'partial_failure',
                    results
                )
        except Exception as e:
            logger.error(f"Error logging sync run: {e}")
    
    def start(self):
        """Start the scheduler"""
        # Schedule daily sync at 1 AM Eastern
        self.scheduler.add_job(
            self.run_daily_sync,
            CronTrigger(
                hour=1,
                minute=0,
                timezone=self.eastern
            ),
            id='ocs_daily_sync',
            name='OCS Daily Position Sync',
            replace_existing=True
        )
        
        # Optional: Add a manual trigger for testing (runs every hour)
        if os.getenv('OCS_HOURLY_TEST', 'false').lower() == 'true':
            self.scheduler.add_job(
                self.run_daily_sync,
                CronTrigger(minute=0),
                id='ocs_hourly_test',
                name='OCS Hourly Test Sync',
                replace_existing=True
            )
            logger.info("⚠️  Hourly test mode enabled")
        
        self.scheduler.start()
        logger.info("OCS Daily Sync Worker started")
        logger.info("Scheduled: Daily at 1:00 AM Eastern")
    
    async def stop(self):
        """Stop the scheduler and cleanup"""
        self.scheduler.shutdown()
        if self.db_pool:
            await self.db_pool.close()
        logger.info("OCS Daily Sync Worker stopped")


async def main():
    """Main entry point"""
    worker = OCSDailySyncWorker()
    
    try:
        await worker.initialize()
        worker.start()
        
        # Keep the worker running
        logger.info("Worker is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
