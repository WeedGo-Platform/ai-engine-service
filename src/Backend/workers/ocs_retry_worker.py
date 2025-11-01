"""
OCS Retry Worker

Retries failed OCS submissions with exponential backoff.
Runs every 5 minutes to process failed events and positions.
"""

import os
import logging
import asyncio
import asyncpg
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.ocs_auth_service import OCSAuthService
from services.ocs_inventory_event_service import OCSInventoryEventService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCSRetryWorker:
    """
    OCS Retry Worker
    
    Retries failed OCS submissions with exponential backoff.
    Runs every 5 minutes to check for failed submissions.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_pool = None
        self.auth_service = None
        self.event_service = None
        
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
            self.event_service = OCSInventoryEventService(
                self.db_pool,
                self.auth_service
            )
            
            logger.info("OCS Retry Worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise
    
    async def get_failed_events(self, limit: int = 50):
        """Get failed events that are ready for retry"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get failed events with exponential backoff
                # Retry immediately, then after 1min, 5min, 15min, 1hr, 6hr, 24hr
                events = await conn.fetch("""
                    WITH retry_schedule AS (
                        SELECT 
                            id,
                            tenant_id,
                            store_id,
                            transaction_id,
                            transaction_type,
                            items_count,
                            retry_count,
                            submitted_at,
                            CASE retry_count
                                WHEN 0 THEN INTERVAL '0 minutes'
                                WHEN 1 THEN INTERVAL '1 minute'
                                WHEN 2 THEN INTERVAL '5 minutes'
                                WHEN 3 THEN INTERVAL '15 minutes'
                                WHEN 4 THEN INTERVAL '1 hour'
                                WHEN 5 THEN INTERVAL '6 hours'
                                ELSE INTERVAL '24 hours'
                            END as backoff_interval
                        FROM ocs_inventory_event_log
                        WHERE status = 'failed'
                        AND retry_count < 7
                    )
                    SELECT *
                    FROM retry_schedule
                    WHERE submitted_at + backoff_interval <= NOW()
                    ORDER BY submitted_at ASC
                    LIMIT $1
                """, limit)
                
                return [dict(event) for event in events]
                
        except Exception as e:
            logger.error(f"Error getting failed events: {e}")
            return []
    
    async def get_failed_positions(self, limit: int = 20):
        """Get failed position submissions ready for retry"""
        try:
            async with self.db_pool.acquire() as conn:
                positions = await conn.fetch("""
                    SELECT 
                        id,
                        tenant_id,
                        store_id,
                        snapshot_date,
                        items_count,
                        submitted_at,
                        error_message
                    FROM ocs_inventory_position_log
                    WHERE status = 'failed'
                    AND submitted_at <= NOW() - INTERVAL '30 minutes'
                    ORDER BY submitted_at ASC
                    LIMIT $1
                """, limit)
                
                return [dict(pos) for pos in positions]
                
        except Exception as e:
            logger.error(f"Error getting failed positions: {e}")
            return []
    
    async def retry_event(self, event: dict):
        """Retry a failed event submission"""
        transaction_id = event['transaction_id']
        
        try:
            logger.info(
                f"Retrying event {transaction_id} "
                f"(attempt {event['retry_count'] + 1})"
            )
            
            # TODO: Reconstruct the original event data
            # For now, we'll just mark it as retried
            # In production, store the original payload in the log
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ocs_inventory_event_log
                    SET 
                        retry_count = retry_count + 1,
                        status = CASE 
                            WHEN retry_count >= 6 THEN 'max_retries'
                            ELSE status
                        END
                    WHERE id = $1
                """, event['id'])
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error retrying event {transaction_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def retry_position(self, position: dict):
        """Retry a failed position submission"""
        store_id = position['store_id']
        snapshot_date = position['snapshot_date']
        
        try:
            logger.info(
                f"Retrying position for store {store_id}, "
                f"date {snapshot_date}"
            )
            
            # Re-submit the position
            from services.ocs_inventory_position_service import OCSInventoryPositionService
            position_service = OCSInventoryPositionService(
                self.db_pool,
                self.auth_service
            )
            
            result = await position_service.submit_daily_position(
                tenant_id=position['tenant_id'],
                store_id=store_id,
                snapshot_date=snapshot_date
            )
            
            if result['success']:
                logger.info(f"✅ Successfully retried position for store {store_id}")
            else:
                logger.error(f"❌ Retry failed for store {store_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrying position for store {store_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_retry_job(self):
        """Run retry job for failed submissions"""
        logger.info("=" * 60)
        logger.info("Starting OCS Retry Job")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 60)
        
        try:
            # Retry failed events
            failed_events = await self.get_failed_events()
            logger.info(f"Found {len(failed_events)} failed events to retry")
            
            event_results = {
                'total': len(failed_events),
                'success': 0,
                'failed': 0
            }
            
            for event in failed_events:
                result = await self.retry_event(event)
                if result['success']:
                    event_results['success'] += 1
                else:
                    event_results['failed'] += 1
                
                await asyncio.sleep(1)  # Rate limiting
            
            # Retry failed positions
            failed_positions = await self.get_failed_positions()
            logger.info(f"Found {len(failed_positions)} failed positions to retry")
            
            position_results = {
                'total': len(failed_positions),
                'success': 0,
                'failed': 0
            }
            
            for position in failed_positions:
                result = await self.retry_position(position)
                if result['success']:
                    position_results['success'] += 1
                else:
                    position_results['failed'] += 1
                
                await asyncio.sleep(2)  # Rate limiting
            
            # Log summary
            logger.info("=" * 60)
            logger.info("OCS Retry Job Complete")
            logger.info(f"Events - Total: {event_results['total']}, "
                       f"Success: {event_results['success']}, "
                       f"Failed: {event_results['failed']}")
            logger.info(f"Positions - Total: {position_results['total']}, "
                       f"Success: {position_results['success']}, "
                       f"Failed: {position_results['failed']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error in retry job: {e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """Start the scheduler"""
        # Schedule retry job every 5 minutes
        self.scheduler.add_job(
            self.run_retry_job,
            IntervalTrigger(minutes=5),
            id='ocs_retry_job',
            name='OCS Retry Job',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("OCS Retry Worker started")
        logger.info("Scheduled: Every 5 minutes")
    
    async def stop(self):
        """Stop the scheduler and cleanup"""
        self.scheduler.shutdown()
        if self.db_pool:
            await self.db_pool.close()
        logger.info("OCS Retry Worker stopped")


async def main():
    """Main entry point"""
    worker = OCSRetryWorker()
    
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
