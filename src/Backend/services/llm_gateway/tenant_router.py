"""
Tenant-Aware LLM Router
Extends LLMRouter with per-tenant configuration and usage tracking

Features:
- Load tenant-specific API tokens from database
- Respect tenant's preferred provider setting
- Auto-failover on rate limits (if enabled by tenant)
- Track all requests to model_usage_stats table
- Cost calculation and monitoring
"""

import asyncio
import asyncpg
import logging
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .router import LLMRouter
from .types import RequestContext, CompletionResult, TaskType
from .providers import (
    BaseProvider,
    OpenRouterProvider,
    GroqProvider,
    LLM7Provider,
    LLM7GPT4Mini,
    LLM7GPT4,
    LLM7Claude,
    LocalProvider
)
from services.model_usage_tracker import get_usage_tracker

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123')
}


class TenantLLMRouter:
    """
    Tenant-aware LLM router with per-tenant configuration and usage tracking
    
    Usage:
        router = TenantLLMRouter()
        await router.initialize()
        
        # Complete with tenant context
        result = await router.complete_for_tenant(
            tenant_id="...",
            messages=[{"role": "user", "content": "Hello"}],
            context=RequestContext(task_type=TaskType.CHAT, estimated_tokens=100),
            endpoint="/api/chat"
        )
    """
    
    def __init__(self):
        """Initialize tenant-aware router"""
        self.db_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        
        # Cache for tenant configurations (expires after 5 minutes)
        self._tenant_config_cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # 5 minutes
        
        logger.info("TenantLLMRouter created")
    
    async def initialize(self):
        """Initialize database connection pool"""
        if self._initialized:
            return
        
        try:
            self.db_pool = await asyncpg.create_pool(
                **DB_CONFIG,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            self._initialized = True
            logger.info("✅ TenantLLMRouter initialized with database connection")
        except Exception as e:
            logger.error(f"❌ Failed to initialize TenantLLMRouter: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self._initialized = False
            logger.info("TenantLLMRouter connection pool closed")
    
    async def _load_tenant_config(self, tenant_id: str) -> Dict:
        """
        Load tenant configuration from database (with caching)
        
        Returns:
            {
                'llm_tokens': {
                    'groq': 'gsk_...',
                    'openrouter': 'sk-or-...',
                    'llm7': 'sk-...'
                },
                'inference_config': {
                    'preferred_provider': 'groq',
                    'auto_failover': true,
                    'preferred_models': {
                        'groq': 'llama-3.3-70b-versatile',
                        'openrouter': 'deepseek/deepseek-r1',
                        'llm7': 'gpt-4o-mini'
                    }
                }
            }
        """
        # Check cache
        now = datetime.now()
        if tenant_id in self._tenant_config_cache:
            cache_age = (now - self._cache_timestamps.get(tenant_id, now)).total_seconds()
            if cache_age < self._cache_ttl_seconds:
                logger.debug(f"Using cached config for tenant {tenant_id}")
                return self._tenant_config_cache[tenant_id]
        
        # Load from database
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT llm_tokens, inference_config
                    FROM tenants
                    WHERE id = $1
                    """,
                    tenant_id
                )
                
                if not row:
                    logger.warning(f"Tenant {tenant_id} not found, using defaults")
                    return {
                        'llm_tokens': {},
                        'inference_config': {
                            'preferred_provider': 'groq',
                            'auto_failover': True,
                            'preferred_models': {}
                        }
                    }
                
                config = {
                    'llm_tokens': row['llm_tokens'] or {},
                    'inference_config': row['inference_config'] or {
                        'preferred_provider': 'groq',
                        'auto_failover': True,
                        'preferred_models': {}
                    }
                }
                
                # Update cache
                self._tenant_config_cache[tenant_id] = config
                self._cache_timestamps[tenant_id] = now
                
                logger.debug(f"Loaded config for tenant {tenant_id}: "
                           f"preferred={config['inference_config'].get('preferred_provider')}, "
                           f"has_tokens={list(config['llm_tokens'].keys())}")
                
                return config
                
        except Exception as e:
            logger.error(f"Failed to load tenant config for {tenant_id}: {e}")
            # Return defaults on error
            return {
                'llm_tokens': {},
                'inference_config': {
                    'preferred_provider': 'groq',
                    'auto_failover': True,
                    'preferred_models': {}
                }
            }
    
    def _create_tenant_router(
        self,
        tenant_id: str,
        tenant_tokens: Dict[str, str],
        preferred_models: Dict[str, str]
    ) -> LLMRouter:
        """
        Create a router instance configured for a specific tenant
        
        Args:
            tenant_id: Tenant UUID
            tenant_tokens: Dict mapping provider to API token
            preferred_models: Dict mapping provider to preferred model
        
        Returns:
            Configured LLMRouter instance
        """
        router = LLMRouter()
        
        # Register Groq if tenant has token
        if tenant_tokens.get('groq'):
            try:
                groq = GroqProvider(api_key=tenant_tokens['groq'])
                
                # Set preferred model if specified
                if 'groq' in preferred_models:
                    groq.set_model(preferred_models['groq'])
                
                router.register_provider(groq)
                logger.debug(f"Registered Groq for tenant {tenant_id} with model {groq.config.model_name}")
            except Exception as e:
                logger.error(f"Failed to register Groq for tenant {tenant_id}: {e}")
        
        # Register OpenRouter if tenant has token
        if tenant_tokens.get('openrouter'):
            try:
                openrouter = OpenRouterProvider(api_key=tenant_tokens['openrouter'])
                
                # Set preferred model if specified
                if 'openrouter' in preferred_models:
                    openrouter.set_model(preferred_models['openrouter'])
                
                router.register_provider(openrouter)
                logger.debug(f"Registered OpenRouter for tenant {tenant_id} with model {openrouter.config.model_name}")
            except Exception as e:
                logger.error(f"Failed to register OpenRouter for tenant {tenant_id}: {e}")
        
        # Register LLM7 if tenant has token
        if tenant_tokens.get('llm7'):
            try:
                # Determine which LLM7 provider based on preferred model
                preferred_model = preferred_models.get('llm7', 'gpt-4o-mini')
                
                if 'gpt-4o-mini' in preferred_model:
                    llm7 = LLM7GPT4Mini(api_key=tenant_tokens['llm7'])
                elif 'gpt-4o' in preferred_model or 'gpt-4-turbo' in preferred_model:
                    llm7 = LLM7GPT4(api_key=tenant_tokens['llm7'])
                elif 'claude' in preferred_model:
                    llm7 = LLM7Claude(api_key=tenant_tokens['llm7'])
                else:
                    llm7 = LLM7GPT4Mini(api_key=tenant_tokens['llm7'])
                
                router.register_provider(llm7)
                logger.debug(f"Registered LLM7 for tenant {tenant_id} with model {llm7.config.model_name}")
            except Exception as e:
                logger.error(f"Failed to register LLM7 for tenant {tenant_id}: {e}")
        
        # Always register system-level providers as fallback
        # These use system environment variables (GROQ_API_KEY, etc.)
        try:
            # Try to register system Groq (if not already registered with tenant token)
            if not tenant_tokens.get('groq'):
                system_groq = GroqProvider()
                if system_groq.is_enabled:
                    router.register_provider(system_groq)
                    logger.debug(f"Registered system Groq as fallback for tenant {tenant_id}")
        except Exception as e:
            logger.debug(f"System Groq not available: {e}")
        
        try:
            # Try to register system OpenRouter
            if not tenant_tokens.get('openrouter'):
                system_or = OpenRouterProvider()
                if system_or.is_enabled:
                    router.register_provider(system_or)
                    logger.debug(f"Registered system OpenRouter as fallback for tenant {tenant_id}")
        except Exception as e:
            logger.debug(f"System OpenRouter not available: {e}")
        
        try:
            # Try to register system LLM7 (no auth required)
            if not tenant_tokens.get('llm7'):
                system_llm7 = LLM7GPT4Mini()
                if system_llm7.is_enabled:
                    router.register_provider(system_llm7)
                    logger.debug(f"Registered system LLM7 as fallback for tenant {tenant_id}")
        except Exception as e:
            logger.debug(f"System LLM7 not available: {e}")
        
        return router
    
    async def complete_for_tenant(
        self,
        tenant_id: str,
        messages: List[Dict],
        context: RequestContext,
        endpoint: str,
        user_id: Optional[str] = None,
        max_retries: int = 3
    ) -> CompletionResult:
        """
        Generate completion for a specific tenant with usage tracking
        
        Args:
            tenant_id: Tenant UUID
            messages: Chat messages in OpenAI format
            context: Request context
            endpoint: API endpoint (e.g., '/api/chat')
            user_id: Optional user UUID
            max_retries: Maximum retry attempts
        
        Returns:
            CompletionResult with response and metadata
        
        Raises:
            AllProvidersExhaustedError: If all providers fail
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Load tenant configuration
            config = await self._load_tenant_config(tenant_id)
            tenant_tokens = config.get('llm_tokens', {})
            inference_config = config.get('inference_config', {})
            preferred_provider = inference_config.get('preferred_provider', 'groq')
            preferred_models = inference_config.get('preferred_models', {})
            auto_failover = inference_config.get('auto_failover', True)
            
            # Create tenant-specific router
            router = self._create_tenant_router(tenant_id, tenant_tokens, preferred_models)
            
            # If preferred provider specified, try it first
            if preferred_provider and auto_failover:
                # Modify context to prefer specific provider
                # This will be handled by router's scoring algorithm
                logger.info(f"Tenant {tenant_id} prefers provider: {preferred_provider}")
            
            # Generate completion
            result = await router.complete(
                messages=messages,
                context=context,
                max_retries=max_retries if auto_failover else 1
            )
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Track usage
            tracker = await get_usage_tracker()
            await tracker.track_request(
                tenant_id=tenant_id,
                provider=self._normalize_provider_name(result.provider),
                model_name=result.model,
                endpoint=endpoint,
                user_id=user_id,
                latency_ms=latency_ms,
                input_tokens=result.tokens_input,
                output_tokens=result.tokens_output,
                status='success',
                metadata={
                    'cached': result.cached,
                    'finish_reason': result.finish_reason,
                    'selection_reason': router.request_history[-1].get('selection_reason') if router.request_history else None
                }
            )
            
            logger.info(
                f"✓ Tenant {tenant_id}: {result.provider}/{result.model} - "
                f"{result.tokens_input}→{result.tokens_output} tokens, "
                f"${result.cost:.6f}, {latency_ms}ms"
            )
            
            return result
            
        except Exception as e:
            # Track failure
            latency_ms = int((time.time() - start_time) * 1000)
            
            tracker = await get_usage_tracker()
            await tracker.track_request(
                tenant_id=tenant_id,
                provider='unknown',
                model_name='unknown',
                endpoint=endpoint,
                user_id=user_id,
                latency_ms=latency_ms,
                status='error',
                error_message=str(e)
            )
            
            logger.error(f"Failed to complete request for tenant {tenant_id}: {e}")
            raise
    
    def _normalize_provider_name(self, provider_name: str) -> str:
        """
        Normalize provider name to database format
        
        Examples:
            'OpenRouter (DeepSeek R1)' → 'openrouter'
            'Groq (Llama 3.3 70B)' → 'groq'
            'LLM7 GPT-4o Mini' → 'llm7'
            'Local Llama' → 'local'
        """
        name_lower = provider_name.lower()
        
        if 'openrouter' in name_lower:
            return 'openrouter'
        elif 'groq' in name_lower:
            return 'groq'
        elif 'llm7' in name_lower:
            return 'llm7'
        elif 'local' in name_lower:
            return 'local'
        else:
            return 'unknown'
    
    async def get_tenant_usage_stats(
        self,
        tenant_id: str,
        hours: int = 24
    ) -> Dict:
        """
        Get usage statistics for a tenant
        
        Args:
            tenant_id: Tenant UUID
            hours: Time window in hours
        
        Returns:
            Usage statistics dictionary
        """
        tracker = await get_usage_tracker()
        return await tracker.get_tenant_usage_stats(tenant_id, hours)
    
    async def check_rate_limit_status(
        self,
        tenant_id: str,
        provider: str,
        time_window_hours: int = 24,
        max_requests: int = 14400
    ) -> Dict:
        """
        Check rate limit status for tenant/provider
        
        Args:
            tenant_id: Tenant UUID
            provider: Provider name
            time_window_hours: Time window
            max_requests: Max allowed requests
        
        Returns:
            Rate limit status dictionary
        """
        tracker = await get_usage_tracker()
        return await tracker.check_rate_limit_status(
            tenant_id,
            provider,
            time_window_hours,
            max_requests
        )
    
    def invalidate_cache(self, tenant_id: Optional[str] = None):
        """
        Invalidate tenant configuration cache
        
        Args:
            tenant_id: Specific tenant to invalidate, or None for all
        """
        if tenant_id:
            if tenant_id in self._tenant_config_cache:
                del self._tenant_config_cache[tenant_id]
                del self._cache_timestamps[tenant_id]
                logger.info(f"Invalidated cache for tenant {tenant_id}")
        else:
            self._tenant_config_cache.clear()
            self._cache_timestamps.clear()
            logger.info("Invalidated all tenant configuration cache")


# Global instance
_tenant_router: Optional[TenantLLMRouter] = None


async def get_tenant_router() -> TenantLLMRouter:
    """Get or create global tenant router instance"""
    global _tenant_router
    
    if _tenant_router is None:
        _tenant_router = TenantLLMRouter()
        await _tenant_router.initialize()
    
    return _tenant_router


async def complete_for_tenant(
    tenant_id: str,
    messages: List[Dict],
    task_type: TaskType,
    estimated_tokens: int,
    endpoint: str,
    **kwargs
) -> CompletionResult:
    """
    Convenience function for tenant-aware LLM completion
    
    Usage:
        result = await complete_for_tenant(
            tenant_id="...",
            messages=[{"role": "user", "content": "Hello"}],
            task_type=TaskType.CHAT,
            estimated_tokens=100,
            endpoint="/api/chat",
            user_id="..."
        )
    """
    router = await get_tenant_router()
    
    context = RequestContext(
        task_type=task_type,
        estimated_tokens=estimated_tokens,
        **kwargs
    )
    
    return await router.complete_for_tenant(
        tenant_id=tenant_id,
        messages=messages,
        context=context,
        endpoint=endpoint,
        user_id=kwargs.get('user_id')
    )
