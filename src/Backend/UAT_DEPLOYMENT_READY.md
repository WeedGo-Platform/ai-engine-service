# ✅ UAT Deployment Ready

## 📦 What's Included

### Lightweight Models (541MB)
- ✅ `models-minimal/LLM/qwen2.5-0.5b-instruct-q4_k_m.gguf` (469MB)
- ✅ `models-minimal/voice/tiny.bin` (72MB)

### Deployment Files
- ✅ `Dockerfile.uat` - Optimized UAT dockerfile
- ✅ `.dockerignore` - Excludes `models/` (53GB), includes `models-minimal/` (541MB)
- ✅ `requirements.txt` - Full requirements (unchanged)

### What's Excluded
- ❌ `models/` folder (53GB) - Too large for free tier
- ❌ `data/rag/` - RAG vector database
- ❌ Heavy ML dependencies work via existing requirements.txt

---

## 🚀 Deployment Command

```bash
# Build Docker image
docker build -f Dockerfile.uat -t weedgo-uat-backend .

# Or deploy to Koyeb with archive
koyeb archive create . \
  --ignore-dir "data" \
  --ignore-dir "models" \
  --ignore-dir "checkpoints" \
  --token <your-token>
```

---

## 📊 Expected Image Size

- Base Python image: ~150MB
- Python dependencies: ~500MB
- Application code: ~50MB
- Lightweight models: ~541MB
- **Total**: ~1.24GB ✅ Under 2GB limit

---

## ✅ Ready to Deploy

All files are in place. No code modifications needed - just deployment infrastructure.
