# LLM Provider Signup Guide

## Quick Start: ZERO Setup Option

**✅ LLM7.io - Already Working (NO SIGNUP NEEDED)**

The LLM Gateway is already functional with LLM7.io provider:
- **NO authentication required**
- **40 requests/min** anonymous access
- **Models:** gpt-4o-mini, gpt-4, claude-3.5-sonnet
- **Test now:** `python3 test_llm7.py`

```python
from services.llm_gateway import LLMRouter, LLM7GPT4Mini

router = LLMRouter()
router.register_provider(LLM7GPT4Mini())  # NO API KEY NEEDED!
result = await router.complete(messages=[...])
```

---

## Manual Signup Instructions

Browser automation hits technical limitations (anti-bot, OAuth, timeouts). Manual signup is faster and more reliable.

### 1. OpenRouter (DeepSeek R1 - Reasoning Model)

**Free Tier:**
- 200 requests/day
- DeepSeek R1 (70B reasoning model)
- Cost: $0

**Signup Steps:**
1. Go to https://openrouter.ai/
2. Click "Sign Up" (top right)
3. Click "Sign in with Google"
4. Complete Google OAuth
5. Navigate to https://openrouter.ai/keys
6. Click "Create API Key"
7. Copy the key (starts with `sk-or-v1-...`)

**Set Environment Variable:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
```

**Test:**
```bash
python3 -c "
from services.llm_gateway import OpenRouterProvider
import asyncio

async def test():
    provider = OpenRouterProvider()
    result = await provider.complete(
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )
    print(f'Response: {result.content}')

asyncio.run(test())
"
```

---

### 2. Groq (Llama 3.3 70B - Ultra-Fast)

**Free Tier:**
- 14,400 requests/day
- Llama 3.3 70B (0.5s latency!)
- Tool calling support
- Cost: $0

**Signup Steps:**
1. Go to https://console.groq.com/
2. Click "Log In" or "Start Building"
3. Click "Continue with Google"
4. Complete Google OAuth
5. Navigate to https://console.groq.com/keys
6. Click "Create API Key"
7. Enter name (e.g., "WeedGo Test")
8. Copy the key (starts with `gsk_...`)

**Set Environment Variable:**
```bash
export GROQ_API_KEY="gsk_YOUR_KEY_HERE"
```

**Test:**
```bash
python3 -c "
from services.llm_gateway import GroqProvider
import asyncio

async def test():
    provider = GroqProvider()
    result = await provider.complete(
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )
    print(f'Response: {result.content}')

asyncio.run(test())
"
```

---

## Full Router Test

Once you have API keys (or just using LLM7), test the full router:

```bash
# Set any keys you have (LLM7 doesn't need one)
export OPENROUTER_API_KEY="sk-or-v1-..."  # Optional
export GROQ_API_KEY="gsk_..."              # Optional

# Run comprehensive test
python3 test_llm_gateway_real.py
```

**Expected Output:**
```
✅ Router Stats:
  Total providers: 3
  - LLM7.io (gpt-4o-mini)
  - OpenRouter (DeepSeek R1)  [if key set]
  - Groq (Llama 3.3 70B)      [if key set]
  - Local (TinyLlama)

✅ Routing Test:
  Selected: Groq (fastest, 0.5s)
  Fallback: LLM7 → Local
  Total cost: $0.00
```

---

## Provider Comparison

| Provider | Setup | Requests/Day | Latency | Best For |
|----------|-------|--------------|---------|----------|
| **LLM7.io** | ✅ NONE | Unlimited* | 2.5s | Instant access |
| **Groq** | 5 min | 14,400 | **0.5s** | Real-time chat |
| **OpenRouter** | 5 min | 200 | 2.0s | Complex reasoning |
| **Local** | ✅ Done | Unlimited | 5.0s | Privacy/offline |

*40 req/min anonymous limit

---

## Integration with FastAPI Backend

Once providers are configured, integrate with WeedGo backend:

```python
# In main.py or ai_service.py
from services.llm_gateway import LLMRouter, RequestContext, TaskType
from services.llm_gateway.providers import (
    LLM7GPT4Mini,
    OpenRouterProvider,
    GroqProvider,
    LocalProvider
)

# Initialize router (do once at startup)
llm_router = LLMRouter()

# Register providers (automatically skip if no API key)
llm_router.register_provider(LLM7GPT4Mini())        # Always available
llm_router.register_provider(OpenRouterProvider())  # If OPENROUTER_API_KEY set
llm_router.register_provider(GroqProvider())        # If GROQ_API_KEY set
llm_router.register_provider(LocalProvider(
    model_callable=v5_engine.current_model,
    model_name=v5_engine.current_model_name
))

# Use in endpoints
@app.post("/chat")
async def chat(request: ChatRequest):
    result = await llm_router.complete(
        messages=request.messages,
        context=RequestContext(
            task_type=TaskType.CHAT,
            estimated_tokens=500
        )
    )

    return {
        "response": result.content,
        "provider": result.provider,
        "latency": result.latency,
        "cost": result.cost
    }
```

---

## Troubleshooting

### Provider Not Showing Up
```bash
# Check if provider is enabled
python3 -c "
from services.llm_gateway import GroqProvider
provider = GroqProvider()
print(f'Enabled: {provider.is_enabled}')
print(f'Has key: {provider.config.api_key is not None}')
"
```

### All Providers Exhausted
- Check API key environment variables are set
- Verify at least LLM7 or Local is available
- Check rate limits haven't been exceeded

### Slow Responses
- Router selects fastest available provider
- Groq = 0.5s (if key set)
- LLM7 = 2.5s (always available)
- Local = 5s (CPU inference)

---

## Next Steps

1. ✅ **Working Now:** LLM7 + Local providers (no setup)
2. **5 minutes:** Sign up for OpenRouter + Groq (manual)
3. **Week 1:** Integrate router into FastAPI backend
4. **Week 2:** Add Redis rate limit tracking
5. **Week 3:** Production deployment

**Estimated Total Time:** 15 minutes to get all providers working
**Cost:** $0/month (free tiers only)
