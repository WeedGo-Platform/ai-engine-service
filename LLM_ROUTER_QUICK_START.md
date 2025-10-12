# LLM Router - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you from POC to production-ready LLM routing.

---

## Step 1: Run the Proof of Concept

### Interactive Demo (Choose your scenario):
```bash
cd src/Backend
python3 llm_router_poc.py
```

You'll see:
```
================================================================================
                    LLM ROUTER PROOF OF CONCEPT
               Intelligent Multi-Provider Routing
================================================================================

Available Demos:
  1. Normal Usage
  2. Rate Limit Handling
  3. Speed Optimization
  4. Development Mode
  5. Cost Comparison
  6. Run All Scenarios
  0. Exit

Select demo (0-6):
```

Choose option **5** for the best overview (Cost Comparison).

### Automated Demo (Runs everything):
```bash
cd src/Backend
python3 run_poc_demo.py
```

This will show you:
- ✅ Task-based routing
- ✅ Automatic failover
- ✅ Cost savings analysis
- ✅ Provider statistics

---

## Step 2: Sign Up for Free APIs (15 minutes)

### Required Providers (Free Tier):

1. **OpenRouter** (200 req/day, reasoning models)
   - Visit: https://openrouter.ai/
   - Sign up with GitHub/Google
   - Get API key from: https://openrouter.ai/keys
   - Copy key: `sk-or-v1-...`

2. **Groq** (14,400 req/day, fastest inference)
   - Visit: https://console.groq.com/
   - Sign up
   - Create API key
   - Copy key: `gsk_...`

3. **Cloudflare Workers AI** (10K neurons/day)
   - Visit: https://dash.cloudflare.com/
   - Create account
   - Go to Workers & Pages → AI
   - Get API token

### Optional Providers (Recommended):

4. **NVIDIA NIM** (Unlimited for development)
   - Visit: https://build.nvidia.com/
   - Join NVIDIA Developer Program (free)
   - Access API catalog

5. **Together AI** ($25 free credit)
   - Visit: https://api.together.xyz/
   - Sign up
   - $25 credit auto-applied

6. **Mistral AI** (1B tokens/month free)
   - Visit: https://console.mistral.ai/
   - Create account
   - Get API key from La Plateforme

### Store Your API Keys:

Create `.env` file in `src/Backend/`:
```bash
# LLM Router API Keys

OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
NVIDIA_API_KEY=nvapi-...
TOGETHER_API_KEY=...
MISTRAL_API_KEY=...

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production
```

---

## Step 3: Test with Real APIs (30 minutes)

### Install Required Packages:
```bash
cd src/Backend
pip install openai httpx aiohttp redis python-dotenv
```

### Test Individual Providers:

```python
# test_providers.py
import os
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()

async def test_openrouter():
    """Test OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-r1:free",
                "messages": [
                    {"role": "user", "content": "Say hello!"}
                ]
            }
        )
        print(f"OpenRouter: {response.json()}")

async def test_groq():
    """Test Groq API"""
    api_key = os.getenv("GROQ_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": "Say hello!"}
                ]
            }
        )
        print(f"Groq: {response.json()}")

# Run tests
asyncio.run(test_openrouter())
asyncio.run(test_groq())
```

Run:
```bash
python3 test_providers.py
```

If you see responses, you're ready to go! 🎉

---

## Step 4: Production Implementation

### Phase 1: Core Integration (Week 1)

#### 1.1 Create LLM Gateway Service

```bash
mkdir -p src/Backend/services/llm_gateway
cd src/Backend/services/llm_gateway
```

Copy POC code:
```bash
# Copy provider classes from POC
cp ../../llm_router_poc.py ./base_providers.py

# Create real provider implementations
touch providers/__init__.py
touch providers/openrouter.py
touch providers/groq.py
touch providers/cloudflare.py
```

#### 1.2 Implement Real Providers

**Example: `providers/openrouter.py`**
```python
import httpx
import os
from typing import List, Dict, Optional, AsyncGenerator
from .base import BaseProvider

class OpenRouterProvider(BaseProvider):
    """Real OpenRouter integration"""

    def __init__(self):
        super().__init__(
            name="OpenRouter (DeepSeek R1)",
            cost_per_1m_tokens=0.0,
            avg_latency=2.0,
            supports_reasoning=True,
            is_free=True
        )
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    async def complete(
        self,
        messages: List[Dict],
        model: str = "deepseek/deepseek-r1:free",
        stream: bool = False,
        **kwargs
    ) -> str:
        """Generate completion using OpenRouter API"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://weedgo.ca",
                    "X-Title": "WeedGo Budtender"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    **kwargs
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"OpenRouter API error: {response.text}")

    async def check_health(self) -> bool:
        """Check if OpenRouter is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False
```

Repeat for Groq, Cloudflare, etc.

#### 1.3 Update Router to Use Real Providers

```python
# services/llm_gateway/router.py
from .providers.openrouter import OpenRouterProvider
from .providers.groq import GroqProvider
from .providers.cloudflare import CloudflareProvider
from .providers.local_llama import LocalLlamaProvider

class LLMRouter:
    def __init__(self):
        self.providers = {
            "openrouter": OpenRouterProvider(),
            "groq": GroqProvider(),
            "cloudflare": CloudflareProvider(),
            "local": LocalLlamaProvider()
        }
        # ... rest of POC router code
```

---

### Phase 2: FastAPI Integration (Week 1)

#### 2.1 Create API Endpoint

```python
# api/llm_endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.llm_gateway.router import LLMRouter

router = APIRouter(prefix="/api/llm", tags=["LLM Gateway"])
llm_router = LLMRouter()

class ChatRequest(BaseModel):
    messages: List[Dict]
    task_type: str = "chat"
    customer_id: str = None

class ChatResponse(BaseModel):
    response: str
    provider: str
    latency: float
    cost: float

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with intelligent routing"""

    context = RequestContext(
        task_type=TaskType(request.task_type),
        estimated_tokens=estimate_tokens(request.messages),
        customer_id=request.customer_id
    )

    result = await llm_router.complete(request.messages, context)

    return ChatResponse(
        response=result["response"],
        provider=result["provider"],
        latency=result["latency"],
        cost=result["cost"]
    )

@router.get("/providers")
async def get_providers():
    """Get provider status"""
    return {
        name: {
            "healthy": provider.is_healthy,
            "quota_remaining": provider.get_quota_remaining_pct(),
            "requests_made": provider.stats.requests_made,
            "avg_latency": provider.stats.avg_latency
        }
        for name, provider in llm_router.providers.items()
    }
```

#### 2.2 Register Router in Main Server

```python
# main_server.py
from api.llm_endpoints import router as llm_router

app.include_router(llm_router)
```

#### 2.3 Test API

```bash
# Start server
python3 main_server.py

# Test chat endpoint
curl -X POST http://localhost:5024/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Recommend a good indica strain"}
    ],
    "task_type": "reasoning"
  }'

# Check provider status
curl http://localhost:5024/api/llm/providers
```

---

### Phase 3: Redis Integration (Week 2)

#### 3.1 Install Redis

```bash
# macOS
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### 3.2 Update Quota Tracker

```python
# services/llm_gateway/quota_tracker.py
import redis.asyncio as redis
from datetime import timedelta

class RedisQuotaTracker:
    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )

    async def track_request(self, provider: str, tokens: int, cost: float):
        """Track request in Redis"""
        pipe = self.redis.pipeline()

        # Increment counters with expiry
        await pipe.incr(f"provider:{provider}:requests:minute")
        await pipe.expire(f"provider:{provider}:requests:minute", 60)

        await pipe.incr(f"provider:{provider}:requests:day")
        await pipe.expire(f"provider:{provider}:requests:day", 86400)

        await pipe.incrby(f"provider:{provider}:tokens:month", tokens)
        await pipe.expire(f"provider:{provider}:tokens:month", 2592000)

        await pipe.incrbyfloat(f"provider:{provider}:cost:month", cost)
        await pipe.expire(f"provider:{provider}:cost:month", 2592000)

        await pipe.execute()

    async def get_usage(self, provider: str) -> Dict:
        """Get usage stats from Redis"""
        return {
            "requests_minute": await self.redis.get(f"provider:{provider}:requests:minute") or 0,
            "requests_day": await self.redis.get(f"provider:{provider}:requests:day") or 0,
            "tokens_month": await self.redis.get(f"provider:{provider}:tokens:month") or 0,
            "cost_month": await self.redis.get(f"provider:{provider}:cost:month") or 0.0
        }
```

---

### Phase 4: Monitoring Dashboard (Week 2)

#### 4.1 Add Analytics Endpoints

```python
# api/llm_endpoints.py

@router.get("/analytics")
async def get_analytics():
    """Get LLM usage analytics"""

    tracker = RedisQuotaTracker()
    analytics = {}

    for provider_name in llm_router.providers.keys():
        usage = await tracker.get_usage(provider_name)
        analytics[provider_name] = usage

    return {
        "providers": analytics,
        "total_requests": sum(p["requests_day"] for p in analytics.values()),
        "total_cost": sum(p["cost_month"] for p in analytics.values()),
        "timestamp": datetime.now().isoformat()
    }
```

#### 4.2 Create Simple Dashboard (Optional)

Add to AI Admin Dashboard:
```typescript
// src/Frontend/ai-admin-dashboard/src/pages/LLMAnalytics.tsx

export const LLMAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetch('/api/llm/analytics')
      .then(res => res.json())
      .then(setAnalytics);
  }, []);

  return (
    <div>
      <h1>LLM Provider Analytics</h1>
      {analytics && (
        <div>
          <p>Total Requests Today: {analytics.total_requests}</p>
          <p>Total Cost This Month: ${analytics.total_cost.toFixed(4)}</p>

          {Object.entries(analytics.providers).map(([name, stats]) => (
            <div key={name}>
              <h3>{name}</h3>
              <p>Requests: {stats.requests_day}</p>
              <p>Tokens: {stats.tokens_month}</p>
              <p>Cost: ${stats.cost_month}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## Step 5: Deployment

### Update requirements.txt:
```txt
# Add to existing requirements.txt

# LLM Router
openai==1.12.0          # OpenAI-compatible client
httpx==0.26.0           # Async HTTP
redis[hiredis]==5.0.1   # Already have this
python-dotenv==1.0.0    # Already have this
```

### Environment Variables for Production:
```bash
# Railway/Render config

OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...

REDIS_URL=redis://red-xxx.redis.cloud:6379

ENVIRONMENT=production
```

### Deploy to Railway:
```bash
# Push to git
git add .
git commit -m "feat: Add LLM Router with multi-provider support"
git push

# Railway auto-deploys!
```

---

## 🎯 Success Checklist

- [ ] POC runs successfully
- [ ] Signed up for all free tier APIs
- [ ] API keys stored in `.env`
- [ ] Tested individual providers
- [ ] Integrated router into FastAPI
- [ ] Redis quota tracking working
- [ ] Monitoring dashboard created
- [ ] Deployed to production
- [ ] Zero-cost operation confirmed!

---

## 📚 Additional Resources

- **POC Results:** See `POC_LLM_ROUTER_RESULTS.md`
- **POC Code:** `src/Backend/llm_router_poc.py` (650 lines)
- **Provider Docs:**
  - OpenRouter: https://openrouter.ai/docs
  - Groq: https://console.groq.com/docs
  - Cloudflare: https://developers.cloudflare.com/workers-ai/

---

## 🆘 Troubleshooting

### "Rate limit exceeded"
- Check quota remaining: `curl http://localhost:5024/api/llm/providers`
- Router should automatically failover to next provider
- If all exhausted, will fall back to local model

### "API key invalid"
- Verify `.env` file exists and has correct keys
- Check environment variable loading: `echo $OPENROUTER_API_KEY`
- Restart server after adding keys

### "Redis connection failed"
- Make sure Redis is running: `redis-cli ping` (should return PONG)
- Check REDIS_URL in .env
- Local development: Use `redis://localhost:6379/0`

### "Provider always returns local"
- Check if API keys are loaded
- Verify providers are healthy: `/api/llm/providers` endpoint
- Check logs for API errors

---

## 💬 Questions?

The POC demonstrates everything needed for production. You now have:

✅ Working code
✅ Comprehensive documentation
✅ Clear implementation path
✅ Cost analysis
✅ Performance benchmarks

**Next:** Sign up for APIs and start integrating! 🚀
