"""
Core types for LLM Gateway
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class TaskType(Enum):
    """Types of AI tasks"""
    REASONING = "reasoning"  # Complex reasoning (product recommendations)
    CHAT = "chat"  # Real-time chat
    SIMPLE = "simple"  # Simple queries
    DEVELOPMENT = "development"  # Development/testing
    TOOL_USE = "tool_use"  # Function calling / tool use


@dataclass
class RequestContext:
    """Context for an LLM request"""
    task_type: TaskType
    estimated_tokens: int
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    is_production: bool = True
    requires_speed: bool = False
    requires_streaming: bool = False
    tools: Optional[List[Dict]] = None
    temperature: float = 0.7
    max_tokens: int = 2000

    @property
    def requires_reasoning(self) -> bool:
        """Check if task requires reasoning capabilities"""
        return self.task_type in [TaskType.REASONING, TaskType.TOOL_USE]

    @property
    def requires_tools(self) -> bool:
        """Check if task requires tool calling"""
        return self.tools is not None and len(self.tools) > 0


@dataclass
class ProviderConfig:
    """Configuration for a provider"""
    name: str
    enabled: bool = True
    cost_per_1m_input_tokens: float = 0.0
    cost_per_1m_output_tokens: float = 0.0
    avg_latency_seconds: float = 2.0
    supports_reasoning: bool = False
    supports_streaming: bool = True
    supports_tools: bool = False
    is_free: bool = True

    # Rate limits
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_month: Optional[int] = None

    # API configuration
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None

    # Health check
    health_check_url: Optional[str] = None
    health_check_interval_seconds: int = 300  # 5 minutes


@dataclass
class ProviderStats:
    """Runtime statistics for a provider"""
    requests_made: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    total_cost: float = 0.0
    errors: int = 0
    total_latency: float = 0.0
    last_used: Optional[datetime] = None
    last_error: Optional[datetime] = None
    last_error_message: Optional[str] = None

    @property
    def avg_latency(self) -> float:
        """Calculate average latency"""
        return self.total_latency / self.requests_made if self.requests_made > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        total = self.requests_made + self.errors
        return self.errors / total if total > 0 else 0.0


@dataclass
class CompletionResult:
    """Result from LLM completion"""
    content: str
    provider: str
    model: str
    selection_reason: str
    latency: float
    tokens_input: int
    tokens_output: int
    cost: float
    cached: bool = False
    tool_calls: Optional[List[Dict]] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Current rate limit state for a provider"""
    minute_count: int = 0
    day_count: int = 0
    month_tokens: int = 0

    minute_reset: datetime = field(default_factory=datetime.now)
    day_reset: datetime = field(default_factory=datetime.now)
    month_reset: datetime = field(default_factory=datetime.now)

    is_rate_limited: bool = False
    limited_until: Optional[datetime] = None


@dataclass
class ProviderHealth:
    """Health status of a provider"""
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_failure_reason: Optional[str] = None


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class RateLimitError(ProviderError):
    """Provider rate limit exceeded"""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider is unavailable"""
    pass


class AllProvidersExhaustedError(Exception):
    """All providers have been exhausted"""
    pass
