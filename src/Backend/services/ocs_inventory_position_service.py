"""
OCS Inventory Position Service

Handles daily inventory position snapshots for OCS reporting.
Submits complete inventory state at 1 AM Eastern daily.
"""

import os
import logging
import asyncpg
import aiohttp
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from decimal import Decimal

from services.ocs_auth_service import OCSAuthService

logger = logging.getLogger(__name__)


class OCSInventoryPositionService:
    """
    OCS Inventory Position Service
    
    Submits daily inventory snapshots to OCS.
    Required: Complete inventory state for all SKUs at 1 AM Eastern daily.
    """
    
    def __init__(self, db_pool: asyncpg.Pool, auth_service: OCSAuthService):
        self.db_pool = db_pool
        self.auth_service = auth_service
        self.ocs_base_url = os.getenv('OCS_API_BASE_URL', 'https://api.ocs.ca')
        self.position_endpoint = f"{self.ocs_base_url}/api/v1/inventory/position"
        
    async def submit_daily_position(
        self,
        tenant_id: str,
        store_id: str,
        snapshot_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Submit daily inventory position to OCS
        
        Args:
            tenant_id: Tenant UUID
            store_id: Store UUID
            snapshot_date: Date for snapshot (default: today)
            
        Returns:
            dict: Submission result with status and details
        """
        if snapshot_date is None:
            snapshot_date = date.today()
            
        try:
            # Get store OCS configuration
            store_config = await self._get_store_config(store_id)
            if not store_config:
                return {
                    'success': False,
                    'error': 'Store not configured for OCS',
                    'store_id': store_id
                }
            
            # Get current inventory snapshot
            inventory_items = await self._get_inventory_snapshot(store_id)
            
            if not inventory_items:
                logger.warning(f"No inventory items found for store {store_id}")
                return {
                    'success': True,
                    'message': 'No inventory to report',
                    'items_count': 0
                }
            
            # Get access token
            access_token = await self.auth_service.get_access_token(tenant_id)
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to get OCS access token',
                    'tenant_id': tenant_id
                }
            
            # Format payload for OCS
            payload = {
                'license_number': store_config['license_number'],
                'snapshot_date': snapshot_date.isoformat(),
                'items': [
                    {
                        'ocs_sku': item['ocs_sku'],
                        'quantity': float(item['quantity']),
                        'unit_cost': float(item['unit_cost']) if item['unit_cost'] else None,
                        'lot_number': item.get('lot_number'),
                        'expiry_date': item.get('expiry_date').isoformat() if item.get('expiry_date') else None
                    }
                    for item in inventory_items
                ]
            }
            
            # Submit to OCS
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                async with session.post(
                    self.position_endpoint,
                    json=payload,
                    headers=headers
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        # Log successful submission
                        await self._log_position_submission(
                            tenant_id=tenant_id,
                            store_id=store_id,
                            snapshot_date=snapshot_date,
                            items_count=len(inventory_items),
                            ocs_response=response_data,
                            status='success'
                        )
                        
                        return {
                            'success': True,
                            'items_count': len(inventory_items),
                            'ocs_response': response_data
                        }
                    else:
                        # Log failed submission
                        await self._log_position_submission(
                            tenant_id=tenant_id,
                            store_id=store_id,
                            snapshot_date=snapshot_date,
                            items_count=len(inventory_items),
                            ocs_response=response_data,
                            status='failed',
                            error_message=f"HTTP {response.status}: {response_data.get('error', 'Unknown error')}"
                        )
                        
                        return {
                            'success': False,
                            'error': f"OCS API error: {response.status}",
                            'ocs_response': response_data
                        }
                        
        except Exception as e:
            logger.error(f"Error submitting inventory position for store {store_id}: {e}")
            
            # Log exception
            await self._log_position_submission(
                tenant_id=tenant_id,
                store_id=store_id,
                snapshot_date=snapshot_date,
                items_count=0,
                status='failed',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_store_config(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Get store OCS configuration"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        id,
                        ocs_key,
                        license_number,
                        tenant_id
                    FROM stores
                    WHERE id = $1
                    AND ocs_key IS NOT NULL
                    AND license_number IS NOT NULL
                """, store_id)
                
                if not row:
                    return None
                
                return dict(row)
                
        except Exception as e:
            logger.error(f"Error getting store config for {store_id}: {e}")
            return None
    
    async def _get_inventory_snapshot(self, store_id: str) -> List[Dict[str, Any]]:
        """Get current inventory snapshot for store"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        oi.sku as ocs_sku,
                        oi.quantity,
                        oi.unit_cost,
                        oi.lot_number,
                        oi.expiry_date
                    FROM ocs_inventory oi
                    WHERE oi.store_id = $1
                    AND oi.quantity > 0
                    ORDER BY oi.sku
                """, store_id)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting inventory snapshot for store {store_id}: {e}")
            return []
    
    async def _log_position_submission(
        self,
        tenant_id: str,
        store_id: str,
        snapshot_date: date,
        items_count: int,
        status: str,
        ocs_response: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log position submission to database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ocs_inventory_position_log (
                        tenant_id,
                        store_id,
                        snapshot_date,
                        items_count,
                        submitted_at,
                        status,
                        ocs_response,
                        error_message
                    ) VALUES ($1, $2, $3, $4, NOW(), $5, $6, $7)
                """, 
                    tenant_id,
                    store_id,
                    snapshot_date,
                    items_count,
                    status,
                    ocs_response,
                    error_message
                )
                
        except Exception as e:
            logger.error(f"Error logging position submission: {e}")
    
    async def get_submission_history(
        self,
        store_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get submission history for a store"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id,
                        snapshot_date,
                        items_count,
                        submitted_at,
                        status,
                        error_message
                    FROM ocs_inventory_position_log
                    WHERE store_id = $1
                    ORDER BY submitted_at DESC
                    LIMIT $2
                """, store_id, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting submission history for store {store_id}: {e}")
            return []
