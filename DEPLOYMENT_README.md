# 🚀 WeedGo Triple-Environment Deployment System

## Overview

This repository includes a **production-ready, multi-cloud deployment strategy** across three independent environments: UAT, Beta, and Pre-PROD. Each environment runs on different hosting platforms to enable performance comparison, cost analysis, and built-in failover capabilities.

**Monthly Cost: $0-5** (vs $250+ on traditional cloud providers)

---

## 📁 Repository Structure

```
.
├── .env.uat                          # UAT backend configuration
├── .env.beta                         # Beta backend configuration
├── .env.preprod                      # Pre-PROD backend configuration
├── .github/
│   └── workflows/
│       └── deploy-multi-env.yml      # Automated CI/CD pipeline
├── scripts/
│   ├── setup-github-secrets.sh       # Interactive secrets setup
│   ├── deploy-environment.sh         # Manual deployment helper
│   └── health-check-all.sh           # Health check all environments
├── src/
│   ├── Backend/
│   │   ├── monitoring/
│   │   │   ├── environment_comparison.py  # Performance dashboard
│   │   │   └── cost_tracker.py           # Cost tracking & alerts
│   │   └── ...
│   └── Frontend/
│       ├── ai-admin-dashboard/
│       │   ├── .env.uat
│       │   ├── .env.beta
│       │   └── .env.preprod
│       ├── weedgo-commerce/
│       │   ├── .env.uat
│       │   ├── .env.beta
│       │   └── .env.preprod
│       ├── chat-commerce-web/
│       │   ├── .env.uat
│       │   ├── .env.beta
│       │   └── .env.preprod
│       └── mobile/weedgo-mobile/
│           ├── .env.uat
│           ├── .env.beta
│           └── .env.preprod
├── DEPLOYMENT_QUICK_START.md         # 2-hour setup guide
├── DEPLOYMENT_RUNBOOK.md             # Detailed deployment procedures
└── TRIPLE_ENVIRONMENT_DEPLOYMENT_STRATEGY.md  # Full strategic overview
```

---

## 🎯 Quick Start

### 1. Read the Documentation (5 minutes)

Start with these docs in order:

1. **[DEPLOYMENT_QUICK_START.md](./DEPLOYMENT_QUICK_START.md)** - Get all 3 environments live in ~2 hours
2. **[TRIPLE_ENVIRONMENT_DEPLOYMENT_STRATEGY.md](./TRIPLE_ENVIRONMENT_DEPLOYMENT_STRATEGY.md)** - Full strategic overview
3. **[DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md)** - Detailed step-by-step procedures

### 2. Set Up GitHub Secrets (10 minutes)

```bash
# Make script executable
chmod +x scripts/setup-github-secrets.sh

# Run interactive setup
./scripts/setup-github-secrets.sh
```

This script will guide you through adding all required secrets to GitHub Actions.

### 3. Deploy Your First Environment (30 minutes)

Start with UAT:

```bash
# Deploy UAT environment
./scripts/deploy-environment.sh uat

# Check health
./scripts/health-check-all.sh
```

---

## 🏗️ Environment Architecture

| Environment | Branch | Backend | Frontends | Database | Redis | Cost |
|-------------|--------|---------|-----------|----------|-------|------|
| **UAT** | `develop` | Koyeb | Cloudflare Pages | Neon | Upstash | $0 |
| **Beta** | `staging` | Render | Netlify | Supabase | Render | $0* |
| **Pre-PROD** | `release` | Railway | Vercel | Railway | Railway | $0-5 |

*Beta has limitations: Render services sleep after 15min idle, free DB expires in 90 days

---

## 🔄 Git Workflow

```
feature/* → develop (UAT) → staging (Beta) → release (Pre-PROD) → main (PROD)
              ↓                 ↓                  ↓
         Auto-deploy      Auto-deploy        Auto-deploy
```

### Example: Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-payment-method

# 2. Make changes, commit
git add .
git commit -m "feat: add new payment method"

# 3. Push and create PR to develop
git push origin feature/new-payment-method
gh pr create --base develop --title "Add new payment method"

# 4. After PR is merged, UAT auto-deploys
# Test in UAT environment

# 5. Promote to Beta
git checkout staging
git merge develop
git push  # Auto-deploys to Beta

# 6. Promote to Pre-PROD
git checkout release
git merge staging
git push  # Auto-deploys to Pre-PROD

# 7. When ready for production
git checkout main
git merge release
git push  # Production deployment (TBD strategy)
```

---

## 🛠️ Useful Commands

### Deployment

```bash
# Deploy to specific environment
./scripts/deploy-environment.sh uat
./scripts/deploy-environment.sh beta
./scripts/deploy-environment.sh preprod

# Deploy to all environments
./scripts/deploy-environment.sh all
```

### Health Checks

```bash
# Check all environments
./scripts/health-check-all.sh

# Manual health check
curl https://weedgo-uat.koyeb.app/health
curl https://weedgo-beta.onrender.com/health
curl https://weedgo-preprod.up.railway.app/health
```

### Monitoring

```bash
# Performance comparison across environments
cd src/Backend
python monitoring/environment_comparison.py
open environment_comparison.html

# Cost tracking and free tier monitoring
python monitoring/cost_tracker.py
open cost_tracking_report.html
```

### GitHub Actions

```bash
# View recent deployments
gh run list

# Watch current deployment
gh run watch

# Manually trigger deployment
gh workflow run deploy-multi-env.yml -f environment=uat
```

---

## 📊 Monitoring Dashboards

### 1. Performance Comparison Dashboard

**File:** `environment_comparison.html` (generated by `environment_comparison.py`)

Shows:
- Response times across all 3 environments
- Success rates
- P95 latency
- Winner by category (fastest, most reliable)

**Run daily:**
```bash
cd src/Backend
python monitoring/environment_comparison.py
```

### 2. Cost Tracking Dashboard

**File:** `cost_tracking_report.html` (generated by `cost_tracker.py`)

Shows:
- Usage vs free tier limits for each platform
- Warnings when approaching limits (>80%)
- Recommendations for cost optimization
- Projected costs if free tiers exceeded

**Run weekly:**
```bash
cd src/Backend
python monitoring/cost_tracker.py
```

---

## ⚠️ Known Limitations & Solutions

### UAT (Cloudflare + Koyeb + Neon)

**Limitation:** Neon free tier has 3GB storage limit

**Solution:**
- Monitor storage usage with alerts at 2.5GB (83%)
- Run `cost_tracker.py` weekly to track usage
- Plan for Neon Pro upgrade ($19/month) when needed

### Beta (Netlify + Render + Supabase)

**Limitations:**
- ⚠️ Render free services sleep after 15min idle (first request slow)
- ⚠️ Render free PostgreSQL expires after 90 days
- Netlify has 100GB bandwidth limit

**Solutions:**
- Use external cron job to ping service every 10 min: `*/10 * * * * curl https://weedgo-beta.onrender.com/health`
- Use Supabase instead of Render PostgreSQL (no expiration)
- Monitor Netlify bandwidth in dashboard

### Pre-PROD (Vercel + Railway)

**Limitation:** Railway $5/month credit may exceed with heavy usage

**Solutions:**
- Monitor Railway usage dashboard weekly
- Set up billing alerts in Railway at $4/month
- Optimize database queries to reduce compute time
- Consider upgrading to Railway Pro if consistently exceeding

---

## 🚀 Deployment Checklist

### Initial Setup (One-Time)

- [ ] Read all documentation
- [ ] Create accounts on all 9 platforms (see DEPLOYMENT_QUICK_START.md)
- [ ] Install CLI tools: `wrangler`, `netlify`, `vercel`, `railway`, `koyeb`, `eas-cli`
- [ ] Run `./scripts/setup-github-secrets.sh`
- [ ] Update all `.env.*` files with actual values
- [ ] Deploy UAT environment
- [ ] Deploy Beta environment
- [ ] Deploy Pre-PROD environment
- [ ] Verify all health checks passing
- [ ] Run first performance comparison
- [ ] Run first cost tracking report

### Daily Operations

- [ ] Monitor GitHub Actions for deployment status
- [ ] Check error logs in Sentry/monitoring tools
- [ ] Review failed deployments (if any)

### Weekly Operations

- [ ] Run `environment_comparison.py` to track performance
- [ ] Run `cost_tracker.py` to monitor free tier usage
- [ ] Review and optimize slow endpoints
- [ ] Check Railway credit usage (Pre-PROD)

### Monthly Operations

- [ ] Review hosting costs and usage trends
- [ ] Backup databases from all environments
- [ ] Rotate API keys and secrets
- [ ] Update dependency versions
- [ ] Performance audit and optimization
- [ ] Review deployment strategy based on collected data

---

## 📚 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **DEPLOYMENT_QUICK_START.md** | 2-hour setup guide | When setting up for the first time |
| **TRIPLE_ENVIRONMENT_DEPLOYMENT_STRATEGY.md** | Full strategic overview | Understanding the overall architecture |
| **DEPLOYMENT_RUNBOOK.md** | Detailed procedures | Step-by-step deployment instructions |
| **DEPLOYMENT_README.md** | This file | Quick reference and overview |

---

## 🆘 Troubleshooting

### "GitHub Actions failing to deploy"

1. Check secrets are configured: `https://github.com/yourorg/yourrepo/settings/secrets/actions`
2. Verify `.github/workflows/deploy-multi-env.yml` exists
3. Check GitHub Actions logs: `gh run view`

### "Backend health check failing"

1. Check platform-specific logs:
   - UAT: `koyeb service logs weedgo-uat-backend --follow`
   - Beta: Render dashboard → Logs
   - Pre-PROD: `railway logs --service backend`

2. Verify environment variables are set correctly
3. Check database connection: `psql $DATABASE_URL -c "SELECT 1"`

### "Frontend showing 404"

1. Verify build succeeded in GitHub Actions
2. Check platform-specific deployment logs
3. Redeploy manually if needed:
   ```bash
   cd src/Frontend/[app-name]
   npm run build
   # Then deploy to platform
   ```

### "Database connection refused"

1. Check if database is active in platform dashboard
2. Verify connection string in `.env.*` files
3. For Neon: Ensure `sslmode=require` in connection string
4. For Railway: Verify `DATABASE_URL` variable exists

---

## 💰 Cost Breakdown

### Current Costs (Free Tier)

| Platform | Service | Free Tier | Monthly Cost |
|----------|---------|-----------|--------------|
| Cloudflare | Pages (14 apps) | Unlimited bandwidth | **$0** |
| Cloudflare | R2 Storage (10GB) | Zero egress fees | **$0** |
| Koyeb | Backend (1 service) | Scale-to-zero | **$0** |
| Neon | PostgreSQL (3GB) | 1 project | **$0** |
| Upstash | Redis (10K cmd/day) | REST API | **$0** |
| Netlify | Pages (14 apps) | 100GB bandwidth | **$0** |
| Render | Backend + Redis | Sleeps after 15min | **$0** |
| Supabase | PostgreSQL (500MB) | 2 projects | **$0** |
| Vercel | Pages (14 apps) | 100GB bandwidth | **$0** |
| Railway | All-in-one | $5/month credit | **$0-5** |
| Expo EAS | Builds (30/month) | Standard queue | **$0** |
| **TOTAL** | | | **$0-5/month** |

### If Free Tiers Exceeded

| Platform | Paid Plan | Monthly Cost |
|----------|-----------|--------------|
| Cloudflare Pages | Pro (unlimited builds) | $20 |
| Neon | Pro (10GB) | $19 |
| Upstash | Pro (100K cmd/day) | $10 |
| Netlify | Pro | $19 |
| Render | Starter (always-on) | $7 |
| Supabase | Pro | $25 |
| Vercel | Pro | $20 |
| Railway | Usage-based | $5-20 |
| Expo EAS | Production | $29 |
| **TOTAL** | | **$154-174/month** |

**Savings with Free Tier Strategy: $149-169/month ($1,788-2,028/year)**

---

## 🏆 Success Metrics

Your deployment strategy is successful when:

✅ All 45 deployments (15 apps × 3 environments) are live
✅ CI/CD automatically deploys to all environments on push
✅ Monitoring dashboards track performance across all platforms
✅ Zero critical errors in any environment for 7 consecutive days
✅ Performance comparison data collected for 30 days
✅ Failover testing demonstrates < 5 minute recovery time
✅ Total monthly cost remains under $10 across all environments
✅ Team can confidently choose production platform based on data

---

## 📞 Support

### Platform Support

- Cloudflare: https://community.cloudflare.com
- Koyeb: support@koyeb.com
- Neon: support@neon.tech
- Upstash: support@upstash.com
- Netlify: support@netlify.com
- Render: support@render.com
- Supabase: support@supabase.io
- Vercel: support@vercel.com
- Railway: team@railway.app

### Internal Documentation

- GitHub Issues: Report bugs and request features
- Team Chat: Discuss deployment strategies
- Weekly Standup: Review deployment metrics

---

## 🎓 Learning Resources

### Platform Documentation

- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Koyeb Docs](https://www.koyeb.com/docs)
- [Neon Docs](https://neon.tech/docs)
- [Upstash Docs](https://docs.upstash.com/)
- [Netlify Docs](https://docs.netlify.com/)
- [Render Docs](https://render.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app/)

### Best Practices

- [12-Factor App Methodology](https://12factor.net/)
- [Multi-Cloud Architecture Patterns](https://cloud.google.com/architecture)
- [CI/CD Best Practices](https://about.gitlab.com/topics/ci-cd/)

---

**Version:** 1.0
**Last Updated:** 2025-01-23
**Maintained By:** Engineering Team
**Status:** Production Ready

**Questions?** Open an issue or check the documentation links above.

🚀 Happy Deploying!
