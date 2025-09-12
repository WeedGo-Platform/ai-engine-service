"""
Province/Territory Repository Implementation
"""

from typing import List, Optional
from uuid import UUID
import asyncpg
import logging
import json

from core.domain.models import ProvinceTerritory, ProvinceType
from core.repositories.interfaces import IProvinceRepository

logger = logging.getLogger(__name__)


class ProvinceRepository(IProvinceRepository):
    """PostgreSQL implementation of Province repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
    
    async def get_by_id(self, province_id: UUID) -> Optional[ProvinceTerritory]:
        """Get province/territory by ID"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM provinces_territories WHERE id = $1"
                row = await conn.fetchrow(query, province_id)
                
                if row:
                    return self._row_to_province(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting province {province_id}: {e}")
                raise
    
    async def get_by_code(self, code: str) -> Optional[ProvinceTerritory]:
        """Get province/territory by code"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM provinces_territories WHERE code = $1"
                row = await conn.fetchrow(query, code.upper())
                
                if row:
                    return self._row_to_province(row)
                return None
                
            except Exception as e:
                logger.error(f"Error getting province by code {code}: {e}")
                raise
    
    async def list_all(self) -> List[ProvinceTerritory]:
        """List all provinces/territories"""
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT * FROM provinces_territories ORDER BY name"
                rows = await conn.fetch(query)
                
                return [self._row_to_province(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Error listing provinces: {e}")
                raise
    
    def _row_to_province(self, row: asyncpg.Record) -> ProvinceTerritory:
        """Convert database row to ProvinceTerritory domain model"""
        
        # Handle settings - could be JSON string or dict
        settings = row.get('settings', {})
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        # Extract language preferences and regulations from settings if present
        language_prefs = settings.get('language_preferences', {'primary': 'en', 'secondary': []})
        regulations = settings.get('cannabis_regulations', {})
        
        return ProvinceTerritory(
            id=row['id'],
            code=row['code'],
            name=row['name'],
            type=ProvinceType(row['type']),  # Column is 'type' not 'province_type'
            tax_rate=row['tax_rate'],
            min_age=row.get('min_age', 19),  # Column is 'min_age'
            regulatory_body=row.get('regulatory_body'),
            delivery_allowed=row.get('delivery_allowed', True),
            pickup_allowed=row.get('pickup_allowed', True),
            settings=settings,  # Pass settings dict directly
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )