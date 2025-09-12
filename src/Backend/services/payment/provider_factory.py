"""
Payment Provider Factory Pattern
Manages creation and caching of tenant-specific payment provider instances
Following SOLID principles and clean architecture
"""

import asyncio
import logging
from typing import Dict, Optional, Any, Type
from datetime import datetime, timezone, timedelta
from uuid import UUID
import asyncpg
from abc import ABC, abstractmethod

from .base import BasePaymentProvider, PaymentError
from .clover_provider import CloverProvider
from .moneris_provider import MonerisProvider
from .interac_provider import InteracProvider
from ..security.credential_manager import CredentialManager, CredentialType

logger = logging.getLogger(__name__)


class ProviderType:
    """Supported payment provider types"""
    CLOVER = "clover"
    MONERIS = "moneris"
    INTERAC = "interac"
    STRIPE = "stripe"
    SQUARE = "square"
    NUVEI = "nuvei"
    PAYBRIGHT = "paybright"


class ProviderRegistry:
    """Registry of available payment provider implementations"""
    
    _providers: Dict[str, Type[BasePaymentProvider]] = {
        ProviderType.CLOVER: CloverProvider,
        ProviderType.MONERIS: MonerisProvider,
        ProviderType.INTERAC: InteracProvider,
        # Additional providers can be registered here
    }
    
    @classmethod
    def register(cls, provider_type: str, provider_class: Type[BasePaymentProvider]):
        """Register a new payment provider implementation"""
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get(cls, provider_type: str) -> Optional[Type[BasePaymentProvider]]:
        """Get a payment provider implementation class"""
        return cls._providers.get(provider_type)
    
    @classmethod
    def list_available(cls) -> list:
        """List all available provider types"""
        return list(cls._providers.keys())


class TenantProviderConfig:
    """Configuration for a tenant's payment provider"""
    
    def __init__(self, config_data: dict):
        self.id = config_data.get('id')
        self.tenant_id = config_data.get('tenant_id')
        self.provider_id = config_data.get('provider_id')
        self.provider_type = config_data.get('provider_type')
        self.environment = config_data.get('environment', 'sandbox')
        self.merchant_id = config_data.get('merchant_id')
        self.store_id = config_data.get('store_id')
        self.location_id = config_data.get('location_id')
        self.is_active = config_data.get('is_active', True)
        self.is_primary = config_data.get('is_primary', False)
        self.capabilities = config_data.get('capabilities', {})
        self.settings = config_data.get('settings', {})
        self.platform_fee_percentage = config_data.get('platform_fee_percentage', 0.02)
        self.platform_fee_fixed = config_data.get('platform_fee_fixed', 0.0)
        self.daily_limit = config_data.get('daily_limit')
        self.transaction_limit = config_data.get('transaction_limit')
        self.health_status = config_data.get('health_status', 'unknown')
        self.last_health_check = config_data.get('last_health_check')
        
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        if not self.is_active:
            return False
        if self.health_status == 'unavailable':
            return False
        # Check if health check is stale (older than 5 minutes)
        if self.last_health_check:
            if datetime.now(timezone.utc) - self.last_health_check > timedelta(minutes=5):
                return False
        return True


class PaymentProviderFactory:
    """
    Factory for creating and managing tenant-specific payment provider instances
    Implements caching, health checking, and failover logic
    """
    
    def __init__(self, db_pool: asyncpg.Pool, credential_manager: CredentialManager):
        self.db_pool = db_pool
        self.credential_manager = credential_manager
        self.logger = logger
        
        # Cache for provider instances
        # Structure: {tenant_id: {provider_type: {instance, created_at, config}}}
        self._provider_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Cache TTL
        self._cache_ttl = timedelta(minutes=30)
        
        # Lock for thread-safe cache operations
        self._cache_lock = asyncio.Lock()
    
    async def get_provider(
        self,
        tenant_id: str,
        provider_type: Optional[str] = None,
        prefer_primary: bool = True
    ) -> BasePaymentProvider:
        """
        Get a payment provider instance for a tenant
        
        Args:
            tenant_id: Tenant UUID
            provider_type: Specific provider type to get
            prefer_primary: Whether to prefer the primary provider
            
        Returns:
            Payment provider instance
            
        Raises:
            PaymentError: If no suitable provider is found
        """
        # Check cache first
        cached_provider = await self._get_cached_provider(tenant_id, provider_type)
        if cached_provider:
            return cached_provider
        
        # Load provider configuration from database
        config = await self._load_provider_config(tenant_id, provider_type, prefer_primary)
        if not config:
            raise PaymentError(
                f"No active payment provider found for tenant {tenant_id}",
                error_code="NO_PROVIDER_CONFIGURED"
            )
        
        # Create provider instance
        provider = await self._create_provider_instance(config)
        
        # Cache the provider
        await self._cache_provider(tenant_id, config.provider_type, provider, config)
        
        return provider
    
    async def get_all_providers(self, tenant_id: str) -> Dict[str, BasePaymentProvider]:
        """
        Get all active payment providers for a tenant
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Dictionary of provider_type -> provider instance
        """
        providers = {}
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT tpp.*, pp.provider_type
                FROM tenant_payment_providers tpp
                JOIN payment_providers pp ON tpp.provider_id = pp.id
                WHERE tpp.tenant_id = $1 AND tpp.is_active = true
            """, tenant_id)
            
            for row in rows:
                config = TenantProviderConfig(dict(row))
                try:
                    provider = await self._create_provider_instance(config)
                    providers[config.provider_type] = provider
                except Exception as e:
                    self.logger.error(f"Failed to create provider {config.provider_type}: {e}")
        
        return providers
    
    async def _load_provider_config(
        self,
        tenant_id: str,
        provider_type: Optional[str],
        prefer_primary: bool
    ) -> Optional[TenantProviderConfig]:
        """Load provider configuration from database"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT tpp.*, pp.provider_type, pp.capabilities as provider_capabilities
                FROM tenant_payment_providers tpp
                JOIN payment_providers pp ON tpp.provider_id = pp.id
                WHERE tpp.tenant_id = $1 AND tpp.is_active = true
            """
            params = [tenant_id]
            
            if provider_type:
                query += " AND pp.provider_type = $2"
                params.append(provider_type)
            
            if prefer_primary:
                query += " ORDER BY tpp.is_primary DESC, tpp.created_at"
            else:
                query += " ORDER BY tpp.health_status = 'healthy' DESC, tpp.created_at"
            
            query += " LIMIT 1"
            
            row = await conn.fetchrow(query, *params)
            
            if row:
                return TenantProviderConfig(dict(row))
            
            return None
    
    async def _create_provider_instance(
        self,
        config: TenantProviderConfig
    ) -> BasePaymentProvider:
        """Create a payment provider instance with credentials"""
        
        # Get provider class from registry
        provider_class = ProviderRegistry.get(config.provider_type)
        if not provider_class:
            raise PaymentError(
                f"Provider type {config.provider_type} not supported",
                error_code="UNSUPPORTED_PROVIDER"
            )
        
        # Retrieve credentials from secure storage
        credential_type_map = {
            ProviderType.CLOVER: CredentialType.CLOVER_API,
            ProviderType.MONERIS: CredentialType.MONERIS_API,
            ProviderType.INTERAC: CredentialType.INTERAC_API,
            ProviderType.STRIPE: CredentialType.STRIPE_API,
            ProviderType.SQUARE: CredentialType.SQUARE_API,
            ProviderType.NUVEI: CredentialType.NUVEI_API,
        }
        
        credential_type = credential_type_map.get(config.provider_type)
        if not credential_type:
            raise PaymentError(
                f"No credential type mapping for {config.provider_type}",
                error_code="CREDENTIAL_TYPE_MISSING"
            )
        
        credentials = await self.credential_manager.retrieve_credential(
            config.tenant_id,
            config.provider_type,
            credential_type
        )
        
        if not credentials:
            raise PaymentError(
                f"No credentials found for tenant {config.tenant_id}, provider {config.provider_type}",
                error_code="CREDENTIALS_NOT_FOUND"
            )
        
        # Merge configuration
        provider_config = {
            **credentials,
            **config.settings,
            'tenant_id': config.tenant_id,
            'tenant_provider_id': config.id,
            'environment': config.environment,
            'merchant_id': config.merchant_id or credentials.get('merchant_id'),
            'store_id': config.store_id or credentials.get('store_id'),
            'location_id': config.location_id or credentials.get('location_id'),
            'platform_fee_percentage': config.platform_fee_percentage,
            'platform_fee_fixed': config.platform_fee_fixed,
            'capabilities': config.capabilities,
            'daily_limit': config.daily_limit,
            'transaction_limit': config.transaction_limit
        }
        
        # Create provider instance
        provider = provider_class(provider_config)
        
        # Set tenant context
        provider.tenant_id = config.tenant_id
        provider.tenant_provider_id = config.id
        
        return provider
    
    async def _get_cached_provider(
        self,
        tenant_id: str,
        provider_type: Optional[str]
    ) -> Optional[BasePaymentProvider]:
        """Get provider from cache if available and not expired"""
        async with self._cache_lock:
            tenant_cache = self._provider_cache.get(tenant_id)
            if not tenant_cache:
                return None
            
            # If specific provider type requested
            if provider_type:
                provider_data = tenant_cache.get(provider_type)
                if provider_data:
                    created_at = provider_data.get('created_at')
                    if datetime.now(timezone.utc) - created_at < self._cache_ttl:
                        return provider_data.get('instance')
                    else:
                        # Remove expired entry
                        del tenant_cache[provider_type]
            else:
                # Return any available cached provider (prefer primary)
                for ptype, provider_data in tenant_cache.items():
                    created_at = provider_data.get('created_at')
                    if datetime.now(timezone.utc) - created_at < self._cache_ttl:
                        config = provider_data.get('config')
                        if config and config.is_primary:
                            return provider_data.get('instance')
                
                # If no primary, return first available
                for ptype, provider_data in tenant_cache.items():
                    created_at = provider_data.get('created_at')
                    if datetime.now(timezone.utc) - created_at < self._cache_ttl:
                        return provider_data.get('instance')
        
        return None
    
    async def _cache_provider(
        self,
        tenant_id: str,
        provider_type: str,
        provider: BasePaymentProvider,
        config: TenantProviderConfig
    ):
        """Cache a provider instance"""
        async with self._cache_lock:
            if tenant_id not in self._provider_cache:
                self._provider_cache[tenant_id] = {}
            
            self._provider_cache[tenant_id][provider_type] = {
                'instance': provider,
                'created_at': datetime.now(timezone.utc),
                'config': config
            }
    
    async def invalidate_cache(
        self,
        tenant_id: Optional[str] = None,
        provider_type: Optional[str] = None
    ):
        """
        Invalidate cached providers
        
        Args:
            tenant_id: Specific tenant to invalidate (None for all)
            provider_type: Specific provider type to invalidate (None for all)
        """
        async with self._cache_lock:
            if tenant_id:
                if tenant_id in self._provider_cache:
                    if provider_type:
                        # Remove specific provider for tenant
                        if provider_type in self._provider_cache[tenant_id]:
                            del self._provider_cache[tenant_id][provider_type]
                    else:
                        # Remove all providers for tenant
                        del self._provider_cache[tenant_id]
            else:
                # Clear entire cache
                self._provider_cache.clear()
    
    async def health_check(self, tenant_id: str, provider_type: str) -> Dict[str, Any]:
        """
        Perform health check on a provider
        
        Args:
            tenant_id: Tenant UUID
            provider_type: Provider type to check
            
        Returns:
            Health check results
        """
        start_time = datetime.now(timezone.utc)
        health_result = {
            'provider_type': provider_type,
            'tenant_id': tenant_id,
            'checked_at': start_time.isoformat(),
            'status': 'unknown',
            'response_time_ms': None,
            'error': None
        }
        
        try:
            # Get provider instance
            provider = await self.get_provider(tenant_id, provider_type)
            
            # Perform health check (implement in each provider)
            if hasattr(provider, 'health_check'):
                is_healthy = await provider.health_check()
                health_result['status'] = 'healthy' if is_healthy else 'degraded'
            else:
                # Basic connectivity check
                health_result['status'] = 'healthy'
            
            # Calculate response time
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            health_result['response_time_ms'] = round(response_time)
            
            # Update database
            await self._update_health_status(
                tenant_id,
                provider_type,
                health_result['status'],
                response_time
            )
            
        except Exception as e:
            health_result['status'] = 'unavailable'
            health_result['error'] = str(e)
            
            # Update database
            await self._update_health_status(
                tenant_id,
                provider_type,
                'unavailable'
            )
        
        return health_result
    
    async def _update_health_status(
        self,
        tenant_id: str,
        provider_type: str,
        status: str,
        response_time_ms: Optional[float] = None
    ):
        """Update provider health status in database"""
        async with self.db_pool.acquire() as conn:
            # Update tenant_payment_providers
            await conn.execute("""
                UPDATE tenant_payment_providers tpp
                SET health_status = $1,
                    last_health_check = CURRENT_TIMESTAMP
                FROM payment_providers pp
                WHERE tpp.provider_id = pp.id
                AND tpp.tenant_id = $2
                AND pp.provider_type = $3
            """, status, tenant_id, provider_type)
            
            # Log health metric
            if response_time_ms is not None:
                await conn.execute("""
                    INSERT INTO payment_provider_health_metrics (
                        tenant_provider_id, response_time_ms, 
                        is_successful, checked_at
                    )
                    SELECT tpp.id, $1, $2, CURRENT_TIMESTAMP
                    FROM tenant_payment_providers tpp
                    JOIN payment_providers pp ON tpp.provider_id = pp.id
                    WHERE tpp.tenant_id = $3 AND pp.provider_type = $4
                    LIMIT 1
                """, int(response_time_ms), status == 'healthy', tenant_id, provider_type)
    
    async def get_failover_provider(
        self,
        tenant_id: str,
        failed_provider_type: str
    ) -> Optional[BasePaymentProvider]:
        """
        Get a failover provider when primary fails
        
        Args:
            tenant_id: Tenant UUID
            failed_provider_type: The provider type that failed
            
        Returns:
            Alternative provider instance or None
        """
        async with self.db_pool.acquire() as conn:
            # Find alternative healthy provider
            row = await conn.fetchrow("""
                SELECT tpp.*, pp.provider_type
                FROM tenant_payment_providers tpp
                JOIN payment_providers pp ON tpp.provider_id = pp.id
                WHERE tpp.tenant_id = $1 
                AND tpp.is_active = true
                AND pp.provider_type != $2
                AND tpp.health_status = 'healthy'
                ORDER BY tpp.is_primary DESC, tpp.created_at
                LIMIT 1
            """, tenant_id, failed_provider_type)
            
            if row:
                config = TenantProviderConfig(dict(row))
                try:
                    return await self._create_provider_instance(config)
                except Exception as e:
                    self.logger.error(f"Failed to create failover provider: {e}")
            
            return None