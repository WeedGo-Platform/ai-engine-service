# Koyeb GitHub Deployment Guide

## Overview
This guide configures Koyeb to automatically build and deploy from your GitHub repository, ensuring the latest code (including CORS fixes) is deployed.

## Prerequisites
- Koyeb account with admin access
- GitHub repository: `WeedGo-Platform/ai-engine-service`
- Environment variables already configured in Koyeb (they will be preserved)

## Step-by-Step Configuration

### 1. Access Service Settings
1. Go to: https://app.koyeb.com/services/59872c17/settings
2. Log in if prompted

### 2. Change Deployment Source
**Current setup:** Docker image (cached, not updating with new code)
**Target setup:** GitHub repository (auto-builds on push)

1. Find the **"Build and deployment"** section
2. Look for **"Source"** or **"Deployment method"**
3. Change from **"Docker"** to **"GitHub"** or **"Git repository"**

### 3. Connect GitHub Repository
1. Click **"Connect GitHub"** or **"Authorize GitHub"**
2. Authorize Koyeb to access your GitHub account
3. Select organization: **WeedGo-Platform**
4. Select repository: **ai-engine-service**

### 4. Configure Build Settings
Set these values:

| Setting | Value |
|---------|-------|
| **Branch** | `main` |
| **Build method** | `Dockerfile` |
| **Dockerfile path** | `./Dockerfile` (or `src/Backend/Dockerfile` if applicable) |
| **Build context** | `./` or `.` (root of repository) |
| **Region** | `fra` (Frankfurt) - keep existing |
| **Instance type** | `free` or current type |

### 5. Verify Environment Variables
The following environment variables should already be set and will be preserved:

```bash
# These are already configured - verify they're still present
ENVIRONMENT=uat
DATABASE_URL=postgresql://neondb_owner:...
DB_HOST=ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_49xrIFTtaqym
DB_PORT=5432
UPSTASH_REDIS_REST_URL=https://powerful-ladybird-21805.upstash.io
UPSTASH_REDIS_REST_TOKEN=AVUtAAIncDI...
JWT_SECRET_KEY=G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=
CORS_ALLOWED_ORIGINS=https://weedgo-uat-admin.pages.dev;...
CORS_ORIGIN_REGEX=https://.*\.weedgo-uat-admin\.pages\.dev|...
```

### 6. Deploy
1. Click **"Save"** or **"Update service"**
2. Koyeb will automatically:
   - Clone the repository
   - Build from the Dockerfile
   - Deploy the new image with environment variables
   - Run health checks

### 7. Monitor Deployment
```bash
# Check deployment status
koyeb deployment list --service 59872c17 --token YOUR_TOKEN | head -5

# Watch deployment logs
koyeb deployment logs <DEPLOYMENT_ID> --type build --token YOUR_TOKEN
koyeb deployment logs <DEPLOYMENT_ID> --type runtime --token YOUR_TOKEN

# Check service health
curl https://weedgo-uat-weedgo-c07d9ce5.koyeb.app/health
```

## Verification

### Check CORS is Working
```bash
# Test CORS preflight
curl -i -X OPTIONS 'https://weedgo-uat-weedgo-c07d9ce5.koyeb.app/api/v1/auth/admin/login' \
  -H 'Origin: https://weedgo-uat-admin.pages.dev' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type'

# Should include this header:
# access-control-allow-origin: https://weedgo-uat-admin.pages.dev
```

### Check Backend Logs
```bash
# Look for CORS configuration logs
koyeb service logs 59872c17 --token YOUR_TOKEN | grep "CORS"

# Should see one of:
# "Using CORS origins from CORS_ALLOWED_ORIGINS environment variable"
# OR
# "Using CORS origins for uat environment"
```

### Test Login
1. Go to: https://weedgo-uat-admin.pages.dev/login
2. Enter credentials:
   - Email: `admin@weedgo.ca`
   - Password: `Password1$`
3. Should successfully log in without CORS errors

## Automatic Deployments

After setup, deployments will trigger automatically:
- **Push to `main` branch** → Koyeb builds and deploys
- **GitHub Actions workflow** → Also triggers Koyeb redeploy
- **Environment variables** → Set once, persist across deployments

## Troubleshooting

### Build Fails
**Check Dockerfile location:**
```bash
# Repository structure should be:
ai-engine-service/
├── Dockerfile (root level)
└── src/
    └── Backend/
        └── api_server.py
```

If Dockerfile is in `src/Backend/`, update Dockerfile path to: `src/Backend/Dockerfile`

### CORS Still Not Working
**Verify logs show CORS configuration:**
```bash
koyeb service logs 59872c17 --token YOUR_TOKEN | grep -A 5 "Using CORS"
```

Should see:
```
Using CORS origins for uat environment: ['https://weedgo-uat-admin.pages.dev', ...]
```

### Environment Variables Not Applied
**Re-save environment variables:**
1. Go to service settings
2. Click into Environment Variables section
3. Click "Save" even if no changes
4. Redeploy

## Benefits of GitHub Deployment

✅ **Always latest code** - Every deployment builds from latest commit
✅ **Environment-aware CORS** - Automatically detects UAT and uses correct origins
✅ **No manual configuration** - CORS works without setting environment variables
✅ **Fallback support** - Can still override with CORS_ALLOWED_ORIGINS if needed
✅ **CI/CD ready** - Integrates with GitHub Actions workflow

## Next Steps

Once GitHub deployment is configured:

1. **Test CORS** - Verify login works without errors
2. **Monitor first deployment** - Check logs for any issues
3. **Update documentation** - Mark this setup as complete
4. **Set up webhooks** (optional) - For instant deployments on push

---

## Summary

The new CORS code is **tested and working locally**. Configuring GitHub deployment will:
- Deploy the working code to Koyeb
- Automatically detect `ENVIRONMENT=uat` and use correct CORS origins
- Eliminate CORS issues permanently
- Enable automatic deployments from GitHub

**Estimated time: 5-10 minutes**
