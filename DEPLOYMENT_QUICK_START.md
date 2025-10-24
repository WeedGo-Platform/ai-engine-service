# 🚀 Quick Start: Triple-Environment Deployment

This guide gets you from zero to all three environments deployed in < 2 hours.

---

## 📝 What You're Building

**45 Total Deployments:**
- 14 frontends × 3 environments = 42 frontend deployments
- 1 backend × 3 environments = 3 backend deployments

**Monthly Cost: $0-5** (vs $250+ on AWS/GCP/Azure)

---

## ⚡ 30-Minute Setup (All Platforms)

### Step 1: Create Accounts (10 minutes)

Open these links in new tabs and sign up:

**UAT Environment:**
- [ ] [Cloudflare](https://dash.cloudflare.com/sign-up) - No CC
- [ ] [Koyeb](https://app.koyeb.com/auth/signup) - No CC
- [ ] [Neon](https://console.neon.tech/signup) - No CC
- [ ] [Upstash](https://console.upstash.com/login) - No CC

**Beta Environment:**
- [ ] [Netlify](https://app.netlify.com/signup) - No CC
- [ ] [Render](https://dashboard.render.com/register) - ⚠️ Requires CC
- [ ] [Supabase](https://supabase.com/dashboard/sign-in) - No CC

**Pre-PROD Environment:**
- [ ] [Vercel](https://vercel.com/signup) - No CC
- [ ] [Railway](https://railway.app/login) - ⚠️ Requires CC

**Mobile (All Environments):**
- [ ] [Expo](https://expo.dev/signup) - No CC

---

### Step 2: Install CLI Tools (10 minutes)

```bash
# Package managers
brew install awscli  # For Cloudflare R2 (S3-compatible)

# Platform CLIs
npm install -g wrangler          # Cloudflare
npm install -g netlify-cli       # Netlify
npm install -g vercel            # Vercel
npm install -g @railway/cli      # Railway
npm install -g eas-cli           # Expo Application Services
brew install koyeb/tap/koyeb-cli # Koyeb

# Verify installations
wrangler --version
netlify --version
vercel --version
railway --version
eas --version
koyeb version
```

---

### Step 3: Update Environment Files (10 minutes)

Fill in credentials from your account dashboards:

**Backend:**
```bash
# Edit these files with your actual values:
nano .env.uat
nano .env.beta
nano .env.preprod
```

**Frontend (for each app):**
```bash
# Admin Dashboard
cd src/Frontend/ai-admin-dashboard
nano .env.uat
nano .env.beta
nano .env.preprod

# Repeat for weedgo-commerce, chat-commerce-web, mobile
```

---

## 🎯 Environment 1: UAT (30 minutes)

### Database Setup (5 minutes)

```bash
# 1. Go to: https://console.neon.tech
# 2. Create project: weedgo-uat
# 3. In SQL Editor, run:

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# 4. Copy connection string to .env.uat
```

### Redis Setup (3 minutes)

```bash
# 1. Go to: https://console.upstash.com
# 2. Create Redis database: weedgo-uat-redis
# 3. Enable REST API
# 4. Copy URL and token to .env.uat
```

### Storage Setup (5 minutes)

```bash
# 1. Go to: https://dash.cloudflare.com → R2
# 2. Create bucket: weedgo-uat-models
# 3. Generate API token
# 4. Copy credentials to .env.uat

# Upload models (if you have them locally)
cd src/Backend
aws s3 sync ./models s3://weedgo-uat-models/ \
  --profile r2 \
  --endpoint-url https://[your-account-id].r2.cloudflarestorage.com
```

### Backend Deployment (10 minutes)

```bash
# Login
koyeb login

# Deploy
cd src/Backend
koyeb service create weedgo-uat-backend \
  --docker Dockerfile \
  --ports 5024:http \
  --env-file ../../.env.uat \
  --regions fra \
  --instance-type free

# Check status
koyeb service logs weedgo-uat-backend --follow
```

### Frontend Deployment (7 minutes)

```bash
# Login
wrangler login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
cp .env.uat .env
npm run build
wrangler pages deploy dist --project-name weedgo-uat-admin

# Deploy Commerce (headless template)
cd ../weedgo-commerce
cp .env.uat .env.headless
npm run build -- --mode headless
wrangler pages deploy dist --project-name weedgo-uat-commerce

# Repeat for other templates as needed
```

### Verify UAT

```bash
curl https://weedgo-uat.koyeb.app/health
# Should return: {"status":"ok"}

open https://weedgo-uat-admin.pages.dev
```

---

## 🎯 Environment 2: Beta (30 minutes)

### Database Setup (5 minutes)

```bash
# 1. Go to: https://supabase.com/dashboard
# 2. Create project: weedgo-beta
# 3. In SQL Editor, run:

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# 4. Go to Storage → Create bucket: models
# 5. Copy all credentials to .env.beta
```

### Backend Deployment (10 minutes)

```bash
# 1. Go to: https://dashboard.render.com
# 2. New → Web Service
# 3. Connect GitHub repo
# 4. Settings:
#    - Name: weedgo-beta-backend
#    - Branch: staging
#    - Runtime: Python 3
#    - Build: pip install -r src/Backend/requirements.txt
#    - Start: cd src/Backend && uvicorn api_server:app --host 0.0.0.0 --port 5024
# 5. Add environment variables from .env.beta
# 6. Create

# Create Redis:
# New → Redis → weedgo-beta-redis → Free
# Copy internal URL to backend env vars
```

### Frontend Deployment (15 minutes)

```bash
# Login
netlify login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
cp .env.beta .env
npm run build
netlify deploy --prod --dir=dist --site weedgo-beta-admin

# Deploy Commerce
cd ../weedgo-commerce
cp .env.beta .env.headless
npm run build -- --mode headless
netlify deploy --prod --dir=dist --site weedgo-beta-commerce
```

### Verify Beta

```bash
# Wait ~30 seconds for Render to start
curl https://weedgo-beta.onrender.com/health

open https://weedgo-beta-admin.netlify.app
```

---

## 🎯 Environment 3: Pre-PROD (30 minutes)

### Database Setup (5 minutes)

```bash
# Install Railway CLI if not done
railway login

# Create project
railway init weedgo-preprod

# Add PostgreSQL
railway add --database postgresql

# Add Redis
railway add --database redis

# Enable pgvector
railway connect postgres
# In psql:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q

# Get DATABASE_URL
railway variables
# Copy to .env.preprod
```

### Backend Deployment (10 minutes)

```bash
# Link repo
cd src/Backend
railway link

# Deploy
railway up --service backend

# Add volume for models
railway volume create models --mount /app/models --size 5

# Check logs
railway logs
```

### Frontend Deployment (15 minutes)

```bash
# Login
vercel login

# Deploy Admin Dashboard
cd src/Frontend/ai-admin-dashboard
cp .env.preprod .env
vercel --prod --name weedgo-preprod-admin

# Deploy Commerce
cd ../weedgo-commerce
cp .env.preprod .env.headless
vercel --prod --name weedgo-preprod-commerce --build-env MODE=headless
```

### Verify Pre-PROD

```bash
curl https://weedgo-preprod.up.railway.app/health

open https://weedgo-preprod-admin.vercel.app
```

---

## 🤖 Automated Deployment Setup (10 minutes)

### Configure GitHub Secrets

```bash
# Go to: GitHub repo → Settings → Secrets and variables → Actions
# Add these secrets (values from your platform dashboards):
```

**UAT Secrets:**
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `KOYEB_TOKEN`

**Beta Secrets:**
- `NETLIFY_AUTH_TOKEN`
- `NETLIFY_SITE_ID_BETA_ADMIN`
- `RENDER_DEPLOY_HOOK_BETA`

**Pre-PROD Secrets:**
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `RAILWAY_TOKEN`

### Test Automated Deployment

```bash
# Create a test commit
git checkout -b test-deployment
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger deployment"

# Push to develop (triggers UAT)
git push origin test-deployment

# Merge to staging (triggers Beta)
git checkout staging
git merge test-deployment
git push

# Merge to release (triggers Pre-PROD)
git checkout release
git merge staging
git push

# Check GitHub Actions
gh run list
gh run watch
```

---

## 📊 Monitor All Environments (5 minutes)

```bash
# Run performance comparison
cd src/Backend
python monitoring/environment_comparison.py

# Open dashboard
open environment_comparison.html
```

**You'll see:**
- Response times for all 3 environments
- Success rates
- Performance winner by category
- Detailed endpoint breakdown

---

## ✅ Success Checklist

After completing all steps, verify:

**UAT:**
- [ ] Backend: https://weedgo-uat.koyeb.app/health returns 200
- [ ] Admin: https://weedgo-uat-admin.pages.dev loads
- [ ] Database: Can query Neon via psql
- [ ] Redis: Can connect via upstash-redis CLI

**Beta:**
- [ ] Backend: https://weedgo-beta.onrender.com/health returns 200 (may take 30s first time)
- [ ] Admin: https://weedgo-beta-admin.netlify.app loads
- [ ] Database: Can query Supabase via psql
- [ ] Redis: Can connect via Render Redis URL

**Pre-PROD:**
- [ ] Backend: https://weedgo-preprod.up.railway.app/health returns 200
- [ ] Admin: https://weedgo-preprod-admin.vercel.app loads
- [ ] Database: Can query Railway Postgres
- [ ] Redis: Can connect via Railway Redis

**Automation:**
- [ ] GitHub Actions workflow file exists: `.github/workflows/deploy-multi-env.yml`
- [ ] All secrets configured in GitHub repo
- [ ] Test push to `develop` triggers UAT deployment
- [ ] Monitoring dashboard runs successfully

---

## 🎉 You're Done!

**Total setup time: ~2 hours**
**Total monthly cost: $0-5**
**Total deployments: 45**

### What You've Achieved:

✅ **Three independent production-ready environments**
✅ **Automated CI/CD pipeline** (push to deploy)
✅ **Performance monitoring dashboard**
✅ **Multi-cloud redundancy** (built-in failover)
✅ **Cost comparison data** (Cloudflare vs Netlify vs Vercel)
✅ **Zero vendor lock-in**

### Next Steps:

1. **Deploy remaining frontends** - You deployed 2 out of 14 apps
2. **Run database migrations** - Populate initial data
3. **Set up mobile apps** - Configure EAS build for each environment
4. **Monitor for 7 days** - Collect performance data
5. **Choose production platform** - Based on real data

---

## 🆘 Common Issues

### "Backend health check failing"

```bash
# Check logs
koyeb service logs weedgo-uat-backend --tail 100
render services logs weedgo-beta-backend
railway logs --service backend

# Common fixes:
# 1. Verify DATABASE_URL is set correctly
# 2. Check if models uploaded to storage
# 3. Ensure Redis credentials are correct
```

### "Frontend shows 404"

```bash
# Redeploy frontend
cd src/Frontend/[app-name]
npm run build
# Then deploy again to platform
```

### "Database connection refused"

```bash
# Test connection directly
psql $DATABASE_URL -c "SELECT 1"

# Common fixes:
# 1. Check if database is active (Neon/Supabase dashboard)
# 2. Verify SSL mode (Neon requires sslmode=require)
# 3. Check IP whitelist (usually not needed for these platforms)
```

---

## 📚 Full Documentation

- **Complete Strategy:** `TRIPLE_ENVIRONMENT_DEPLOYMENT_STRATEGY.md`
- **Detailed Runbook:** `DEPLOYMENT_RUNBOOK.md`
- **CI/CD Pipeline:** `.github/workflows/deploy-multi-env.yml`
- **Monitoring Script:** `src/Backend/monitoring/environment_comparison.py`

---

**Happy Deploying! 🚀**
