"""
OCS Event Worker

Handles real-time inventory event submissions to OCS.
Processes events from a Redis queue for reliable async processing.
"""

import os
import logging
import asyncio
import asyncpg
import redis
import json
from typing import Dict, Any

from services.ocs_auth_service import OCSAuthService
from services.ocs_inventory_event_service import OCSInventoryEventService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCSEventWorker:
    """
    OCS Event Worker
    
    Processes inventory events from Redis queue and submits to OCS.
    Provides reliable async processing of real-time transactions.
    """
    
    def __init__(self):
        self.db_pool = None
        self.auth_service = None
        self.event_service = None
        self.redis_client = None
        self.running = False
        self.queue_name = 'ocs_events'
        
    async def initialize(self):
        """Initialize database pool and services"""
        try:
            # Create database pool
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5434)),
                database=os.getenv('DB_NAME', 'ai_engine'),
                user=os.getenv('DB_USER', 'weedgo'),
                password=os.getenv('DB_PASSWORD', 'your_password_here'),
                min_size=2,
                max_size=10
            )
            
            # Initialize Redis client
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True
            )
            
            # Initialize services
            self.auth_service = OCSAuthService(self.db_pool)
            self.event_service = OCSInventoryEventService(
                self.db_pool,
                self.auth_service
            )
            
            logger.info("OCS Event Worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise
    
    async def process_event(self, event_data: Dict[str, Any]):
        """Process a single inventory event"""
        transaction_id = event_data.get('transaction_id', 'unknown')
        
        try:
            logger.info(f"Processing event for transaction: {transaction_id}")
            
            result = await self.event_service.submit_transaction_event(
                tenant_id=event_data['tenant_id'],
                store_id=event_data['store_id'],
                transaction_type=event_data['transaction_type'],
                items=event_data['items'],
                transaction_id=transaction_id,
                transaction_date=event_data.get('transaction_date'),
                metadata=event_data.get('metadata')
            )
            
            if result['success']:
                logger.info(f"✅ Successfully submitted event for transaction {transaction_id}")
            else:
                logger.error(f"❌ Failed to submit event for transaction {transaction_id}: {result.get('error')}")
                # Re-queue for retry if it's a temporary failure
                if self._is_retryable_error(result.get('error')):
                    await self.enqueue_event(event_data, retry=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Exception processing event {transaction_id}: {e}")
            # Re-queue for retry
            await self.enqueue_event(event_data, retry=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_retryable_error(self, error: str) -> bool:
        """Check if error is retryable (network, timeout, etc.)"""
        if not error:
            return False
        
        retryable_keywords = [
            'timeout',
            'connection',
            'network',
            '503',
            '502',
            '504',
            'temporary'
        ]
        
        error_lower = error.lower()
        return any(keyword in error_lower for keyword in retryable_keywords)
    
    async def enqueue_event(self, event_data: Dict[str, Any], retry: bool = False):
        """Add event to Redis queue"""
        try:
            # Add retry count
            if retry:
                event_data['retry_count'] = event_data.get('retry_count', 0) + 1
                
                # Don't retry more than 3 times
                if event_data['retry_count'] > 3:
                    logger.warning(f"Max retries reached for transaction {event_data.get('transaction_id')}")
                    return False
            
            # Push to queue
            self.redis_client.rpush(
                self.queue_name,
                json.dumps(event_data)
            )
            
            logger.debug(f"Enqueued event for transaction {event_data.get('transaction_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueueing event: {e}")
            return False
    
    async def run(self):
        """Main worker loop - processes events from queue"""
        logger.info("Starting OCS Event Worker")
        self.running = True
        
        while self.running:
            try:
                # Blocking pop with 1 second timeout
                event_json = self.redis_client.blpop(self.queue_name, timeout=1)
                
                if event_json:
                    _, event_data_str = event_json
                    event_data = json.loads(event_data_str)
                    
                    # Process the event
                    await self.process_event(event_data)
                    
                    # Small delay to prevent overwhelming the API
                    await asyncio.sleep(0.1)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in queue: {e}")
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(5)  # Back off on errors
    
    async def stop(self):
        """Stop the worker"""
        logger.info("Stopping OCS Event Worker")
        self.running = False
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("OCS Event Worker stopped")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            return self.redis_client.llen(self.queue_name)
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0


async def main():
    """Main entry point"""
    worker = OCSEventWorker()
    
    try:
        await worker.initialize()
        
        logger.info("Worker is running. Press Ctrl+C to stop.")
        await worker.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
