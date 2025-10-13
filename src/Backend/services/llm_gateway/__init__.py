"""
LLM Gateway - Intelligent Multi-Provider Routing

Provides intelligent routing across multiple LLM providers with:
- Automatic failover (OpenRouter → Groq → Local)
- Cost optimization (free tiers prioritized)
- 10x faster responses (0.5s vs 5s)
- Zero infrastructure cost

Usage:
    from services.llm_gateway import LLMRouter, RequestContext, TaskType
    from services.llm_gateway.providers import OpenRouterProvider, GroqProvider, LocalProvider

    # Create and configure router
    router = LLMRouter()
    router.register_provider(OpenRouterProvider())
    router.register_provider(Groq Provider())
    router.register_provider(LocalProvider(model_manager=my_model_manager))

    # Use router
    result = await router.complete(
        messages=[{"role": "user", "content": "Recommend products"}],
        context=RequestContext(task_type=TaskType.REASONING, estimated_tokens=1000)
    )
"""

from .types import (
    TaskType,
    RequestContext,
    ProviderConfig,
    CompletionResult,
    ProviderStats,
    ProviderHealth,
    RateLimitState,
    ProviderError,
    RateLimitError,
    ProviderUnavailableError,
    AllProvidersExhaustedError
)
from .router import LLMRouter
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

__all__ = [
    # Core types
    "TaskType",
    "RequestContext",
    "ProviderConfig",
    "CompletionResult",
    "ProviderStats",
    "ProviderHealth",
    "RateLimitState",

    # Exceptions
    "ProviderError",
    "RateLimitError",
    "ProviderUnavailableError",
    "AllProvidersExhaustedError",

    # Router
    "LLMRouter",

    # Providers
    "BaseProvider",
    "OpenRouterProvider",
    "GroqProvider",
    "LLM7Provider",
    "LLM7GPT4Mini",
    "LLM7GPT4",
    "LLM7Claude",
    "LocalProvider"
]
