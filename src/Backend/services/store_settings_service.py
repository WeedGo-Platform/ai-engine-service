"""
Store Settings Service
Manages all store settings using the consolidated store_settings table
"""

import asyncpg
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, time, date
import json

logger = logging.getLogger(__name__)


class StoreSettingsService:
    """Service for managing store settings using JSONB storage"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool

    async def get_store_hours(self, store_id: UUID) -> Dict[str, Any]:
        """Get regular store hours"""
        try:
            async with self.db_pool.acquire() as conn:
                hours_json = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'regular_hours'
                """, store_id)

                return hours_json if hours_json else {}

        except Exception as e:
            logger.error(f"Error getting store hours: {str(e)}")
            return {}

    async def update_store_hours(self, store_id: UUID, hours: Dict[str, Any]) -> bool:
        """Update regular store hours"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, 'hours', 'regular_hours', $2::jsonb, 'Regular store operating hours')
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, json.dumps(hours))

                return True

        except Exception as e:
            logger.error(f"Error updating store hours: {str(e)}")
            return False

    async def get_special_hours(self, store_id: UUID) -> List[Dict[str, Any]]:
        """Get special hours overrides"""
        try:
            async with self.db_pool.acquire() as conn:
                special_hours = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'special_hours'
                """, store_id)

                return special_hours if isinstance(special_hours, list) else []

        except Exception as e:
            logger.error(f"Error getting special hours: {str(e)}")
            return []

    async def add_special_hours(self, store_id: UUID, special: Dict[str, Any]) -> bool:
        """Add special hours entry"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get existing special hours
                special_hours = await self.get_special_hours(store_id)

                # Add new entry
                special_hours.append(special)

                # Update database
                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, 'hours', 'special_hours', $2::jsonb, 'Special hours overrides for specific dates')
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, json.dumps(special_hours))

                return True

        except Exception as e:
            logger.error(f"Error adding special hours: {str(e)}")
            return False

    async def get_holiday_hours(self, store_id: UUID) -> List[Dict[str, Any]]:
        """Get holiday hours configuration"""
        try:
            async with self.db_pool.acquire() as conn:
                holiday_hours = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'holiday_hours'
                """, store_id)

                return holiday_hours if isinstance(holiday_hours, list) else []

        except Exception as e:
            logger.error(f"Error getting holiday hours: {str(e)}")
            return []

    async def update_holiday_hours(self, store_id: UUID, holidays: List[Dict[str, Any]]) -> bool:
        """Update holiday hours configuration"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, 'hours', 'holiday_hours', $2::jsonb, 'Holiday hours configuration')
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, json.dumps(holidays))

                return True

        except Exception as e:
            logger.error(f"Error updating holiday hours: {str(e)}")
            return False

    async def get_hours_settings(self, store_id: UUID) -> Dict[str, Any]:
        """Get general hours settings"""
        try:
            async with self.db_pool.acquire() as conn:
                settings = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'settings'
                """, store_id)

                return settings if settings else {
                    'timezone': 'America/Toronto',
                    'auto_close_warning_minutes': 15,
                    'allow_orders_when_closed': False,
                    'display_next_open_time': True
                }

        except Exception as e:
            logger.error(f"Error getting hours settings: {str(e)}")
            return {}

    async def update_hours_settings(self, store_id: UUID, settings: Dict[str, Any]) -> bool:
        """Update general hours settings"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, 'hours', 'settings', $2::jsonb, 'General hours settings and configuration')
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, json.dumps(settings))

                return True

        except Exception as e:
            logger.error(f"Error updating hours settings: {str(e)}")
            return False

    async def get_ai_agents_config(self, store_id: UUID) -> Dict[str, Any]:
        """Get AI agents configuration"""
        try:
            async with self.db_pool.acquire() as conn:
                agents_config = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'ai' AND key = 'agents'
                """, store_id)

                return agents_config if agents_config else {
                    'chat_agent': {'enabled': True, 'model': 'gpt-4'},
                    'recommendation_agent': {'enabled': True, 'model': 'gpt-3.5-turbo'},
                    'analytics_agent': {'enabled': False, 'model': 'gpt-4'}
                }

        except Exception as e:
            logger.error(f"Error getting AI agents config: {str(e)}")
            return {}

    async def update_ai_agent_config(self, store_id: UUID, agent_name: str, config: Dict[str, Any]) -> bool:
        """Update specific AI agent configuration"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current config
                agents_config = await self.get_ai_agents_config(store_id)

                # Update specific agent
                agents_config[agent_name] = config

                # Save back
                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, 'ai', 'agents', $2::jsonb, 'AI agents configuration for the store')
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, json.dumps(agents_config))

                return True

        except Exception as e:
            logger.error(f"Error updating AI agent config: {str(e)}")
            return False

    async def get_setting(self, store_id: UUID, category: str, key: str) -> Optional[Any]:
        """Get a specific setting value"""
        try:
            async with self.db_pool.acquire() as conn:
                value = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = $2 AND key = $3
                """, store_id, category, key)

                return value

        except Exception as e:
            logger.error(f"Error getting setting: {str(e)}")
            return None

    async def update_setting(self, store_id: UUID, category: str, key: str, value: Any, description: str = None) -> bool:
        """Update a specific setting"""
        try:
            async with self.db_pool.acquire() as conn:
                if not isinstance(value, (dict, list)):
                    value = {'value': value}

                await conn.execute("""
                    INSERT INTO store_settings (store_id, category, key, value, description)
                    VALUES ($1, $2, $3, $4::jsonb, $5)
                    ON CONFLICT (store_id, category, key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        description = COALESCE(EXCLUDED.description, store_settings.description),
                        updated_at = CURRENT_TIMESTAMP
                """, store_id, category, key, json.dumps(value), description)

                return True

        except Exception as e:
            logger.error(f"Error updating setting: {str(e)}")
            return False

    async def get_all_settings(self, store_id: UUID, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all settings for a store, optionally filtered by category"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT category, key, value, description, created_at, updated_at
                    FROM store_settings
                    WHERE store_id = $1
                """
                params = [store_id]

                if category:
                    query += " AND category = $2"
                    params.append(category)

                query += " ORDER BY category, key"

                rows = await conn.fetch(query, *params)

                settings = []
                for row in rows:
                    settings.append({
                        'category': row['category'],
                        'key': row['key'],
                        'value': row['value'],
                        'description': row['description'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                    })

                return settings

        except Exception as e:
            logger.error(f"Error getting all settings: {str(e)}")
            return []