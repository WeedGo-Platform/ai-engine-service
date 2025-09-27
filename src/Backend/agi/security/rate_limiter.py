"""
Rate Limiting System for AGI Platform
Implements various rate limiting strategies to prevent abuse
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib

from agi.core.database import get_db_manager
from agi.security.audit_logger import get_audit_logger, AuditEvent, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"  # Simple fixed time window
    SLIDING_WINDOW = "sliding_window"  # Sliding window with better accuracy
    TOKEN_BUCKET = "token_bucket"  # Token bucket for burst allowance
    LEAKY_BUCKET = "leaky_bucket"  # Leaky bucket for smooth rate limiting
    ADAPTIVE = "adaptive"  # Adaptive based on system load


class RateLimitScope(Enum):
    """Scopes for rate limiting"""
    GLOBAL = "global"  # System-wide limit
    USER = "user"  # Per-user limit
    IP = "ip"  # Per-IP address limit
    SESSION = "session"  # Per-session limit
    API_KEY = "api_key"  # Per-API key limit
    RESOURCE = "resource"  # Per-resource limit
    ACTION = "action"  # Per-action limit


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    name: str
    scope: RateLimitScope
    strategy: RateLimitStrategy
    limit: int  # Number of requests
    window_seconds: int  # Time window in seconds
    burst_size: Optional[int] = None  # For token bucket
    priority: int = 0  # Higher priority rules are checked first
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_key(self, identifier: str, resource: Optional[str] = None) -> str:
        """Generate cache key for this rule"""
        parts = [self.name, self.scope.value, identifier]
        if resource:
            parts.append(resource)
        return ":".join(parts)


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until retry
    rule_name: Optional[str] = None
    reason: Optional[str] = None


class RateLimiter:
    """
    Comprehensive rate limiting system
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize rate limiter"""
        if not hasattr(self, '_initialized'):
            self.db_manager = None
            self._rules: Dict[str, RateLimitRule] = {}
            self._cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache
            self._cleanup_interval = 60  # Cleanup every minute
            self._cleanup_task = None
            self.audit_logger = None
            self._initialized = False
    
    async def initialize(self):
        """Initialize the rate limiting system"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Get database manager
                self.db_manager = await get_db_manager()
                
                # Get audit logger
                self.audit_logger = await get_audit_logger()
                
                # Create tables
                await self._create_tables()
                
                # Load default rules
                await self._load_default_rules()
                
                # Start cleanup task
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
                
                self._initialized = True
                logger.info("Rate limiter initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize rate limiter: {e}")
                raise
    
    async def _create_tables(self):
        """Create rate limiting tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS agi_rate_limit_rules (
                name TEXT PRIMARY KEY,
                scope TEXT NOT NULL,
                strategy TEXT NOT NULL,
                limit_value INTEGER NOT NULL,
                window_seconds INTEGER NOT NULL,
                burst_size INTEGER,
                priority INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT true,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_rate_limit_buckets (
                key TEXT PRIMARY KEY,
                tokens FLOAT NOT NULL,
                last_update TIMESTAMPTZ NOT NULL,
                metadata JSONB DEFAULT '{}'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_rate_limit_violations (
                id SERIAL PRIMARY KEY,
                rule_name TEXT NOT NULL,
                identifier TEXT NOT NULL,
                resource TEXT,
                attempts INTEGER NOT NULL,
                window_start TIMESTAMPTZ NOT NULL,
                window_end TIMESTAMPTZ NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for query in queries:
            await self.db_manager.execute(query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_rate_limit_rules_scope ON agi_rate_limit_rules(scope)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limit_buckets_last_update ON agi_rate_limit_buckets(last_update)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_rule ON agi_rate_limit_violations(rule_name)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_identifier ON agi_rate_limit_violations(identifier)"
        ]
        
        for index in indexes:
            await self.db_manager.execute(index)
    
    async def _load_default_rules(self):
        """Load default rate limit rules"""
        default_rules = [
            # Global system limits
            RateLimitRule(
                name="global_requests",
                scope=RateLimitScope.GLOBAL,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=10000,
                window_seconds=60  # 10k requests per minute globally
            ),
            
            # Per-user limits
            RateLimitRule(
                name="user_requests",
                scope=RateLimitScope.USER,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                limit=100,
                window_seconds=60,  # 100 requests per minute per user
                burst_size=20  # Allow bursts up to 20
            ),
            
            # Model invocation limits
            RateLimitRule(
                name="model_invocations",
                scope=RateLimitScope.USER,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=50,
                window_seconds=3600,  # 50 model calls per hour
                metadata={"resource_type": "model"}
            ),
            
            # Tool execution limits
            RateLimitRule(
                name="tool_executions",
                scope=RateLimitScope.USER,
                strategy=RateLimitStrategy.FIXED_WINDOW,
                limit=200,
                window_seconds=3600,  # 200 tool calls per hour
                metadata={"resource_type": "tool"}
            ),
            
            # IP-based limits
            RateLimitRule(
                name="ip_requests",
                scope=RateLimitScope.IP,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=500,
                window_seconds=60,  # 500 requests per minute per IP
                priority=1  # Check IP limits first
            ),
            
            # API key limits
            RateLimitRule(
                name="api_key_requests",
                scope=RateLimitScope.API_KEY,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                limit=1000,
                window_seconds=3600,  # 1000 requests per hour per API key
                burst_size=100
            )
        ]
        
        for rule in default_rules:
            await self.add_rule(rule)
            self._rules[rule.name] = rule
    
    async def add_rule(self, rule: RateLimitRule):
        """Add or update a rate limit rule"""
        await self.db_manager.execute(
            """
            INSERT INTO agi_rate_limit_rules (
                name, scope, strategy, limit_value, window_seconds,
                burst_size, priority, enabled, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (name) DO UPDATE SET
                scope = $2,
                strategy = $3,
                limit_value = $4,
                window_seconds = $5,
                burst_size = $6,
                priority = $7,
                enabled = $8,
                metadata = $9,
                updated_at = CURRENT_TIMESTAMP
            """,
            rule.name,
            rule.scope.value,
            rule.strategy.value,
            rule.limit,
            rule.window_seconds,
            rule.burst_size,
            rule.priority,
            rule.enabled,
            json.dumps(rule.metadata)
        )
        
        self._rules[rule.name] = rule
        logger.info(f"Added/updated rate limit rule: {rule.name}")
    
    async def check_rate_limit(
        self,
        identifier: str,
        scope: RateLimitScope = RateLimitScope.USER,
        resource: Optional[str] = None,
        increment: int = 1
    ) -> RateLimitResult:
        """
        Check if request is within rate limits
        
        Args:
            identifier: User ID, IP address, session ID, etc.
            scope: Scope to check
            resource: Optional resource identifier
            increment: Number of requests to count
        
        Returns:
            Rate limit result
        """
        # Get applicable rules
        rules = self._get_applicable_rules(scope, resource)
        
        # Sort by priority
        rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Check each rule
        for rule in rules:
            if not rule.enabled:
                continue
            
            result = await self._check_rule(rule, identifier, resource, increment)
            
            if not result.allowed:
                # Log rate limit violation
                await self._log_violation(rule, identifier, resource, increment)
                return result
        
        # All checks passed
        return RateLimitResult(
            allowed=True,
            remaining=float('inf'),
            reset_at=datetime.utcnow() + timedelta(seconds=60)
        )
    
    def _get_applicable_rules(self, scope: RateLimitScope, resource: Optional[str]) -> list:
        """Get rules applicable to the given scope and resource"""
        applicable = []
        
        for rule in self._rules.values():
            if rule.scope == scope:
                # Check if resource matches
                if resource and rule.metadata.get("resource_type"):
                    if rule.metadata["resource_type"] == resource:
                        applicable.append(rule)
                else:
                    applicable.append(rule)
        
        return applicable
    
    async def _check_rule(
        self,
        rule: RateLimitRule,
        identifier: str,
        resource: Optional[str],
        increment: int
    ) -> RateLimitResult:
        """Check a specific rate limit rule"""
        key = rule.get_key(identifier, resource)
        
        if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window(key, rule, increment)
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(key, rule, increment)
        elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(key, rule, increment)
        elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return await self._check_leaky_bucket(key, rule, increment)
        elif rule.strategy == RateLimitStrategy.ADAPTIVE:
            return await self._check_adaptive(key, rule, increment)
        else:
            logger.warning(f"Unknown strategy: {rule.strategy}")
            return RateLimitResult(allowed=True, remaining=rule.limit, reset_at=datetime.utcnow())
    
    async def _check_fixed_window(
        self,
        key: str,
        rule: RateLimitRule,
        increment: int
    ) -> RateLimitResult:
        """Fixed window rate limiting"""
        now = time.time()
        window_start = int(now / rule.window_seconds) * rule.window_seconds
        window_key = f"{key}:{window_start}"
        
        # Get current count
        if window_key in self._cache:
            count = self._cache[window_key].get('count', 0)
        else:
            count = 0
        
        # Check limit
        if count + increment > rule.limit:
            reset_time = datetime.fromtimestamp(window_start + rule.window_seconds)
            retry_after = int(window_start + rule.window_seconds - now)
            
            return RateLimitResult(
                allowed=False,
                remaining=max(0, rule.limit - count),
                reset_at=reset_time,
                retry_after=retry_after,
                rule_name=rule.name,
                reason=f"Rate limit exceeded: {rule.name}"
            )
        
        # Update count
        self._cache[window_key] = {
            'count': count + increment,
            'window_start': window_start
        }
        
        reset_time = datetime.fromtimestamp(window_start + rule.window_seconds)
        return RateLimitResult(
            allowed=True,
            remaining=rule.limit - (count + increment),
            reset_at=reset_time,
            rule_name=rule.name
        )
    
    async def _check_sliding_window(
        self,
        key: str,
        rule: RateLimitRule,
        increment: int
    ) -> RateLimitResult:
        """Sliding window rate limiting using timestamps"""
        now = time.time()
        window_start = now - rule.window_seconds
        
        # Get request timestamps from cache
        if key not in self._cache:
            self._cache[key] = {'timestamps': []}
        
        timestamps = self._cache[key]['timestamps']
        
        # Remove old timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        
        # Check limit
        if len(timestamps) + increment > rule.limit:
            oldest_timestamp = timestamps[0] if timestamps else now
            reset_time = datetime.fromtimestamp(oldest_timestamp + rule.window_seconds)
            retry_after = int(oldest_timestamp + rule.window_seconds - now)
            
            return RateLimitResult(
                allowed=False,
                remaining=max(0, rule.limit - len(timestamps)),
                reset_at=reset_time,
                retry_after=retry_after,
                rule_name=rule.name,
                reason=f"Rate limit exceeded: {rule.name}"
            )
        
        # Add new timestamps
        for _ in range(increment):
            timestamps.append(now)
        
        self._cache[key]['timestamps'] = timestamps
        
        reset_time = datetime.fromtimestamp(now + rule.window_seconds)
        return RateLimitResult(
            allowed=True,
            remaining=rule.limit - len(timestamps),
            reset_at=reset_time,
            rule_name=rule.name
        )
    
    async def _check_token_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        increment: int
    ) -> RateLimitResult:
        """Token bucket rate limiting"""
        now = time.time()
        refill_rate = rule.limit / rule.window_seconds
        max_tokens = rule.burst_size or rule.limit
        
        # Get or create bucket
        bucket_key = f"bucket:{key}"
        row = await self.db_manager.fetchone(
            "SELECT tokens, last_update FROM agi_rate_limit_buckets WHERE key = $1",
            bucket_key
        )
        
        if row:
            tokens = row['tokens']
            last_update = row['last_update'].timestamp()
        else:
            tokens = max_tokens
            last_update = now
        
        # Refill tokens
        time_passed = now - last_update
        tokens = min(max_tokens, tokens + (time_passed * refill_rate))
        
        # Check if enough tokens
        if tokens < increment:
            tokens_needed = increment - tokens
            seconds_until_available = tokens_needed / refill_rate
            reset_time = datetime.fromtimestamp(now + seconds_until_available)
            
            return RateLimitResult(
                allowed=False,
                remaining=int(tokens),
                reset_at=reset_time,
                retry_after=int(seconds_until_available),
                rule_name=rule.name,
                reason=f"Not enough tokens: {rule.name}"
            )
        
        # Consume tokens
        tokens -= increment
        
        # Update bucket
        await self.db_manager.execute(
            """
            INSERT INTO agi_rate_limit_buckets (key, tokens, last_update)
            VALUES ($1, $2, $3)
            ON CONFLICT (key) DO UPDATE SET
                tokens = $2,
                last_update = $3
            """,
            bucket_key,
            tokens,
            datetime.fromtimestamp(now)
        )
        
        reset_time = datetime.fromtimestamp(now + rule.window_seconds)
        return RateLimitResult(
            allowed=True,
            remaining=int(tokens),
            reset_at=reset_time,
            rule_name=rule.name
        )
    
    async def _check_leaky_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        increment: int
    ) -> RateLimitResult:
        """Leaky bucket rate limiting (similar to token bucket but with constant drain)"""
        # For simplicity, using token bucket implementation with different parameters
        return await self._check_token_bucket(key, rule, increment)
    
    async def _check_adaptive(
        self,
        key: str,
        rule: RateLimitRule,
        increment: int
    ) -> RateLimitResult:
        """Adaptive rate limiting based on system load"""
        # Get system load factor (simplified)
        load_factor = await self._get_system_load()
        
        # Adjust limit based on load
        adjusted_limit = int(rule.limit * (2.0 - load_factor))  # Reduce limit as load increases
        
        # Use sliding window with adjusted limit
        adjusted_rule = RateLimitRule(
            name=rule.name,
            scope=rule.scope,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            limit=adjusted_limit,
            window_seconds=rule.window_seconds,
            priority=rule.priority,
            enabled=rule.enabled
        )
        
        return await self._check_sliding_window(key, adjusted_rule, increment)
    
    async def _get_system_load(self) -> float:
        """Get system load factor (0.0 to 1.0)"""
        # Simplified: Check recent request count
        recent_requests = await self.db_manager.fetchone(
            """
            SELECT COUNT(*) as count
            FROM agi_rate_limit_violations
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 minute'
            """
        )
        
        if recent_requests:
            # Normalize to 0-1 range (assuming 100 violations/minute is high load)
            load = min(1.0, recent_requests['count'] / 100.0)
        else:
            load = 0.0
        
        return load
    
    async def _log_violation(
        self,
        rule: RateLimitRule,
        identifier: str,
        resource: Optional[str],
        attempts: int
    ):
        """Log rate limit violation"""
        try:
            # Log to database
            await self.db_manager.execute(
                """
                INSERT INTO agi_rate_limit_violations (
                    rule_name, identifier, resource, attempts,
                    window_start, window_end, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                rule.name,
                identifier,
                resource,
                attempts,
                datetime.utcnow() - timedelta(seconds=rule.window_seconds),
                datetime.utcnow(),
                json.dumps({"scope": rule.scope.value, "strategy": rule.strategy.value})
            )
            
            # Log to audit logger
            if self.audit_logger:
                await self.audit_logger.log_event(AuditEvent(
                    event_type=AuditEventType.SECURITY_RATE_LIMITED,
                    severity=AuditSeverity.WARNING,
                    user_id=identifier if rule.scope == RateLimitScope.USER else None,
                    action="rate_limit_exceeded",
                    metadata={
                        "rule_name": rule.name,
                        "identifier": identifier,
                        "resource": resource,
                        "attempts": attempts,
                        "limit": rule.limit,
                        "window_seconds": rule.window_seconds
                    }
                ))
                
        except Exception as e:
            logger.error(f"Failed to log rate limit violation: {e}")
    
    async def _cleanup_loop(self):
        """Cleanup old data periodically"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                # Clean old cache entries
                now = time.time()
                keys_to_delete = []
                
                for key, data in self._cache.items():
                    if 'timestamps' in data:
                        # Clean old timestamps
                        data['timestamps'] = [
                            ts for ts in data['timestamps']
                            if ts > now - 3600  # Keep last hour
                        ]
                        if not data['timestamps']:
                            keys_to_delete.append(key)
                    elif 'window_start' in data:
                        # Clean old fixed windows
                        if data['window_start'] < now - 3600:
                            keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._cache[key]
                
                # Clean old violations
                await self.db_manager.execute(
                    "DELETE FROM agi_rate_limit_violations WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days'"
                )
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def get_usage_stats(self, identifier: str, scope: RateLimitScope) -> Dict[str, Any]:
        """Get usage statistics for an identifier"""
        stats = {}
        
        # Get applicable rules
        rules = self._get_applicable_rules(scope, None)
        
        for rule in rules:
            key = rule.get_key(identifier)
            
            # Get current usage
            if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                if key in self._cache:
                    timestamps = self._cache[key].get('timestamps', [])
                    now = time.time()
                    window_start = now - rule.window_seconds
                    active_timestamps = [ts for ts in timestamps if ts > window_start]
                    usage = len(active_timestamps)
                else:
                    usage = 0
            else:
                # For other strategies, query the database or cache
                usage = 0  # Simplified
            
            stats[rule.name] = {
                'limit': rule.limit,
                'used': usage,
                'remaining': max(0, rule.limit - usage),
                'window_seconds': rule.window_seconds,
                'strategy': rule.strategy.value
            }
        
        return stats


# Singleton accessor
_limiter_instance = None

async def get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter"""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RateLimiter()
        await _limiter_instance.initialize()
    return _limiter_instance
