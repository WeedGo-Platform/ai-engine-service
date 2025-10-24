# 🚀 Multi-Environment Deployment Runbook

This guide walks through deploying to all three environments: **UAT**, **Beta**, and **Pre-PROD**.

## 📋 Quick Reference

| Environment | Branch | Backend | Frontend | Database | Redis |
|-------------|--------|---------|----------|----------|-------|
| **UAT** | `develop` | Koyeb | Cloudflare Pages | Neon | Upstash |
| **Beta** | `staging` | Render | Netlify | Supabase | Render |
| **Pre-PROD** | `release` | Railway | Vercel | Railway | Railway |

## 🎯 Deployment Strategy

```
Local Dev → develop (UAT) → staging (Beta) → release (Pre-PROD) → main (PROD - TBD)
```

---

## Environment 1: UAT Deployment

### Prerequisites
- [ ] Cloudflare account with Pages & R2 access
- [ ] Koyeb account (no credit card)
- [ ] Neon PostgreSQL database created
- [ ] Upstash Redis database created

### One-Time Setup

#### 1. Create Neon Database
```bash
# Go to: https://console.neon.tech
# Create project: weedgo-uat
# Enable extensions:
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### 2. Run Database Migrations
```bash
# Copy connection string from Neon dashboard
export DATABASE_URL="postgresql://neondb_owner:xxx@ep-xxx.neon.tech/neondb"

# Run migrations
cd src/Backend
python run_migrations.py --env uat
```

#### 3. Upload Models to Cloudflare R2
```bash
# Install AWS CLI (R2 is S3-compatible)
brew install awscli  # or: pip install awscli

# Configure for R2
aws configure --profile r2
# AWS Access Key ID: [Your R2 Access Key]
# AWS Secret Access Key: [Your R2 Secret Key]
# Default region: auto
# Default output: json

# Upload models
cd src/Backend
aws s3 sync ./models s3://weedgo-uat-models/ \
  --profile r2 \
  --endpoint-url https://[account-id].r2.cloudflarestorage.com
```

#### 4. Deploy Backend to Koyeb
```bash
# Install Koyeb CLI
brew install koyeb/tap/koyeb-cli

# Login
koyeb login

# Create app from GitHub
koyeb app init weedgo-uat \
  --git github.com/yourorg/weedgo \
  --git-branch develop \
  --git-builder dockerfile \
  --git-dockerfile src/Backend/Dockerfile \
  --ports 5024:http \
  --routes /:5024 \
  --env DATABASE_URL=$DATABASE_URL \
  --env UPSTASH_REDIS_REST_URL=$UPSTASH_REDIS_REST_URL \
  --env UPSTASH_REDIS_REST_TOKEN=$UPSTASH_REDIS_REST_TOKEN \
  --regions fra \
  --instance-type free

# Enable auto-deploy on push to develop branch
koyeb app update weedgo-uat --git-autodepl oy
```

#### 5. Deploy Frontends to Cloudflare Pages
```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
npm run build
wrangler pages deploy dist --project-name weedgo-uat-admin

# Deploy Commerce Templates (repeat for each)
cd src/Frontend/weedgo-commerce
npm run build -- --mode headless
wrangler pages deploy dist --project-name weedgo-uat-commerce-headless

npm run build -- --mode pot-palace
wrangler pages deploy dist --project-name weedgo-uat-commerce-pot-palace

npm run build -- --mode modern
wrangler pages deploy dist --project-name weedgo-uat-commerce-modern
```

### Continuous Deployment

Once set up, deployments are automatic:
1. Push to `develop` branch
2. GitHub Actions triggers UAT deployment
3. Backend deploys to Koyeb
4. Frontends deploy to Cloudflare Pages
5. Health checks verify deployment

### Verification

```bash
# Check backend health
curl https://weedgo-uat.koyeb.app/health

# Check frontend (should return 200)
curl -I https://weedgo-uat-admin.pages.dev

# Test API endpoint
curl https://weedgo-uat.koyeb.app/api/v1/products?limit=5
```

### Rollback Procedure

```bash
# Koyeb: Redeploy previous version
koyeb service redeploy weedgo-uat --deployment [previous-deployment-id]

# Cloudflare Pages: Rollback via dashboard
# Go to: Pages → weedgo-uat-admin → Deployments → [previous] → Rollback
```

---

## Environment 2: Beta Deployment

### Prerequisites
- [ ] Netlify account (no credit card)
- [ ] Render account (requires credit card, won't charge)
- [ ] Supabase project created

### One-Time Setup

#### 1. Create Supabase Project
```bash
# Go to: https://supabase.com/dashboard
# Create project: weedgo-beta
# Copy credentials from Settings → API

# Enable extensions in SQL Editor:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# Create storage bucket for models
# Go to: Storage → New Bucket
# Name: models
# Public: No
```

#### 2. Run Database Migrations
```bash
export DATABASE_URL="postgresql://postgres.xxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

cd src/Backend
python run_migrations.py --env beta
```

#### 3. Deploy Backend to Render
```bash
# Go to: https://dashboard.render.com
# New → Web Service
# Connect GitHub repo
# Settings:
#   - Name: weedgo-beta-backend
#   - Branch: staging
#   - Runtime: Python 3
#   - Build Command: pip install -r src/Backend/requirements.txt
#   - Start Command: uvicorn src.Backend.api_server:app --host 0.0.0.0 --port 5024
#   - Plan: Free
# Environment Variables: Add from .env.beta

# Create Redis
# New → Redis
# Name: weedgo-beta-redis
# Plan: Free
# Copy internal Redis URL to backend env vars
```

#### 4. Deploy Frontends to Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
npm run build
netlify deploy --prod --dir=dist --site weedgo-beta-admin

# Deploy Commerce
cd src/Frontend/weedgo-commerce
npm run build -- --mode headless
netlify deploy --prod --dir=dist --site weedgo-beta-commerce
```

### Continuous Deployment

1. Push to `staging` branch
2. Render auto-deploys backend (may take 2-3 minutes)
3. Netlify auto-deploys frontends
4. ⚠️ **Note:** Free Render services sleep after 15min inactivity (first request may be slow)

### Verification

```bash
# Check backend (wait for wake-up on first request)
curl https://weedgo-beta.onrender.com/health

# Check frontend
curl -I https://weedgo-beta-admin.netlify.app

# Test API
curl https://weedgo-beta.onrender.com/api/v1/products?limit=5
```

### Important Beta Limitations

⚠️ **Render Free Tier Limitations:**
- Services sleep after 15 minutes of inactivity
- Free PostgreSQL databases expire after 90 days
- Monthly hours limited to 750 hours

**Mitigation:** Use external cron job to ping service every 10 minutes during business hours:
```bash
# Add to crontab or use services like cron-job.org
*/10 * * * * curl https://weedgo-beta.onrender.com/health
```

---

## Environment 3: Pre-PROD Deployment

### Prerequisites
- [ ] Vercel account (no credit card)
- [ ] Railway account (requires credit card, $5/month usage-based)

### One-Time Setup

#### 1. Create Railway Project
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init weedgo-preprod

# Add PostgreSQL
railway add --database postgresql

# Add Redis
railway add --database redis

# Enable pgvector extension
railway connect postgres
# In psql prompt:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

#### 2. Run Database Migrations
```bash
export DATABASE_URL=$(railway variables get DATABASE_URL)

cd src/Backend
python run_migrations.py --env preprod
```

#### 3. Deploy Backend to Railway
```bash
# Link to GitHub repo
railway link

# Deploy from release branch
railway up --service backend --branch release

# Add volume for model storage
railway volume create models --mount /app/models --size 5
```

#### 4. Deploy Frontends to Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
vercel --prod --name weedgo-preprod-admin

# Deploy Commerce
cd src/Frontend/weedgo-commerce
vercel --prod --name weedgo-preprod-commerce --build-env MODE=headless
```

### Continuous Deployment

1. Push to `release` branch
2. Railway auto-deploys backend
3. Vercel auto-deploys frontends
4. All services always-on (no cold starts)

### Verification

```bash
# Check backend
curl https://weedgo-preprod.up.railway.app/health

# Check frontend
curl -I https://weedgo-preprod-admin.vercel.app

# Test API
curl https://weedgo-preprod.up.railway.app/api/v1/products?limit=5
```

### Railway Credit Monitoring

```bash
# Check usage
railway status

# View credits remaining
railway info
```

⚠️ **Cost Alert:** Railway $5/month credit typically covers:
- 1 backend service (always-on)
- 1 PostgreSQL database
- 1 Redis instance
- 5GB storage volume

Monitor usage at: https://railway.app/account/usage

---

## 📊 Environment Comparison Checklist

After deploying all three, verify:

| Feature | UAT (Cloudflare) | Beta (Netlify) | Pre-PROD (Vercel) |
|---------|------------------|----------------|-------------------|
| Backend Up | [ ] | [ ] | [ ] |
| Admin Dashboard | [ ] | [ ] | [ ] |
| Commerce Storefront | [ ] | [ ] | [ ] |
| Database Connected | [ ] | [ ] | [ ] |
| Redis Connected | [ ] | [ ] | [ ] |
| Health Check Passing | [ ] | [ ] | [ ] |
| CORS Configured | [ ] | [ ] | [ ] |
| SSL Enabled | [ ] | [ ] | [ ] |

---

## 🔄 Deployment Workflow

### Daily Development Flow

```bash
# Feature development
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create PR → develop (triggers UAT deployment after merge)
gh pr create --base develop --title "Add new feature"

# After UAT testing passes, merge to staging (triggers Beta)
git checkout staging
git merge develop
git push

# After Beta testing passes, merge to release (triggers Pre-PROD)
git checkout release
git merge staging
git push

# After Pre-PROD testing passes, merge to main (PROD - when ready)
git checkout main
git merge release
git push
```

### Manual Deployment (Emergency)

```bash
# Deploy specific environment manually via GitHub Actions
gh workflow run deploy-multi-env.yml \
  -f environment=uat  # or beta, preprod, all
```

---

## 🚨 Troubleshooting

### Issue: Backend health check failing

**UAT (Koyeb):**
```bash
# Check logs
koyeb service logs weedgo-uat --follow

# Check service status
koyeb service get weedgo-uat
```

**Beta (Render):**
```bash
# Render dashboard → Logs
# Or use Render CLI:
render services logs weedgo-beta-backend
```

**Pre-PROD (Railway):**
```bash
# Check logs
railway logs --service backend

# Check deployment status
railway status
```

### Issue: Database connection failing

```bash
# Test connection directly
psql $DATABASE_URL -c "SELECT 1"

# For each environment:
# UAT (Neon): Check if IP is whitelisted (Neon has no IP restrictions by default)
# Beta (Supabase): Check connection pooler settings
# Pre-PROD (Railway): Verify DATABASE_URL variable is set
```

### Issue: Frontend showing old version

**Cloudflare Pages:**
```bash
# Purge cache
wrangler pages deployment list --project-name weedgo-uat-admin
wrangler pages deployment delete [deployment-id]
# Then redeploy
```

**Netlify:**
```bash
# Clear cache and redeploy
netlify deploy --prod --dir=dist --clear-cache
```

**Vercel:**
```bash
# Redeploy
vercel --prod --force
```

---

## 📈 Performance Monitoring

### Response Time Comparison

```bash
# Automated test script
#!/bin/bash

echo "Testing UAT (Cloudflare + Koyeb)..."
time curl -s https://weedgo-uat.koyeb.app/api/v1/products?limit=10 > /dev/null

echo "Testing Beta (Netlify + Render)..."
time curl -s https://weedgo-beta.onrender.com/api/v1/products?limit=10 > /dev/null

echo "Testing Pre-PROD (Vercel + Railway)..."
time curl -s https://weedgo-preprod.up.railway.app/api/v1/products?limit=10 > /dev/null
```

### Load Testing

```bash
# Install Apache Bench
brew install apache-bench

# Test each environment
ab -n 100 -c 10 https://weedgo-uat.koyeb.app/api/v1/products
ab -n 100 -c 10 https://weedgo-beta.onrender.com/api/v1/products
ab -n 100 -c 10 https://weedgo-preprod.up.railway.app/api/v1/products
```

---

## 🎯 Success Criteria

Before considering an environment "production-ready", verify:

- [ ] Average response time < 500ms
- [ ] 99.9% uptime over 7 days
- [ ] Zero critical errors in logs
- [ ] All automated tests passing
- [ ] Database migrations successful
- [ ] Redis cache hit rate > 80%
- [ ] SSL certificates valid
- [ ] CORS configured correctly
- [ ] Rate limiting working
- [ ] Authentication/authorization working
- [ ] File uploads functional
- [ ] WebSocket connections stable (for chat)
- [ ] Voice features working (UAT & Pre-PROD only - Render may timeout)

---

## 📞 Support Contacts

| Platform | Status Page | Support |
|----------|-------------|---------|
| Cloudflare | https://www.cloudflarestatus.com | https://community.cloudflare.com |
| Koyeb | https://status.koyeb.com | support@koyeb.com |
| Neon | https://neonstatus.com | support@neon.tech |
| Upstash | https://status.upstash.com | support@upstash.com |
| Netlify | https://www.netlifystatus.com | support@netlify.com |
| Render | https://status.render.com | support@render.com |
| Supabase | https://status.supabase.com | support@supabase.io |
| Vercel | https://www.vercel-status.com | support@vercel.com |
| Railway | https://status.railway.app | team@railway.app |
