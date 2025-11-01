# Google Cloud Run Deployment Guide - UAT Backend

## Why Cloud Run?
- ✅ **No 2GB image size limit** (handles our 3.7GB image)
- ✅ **Truly free tier**: 2M requests/month, 360,000 GB-seconds
- ✅ **Auto-scales to zero** (no charges when idle)
- ✅ **Fast deployment** from Docker images
- ✅ **Better performance** than Koyeb free tier

---

## Prerequisites
- Google account (can use personal Gmail)
- Docker image with CORS fix (already built locally)
- 10 minutes of time

---

## Step 1: Set Up Google Cloud Project

### 1.1 Create/Select Project
```bash
# Authenticate with Google Cloud
gcloud auth login

# Create a new project (or use existing one)
gcloud projects create weedgo-uat-2025 --name="WeedGo UAT"

# Set as active project
gcloud config set project weedgo-uat-2025

# Link billing account (required for Cloud Run, but stays within free tier)
# You'll be prompted to enable billing in the console
gcloud beta billing projects link weedgo-uat-2025
```

### 1.2 Enable Required APIs
```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Artifact Registry (for storing Docker images)
gcloud services enable artifactregistry.googleapis.com

# Enable Cloud Build (for building images)
gcloud services enable cloudbuild.googleapis.com
```

---

## Step 2: Build and Push Docker Image

### 2.1 Create Artifact Registry Repository
```bash
# Create repository in us-central1 (free tier region)
gcloud artifacts repositories create weedgo-uat \
    --repository-format=docker \
    --location=us-central1 \
    --description="WeedGo UAT Backend Images"

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 2.2 Build and Push Image
```bash
# Navigate to backend directory
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend

# Build image with Cloud Run tag
docker build -t us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:cors-fix -f Dockerfile.uat .

# Push to Artifact Registry (this may take 5-10 minutes for 3.7GB image)
docker push us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:cors-fix
```

---

## Step 3: Deploy to Cloud Run

### 3.1 Create Environment Variables File
Create a file named `.env.cloudrun` with your environment variables:

```bash
cat > .env.cloudrun << 'EOF'
ENVIRONMENT=uat
DATABASE_URL=postgresql://neondb_owner:npg_49xrIFTtaqym@ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
DB_HOST=ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_49xrIFTtaqym
DB_PORT=5432
UPSTASH_REDIS_REST_URL=https://powerful-ladybird-21805.upstash.io
UPSTASH_REDIS_REST_TOKEN=AVUtAAIncDI...
JWT_SECRET_KEY=G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=
CORS_ALLOWED_ORIGINS=https://weedgo-uat-admin.pages.dev;https://weedgo-uat-commerce-headless.pages.dev;https://weedgo-uat-commerce-pot-palace.pages.dev;https://weedgo-uat-commerce-modern.pages.dev
CORS_ORIGIN_REGEX=https://.*\.weedgo-uat-.*\.pages\.dev
PORT=8080
EOF
```

### 3.2 Deploy Service
```bash
# Deploy to Cloud Run
gcloud run deploy weedgo-uat-backend \
    --image=us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:cors-fix \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --port=5024 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --env-vars-file=.env.cloudrun \
    --set-env-vars=PORT=8080

# Note: Cloud Run requires apps to listen on PORT env var (defaults to 8080)
# You may need to update api_server.py to use PORT env var
```

---

## Step 4: Update Backend to Use PORT Environment Variable

Cloud Run requires your app to listen on the port specified by the `PORT` environment variable.

Update `api_server.py`:

```python
# Find the line that starts uvicorn
# Change from:
uvicorn.run(app, host="0.0.0.0", port=5024)

# To:
import os
port = int(os.getenv("PORT", 5024))
uvicorn.run(app, host="0.0.0.0", port=port)
```

Then rebuild and redeploy:
```bash
# Rebuild with PORT support
docker build -t us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:latest -f Dockerfile.uat .
docker push us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:latest

# Redeploy
gcloud run deploy weedgo-uat-backend \
    --image=us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:latest \
    --region=us-central1
```

---

## Step 5: Get Service URL and Test

### 5.1 Get Cloud Run URL
```bash
# Get the service URL
gcloud run services describe weedgo-uat-backend \
    --region=us-central1 \
    --format='value(status.url)'

# Example output: https://weedgo-uat-backend-abc123-uc.a.run.app
```

### 5.2 Test CORS
```bash
# Test CORS preflight
curl -i -X OPTIONS 'https://YOUR-CLOUDRUN-URL/api/v1/auth/admin/login' \
  -H 'Origin: https://weedgo-uat-admin.pages.dev' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type'

# Should see:
# access-control-allow-origin: https://weedgo-uat-admin.pages.dev
# access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
```

### 5.3 Test Health Endpoint
```bash
curl https://YOUR-CLOUDRUN-URL/health
# Should return: {"status":"healthy"}
```

---

## Step 6: Update Frontend Configuration

Update your Cloudflare Pages frontend to use the new Cloud Run URL:

1. Go to Cloudflare Pages dashboard
2. Navigate to Settings > Environment Variables
3. Update `VITE_API_BASE_URL` or equivalent:
   - Old: `https://weedgo-uat-weedgo-c07d9ce5.koyeb.app`
   - New: `https://YOUR-CLOUDRUN-URL`

4. Redeploy frontend to pick up new environment variable

---

## Step 7: Test Login Flow

1. Go to: https://weedgo-uat-admin.pages.dev/login
2. Enter credentials:
   - Email: `admin@weedgo.ca`
   - Password: `Password1$`
3. Should successfully log in without CORS errors!

---

## Cost Monitoring

### Free Tier Limits (Always Free)
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds of compute time
- 1 GB network egress

### Check Usage
```bash
# View service metrics
gcloud run services describe weedgo-uat-backend \
    --region=us-central1 \
    --format='table(status.url,status.traffic)'

# Set up billing alerts (recommended)
gcloud alpha billing budgets create \
    --billing-account=YOUR-BILLING-ACCOUNT-ID \
    --display-name="WeedGo UAT Budget Alert" \
    --budget-amount=5USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90
```

---

## Continuous Deployment (Optional)

### Option A: Deploy from GitHub (Recommended)
```bash
# Connect Cloud Run to your GitHub repository
gcloud run services update weedgo-uat-backend \
    --source=https://github.com/WeedGo-Platform/ai-engine-service \
    --source-revision=main \
    --region=us-central1
```

### Option B: GitHub Actions CI/CD
Create `.github/workflows/deploy-cloudrun.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths:
      - 'src/Backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Build and Push
        run: |
          gcloud builds submit src/Backend \
            --tag=us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy weedgo-uat-backend \
            --image=us-central1-docker.pkg.dev/weedgo-uat-2025/weedgo-uat/backend:${{ github.sha }} \
            --region=us-central1
```

---

## Troubleshooting

### Build Fails
**Check build logs:**
```bash
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Deployment Fails
**Check service logs:**
```bash
gcloud run services logs read weedgo-uat-backend --region=us-central1 --limit=50
```

### CORS Still Not Working
**Verify environment variables:**
```bash
gcloud run services describe weedgo-uat-backend \
    --region=us-central1 \
    --format='value(spec.template.spec.containers[0].env)'
```

**Check application logs for CORS configuration:**
```bash
gcloud run services logs read weedgo-uat-backend \
    --region=us-central1 \
    --filter='textPayload:"CORS"'
```

### Cold Starts Too Slow
**Increase minimum instances (costs money):**
```bash
gcloud run services update weedgo-uat-backend \
    --region=us-central1 \
    --min-instances=1
```

---

## Comparison: Cloud Run vs Koyeb

| Feature | Cloud Run | Koyeb Free |
|---------|-----------|------------|
| Image Size Limit | None | 2 GB |
| Cold Start | ~2 seconds | ~3-5 seconds |
| Always On | Optional ($$) | ✅ Free |
| Free Requests | 2M/month | 2.5M/month |
| Memory | Up to 32GB | 512MB |
| Custom Domains | ✅ Free | ✅ Free |
| Auto-scale to Zero | ✅ | ❌ |

---

## Next Steps

1. **Complete authentication**: Run `gcloud auth login`
2. **Create project**: `gcloud projects create weedgo-uat-2025`
3. **Build and push**: Follow Step 2 commands
4. **Deploy**: Run deploy command from Step 3.2
5. **Update frontend**: Point to new Cloud Run URL
6. **Test**: Verify CORS is working

**Estimated time**: 15-20 minutes (mostly waiting for Docker push)

---

## Summary

✅ **No image size limit** - Your 3.7GB image is fine
✅ **Truly free** - Within free tier limits for UAT usage
✅ **CORS fix deployed** - Latest code with environment-aware CORS
✅ **Auto-scales** - Handles traffic spikes, scales to zero when idle
✅ **Better performance** - Google's infrastructure
✅ **Easy CI/CD** - Connect to GitHub for automatic deployments

The CORS fix you implemented will work perfectly on Cloud Run because:
- Environment variable `ENVIRONMENT=uat` is automatically detected
- Correct Cloudflare Pages URLs are used
- No manual CORS configuration needed
