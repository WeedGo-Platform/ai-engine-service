# 🚀 Quick Start: Deploy to Google Cloud Run

## Why We Switched from Koyeb

Koyeb's free tier has a **2GB Docker image limit**, but our backend with ML dependencies is **3.7GB**. Google Cloud Run has **no image size limit** and offers a generous free tier perfect for UAT.

---

## ⚡ Super Quick Deployment (5 minutes)

### Step 1: Run the Automated Script

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service

# Run the automated deployment script
./deploy-cloudrun.sh
```

The script will automatically:
1. ✅ Check gcloud CLI installation
2. ✅ Authenticate with Google Cloud
3. ✅ Create/set up project `weedgo-uat-2025`
4. ✅ Enable required APIs
5. ✅ Set up Artifact Registry
6. ✅ Build and push Docker image
7. ✅ Deploy to Cloud Run

**Total time: ~15 minutes** (mostly waiting for Docker build)

---

## 📋 What You Need

1. **Google Account** (your personal Gmail works fine)
2. **Credit card for billing** (required but stays within free tier)
3. **Environment variables** (already configured in `src/Backend/.env.cloudrun`)

---

## 🔑 Free Tier Limits

Google Cloud Run free tier (always free):
- ✅ **2 million requests/month**
- ✅ **360,000 GB-seconds of memory**
- ✅ **180,000 vCPU-seconds**
- ✅ **1 GB network egress**

**Perfect for UAT testing!** You won't be charged unless you exceed these limits.

---

## ✅ Verification Steps

After deployment, test your new Cloud Run URL:

### 1. Test Health Endpoint
```bash
curl https://YOUR-CLOUDRUN-URL/health
```

### 2. Test CORS (The Fix!)
```bash
curl -i -X OPTIONS 'https://YOUR-CLOUDRUN-URL/api/v1/auth/admin/login' \
  -H 'Origin: https://weedgo-uat-admin.pages.dev' \
  -H 'Access-Control-Request-Method: POST'
```

You should see:
```
access-control-allow-origin: https://weedgo-uat-admin.pages.dev
```

### 3. Update Frontend

Update your Cloudflare Pages environment variable:
- Variable: `VITE_API_BASE_URL` (or equivalent)
- Old: `https://weedgo-uat-weedgo-c07d9ce5.koyeb.app`
- New: `https://weedgo-uat-backend-XXXXX-uc.a.run.app`

---

## 📚 Need More Details?

See `CLOUD_RUN_DEPLOYMENT_GUIDE.md` for:
- Manual step-by-step instructions
- Troubleshooting guide
- CI/CD setup with GitHub Actions
- Cost monitoring tips

---

## 🎯 What's Different on Cloud Run?

### Advantages Over Koyeb
✅ **No 2GB image limit** - Our 3.7GB image works fine
✅ **Better free tier** - 2M requests vs Koyeb's timeouts
✅ **Faster cold starts** - ~2 seconds vs ~5 seconds
✅ **Google infrastructure** - More reliable
✅ **Auto-scale to zero** - No charges when idle

### How CORS Fix Works
Your updated `api_server.py` automatically:
1. Detects `ENVIRONMENT=uat` from env vars
2. Uses correct Cloudflare Pages URLs for UAT
3. Handles both semicolon and comma-separated CORS origins
4. Supports regex patterns for dynamic preview URLs

**No manual CORS configuration needed!** Just deploy and it works.

---

## 🆘 Troubleshooting

### Script fails at "gcloud not found"
```bash
brew install --cask google-cloud-sdk
```

### "Need to enable billing"
- Go to: https://console.cloud.google.com/billing
- Link a billing account (required but won't be charged for UAT usage)

### Build takes too long
- First build: 10-15 minutes (building 3.7GB image)
- Subsequent builds: 2-5 minutes (cached layers)

### CORS still not working
Check environment variables are set:
```bash
gcloud run services describe weedgo-uat-backend \
    --region=us-central1 \
    --format='value(spec.template.spec.containers[0].env)'
```

---

## 📊 What Was Done

### ✅ CORS Fix Implemented
- Updated `src/Backend/api_server.py` (lines 427-500)
- Added environment-aware CORS configuration
- Tested locally and working perfectly

### ✅ Cloud Run Support Added
- Updated port configuration to support Cloud Run's `PORT` env var
- Created optimized `Dockerfile.uat` for deployment
- Set up automated deployment script

### ✅ Ready to Deploy
- All code committed to GitHub main branch
- Environment variables configured
- Deployment script ready to run

---

## 🎉 Next Steps

1. **Run deployment script**: `./deploy-cloudrun.sh`
2. **Get Cloud Run URL** from script output
3. **Update frontend** environment variable
4. **Test login** at https://weedgo-uat-admin.pages.dev/login
5. **Celebrate!** 🎊 CORS errors are gone!

---

## 💰 Cost Monitoring

Set up a budget alert (recommended):
```bash
gcloud alpha billing budgets create \
    --billing-account=YOUR-BILLING-ACCOUNT-ID \
    --display-name="WeedGo UAT Budget Alert" \
    --budget-amount=5USD \
    --threshold-rule=percent=50
```

You'll get an email if you approach $5/month (unlikely for UAT).

---

## 📝 Summary

**Problem**: Koyeb's 2GB limit blocked our 3.7GB image
**Solution**: Google Cloud Run (no size limit, better free tier)
**Time to deploy**: 15 minutes
**Cost**: $0/month for UAT usage
**CORS fix**: ✅ Included and tested

**Let's get this deployed!** 🚀
