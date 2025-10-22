"""
Model Usage Tracking Service
Tracks all LLM requests for analytics, billing, and rate limit monitoring
"""
import asyncio
import asyncpg
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

# Cost per 1M tokens (approximate, adjust based on actual pricing)
COST_PER_MILLION_TOKENS = {
    'groq': {
        'llama-3.3-70b-versatile': {'input': 0.59, 'output': 0.79},
        'llama-3.1-70b-versatile': {'input': 0.59, 'output': 0.79},
        'mixtral-8x7b-32768': {'input': 0.24, 'output': 0.24},
    },
    'openrouter': {
        'deepseek/deepseek-r1': {'input': 0.55, 'output': 2.19},
        'anthropic/claude-3.5-sonnet': {'input': 3.0, 'output': 15.0},
        'google/gemini-pro-1.5': {'input': 1.25, 'output': 5.0},
    },
    'llm7': {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 5.0, 'output': 15.0},
        'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
    },
    'local': {
        'default': {'input': 0.0, 'output': 0.0}
    }
}


class ModelUsageTracker:
    """
    Async service to track LLM usage in real-time
    """
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
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
            logger.info("✅ ModelUsageTracker initialized with connection pool")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ModelUsageTracker: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self._initialized = False
            logger.info("ModelUsageTracker connection pool closed")
    
    def calculate_cost(
        self,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """
        Calculate estimated cost for a request
        """
        try:
            # Get pricing for provider/model
            provider_pricing = COST_PER_MILLION_TOKENS.get(provider, {})
            model_pricing = provider_pricing.get(model_name, provider_pricing.get('default', {'input': 0.0, 'output': 0.0}))
            
            # Calculate cost per token
            input_cost = (input_tokens / 1_000_000) * model_pricing['input']
            output_cost = (output_tokens / 1_000_000) * model_pricing['output']
            
            total_cost = Decimal(str(input_cost + output_cost)).quantize(Decimal('0.000001'))
            return total_cost
            
        except Exception as e:
            logger.warning(f"Failed to calculate cost: {e}")
            return Decimal('0.0')
    
    async def track_request(
        self,
        tenant_id: str,
        provider: str,
        model_name: str,
        endpoint: str,
        user_id: Optional[str] = None,
        latency_ms: Optional[int] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        status: str = 'success',
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track a single LLM request (async, non-blocking)
        
        Args:
            tenant_id: Tenant UUID
            provider: 'groq', 'openrouter', 'llm7', or 'local'
            model_name: Name of the model used
            endpoint: API endpoint (e.g., '/api/chat')
            user_id: Optional user UUID
            latency_ms: Response time in milliseconds
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            status: 'success', 'error', 'rate_limit', 'timeout'
            error_message: Error description if status != 'success'
            metadata: Additional metadata (JSONB)
        
        Returns:
            Usage record ID (UUID) or None if failed
        """
        if not self._initialized:
            logger.warning("ModelUsageTracker not initialized, skipping tracking")
            return None
        
        try:
            # Calculate cost
            estimated_cost = self.calculate_cost(provider, model_name, input_tokens, output_tokens)
            
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Insert asynchronously (fire and forget)
            async with self.db_pool.acquire() as conn:
                usage_id = await conn.fetchval(
                    """
                    SELECT track_model_usage(
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    )
                    """,
                    tenant_id,
                    provider,
                    model_name,
                    request_id,
                    endpoint,
                    user_id,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    status,
                    error_message,
                    float(estimated_cost),
                    metadata or {}
                )
                
                logger.debug(
                    f"✓ Tracked: {provider}/{model_name} - "
                    f"{input_tokens + output_tokens} tokens, "
                    f"{latency_ms}ms, ${estimated_cost}"
                )
                
                return str(usage_id)
                
        except Exception as e:
            logger.error(f"Failed to track usage: {e}")
            return None
    
    async def get_tenant_usage_stats(
        self,
        tenant_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a tenant
        
        Args:
            tenant_id: Tenant UUID
            hours: Time window in hours (default: 24)
        
        Returns:
            Dictionary with usage stats
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query real-time stats
                stats = await conn.fetch(
                    """
                    SELECT 
                        provider,
                        model_name,
                        COUNT(*) as total_requests,
                        COUNT(*) FILTER (WHERE status = 'success') as successful_requests,
                        COUNT(*) FILTER (WHERE status = 'rate_limit') as rate_limited_requests,
                        SUM(total_tokens) as total_tokens,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        AVG(latency_ms) as avg_latency_ms,
                        MIN(latency_ms) as min_latency_ms,
                        MAX(latency_ms) as max_latency_ms,
                        SUM(estimated_cost_usd) as total_cost_usd,
                        MAX(timestamp) as last_used_at
                    FROM model_usage_stats
                    WHERE tenant_id = $1
                      AND timestamp >= NOW() - INTERVAL '1 hour' * $2
                    GROUP BY provider, model_name
                    ORDER BY total_requests DESC
                    """,
                    tenant_id,
                    hours
                )
                
                # Format results
                result = {
                    'tenant_id': tenant_id,
                    'time_window_hours': hours,
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost_usd': 0.0,
                    'by_provider': {},
                    'by_model': []
                }
                
                for row in stats:
                    provider = row['provider']
                    model_name = row['model_name']
                    
                    # Add to totals
                    result['total_requests'] += row['total_requests']
                    result['total_tokens'] += row['total_tokens'] or 0
                    result['total_cost_usd'] += float(row['total_cost_usd'] or 0)
                    
                    # Group by provider
                    if provider not in result['by_provider']:
                        result['by_provider'][provider] = {
                            'requests': 0,
                            'tokens': 0,
                            'cost_usd': 0.0,
                            'models': []
                        }
                    
                    result['by_provider'][provider]['requests'] += row['total_requests']
                    result['by_provider'][provider]['tokens'] += row['total_tokens'] or 0
                    result['by_provider'][provider]['cost_usd'] += float(row['total_cost_usd'] or 0)
                    result['by_provider'][provider]['models'].append(model_name)
                    
                    # Add to model list
                    result['by_model'].append({
                        'provider': provider,
                        'model': model_name,
                        'requests': row['total_requests'],
                        'successful': row['successful_requests'],
                        'rate_limited': row['rate_limited_requests'],
                        'tokens': {
                            'total': row['total_tokens'] or 0,
                            'input': row['input_tokens'] or 0,
                            'output': row['output_tokens'] or 0
                        },
                        'latency_ms': {
                            'avg': float(row['avg_latency_ms'] or 0),
                            'min': row['min_latency_ms'],
                            'max': row['max_latency_ms']
                        },
                        'cost_usd': float(row['total_cost_usd'] or 0),
                        'last_used_at': row['last_used_at'].isoformat() if row['last_used_at'] else None
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get tenant usage stats: {e}")
            return {
                'error': str(e),
                'tenant_id': tenant_id
            }
    
    async def check_rate_limit_status(
        self,
        tenant_id: str,
        provider: str,
        time_window_hours: int = 24,
        max_requests: int = 14400  # Groq free tier: 14,400/day
    ) -> Dict[str, Any]:
        """
        Check if tenant is approaching rate limits
        
        Args:
            tenant_id: Tenant UUID
            provider: Provider to check
            time_window_hours: Time window (default: 24h)
            max_requests: Maximum requests allowed
        
        Returns:
            Rate limit status information
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Count requests in time window
                result = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as request_count,
                        COUNT(*) FILTER (WHERE status = 'rate_limit') as rate_limited_count
                    FROM model_usage_stats
                    WHERE tenant_id = $1
                      AND provider = $2
                      AND timestamp >= NOW() - INTERVAL '1 hour' * $3
                    """,
                    tenant_id,
                    provider,
                    time_window_hours
                )
                
                request_count = result['request_count']
                rate_limited_count = result['rate_limited_count']
                
                # Calculate percentage used
                usage_percentage = (request_count / max_requests) * 100 if max_requests > 0 else 0
                
                # Determine status
                if usage_percentage >= 95:
                    status = 'critical'
                    should_failover = True
                elif usage_percentage >= 80:
                    status = 'warning'
                    should_failover = True
                elif usage_percentage >= 50:
                    status = 'normal'
                    should_failover = False
                else:
                    status = 'healthy'
                    should_failover = False
                
                return {
                    'tenant_id': tenant_id,
                    'provider': provider,
                    'time_window_hours': time_window_hours,
                    'request_count': request_count,
                    'rate_limited_count': rate_limited_count,
                    'max_requests': max_requests,
                    'remaining_requests': max_requests - request_count,
                    'usage_percentage': round(usage_percentage, 2),
                    'status': status,
                    'should_failover': should_failover
                }
                
        except Exception as e:
            logger.error(f"Failed to check rate limit status: {e}")
            return {
                'error': str(e),
                'tenant_id': tenant_id,
                'provider': provider,
                'status': 'unknown'
            }


# Global instance
_usage_tracker: Optional[ModelUsageTracker] = None


async def get_usage_tracker() -> ModelUsageTracker:
    """Get or create global usage tracker instance"""
    global _usage_tracker
    
    if _usage_tracker is None:
        _usage_tracker = ModelUsageTracker()
        await _usage_tracker.initialize()
    
    return _usage_tracker


async def track_usage(
    tenant_id: str,
    provider: str,
    model_name: str,
    endpoint: str,
    **kwargs
) -> Optional[str]:
    """
    Convenience function to track usage
    
    Usage:
        await track_usage(
            tenant_id="...",
            provider="groq",
            model_name="llama-3.3-70b-versatile",
            endpoint="/api/chat",
            latency_ms=1500,
            input_tokens=100,
            output_tokens=200,
            status="success"
        )
    """
    tracker = await get_usage_tracker()
    return await tracker.track_request(
        tenant_id=tenant_id,
        provider=provider,
        model_name=model_name,
        endpoint=endpoint,
        **kwargs
    )
