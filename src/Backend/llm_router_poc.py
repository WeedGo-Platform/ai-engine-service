#!/usr/bin/env python3
"""
LLM Router Proof of Concept
Demonstrates intelligent provider switching with rate limits, quota tracking, and failover

This POC simulates:
- Multiple LLM providers (OpenRouter, Groq, Cloudflare, Local)
- Rate limiting and quota management
- Intelligent routing based on cost, speed, availability
- Automatic failover when providers are exhausted
- Real-time provider switching visualization
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json


# ============================================================================
# CORE TYPES
# ============================================================================

class TaskType(Enum):
    """Types of AI tasks"""
    REASONING = "reasoning"  # Complex product recommendations
    CHAT = "chat"  # Real-time customer chat
    SIMPLE = "simple"  # Simple queries
    DEVELOPMENT = "development"  # Dev/testing


@dataclass
class RequestContext:
    """Context for an LLM request"""
    task_type: TaskType
    estimated_tokens: int
    customer_id: Optional[str] = None
    is_production: bool = True
    requires_speed: bool = False

    @property
    def requires_reasoning(self) -> bool:
        return self.task_type == TaskType.REASONING


@dataclass
class ProviderStats:
    """Statistics for a provider"""
    requests_made: int = 0
    tokens_used: int = 0
    total_cost: float = 0.0
    errors: int = 0
    total_latency: float = 0.0
    last_used: Optional[datetime] = None

    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.requests_made if self.requests_made > 0 else 0.0


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_month: Optional[int] = None

    # Tracking
    minute_counter: int = 0
    day_counter: int = 0
    month_counter: int = 0
    minute_reset: datetime = field(default_factory=datetime.now)
    day_reset: datetime = field(default_factory=datetime.now)
    month_reset: datetime = field(default_factory=datetime.now)


# ============================================================================
# PROVIDER BASE CLASS
# ============================================================================

class BaseProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(
        self,
        name: str,
        cost_per_1m_tokens: float,
        avg_latency: float,
        rate_limits: RateLimitConfig,
        supports_reasoning: bool = False,
        is_free: bool = False
    ):
        self.name = name
        self.cost_per_1m_tokens = cost_per_1m_tokens
        self.avg_latency_seconds = avg_latency
        self.rate_limits = rate_limits
        self.supports_reasoning = supports_reasoning
        self.is_free = is_free
        self.is_healthy = True
        self.stats = ProviderStats()

    def check_rate_limits(self) -> bool:
        """Check if provider has capacity"""
        now = datetime.now()

        # Reset counters if time windows expired
        if now > self.rate_limits.minute_reset:
            self.rate_limits.minute_counter = 0
            self.rate_limits.minute_reset = now + timedelta(minutes=1)

        if now > self.rate_limits.day_reset:
            self.rate_limits.day_counter = 0
            self.rate_limits.day_reset = now + timedelta(days=1)

        if now > self.rate_limits.month_reset:
            self.rate_limits.month_counter = 0
            self.rate_limits.month_reset = now + timedelta(days=30)

        # Check limits
        if self.rate_limits.requests_per_minute:
            if self.rate_limits.minute_counter >= self.rate_limits.requests_per_minute:
                return False

        if self.rate_limits.requests_per_day:
            if self.rate_limits.day_counter >= self.rate_limits.requests_per_day:
                return False

        if self.rate_limits.tokens_per_month:
            if self.rate_limits.month_counter >= self.rate_limits.tokens_per_month:
                return False

        return True

    def record_usage(self, tokens: int):
        """Record usage and update counters"""
        self.rate_limits.minute_counter += 1
        self.rate_limits.day_counter += 1
        self.rate_limits.month_counter += tokens

        cost = (tokens / 1_000_000) * self.cost_per_1m_tokens

        self.stats.requests_made += 1
        self.stats.tokens_used += tokens
        self.stats.total_cost += cost
        self.stats.total_latency += self.avg_latency_seconds
        self.stats.last_used = datetime.now()

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for tokens"""
        return (tokens / 1_000_000) * self.cost_per_1m_tokens

    @abstractmethod
    async def complete(self, messages: List[Dict], tokens: int) -> str:
        """Generate completion (mock)"""
        pass

    def get_quota_remaining_pct(self) -> float:
        """Get remaining quota as percentage"""
        if not self.rate_limits.requests_per_day:
            return 100.0

        used = self.rate_limits.day_counter
        limit = self.rate_limits.requests_per_day
        remaining = max(0, limit - used)
        return (remaining / limit) * 100

    def __repr__(self):
        return f"{self.name} (${self.cost_per_1m_tokens}/1M tokens, {self.avg_latency_seconds}s latency)"


# ============================================================================
# CONCRETE PROVIDER IMPLEMENTATIONS
# ============================================================================

class OpenRouterProvider(BaseProvider):
    """OpenRouter - Free tier with DeepSeek R1"""

    def __init__(self):
        super().__init__(
            name="OpenRouter (DeepSeek R1)",
            cost_per_1m_tokens=0.0,  # Free tier
            avg_latency=2.0,
            rate_limits=RateLimitConfig(
                requests_per_minute=20,
                requests_per_day=200
            ),
            supports_reasoning=True,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[OpenRouter/DeepSeek-R1] Reasoning response with {tokens} tokens"


class GroqProvider(BaseProvider):
    """Groq - Ultra-fast inference"""

    def __init__(self):
        super().__init__(
            name="Groq (Llama 3.3 70B)",
            cost_per_1m_tokens=0.0,  # Free tier
            avg_latency=0.5,  # Super fast!
            rate_limits=RateLimitConfig(
                requests_per_minute=100,
                requests_per_day=14400  # Very generous
            ),
            supports_reasoning=False,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[Groq/Llama-3.3-70B] Fast response with {tokens} tokens"


class CloudflareProvider(BaseProvider):
    """Cloudflare Workers AI - Edge inference"""

    def __init__(self):
        super().__init__(
            name="Cloudflare Workers AI",
            cost_per_1m_tokens=0.0,  # Free tier (10K neurons/day)
            avg_latency=1.0,
            rate_limits=RateLimitConfig(
                requests_per_day=1000,  # ~10K neurons ≈ 100K tokens ≈ 1K requests
                tokens_per_month=3_000_000  # ~3M tokens/month
            ),
            supports_reasoning=False,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[Cloudflare/GPT-OSS] Edge response with {tokens} tokens"


class NVIDIANIMProvider(BaseProvider):
    """NVIDIA NIM - Unlimited for development"""

    def __init__(self):
        super().__init__(
            name="NVIDIA NIM (Dev)",
            cost_per_1m_tokens=0.0,  # Free for development
            avg_latency=1.5,
            rate_limits=RateLimitConfig(
                # Unlimited for development
            ),
            supports_reasoning=True,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[NVIDIA-NIM/Llama-3.1] DGX Cloud response with {tokens} tokens"


class MistralProvider(BaseProvider):
    """Mistral AI - Free tier"""

    def __init__(self):
        super().__init__(
            name="Mistral (Mixtral 8x7B)",
            cost_per_1m_tokens=0.0,  # Free tier
            avg_latency=1.8,
            rate_limits=RateLimitConfig(
                requests_per_minute=60,
                tokens_per_month=1_000_000_000  # 1B tokens/month!
            ),
            supports_reasoning=False,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[Mistral/Mixtral-8x7B] Response with {tokens} tokens"


class LocalLlamaProvider(BaseProvider):
    """Local llama-cpp-python - Always available"""

    def __init__(self):
        super().__init__(
            name="Local Llama (llama-cpp-python)",
            cost_per_1m_tokens=0.0,  # Free (but uses compute)
            avg_latency=5.0,  # Slower on CPU
            rate_limits=RateLimitConfig(
                # No limits (local)
            ),
            supports_reasoning=False,
            is_free=True
        )

    async def complete(self, messages: List[Dict], tokens: int) -> str:
        await asyncio.sleep(self.avg_latency_seconds)
        return f"[Local/Llama-7B] Local CPU response with {tokens} tokens"


# ============================================================================
# LLM ROUTER
# ============================================================================

class LLMRouter:
    """Intelligent LLM provider router"""

    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()
        self.total_requests = 0
        self.total_cost = 0.0

    def _initialize_providers(self):
        """Initialize all available providers"""
        providers = [
            OpenRouterProvider(),
            GroqProvider(),
            CloudflareProvider(),
            NVIDIANIMProvider(),
            MistralProvider(),
            LocalLlamaProvider()
        ]

        for provider in providers:
            self.providers[provider.name] = provider

    def score_provider(
        self,
        provider: BaseProvider,
        context: RequestContext
    ) -> Tuple[float, str]:
        """
        Score a provider based on multiple factors
        Returns: (score, reason)
        Score: 0-100 (higher is better)
        """
        score = 50.0
        reasons = []

        # Factor 1: Cost (free = +30)
        if provider.is_free:
            score += 30
            reasons.append("FREE")

        # Factor 2: Quota remaining (+0 to +20)
        quota_pct = provider.get_quota_remaining_pct()
        quota_bonus = quota_pct * 0.2
        score += quota_bonus
        if quota_pct > 80:
            reasons.append(f"HIGH_QUOTA({quota_pct:.0f}%)")
        elif quota_pct < 20:
            reasons.append(f"LOW_QUOTA({quota_pct:.0f}%)")

        # Factor 3: Health (+10 or -30)
        if provider.is_healthy:
            score += 10
        else:
            score -= 30
            reasons.append("UNHEALTHY")

        # Factor 4: Latency (faster = better, max +10)
        if provider.avg_latency_seconds < 1.0:
            score += 10
            reasons.append("FAST")
        elif provider.avg_latency_seconds < 2.0:
            score += 5
        elif provider.avg_latency_seconds > 4.0:
            score -= 5
            reasons.append("SLOW")

        # Factor 5: Task suitability (+15 for perfect match)
        if context.requires_reasoning and provider.supports_reasoning:
            score += 15
            reasons.append("REASONING_CAPABLE")

        if context.requires_speed and provider.avg_latency_seconds < 1.0:
            score += 15
            reasons.append("SPEED_OPTIMIZED")

        # Factor 6: Environment preference
        if not context.is_production and "Local" in provider.name:
            score += 20
            reasons.append("DEV_PREFERRED")

        # Factor 7: Rate limit check (critical)
        if not provider.check_rate_limits():
            score = 0
            reasons = ["RATE_LIMITED"]

        reason_str = ", ".join(reasons) if reasons else "AVAILABLE"
        return score, reason_str

    async def route_request(
        self,
        messages: List[Dict],
        context: RequestContext
    ) -> Tuple[BaseProvider, str]:
        """
        Route request to best available provider
        Returns: (provider, selection_reason)
        """
        # Score all providers
        scored = []
        for provider in self.providers.values():
            score, reason = self.score_provider(provider, context)
            scored.append((score, reason, provider))

        # Sort by score (highest first)
        scored.sort(reverse=True, key=lambda x: x[0])

        # Select best available provider
        for score, reason, provider in scored:
            if score > 0:  # Has capacity
                return provider, f"score={score:.1f} ({reason})"

        # Fallback to local (always available)
        local = self.providers["Local Llama (llama-cpp-python)"]
        return local, "FALLBACK (all providers exhausted)"

    async def complete(
        self,
        messages: List[Dict],
        context: RequestContext
    ) -> Dict:
        """
        Complete a request using the best available provider
        """
        # Route to provider
        provider, selection_reason = await self.route_request(messages, context)

        # Track routing decision
        self.total_requests += 1

        # Generate completion
        start = time.time()
        try:
            response = await provider.complete(messages, context.estimated_tokens)
            latency = time.time() - start

            # Record usage
            provider.record_usage(context.estimated_tokens)
            self.total_cost += provider.estimate_cost(context.estimated_tokens)

            return {
                "response": response,
                "provider": provider.name,
                "selection_reason": selection_reason,
                "latency": latency,
                "cost": provider.estimate_cost(context.estimated_tokens),
                "tokens": context.estimated_tokens
            }

        except Exception as e:
            provider.is_healthy = False
            provider.stats.errors += 1

            # Retry with next provider
            return await self.complete(messages, context)

    def print_stats(self):
        """Print router statistics"""
        print("\n" + "="*80)
        print("LLM ROUTER STATISTICS")
        print("="*80)
        print(f"Total Requests: {self.total_requests}")
        print(f"Total Cost: ${self.total_cost:.4f}")
        print(f"\nPer-Provider Stats:")
        print("-"*80)

        for provider in self.providers.values():
            stats = provider.stats
            if stats.requests_made > 0:
                print(f"\n{provider.name}:")
                print(f"  Requests: {stats.requests_made}")
                print(f"  Tokens: {stats.tokens_used:,}")
                print(f"  Cost: ${stats.total_cost:.4f}")
                print(f"  Avg Latency: {stats.avg_latency:.2f}s")
                print(f"  Quota Remaining: {provider.get_quota_remaining_pct():.1f}%")

                # Show rate limits
                if provider.rate_limits.requests_per_day:
                    used = provider.rate_limits.day_counter
                    limit = provider.rate_limits.requests_per_day
                    print(f"  Daily Limit: {used}/{limit} ({(used/limit*100):.1f}% used)")


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

async def demo_scenario_1_normal_usage():
    """Scenario 1: Normal usage - should use free tiers efficiently"""
    print("\n" + "🟢 " + "="*78)
    print("SCENARIO 1: Normal Usage (30 requests)")
    print("Expected: Smart distribution across free tiers")
    print("="*80)

    router = LLMRouter()

    scenarios = [
        (TaskType.REASONING, 1000, "Product recommendation"),
        (TaskType.CHAT, 500, "Customer chat"),
        (TaskType.SIMPLE, 300, "Simple query"),
    ]

    for i in range(30):
        task_type, tokens, description = random.choice(scenarios)
        context = RequestContext(
            task_type=task_type,
            estimated_tokens=tokens,
            is_production=True
        )

        result = await router.complete(
            [{"role": "user", "content": "test"}],
            context
        )

        print(f"\n#{i+1} {description} ({task_type.value}):")
        print(f"  ✓ Provider: {result['provider']}")
        print(f"  ✓ Reason: {result['selection_reason']}")
        print(f"  ✓ Latency: {result['latency']:.2f}s")
        print(f"  ✓ Cost: ${result['cost']:.6f}")

    router.print_stats()


async def demo_scenario_2_rate_limit_exhaustion():
    """Scenario 2: Exhaust OpenRouter, should failover to others"""
    print("\n" + "🟡 " + "="*78)
    print("SCENARIO 2: Rate Limit Exhaustion")
    print("Expected: OpenRouter → Groq → Cloudflare → Others")
    print("="*80)

    router = LLMRouter()

    # Make 250 requests (exceeds OpenRouter's 200/day limit)
    for i in range(250):
        context = RequestContext(
            task_type=TaskType.REASONING,
            estimated_tokens=800,
            is_production=True
        )

        result = await router.complete(
            [{"role": "user", "content": "recommend products"}],
            context
        )

        if i in [0, 50, 100, 150, 199, 200, 201, 220, 240]:
            print(f"\n#{i+1} Request:")
            print(f"  ✓ Provider: {result['provider']}")
            print(f"  ✓ Reason: {result['selection_reason']}")

    router.print_stats()


async def demo_scenario_3_speed_critical():
    """Scenario 3: Speed-critical requests should use Groq"""
    print("\n" + "🔵 " + "="*78)
    print("SCENARIO 3: Speed-Critical Requests (Real-time Chat)")
    print("Expected: Groq dominates (fastest provider)")
    print("="*80)

    router = LLMRouter()

    for i in range(20):
        context = RequestContext(
            task_type=TaskType.CHAT,
            estimated_tokens=500,
            is_production=True,
            requires_speed=True  # Speed is critical!
        )

        result = await router.complete(
            [{"role": "user", "content": "quick response needed"}],
            context
        )

        print(f"\n#{i+1} Speed-critical chat:")
        print(f"  ✓ Provider: {result['provider']}")
        print(f"  ✓ Latency: {result['latency']:.2f}s")
        print(f"  ✓ Reason: {result['selection_reason']}")

    router.print_stats()


async def demo_scenario_4_development_mode():
    """Scenario 4: Development mode should prefer local"""
    print("\n" + "🟣 " + "="*78)
    print("SCENARIO 4: Development Mode")
    print("Expected: Local Llama preferred (save API quotas for prod)")
    print("="*80)

    router = LLMRouter()

    for i in range(15):
        context = RequestContext(
            task_type=TaskType.DEVELOPMENT,
            estimated_tokens=600,
            is_production=False  # Development mode!
        )

        result = await router.complete(
            [{"role": "user", "content": "testing"}],
            context
        )

        print(f"\n#{i+1} Dev request:")
        print(f"  ✓ Provider: {result['provider']}")
        print(f"  ✓ Reason: {result['selection_reason']}")

    router.print_stats()


async def demo_scenario_5_cost_comparison():
    """Scenario 5: Cost comparison vs paid APIs"""
    print("\n" + "💰 " + "="*78)
    print("SCENARIO 5: Cost Comparison (100 requests)")
    print("Expected: $0.00 with free tier vs ~$0.50 with GPT-4")
    print("="*80)

    router = LLMRouter()

    # Simulate 100 requests
    total_tokens = 0
    for i in range(100):
        task_type = random.choice([TaskType.REASONING, TaskType.CHAT, TaskType.SIMPLE])
        tokens = random.randint(300, 1500)
        total_tokens += tokens

        context = RequestContext(
            task_type=task_type,
            estimated_tokens=tokens,
            is_production=True
        )

        result = await router.complete(
            [{"role": "user", "content": "test"}],
            context
        )

    # Calculate hypothetical costs
    gpt4_cost = (total_tokens / 1_000_000) * 30  # GPT-4: ~$30/1M tokens
    claude_cost = (total_tokens / 1_000_000) * 15  # Claude: ~$15/1M tokens
    deepseek_paid_cost = (total_tokens / 1_000_000) * 2.19  # DeepSeek paid: $2.19/1M

    print(f"\n📊 Cost Analysis for {total_tokens:,} tokens:")
    print(f"  • Our Router (free tiers): ${router.total_cost:.4f}")
    print(f"  • GPT-4 (if paid):         ${gpt4_cost:.4f}")
    print(f"  • Claude (if paid):        ${claude_cost:.4f}")
    print(f"  • DeepSeek (if paid):      ${deepseek_paid_cost:.4f}")
    print(f"\n💵 Savings: ${gpt4_cost:.2f} (100% cost reduction!)")

    router.print_stats()


# ============================================================================
# MAIN DEMO
# ============================================================================

async def main():
    """Run all demo scenarios"""
    print("\n" + "="*80)
    print(" "*20 + "LLM ROUTER PROOF OF CONCEPT")
    print(" "*15 + "Intelligent Multi-Provider Routing")
    print("="*80)

    demos = [
        ("Normal Usage", demo_scenario_1_normal_usage),
        ("Rate Limit Handling", demo_scenario_2_rate_limit_exhaustion),
        ("Speed Optimization", demo_scenario_3_speed_critical),
        ("Development Mode", demo_scenario_4_development_mode),
        ("Cost Comparison", demo_scenario_5_cost_comparison),
    ]

    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run All Scenarios")
    print("  0. Exit")

    try:
        choice = input("\nSelect demo (0-6): ").strip()

        if choice == "0":
            print("Exiting...")
            return

        choice_num = int(choice)

        if 1 <= choice_num <= len(demos):
            _, demo_func = demos[choice_num - 1]
            await demo_func()

        elif choice_num == len(demos) + 1:
            for name, demo_func in demos:
                await demo_func()
                await asyncio.sleep(2)  # Pause between demos

        else:
            print("Invalid choice!")

    except (ValueError, KeyboardInterrupt):
        print("\nExiting...")

    print("\n" + "="*80)
    print("✅ Proof of Concept Complete!")
    print("="*80)
    print("\nKey Takeaways:")
    print("  • Router intelligently selects best provider based on:")
    print("    - Cost (free tiers prioritized)")
    print("    - Rate limits (automatic failover)")
    print("    - Task requirements (reasoning, speed)")
    print("    - Environment (dev vs prod)")
    print("  • Automatic failover when providers exhausted")
    print("  • Zero-cost operation across multiple free tiers")
    print("  • 5,000+ requests/day capacity for FREE")
    print("\n💡 Ready for production implementation!")


if __name__ == "__main__":
    asyncio.run(main())
