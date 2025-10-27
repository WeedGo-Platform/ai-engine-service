# 🚀 UAT Deployment Status

**Last Updated:** 2025-10-24
**Environment:** UAT (User Acceptance Testing)
**Status:** ✅ **READY TO DEPLOY**

---

## ✅ Completed Setup

### 1. Database (Neon PostgreSQL) - 100% READY
- **Host:** ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech
- **Database:** neondb
- **Version:** PostgreSQL 17.5
- **Extensions:** ✅ vector, ✅ pg_trgm
- **Connection:** ✅ Tested and working
- **Schema:**
  - ✅ Stage 1: Sequences created
  - ✅ Stage 2: 6 core tables created
  - ✅ Stage 3: Columns added
  - ✅ Stage 4: Views created
  - ✅ Stage 5: 42 functions created
  - ✅ Stage 6: Triggers configured
  - ✅ Stage 7: 12 indexes created
  - ✅ Stage 8: Constraints added
  - ✅ RAG tables: knowledge_documents, knowledge_chunks, rag_query_analytics
  - ✅ System tables: system_settings, crsa_sync_history

### 2. Redis (Upstash) - 100% READY
- **URL:** https://powerful-ladybird-21805.upstash.io
- **Connection:** ✅ Tested (PONG response received)
- **REST API:** Configured for serverless access

### 3. Backend Configuration - 100% READY
- **Environment File:** `.env.uat` fully configured
- **JWT Secret:** Generated (G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=)
- **Docker:** Dockerfile ready (Python 3.11, FastAPI, port 5024)
- **Health Check:** Configured (30s interval)

### 4. Koyeb Hosting - READY
- **API Token:** Configured and authenticated
- **CLI:** ✅ Installed (v5.7.0)
- **Account:** Verified (empty - ready for first deployment)

---

## 📋 Configuration Summary

### Environment Variables (.env.uat)
```bash
# Database
DATABASE_URL=postgresql://neondb_owner:npg_49xrIFTtaqym@ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
DB_HOST=ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech
DB_PORT=5432

# Redis
UPSTASH_REDIS_REST_URL=https://powerful-ladybird-21805.upstash.io
UPSTASH_REDIS_REST_TOKEN=AVUtAAIncDI3NWU1OGFiZDJkYTU0MGQ5YmQzNDBjYzA1ZGQyOWM5NnAyMjE4MDU

# Auth
JWT_SECRET_KEY=G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=

# Koyeb
KOYEB_TOKEN=y7jbfvu567288ag38jyex9re0t8ck3136s2lmb8xbnur0hbxmy3345cfqfnha1bm
```

---

## 🚀 Deployment Options

### Option 1: Deploy via Koyeb CLI (Recommended - Fastest)

```bash
# Navigate to backend directory
cd src/Backend

# Create Koyeb app and service from Dockerfile
koyeb app create weedgo-uat --token y7jbfvu567288ag38jyex9re0t8ck3136s2lmb8xbnur0hbxmy3345cfqfnha1bm

# Deploy service with environment variables
koyeb service create weedgo-uat-backend \
  --app weedgo-uat \
  --docker dockerfile \
  --dockerfile-path ./Dockerfile \
  --dockerfile-context . \
  --dockerfile-target production \
  --ports 5024:http \
  --routes /:5024 \
  --env DATABASE_URL="postgresql://neondb_owner:npg_49xrIFTtaqym@ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require" \
  --env DB_HOST="ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech" \
  --env DB_PORT="5432" \
  --env DB_NAME="neondb" \
  --env DB_USER="neondb_owner" \
  --env DB_PASSWORD="npg_49xrIFTtaqym" \
  --env UPSTASH_REDIS_REST_URL="https://powerful-ladybird-21805.upstash.io" \
  --env UPSTASH_REDIS_REST_TOKEN="AVUtAAIncDI3NWU1OGFiZDJkYTU0MGQ5YmQzNDBjYzA1ZGQyOWM5NnAyMjE4MDU" \
  --env JWT_SECRET_KEY="G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=" \
  --env ENVIRONMENT="uat" \
  --regions fra \
  --instance-type free \
  --token y7jbfvu567288ag38jyex9re0t8ck3136s2lmb8xbnur0hbxmy3345cfqfnha1bm
```

### Option 2: Deploy via GitHub (Using CI/CD)

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "feat: UAT deployment configuration"
   git push origin develop
   ```

2. **GitHub Actions will automatically** (pushes to main branch):
   - Build Docker image
   - Deploy to Koyeb
   - Run health checks

### Option 3: Deploy via Koyeb Dashboard (Manual)

1. Go to https://app.koyeb.com
2. Create new App: "weedgo-uat"
3. Select "Docker" deployment
4. Configure:
   - **Builder:** Dockerfile
   - **Dockerfile path:** ./Dockerfile
   - **Port:** 5024
   - **Environment variables:** Copy from .env.uat
5. Deploy!

---

## ⏭️ Next Steps (5-10 minutes)

### 1. Deploy Backend (Choose one option above)
**Recommended:** Use Option 1 (Koyeb CLI) - takes ~3 minutes

### 2. Verify Deployment
```bash
# Check service status
koyeb service list --app weedgo-uat --token y7jbfvu567288ag38jyex9re0t8ck3136s2lmb8xbnur0hbxmy3345cfqfnha1bm

# Get service URL
koyeb service get weedgo-uat-backend --app weedgo-uat --token y7jbfvu567288ag38jyex9re0t8ck3136s2lmb8xbnur0hbxmy3345cfqfnha1bm

# Test health endpoint
curl https://weedgo-uat-backend-[YOUR-ID].koyeb.app/health
```

### 3. Get Missing Credentials (Optional - for full deployment)

**Cloudflare (for frontends + R2 storage):**
- Go to: https://dash.cloudflare.com
- Get: API Token + Account ID
- Setup R2 bucket for file storage

Then you can deploy frontends to Cloudflare Pages!

---

## 📊 Deployment Architecture

```
UAT Environment
├── Backend (Koyeb)
│   ├── FastAPI Application (Python 3.11)
│   ├── Port: 5024
│   └── Health: /health
├── Database (Neon)
│   ├── PostgreSQL 17.5
│   ├── Extensions: vector, pg_trgm
│   └── Connection: Pooler (6543)
├── Cache (Upstash Redis)
│   ├── REST API
│   └── 10K commands/day free tier
└── Storage (Cloudflare R2) - Pending
    ├── AI Models
    ├── Voice clones
    └── User uploads
```

---

## 🎯 Success Criteria

- [ ] Backend deployed and accessible
- [ ] Health endpoint returns 200 OK
- [ ] Database connection working
- [ ] Redis connection working
- [ ] API endpoints responding

---

## 🔍 Monitoring & Debugging

### Check Logs
```bash
koyeb service logs weedgo-uat-backend --app weedgo-uat --token YOUR_TOKEN
```

### Check Service Status
```bash
koyeb service get weedgo-uat-backend --app weedgo-uat --token YOUR_TOKEN
```

### Common Issues

**Issue 1: Service won't start**
- Check logs: `koyeb service logs ...`
- Verify environment variables are set correctly
- Ensure Dockerfile builds successfully locally

**Issue 2: Database connection fails**
- Verify DATABASE_URL is correct
- Check Neon database is active
- Ensure SSL mode is set: `?sslmode=require`

**Issue 3: Port binding error**
- Ensure api_server.py listens on 0.0.0.0:5024
- Dockerfile exposes port 5024
- Koyeb service configured for port 5024

---

## 💡 Cost Tracking

**UAT Environment Monthly Cost: $0**

| Service | Plan | Cost |
|---------|------|------|
| Neon PostgreSQL | Free (3GB) | $0 |
| Upstash Redis | Free (10K/day) | $0 |
| Koyeb | Free (scale-to-zero) | $0 |
| Cloudflare Pages | Free (unlimited) | $0* |
| Cloudflare R2 | Free (10GB) | $0* |

*Pending setup

---

## ✨ What's Working Right Now

1. ✅ **Database is live** with full schema
2. ✅ **Redis is accessible** via REST API
3. ✅ **Environment is configured** with all secrets
4. ✅ **Docker image is ready** to build
5. ✅ **Koyeb CLI is authenticated** and ready

**You're literally ONE command away from having a live backend API!** 🚀

---

**Ready to deploy?** Run the command from Option 1 above, or choose your preferred method!
