# 🔐 Platform Secret Management Setup Guide

**Last Updated**: 2025-10-30
**Purpose**: Guide for securely managing secrets across different deployment platforms

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Koyeb Secrets](#koyeb-secrets-uat-production)
3. [Google Cloud Run](#google-cloud-run)
4. [Vercel Environment Variables](#vercel-environment-variables)
5. [Cloudflare Pages](#cloudflare-pages)
6. [Render](#render)
7. [Railway](#railway)
8. [Local Development](#local-development)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Why Use Platform Secret Managers?

✅ **Security**: Secrets encrypted at rest and in transit
✅ **Access Control**: Role-based access to secrets
✅ **Audit Logs**: Track who accessed secrets when
✅ **Zero Git Exposure**: Secrets never touch your repository
✅ **Easy Rotation**: Update secrets without redeploying code

### Architecture

```
┌─────────────────────────────────────────────┐
│           Git Repository                     │
│  (Public or Private - Doesn't Matter)       │
├─────────────────────────────────────────────┤
│                                              │
│  ✅ Source Code                              │
│  ✅ .env.example (templates)                 │
│  ✅ Configuration (non-sensitive)            │
│                                              │
│  ❌ NO real API keys                         │
│  ❌ NO passwords                             │
│  ❌ NO tokens                                │
└─────────────────────────────────────────────┘
                    ↓
        ┌──────────────────────┐
        │  Platform Deploys    │
        │  Injects Secrets     │
        └──────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        Running Application                   │
│  Environment Variables Available at Runtime  │
└─────────────────────────────────────────────┘
```

---

## Koyeb Secrets (UAT, Production)

### Overview
Koyeb is your primary deployment platform for UAT and Production environments.

### Creating Secrets via CLI

```bash
# Login to Koyeb
koyeb login

# Create a secret
koyeb secret create SECRET_NAME --value "secret-value-here"

# Examples:
koyeb secret create DATABASE_URL --value "postgresql://user:pass@host/db"
koyeb secret create OPENROUTER_API_KEY --value "sk-or-v1-xxxxx"
koyeb secret create JWT_SECRET_KEY --value "your-jwt-secret"
```

### Creating Secrets via Dashboard

1. **Login**: https://app.koyeb.com/
2. **Navigate**: Settings → Secrets
3. **Create**:
   - Click "Create Secret"
   - Name: `OPENROUTER_API_KEY`
   - Value: `sk-or-v1-xxxxx`
   - Click "Create"

### Using Secrets in Services

#### Option 1: Via Dashboard
1. Go to your service
2. Navigate to "Environment Variables"
3. Click "Add Variable"
4. Type: "Secret"
5. Key: `OPENROUTER_API_KEY`
6. Secret: Select from dropdown
7. Save and redeploy

#### Option 2: Via CLI
```bash
koyeb service update weedgo-uat \
  --env OPENROUTER_API_KEY="@OPENROUTER_API_KEY" \
  --env GROQ_API_KEY="@GROQ_API_KEY"
```

#### Option 3: Via koyeb.yaml
```yaml
services:
  - name: weedgo-uat
    env:
      - key: OPENROUTER_API_KEY
        secret: OPENROUTER_API_KEY
      - key: GROQ_API_KEY
        secret: GROQ_API_KEY
      - key: DATABASE_URL
        secret: DATABASE_URL
```

### Complete Setup Example

```bash
# 1. Create all secrets
koyeb secret create DATABASE_URL --value "postgresql://..."
koyeb secret create OPENROUTER_API_KEY --value "sk-or-v1-..."
koyeb secret create GROQ_API_KEY --value "gsk_..."
koyeb secret create TWILIO_AUTH_TOKEN --value "..."
koyeb secret create SENDGRID_API_KEY --value "SG...."
koyeb secret create MAPBOX_API_KEY --value "pk...."
koyeb secret create JWT_SECRET_KEY --value "..."
koyeb secret create SECRET_KEY --value "..."
koyeb secret create UPSTASH_REDIS_REST_URL --value "https://..."
koyeb secret create UPSTASH_REDIS_REST_TOKEN --value "..."

# 2. Deploy service with secrets
koyeb service create weedgo-uat \
  --app weedgo \
  --docker docker.io/your-image:latest \
  --ports 8080:http \
  --routes /:8080 \
  --env OPENROUTER_API_KEY="@OPENROUTER_API_KEY" \
  --env GROQ_API_KEY="@GROQ_API_KEY" \
  --env DATABASE_URL="@DATABASE_URL" \
  --env JWT_SECRET_KEY="@JWT_SECRET_KEY" \
  --env SECRET_KEY="@SECRET_KEY" \
  --env TWILIO_AUTH_TOKEN="@TWILIO_AUTH_TOKEN" \
  --env SENDGRID_API_KEY="@SENDGRID_API_KEY" \
  --env MAPBOX_API_KEY="@MAPBOX_API_KEY" \
  --env UPSTASH_REDIS_REST_URL="@UPSTASH_REDIS_REST_URL" \
  --env UPSTASH_REDIS_REST_TOKEN="@UPSTASH_REDIS_REST_TOKEN"
```

### Managing Secrets

```bash
# List all secrets
koyeb secret list

# Update a secret
koyeb secret update OPENROUTER_API_KEY --value "new-value"

# Delete a secret
koyeb secret delete OLD_SECRET_NAME

# After updating secrets, redeploy:
koyeb service redeploy weedgo-uat
```

---

## Google Cloud Run

### Overview
Google Cloud Secret Manager provides enterprise-grade secret management.

### Setup

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Creating Secrets

```bash
# Create a secret
echo -n "secret-value-here" | gcloud secrets create SECRET_NAME --data-file=-

# Examples:
echo -n "postgresql://user:pass@host/db" | gcloud secrets create DATABASE_URL --data-file=-
echo -n "sk-or-v1-xxxxx" | gcloud secrets create OPENROUTER_API_KEY --data-file=-
echo -n "your-jwt-secret" | gcloud secrets create JWT_SECRET_KEY --data-file=-
```

### Granting Access

```bash
# Grant Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Using Secrets in Cloud Run

#### Option 1: Environment Variables
```bash
gcloud run deploy weedgo-uat \
  --image gcr.io/PROJECT/weedgo:latest \
  --region us-central1 \
  --update-secrets=OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest \
  --update-secrets=DATABASE_URL=DATABASE_URL:latest \
  --update-secrets=JWT_SECRET_KEY=JWT_SECRET_KEY:latest
```

#### Option 2: YAML Configuration
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: weedgo-uat
spec:
  template:
    spec:
      containers:
        - image: gcr.io/PROJECT/weedgo:latest
          env:
            - name: OPENROUTER_API_KEY
              valueFrom:
                secretKeyRef:
                  name: OPENROUTER_API_KEY
                  key: latest
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: DATABASE_URL
                  key: latest
```

Deploy:
```bash
gcloud run services replace cloudrun.yaml --region us-central1
```

### Managing Secrets

```bash
# List secrets
gcloud secrets list

# View secret versions
gcloud secrets versions list SECRET_NAME

# Update a secret (creates new version)
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Access a secret (for debugging)
gcloud secrets versions access latest --secret="SECRET_NAME"

# Delete a secret
gcloud secrets delete SECRET_NAME
```

---

## Vercel Environment Variables

### Overview
Vercel provides environment variables for frontend deployments.

### Via Dashboard

1. **Login**: https://vercel.com/dashboard
2. **Navigate**: Your Project → Settings → Environment Variables
3. **Add Variable**:
   - Name: `VITE_API_URL`
   - Value: `https://api.weedgo.com`
   - Environments: Select Production, Preview, Development
   - Click "Save"

### Via CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Add environment variable
vercel env add VITE_API_URL

# You'll be prompted for:
# - Value
# - Which environments (production, preview, development)

# Pull environment variables to local
vercel env pull .env.local
```

### Environment Types

```bash
# Production (live site)
vercel env add VITE_API_URL production
# Value: https://api.weedgo.com

# Preview (PR deployments)
vercel env add VITE_API_URL preview
# Value: https://weedgo-uat.koyeb.app

# Development (local)
vercel env add VITE_API_URL development
# Value: http://localhost:6024
```

### Frontend .env Setup

```bash
# Create .env.local for local development
cat > .env.local << EOF
VITE_API_URL=http://localhost:6024
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
EOF

# .env.local is already in .gitignore
```

---

## Cloudflare Pages

### Overview
Cloudflare Pages for frontend hosting with environment variables.

### Via Dashboard

1. **Login**: https://dash.cloudflare.com/
2. **Navigate**: Workers & Pages → Your Project → Settings → Environment Variables
3. **Add Variable**:
   - Variable name: `VITE_API_URL`
   - Value: `https://api.weedgo.com`
   - Environment: Production / Preview
   - Save

### Via Wrangler CLI

```bash
# Install Wrangler
npm i -g wrangler

# Login
wrangler login

# Create secret
wrangler pages secret put VITE_API_URL
# Paste value when prompted

# Or from file
echo "https://api.weedgo.com" | wrangler pages secret put VITE_API_URL
```

### Environment-Specific Variables

```bash
# Production
wrangler pages secret put VITE_API_URL --env production
# Enter: https://api.weedgo.com

# Preview
wrangler pages secret put VITE_API_URL --env preview
# Enter: https://weedgo-uat.koyeb.app
```

---

## Render

### Overview
Render provides environment groups and per-service environment variables.

### Via Dashboard

1. **Login**: https://dashboard.render.com/
2. **Navigate**: Your Service → Environment
3. **Add Environment Variable**:
   - Key: `OPENROUTER_API_KEY`
   - Value: `sk-or-v1-xxxxx`
   - Click "Save Changes"
4. Service will auto-redeploy

### Environment Groups

**For shared secrets across services:**

1. Navigate: Environment → Environment Groups
2. Create Group: "WeedGo Shared Secrets"
3. Add variables:
   - `OPENROUTER_API_KEY`
   - `GROQ_API_KEY`
   - `MAPBOX_API_KEY`
4. Link to services

### Via render.yaml

```yaml
services:
  - type: web
    name: weedgo-beta
    env: python
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: weedgo-beta-db
          property: connectionString
      - key: OPENROUTER_API_KEY
        sync: false  # Secret, not synced from repo
      - key: JWT_SECRET_KEY
        generateValue: true  # Auto-generate on first deploy
```

---

## Railway

### Overview
Railway provides project-level and service-level environment variables.

### Via Dashboard

1. **Login**: https://railway.app/
2. **Navigate**: Project → Variables
3. **Add Variable**:
   - Variable: `OPENROUTER_API_KEY`
   - Value: `sk-or-v1-xxxxx`
   - Click outside to save
4. Redeploy if needed

### Via CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Add variable
railway variables set OPENROUTER_API_KEY="sk-or-v1-xxxxx"

# View all variables
railway variables

# Redeploy
railway up
```

### Reference from Another Service

```bash
# Reference database URL from database service
# In your web service variables:
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

---

## Local Development

### Setup .env.test File

```bash
# Navigate to backend
cd src/Backend

# Copy example file
cp .env.test.example .env.test

# Edit with your local secrets
nano .env.test
```

### Get API Keys for Development

1. **OpenRouter**: https://openrouter.ai/keys
   - Create key: "WeedGo Dev"
   - Free tier: 200 requests/day

2. **Groq**: https://console.groq.com/keys
   - Create key: "WeedGo Dev"
   - Free tier: 14,400 requests/day

3. **Mapbox**: https://account.mapbox.com/access-tokens/
   - Create token: "WeedGo Dev"
   - Free tier: 50,000 requests/month

4. **Twilio**: https://console.twilio.com/
   - Use trial account for dev
   - Get Account SID and Auth Token

5. **SendGrid**: https://app.sendgrid.com/settings/api_keys
   - Create key: "WeedGo Dev"
   - Free tier: 100 emails/day

### Local .env.test Template

```bash
# Database (local PostgreSQL)
DATABASE_URL=postgresql://weedgo:password@localhost:5434/ai_engine
DB_HOST=localhost
DB_PORT=5434
DB_NAME=ai_engine
DB_USER=weedgo
DB_PASSWORD=your-local-password

# Security (generate locally)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# API Keys (dev/test keys only!)
OPENROUTER_API_KEY=sk-or-v1-YOUR_DEV_KEY
GROQ_API_KEY=gsk_YOUR_DEV_KEY
MAPBOX_API_KEY=pk.YOUR_DEV_KEY
TWILIO_ACCOUNT_SID=YOUR_TRIAL_SID
TWILIO_AUTH_TOKEN=YOUR_TRIAL_TOKEN
SENDGRID_API_KEY=SG.YOUR_DEV_KEY

# Feature Flags
USE_CLOUD_INFERENCE=true
ENABLE_VOICE=true
ENABLE_RAG=true
```

---

## Best Practices

### 1. Separation of Environments

```
Dev/Test    → Separate API keys (free/trial tiers)
UAT/Staging → Separate API keys (paid plans)
Production  → Dedicated API keys (paid plans with SLA)
```

### 2. Never Commit Secrets

```bash
# Always check before commit
git diff --cached

# If you accidentally add secrets:
git reset HEAD file-with-secrets
git checkout file-with-secrets
```

### 3. Use Different Secrets Per Environment

```
❌ DON'T: Use same JWT_SECRET_KEY everywhere
✅ DO: Generate unique secret for each environment
```

### 4. Rotate Secrets Regularly

```
Production: Every 90 days
UAT/Staging: Every 180 days
Development: Annually or on suspected compromise
```

### 5. Document Secret Locations

Keep a team wiki or doc with:
- Which secrets are used in each environment
- Where they're stored (which platform)
- Who has access
- Last rotation date

### 6. Use Secret Managers for Everything

```
❌ DON'T: Store secrets in:
   - Git repository
   - Deployment scripts
   - CI/CD configs (hardcoded)
   - Shared documents

✅ DO: Store secrets in:
   - Platform secret managers
   - Team password managers (1Password, LastPass)
   - Environment variables (injected at runtime)
```

### 7. Minimum Necessary Access

```
Frontend: Only VITE_* public variables
Backend: Full access to secrets
CI/CD: Read-only access to specific secrets
Developers: Access to dev/test secrets only
```

---

## Troubleshooting

### Secret Not Available at Runtime

**Symptom**: `KeyError: 'OPENROUTER_API_KEY'`

**Solutions**:
```bash
# 1. Check secret exists in platform
koyeb secret list | grep OPENROUTER

# 2. Check service references secret
koyeb service get weedgo-uat | grep OPENROUTER

# 3. Redeploy service
koyeb service redeploy weedgo-uat

# 4. Check application logs
koyeb service logs weedgo-uat
```

### Secret Value Not Updating

**Problem**: Updated secret but app still uses old value

**Solutions**:
```bash
# 1. Ensure secret was updated
koyeb secret list

# 2. Redeploy service (required!)
koyeb service redeploy weedgo-uat

# 3. Check secret version
# For Cloud Run:
gcloud secrets versions list SECRET_NAME
```

### Wrong Environment Getting Secrets

**Problem**: Production using test API keys

**Solutions**:
```bash
# 1. Check which secrets service uses
# Koyeb:
koyeb service get weedgo-prod --output json | jq '.env'

# 2. Verify secret names are correct
# Should be: OPENROUTER_API_KEY (not OPENROUTER_API_KEY_TEST)

# 3. Check secret values (carefully!)
koyeb secret list
```

### Local Development Not Working

**Problem**: Can't connect to services locally

**Solutions**:
```bash
# 1. Check .env.test exists
ls -la src/Backend/.env.test

# 2. Check .env.test has correct values
cat src/Backend/.env.test | grep API_KEY

# 3. Ensure .env.test is loaded
# Add to your app:
from dotenv import load_dotenv
load_dotenv('.env.test')

# 4. Check working directory
pwd  # Should be in project root
```

---

## Security Checklist

Before deploying to any environment:

- [ ] No secrets in git repository
- [ ] No secrets in git history
- [ ] All secrets in platform secret manager
- [ ] .env.example files documented
- [ ] .gitignore protects .env files
- [ ] Different secrets per environment
- [ ] Team has access via password manager
- [ ] Rotation schedule defined
- [ ] Monitoring/alerting configured
- [ ] Access logs reviewed regularly

---

## Additional Resources

- [12-Factor App: Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Koyeb Secrets Documentation](https://www.koyeb.com/docs/reference/secrets)
- [Google Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Cloudflare Pages Env Vars](https://developers.cloudflare.com/pages/platform/build-configuration/#environment-variables)

---

## Quick Reference

### Create Secret
```bash
# Koyeb
koyeb secret create NAME --value "value"

# Google Cloud
echo -n "value" | gcloud secrets create NAME --data-file=-

# Vercel
vercel env add NAME

# Cloudflare
wrangler pages secret put NAME

# Render
# Use dashboard: Environment → Add Variable

# Railway
railway variables set NAME="value"
```

### Update Secret
```bash
# Koyeb
koyeb secret update NAME --value "new-value"
koyeb service redeploy SERVICE_NAME

# Google Cloud
echo -n "new-value" | gcloud secrets versions add NAME --data-file=-

# Vercel
vercel env rm NAME
vercel env add NAME

# Cloudflare
wrangler pages secret put NAME  # Overwrites

# Others: Use dashboard
```

### Delete Secret
```bash
# Koyeb
koyeb secret delete NAME

# Google Cloud
gcloud secrets delete NAME

# Vercel
vercel env rm NAME

# Cloudflare
wrangler pages secret delete NAME
```

---

**Remember**: When in doubt, use the platform secret manager. Never commit secrets to git!
