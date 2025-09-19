"""
Tenant Service
Manages tenant configuration, features, and payment providers
"""

import asyncpg
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant management operations"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool

    async def get_tenant_settings(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get all settings for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get tenant basic info
                tenant = await conn.fetchrow(
                    "SELECT * FROM tenants WHERE id = $1",
                    tenant_id
                )

                if not tenant:
                    raise ValueError(f"Tenant {tenant_id} not found")

                # Get all settings
                settings_rows = await conn.fetch(
                    """
                    SELECT setting_key, setting_value, setting_type
                    FROM tenant_settings
                    WHERE tenant_id = $1
                    """,
                    tenant_id
                )

                settings = {}
                for row in settings_rows:
                    key = row['setting_key']
                    value = row['setting_value']
                    settings[key] = value if isinstance(value, dict) else {'value': value}

                # Get features
                features = await conn.fetch(
                    """
                    SELECT feature_name, is_enabled, configuration
                    FROM tenant_features
                    WHERE tenant_id = $1
                    """,
                    tenant_id
                )

                feature_dict = {}
                for feature in features:
                    feature_dict[feature['feature_name']] = {
                        'enabled': feature['is_enabled'],
                        'config': feature['configuration'] or {}
                    }

                return {
                    'tenant_id': str(tenant_id),
                    'name': tenant['name'],
                    'settings': settings,
                    'features': feature_dict,
                    'created_at': tenant['created_at'].isoformat() if tenant['created_at'] else None
                }

        except Exception as e:
            logger.error(f"Error getting tenant settings: {str(e)}")
            raise

    async def update_tenant_setting(
        self,
        tenant_id: UUID,
        setting_key: str,
        setting_value: Any,
        setting_type: str = 'general'
    ) -> bool:
        """Update a specific tenant setting"""
        try:
            async with self.db_pool.acquire() as conn:
                # Convert value to JSONB if needed
                if not isinstance(setting_value, (dict, list)):
                    setting_value = {'value': setting_value}

                await conn.execute(
                    """
                    INSERT INTO tenant_settings (tenant_id, setting_key, setting_value, setting_type)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (tenant_id, setting_key)
                    DO UPDATE SET
                        setting_value = EXCLUDED.setting_value,
                        setting_type = EXCLUDED.setting_type,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    tenant_id,
                    setting_key,
                    json.dumps(setting_value),
                    setting_type
                )

                return True

        except Exception as e:
            logger.error(f"Error updating tenant setting: {str(e)}")
            return False

    async def toggle_feature(
        self,
        tenant_id: UUID,
        feature_name: str,
        enabled: bool,
        configuration: Optional[Dict] = None
    ) -> bool:
        """Enable or disable a tenant feature"""
        try:
            async with self.db_pool.acquire() as conn:
                config_json = json.dumps(configuration) if configuration else '{}'

                await conn.execute(
                    """
                    INSERT INTO tenant_features (tenant_id, feature_name, is_enabled, configuration, enabled_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (tenant_id, feature_name)
                    DO UPDATE SET
                        is_enabled = EXCLUDED.is_enabled,
                        configuration = EXCLUDED.configuration,
                        enabled_at = CASE
                            WHEN EXCLUDED.is_enabled THEN CURRENT_TIMESTAMP
                            ELSE tenant_features.enabled_at
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    tenant_id,
                    feature_name,
                    enabled,
                    config_json,
                    datetime.utcnow() if enabled else None
                )

                logger.info(f"Feature {feature_name} {'enabled' if enabled else 'disabled'} for tenant {tenant_id}")
                return True

        except Exception as e:
            logger.error(f"Error toggling feature: {str(e)}")
            return False

    async def get_payment_providers(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get all payment providers for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        provider_name,
                        provider_type,
                        is_active,
                        is_default,
                        supported_methods,
                        fee_structure,
                        created_at
                    FROM tenant_payment_providers
                    WHERE tenant_id = $1
                    ORDER BY is_default DESC, provider_name
                    """,
                    tenant_id
                )

                providers = []
                for row in rows:
                    providers.append({
                        'id': str(row['id']),
                        'name': row['provider_name'],
                        'type': row['provider_type'],
                        'active': row['is_active'],
                        'default': row['is_default'],
                        'supported_methods': row['supported_methods'] or [],
                        'fee_structure': row['fee_structure'] or {},
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })

                return providers

        except Exception as e:
            logger.error(f"Error getting payment providers: {str(e)}")
            return []

    async def add_payment_provider(
        self,
        tenant_id: UUID,
        provider_name: str,
        provider_type: str,
        configuration: Dict[str, Any],
        credentials: Dict[str, Any],
        is_default: bool = False
    ) -> Optional[str]:
        """Add a payment provider for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                # If setting as default, unset other defaults
                if is_default:
                    await conn.execute(
                        """
                        UPDATE tenant_payment_providers
                        SET is_default = false
                        WHERE tenant_id = $1 AND provider_type = $2
                        """,
                        tenant_id,
                        provider_type
                    )

                result = await conn.fetchrow(
                    """
                    INSERT INTO tenant_payment_providers (
                        tenant_id,
                        provider_name,
                        provider_type,
                        configuration,
                        credentials,
                        is_default,
                        is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, true)
                    RETURNING id
                    """,
                    tenant_id,
                    provider_name,
                    provider_type,
                    json.dumps(configuration),
                    json.dumps(credentials),  # Should be encrypted in production
                    is_default
                )

                logger.info(f"Added payment provider {provider_name} for tenant {tenant_id}")
                return str(result['id'])

        except Exception as e:
            logger.error(f"Error adding payment provider: {str(e)}")
            return None

    async def get_subscription(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get active subscription for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT *
                    FROM tenant_subscriptions
                    WHERE tenant_id = $1 AND status = 'active'
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    tenant_id
                )

                if not row:
                    return None

                return {
                    'id': str(row['id']),
                    'plan_name': row['plan_name'],
                    'plan_type': row['plan_type'],
                    'status': row['status'],
                    'billing_cycle': row['billing_cycle'],
                    'price': float(row['price_per_cycle']) if row['price_per_cycle'] else 0,
                    'currency': row['currency'],
                    'current_period_start': row['current_period_start'].isoformat() if row['current_period_start'] else None,
                    'current_period_end': row['current_period_end'].isoformat() if row['current_period_end'] else None,
                    'metadata': row['metadata'] or {}
                }

        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            return None

    async def create_subscription(
        self,
        tenant_id: UUID,
        plan_name: str,
        plan_type: str,
        billing_cycle: str,
        price: Decimal
    ) -> Optional[str]:
        """Create a new subscription for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                # Cancel existing active subscriptions
                await conn.execute(
                    """
                    UPDATE tenant_subscriptions
                    SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = $1 AND status = 'active'
                    """,
                    tenant_id
                )

                # Create new subscription
                result = await conn.fetchrow(
                    """
                    INSERT INTO tenant_subscriptions (
                        tenant_id,
                        plan_name,
                        plan_type,
                        billing_cycle,
                        price_per_cycle,
                        current_period_start,
                        current_period_end
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP + INTERVAL '1 ' || $4
                    )
                    RETURNING id
                    """,
                    tenant_id,
                    plan_name,
                    plan_type,
                    billing_cycle,
                    price
                )

                logger.info(f"Created subscription {plan_name} for tenant {tenant_id}")
                return str(result['id'])

        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None

    async def check_feature_enabled(
        self,
        tenant_id: UUID,
        feature_name: str
    ) -> bool:
        """Check if a specific feature is enabled for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT is_enabled
                    FROM tenant_features
                    WHERE tenant_id = $1 AND feature_name = $2
                    """,
                    tenant_id,
                    feature_name
                )

                return result if result is not None else False

        except Exception as e:
            logger.error(f"Error checking feature: {str(e)}")
            return False