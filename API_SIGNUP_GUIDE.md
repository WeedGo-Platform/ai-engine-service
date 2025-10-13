# API Signup Guide - Free Tier LLM Providers

Complete step-by-step guide to sign up for free LLM APIs.

---

## ✅ Summary

| Provider | Speed | Free Tier | Signup Time | Card Required? |
|----------|-------|-----------|-------------|----------------|
| **OpenRouter** | 2.0s | 200 req/day | 2 min | No |
| **Groq** | 0.5s ⚡ | 14,400 req/day | 2 min | No |

**Total capacity: 14,600+ requests/day for FREE**

---

## 1. OpenRouter (DeepSeek R1 - Reasoning)

### Why OpenRouter?
- **DeepSeek R1**: Best reasoning model (beats GPT-4)
- **200 requests/day**: Perfect for product recommendations
- **$0 cost**: Free tier with no credit card

### Signup Steps:

1. **Go to OpenRouter**
   ```
   https://openrouter.ai/
   ```

2. **Create Account** (Choose one):
   - ✅ **Google** (Recommended - fastest)
   - GitHub
   - MetaMask

3. **Get API Key**:
   - After signup, you'll see your dashboard
   - Navigate to: https://openrouter.ai/keys
   - Click "Create Key" or copy existing key
   - Copy the `OPENROUTER_API_KEY`

4. **Set Environment Variable**:
   ```bash
   # Add to your shell profile (~/.zshrc or ~/.bash_profile)
   export OPENROUTER_API_KEY="sk-or-v1-..."

   # Or set temporarily:
   export OPENROUTER_API_KEY="your_key_here"
   ```

5. **Verify**:
   ```bash
   echo $OPENROUTER_API_KEY
   # Should print your key
   ```

### Free Tier Details:
- **Rate Limits**:
  - 20 requests/minute
  - 200 requests/day
- **Models**: DeepSeek R1 (free)
- **No credit card required**
- **No expiration**

---

## 2. Groq (Llama 3.3 70B - Ultra Fast)

### Why Groq?
- **Lightning Fast**: 0.5s responses (10x faster!)
- **14,400 requests/day**: Massive free tier
- **Llama 3.3 70B**: High quality model
- **Perfect for real-time chat**

### Signup Steps:

1. **Go to Groq Console**
   ```
   https://console.groq.com/
   ```

2. **Create Account**:
   - Click "Start Building" or "Log In"
   - Sign up with:
     - Google (Recommended)
     - GitHub
     - Email

3. **Access Dashboard**:
   - After login, you'll see the Groq Cloud console
   - Look for "API Keys" in the left navigation

4. **Create API Key**:
   - Click "API Keys" → "Create API Key"
   - Name it: "WeedGo AI Engine"
   - Copy the generated key (starts with `gsk_...`)

5. **Set Environment Variable**:
   ```bash
   # Add to your shell profile (~/.zshrc or ~/.bash_profile)
   export GROQ_API_KEY="gsk_..."

   # Or set temporarily:
   export GROQ_API_KEY="your_key_here"
   ```

6. **Verify**:
   ```bash
   echo $GROQ_API_KEY
   # Should print your key
   ```

### Free Tier Details:
- **Rate Limits**:
  - 100 requests/minute (burst)
  - 10 requests/minute (sustained)
  - 14,400 requests/day
  - 6,000 tokens/minute
- **Models**: Llama 3.3 70B, Mixtral, etc.
- **No credit card required**
- **No expiration**

---

## 3. Quick Test After Signup

Once you have both API keys set:

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend

# Test with REAL APIs
python3 test_llm_gateway_real.py
```

**Expected output:**
```
✓ OpenRouter API Key: Set
✓ Groq API Key: Set
✓ Registered OpenRouter (DeepSeek R1)
✓ Groq (Llama 3.3 70B)
✓ Local (tinyllama_1.1b_chat_v1.0.q4_k_m)

✅ SUCCESS - Got REAL response!
  Provider: Groq (Llama 3.3 70B)    ← Should use Groq (fastest)
  Response: [Real AI response]
  Latency: 0.5s                      ← 10x faster than local!
```

---

## 4. Persistent Configuration

To make API keys permanent:

### macOS/Linux:

```bash
# Edit your shell profile
nano ~/.zshrc  # or ~/.bash_profile if using bash

# Add these lines at the end:
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
export GROQ_API_KEY="gsk_YOUR_KEY_HERE"

# Save and reload:
source ~/.zshrc
```

### Verify Persistence:

```bash
# Close and reopen terminal, then:
env | grep -E '(OPENROUTER|GROQ)'

# Should show both keys
```

---

## 5. Troubleshooting

### Issue: "API Key not set"
```bash
# Check if key is set:
echo $OPENROUTER_API_KEY
echo $GROQ_API_KEY

# If empty, set them again:
export OPENROUTER_API_KEY="your_key"
export GROQ_API_KEY="your_key"
```

### Issue: "Rate limit exceeded"
- OpenRouter: Wait 1 minute (20/min limit) or 24 hours (200/day limit)
- Groq: Wait 1 minute (10/min sustained limit)
- Router will automatically failover to next provider

### Issue: "Provider unavailable"
- Check internet connection
- Verify API key is valid
- Router will automatically use fallback provider

---

## 6. Cost Comparison

### With Free Tiers (What we built):
- **OpenRouter**: $0
- **Groq**: $0
- **Local**: $0
- **Total**: **$0/month** ✅

### Without (Typical paid approach):
- GPT-4: ~$40/month
- Claude: ~$30/month
- Local GPU server: ~$50/month
- **Total**: **$120/month** ❌

**Savings: $120/month = $1,440/year**

---

## 7. Next Steps After Signup

1. ✅ **Sign up for both APIs** (you are here)
2. ✅ **Set environment variables**
3. ✅ **Run test**: `python3 test_llm_gateway_real.py`
4. 🔲 **Integrate with FastAPI** (Week 2)
5. 🔲 **Add Redis rate limiting** (Week 2)
6. 🔲 **Deploy to production** (Week 3)

---

## 8. Support

### OpenRouter:
- Docs: https://openrouter.ai/docs
- Discord: https://discord.gg/openrouter
- Status: https://status.openrouter.ai/

### Groq:
- Docs: https://console.groq.com/docs
- Discord: https://groq.com/discord
- Status: https://status.groq.com/

---

**🎉 Once you complete these signups, you'll have access to 14,600+ FREE AI requests per day!**
