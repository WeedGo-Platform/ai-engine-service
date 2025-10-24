# 🚀 Triple-Environment Deployment Strategy

## Executive Summary

This document outlines the **multi-cloud, zero-cost deployment strategy** for the WeedGo Cannabis Commerce Platform across three independent environments: **UAT**, **Beta**, and **Pre-PROD**. Each environment uses different hosting platforms to enable performance comparison, cost analysis, and built-in redundancy/failover capabilities.

---

## 🎯 Strategic Objectives

1. **Performance Benchmarking** - Real-world data comparing Cloudflare, Netlify, and Vercel
2. **Cost Validation** - Verify which "free tier" platforms remain sustainable under load
3. **Redundancy & Failover** - Three independent infrastructures provide natural disaster recovery
4. **Platform Evaluation** - Test platform-specific features before committing to production
5. **Risk Mitigation** - No vendor lock-in; proven alternatives ready to deploy

---

## 📊 Environment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  WeedGo Multi-Environment Setup                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  UAT Environment (develop branch)                               │
│  ├─ 14 Frontends → Cloudflare Pages (Unlimited bandwidth)      │
│  ├─ Backend API → Koyeb (Scale-to-zero, no CC required)        │
│  ├─ PostgreSQL → Neon (3GB, pgvector support)                  │
│  ├─ Redis → Upstash (10K commands/day, REST API)               │
│  └─ Storage → Cloudflare R2 (10GB, zero egress fees)           │
│                                                                 │
│  Beta Environment (staging branch)                              │
│  ├─ 14 Frontends → Netlify (100GB bandwidth, JAMstack)         │
│  ├─ Backend API → Render (Free, sleeps after 15min)            │
│  ├─ PostgreSQL → Supabase (500MB, pgvector support)            │
│  ├─ Redis → Render Redis (Included with backend)               │
│  └─ Storage → Supabase Storage (1GB)                           │
│                                                                 │
│  Pre-PROD Environment (release branch)                          │
│  ├─ 14 Frontends → Vercel (100GB bandwidth, Edge Functions)    │
│  ├─ Backend API → Railway (Always-on, usage-based)             │
│  ├─ PostgreSQL → Railway (Shared with backend)                 │
│  ├─ Redis → Railway Redis (Shared credits)                     │
│  └─ Storage → Railway Volumes (5GB)                            │
│                                                                 │
│  Mobile (All Environments)                                      │
│  └─ Expo EAS Build → 3 separate release channels               │
│     ├─ uat channel → UAT backend                               │
│     ├─ beta channel → Beta backend                             │
│     └─ preprod channel → Pre-PROD backend                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Application Inventory

### Frontend Applications (14 deployments total)

| App | Templates/Instances | Port Range | Tech Stack |
|-----|---------------------|------------|------------|
| **weedgo-commerce** | 3 (pot-palace, modern, headless) | 3000, 3004, 3005 | React 19 + Vite 7 + PWA |
| **ai-admin-dashboard** | 1 | 3003 | React 18 + Vite 5 + i18n (29 languages) |
| **chat-commerce-web** | 8 (8 different themes) | 5173-5180 | React 19 + Vite 7 + Socket.io |
| **weedgo-mobile** | 3 (one per environment) | Native | React Native + Expo 54 |

**Total**: 15 deployments across 3 environments = **45 total deployments**

### Backend Services

- **Python FastAPI Backend** (api_server.py)
  - AI/ML: llama-cpp-python, sentence-transformers
  - RAG: pgvector, faiss-cpu, spacy, NLTK
  - Voice: Coqui TTS (XTTS v2), StyleTTS2, Google Cloud TTS
  - Auth: JWT, Passlib, python-jose
  - Real-time: WebSockets for chat
  - Monitoring: OpenTelemetry, Prometheus

### Database Requirements

- **PostgreSQL 16** with extensions:
  - `pgvector` - Vector embeddings for RAG/semantic search
  - `pg_trgm` - Fuzzy text matching for product search
  - `uuid-ossp` - UUID generation

- **Redis 7**
  - Session management
  - Rate limiting
  - Caching layer
  - Real-time pub/sub

- **File Storage**
  - ML models (~8GB): XTTS v2, StyleTTS2, embeddings
  - User uploads: Product images, voice samples
  - Backups: Database snapshots

---

## 💰 Cost Analysis

### Monthly Costs by Environment

| Environment | Platform Costs | Free Tier Limits | Estimated Usage | Monthly Cost |
|-------------|----------------|------------------|-----------------|--------------|
| **UAT** | Cloudflare + Koyeb + Neon + Upstash | All unlimited/generous | 50-100 users, moderate load | **$0** |
| **Beta** | Netlify + Render + Supabase | 100GB BW, 750h compute | 20-50 users, light load | **$0*** |
| **Pre-PROD** | Vercel + Railway | $5 credit/month | 30-80 users, testing load | **$0-5** |

**Total Across All 3 Environments: $0-5/month**

*Beta Render limitations: Services sleep after 15min idle, free PostgreSQL expires after 90 days

### Cost Comparison: Free vs Traditional Cloud

| Setup | UAT | Beta | Pre-PROD | **TOTAL** |
|-------|-----|------|----------|-----------|
| **Free Tier Strategy** | $0 | $0 | $0-5 | **$0-5/month** |
| **AWS Equivalent** | $85 | $85 | $85 | **$255/month** |
| **GCP Equivalent** | $90 | $90 | $90 | **$270/month** |
| **Azure Equivalent** | $95 | $95 | $95 | **$285/month** |

**Annual Savings: $3,000 - $3,400**

---

## 🔄 Git Workflow & Deployment Pipeline

### Branch Strategy

```
feature/* → develop (UAT) → staging (Beta) → release (Pre-PROD) → main (PROD)
              ↓                 ↓                  ↓
         Auto-deploy      Auto-deploy        Auto-deploy
```

### Continuous Deployment

**GitHub Actions automatically deploys on push:**

| Branch | Environment | Trigger | Backend | Frontends | Mobile |
|--------|-------------|---------|---------|-----------|--------|
| `develop` | UAT | Push/PR merge | Koyeb | Cloudflare Pages | EAS `uat` |
| `staging` | Beta | Push/PR merge | Render | Netlify | EAS `beta` |
| `release` | Pre-PROD | Push/PR merge | Railway | Vercel | EAS `preprod` |
| `main` | PROD (TBD) | Manual trigger | TBD | TBD | EAS `production` |

### Deployment Timeline

From commit to live:
- **UAT**: ~3-5 minutes (Koyeb + Cloudflare Pages)
- **Beta**: ~5-10 minutes (Render wake + Netlify) - longer if cold start
- **Pre-PROD**: ~4-7 minutes (Railway + Vercel)

---

## 📈 Performance Benchmarking

### Automated Monitoring

Run daily performance comparison:

```bash
python src/Backend/monitoring/environment_comparison.py
```

Generates:
- `environment_comparison.html` - Visual dashboard
- `environment_comparison.json` - API data for tracking

### Key Metrics Tracked

| Metric | Description | Target |
|--------|-------------|--------|
| **Response Time (Avg)** | Average API response time | <500ms |
| **Response Time (P95)** | 95th percentile response | <1000ms |
| **Success Rate** | % of successful requests | >99% |
| **Uptime** | % time service is available | >99.9% |
| **Cold Start Time** | Time to wake from sleep (Beta only) | <15s |
| **Database Query Time** | Avg database query duration | <100ms |

### Historical Performance Data

**Week 1 Example Results:**

| Environment | Avg Response | P95 | Success Rate | Cold Start |
|-------------|--------------|-----|--------------|------------|
| UAT (Cloudflare + Koyeb) | 245ms | 420ms | 99.8% | N/A (always on) |
| Beta (Netlify + Render) | 380ms* | 2100ms* | 97.2% | 12s* |
| Pre-PROD (Vercel + Railway) | 210ms | 380ms | 99.9% | N/A (always on) |

*Beta performance impacted by Render free tier limitations (cold starts)

**Winner by Category:**
- 🏆 Fastest Average: Pre-PROD (Railway)
- 🏆 Most Reliable: Pre-PROD (Railway)
- 🏆 Best Free Option: UAT (Cloudflare + Koyeb)

---

## 🔧 Configuration Management

### Environment Variables

Each environment has dedicated config files:

**Backend:**
- `.env.uat` - UAT environment (Neon, Upstash, R2)
- `.env.beta` - Beta environment (Supabase, Render Redis)
- `.env.preprod` - Pre-PROD environment (Railway all-in-one)

**Frontend (per app):**
- `.env.uat` - Points to `weedgo-uat.koyeb.app`
- `.env.beta` - Points to `weedgo-beta.onrender.com`
- `.env.preprod` - Points to `weedgo-preprod.up.railway.app`

### Secrets Management

**GitHub Actions Secrets Required:**

```yaml
# UAT Environment
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
KOYEB_TOKEN
NEON_CONNECTION_STRING
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY

# Beta Environment
NETLIFY_AUTH_TOKEN
RENDER_DEPLOY_HOOK_BETA
SUPABASE_URL
SUPABASE_SERVICE_KEY

# Pre-PROD Environment
VERCEL_TOKEN
VERCEL_ORG_ID
RAILWAY_TOKEN
```

---

## 🛡️ Redundancy & Failover Strategy

### Traffic Routing

Use DNS load balancing to distribute traffic:

```nginx
# Example: Route 90% to primary, 10% to beta for comparison
upstream weedgo_backends {
    server weedgo-uat.koyeb.app weight=90;
    server weedgo-beta.onrender.com weight=10;
    server weedgo-preprod.up.railway.app backup;  # Failover only
}
```

### Automatic Failover

Implement health check monitoring:

```python
# Pseudo-code for DNS failover
if uat_health_check_fails:
    route_traffic_to = "beta"
    alert_team("UAT down, failover to Beta")

if uat_health_check_fails and beta_health_check_fails:
    route_traffic_to = "preprod"
    alert_team("UAT and Beta down, failover to Pre-PROD")
```

### Database Synchronization (Optional)

For true redundancy, implement hourly database replication:

```bash
# Neon → Supabase → Railway
pg_dump $NEON_DB_URL | psql $SUPABASE_DB_URL
pg_dump $NEON_DB_URL | psql $RAILWAY_DB_URL
```

**Note:** This is optional for UAT/Beta/Pre-PROD as they typically have isolated test data.

---

## 📋 Deployment Checklist

### Initial Setup (One-Time)

#### UAT Environment
- [ ] Create Cloudflare account, enable Pages & R2
- [ ] Create Koyeb account (no CC)
- [ ] Create Neon PostgreSQL database
- [ ] Enable pgvector & pg_trgm extensions
- [ ] Create Upstash Redis database
- [ ] Upload ML models to R2
- [ ] Deploy backend to Koyeb
- [ ] Deploy 14 frontends to Cloudflare Pages
- [ ] Configure GitHub Actions secrets
- [ ] Test all deployments

#### Beta Environment
- [ ] Create Netlify account (no CC)
- [ ] Create Render account (requires CC)
- [ ] Create Supabase project
- [ ] Enable pgvector & pg_trgm extensions
- [ ] Create Render Redis
- [ ] Create Supabase storage bucket
- [ ] Deploy backend to Render
- [ ] Deploy 14 frontends to Netlify
- [ ] Configure GitHub Actions secrets
- [ ] Set up health check ping (mitigate cold starts)
- [ ] Test all deployments

#### Pre-PROD Environment
- [ ] Create Vercel account (no CC)
- [ ] Create Railway account (requires CC, $5/month)
- [ ] Create Railway PostgreSQL & Redis
- [ ] Enable pgvector extension
- [ ] Create Railway volume for models
- [ ] Deploy backend to Railway
- [ ] Deploy 14 frontends to Vercel
- [ ] Configure GitHub Actions secrets
- [ ] Test all deployments

#### Mobile (All Environments)
- [ ] Create Expo account
- [ ] Configure 3 release channels (uat, beta, preprod)
- [ ] Build and publish to each channel
- [ ] Distribute to testers via TestFlight/Internal Testing

### Daily Operations

- [ ] Monitor environment_comparison dashboard
- [ ] Check for failed deployments in GitHub Actions
- [ ] Review error logs in Sentry/monitoring tools
- [ ] Track free tier usage limits
- [ ] Respond to platform status page notifications

### Weekly Operations

- [ ] Run full integration tests on all 3 environments
- [ ] Compare performance metrics week-over-week
- [ ] Review and optimize slow endpoints
- [ ] Update documentation if infrastructure changes

### Monthly Operations

- [ ] Review hosting costs (Railway usage, any overages)
- [ ] Backup databases from all environments
- [ ] Rotate API keys and secrets
- [ ] Update dependency versions
- [ ] Performance audit and optimization

---

## 🚨 Known Limitations & Mitigation

### UAT (Cloudflare + Koyeb + Neon)

**Limitations:**
- Koyeb free tier: 1 service only
- Neon free tier: 3GB storage limit

**Mitigation:**
- Monitor storage usage with alerts at 2.5GB (83%)
- Plan for Neon Pro upgrade ($19/month) if needed

### Beta (Netlify + Render + Supabase)

**Limitations:**
- ⚠️ Render free services sleep after 15min idle
- ⚠️ Render free PostgreSQL expires after 90 days
- Netlify: 100GB bandwidth limit
- Supabase: 500MB storage limit

**Mitigation:**
- External cron job pings service every 10 min during business hours
- Use Supabase instead of Render PostgreSQL (no expiration)
- Monitor Netlify bandwidth usage
- Alert at 400MB storage usage (80%)

### Pre-PROD (Vercel + Railway)

**Limitations:**
- Railway: $5/month credit (may exceed with heavy usage)
- Vercel: 100GB bandwidth limit

**Mitigation:**
- Monitor Railway usage dashboard weekly
- Set up billing alerts in Railway
- Optimize database queries to reduce compute
- Cache aggressively to reduce bandwidth

---

## 📞 Support & Resources

### Platform Documentation

| Platform | Docs | Status Page | Support |
|----------|------|-------------|---------|
| Cloudflare | [docs.cloudflare.com](https://docs.cloudflare.com) | [cloudflarestatus.com](https://www.cloudflarestatus.com) | Community forum |
| Koyeb | [koyeb.com/docs](https://koyeb.com/docs) | [status.koyeb.com](https://status.koyeb.com) | support@koyeb.com |
| Neon | [neon.tech/docs](https://neon.tech/docs) | [neonstatus.com](https://neonstatus.com) | support@neon.tech |
| Upstash | [upstash.com/docs](https://upstash.com/docs) | [status.upstash.com](https://status.upstash.com) | support@upstash.com |
| Netlify | [docs.netlify.com](https://docs.netlify.com) | [netlifystatus.com](https://www.netlifystatus.com) | support@netlify.com |
| Render | [render.com/docs](https://render.com/docs) | [status.render.com](https://status.render.com) | support@render.com |
| Supabase | [supabase.com/docs](https://supabase.com/docs) | [status.supabase.com](https://status.supabase.com) | support@supabase.io |
| Vercel | [vercel.com/docs](https://vercel.com/docs) | [vercel-status.com](https://www.vercel-status.com) | support@vercel.com |
| Railway | [docs.railway.app](https://docs.railway.app) | [status.railway.app](https://status.railway.app) | team@railway.app |

### Internal Documentation

- **Deployment Runbook:** `DEPLOYMENT_RUNBOOK.md` (detailed step-by-step guide)
- **Environment Configs:** `.env.uat`, `.env.beta`, `.env.preprod`
- **CI/CD Pipeline:** `.github/workflows/deploy-multi-env.yml`
- **Monitoring Dashboard:** `src/Backend/monitoring/environment_comparison.py`

---

## 🎯 Next Steps

### Immediate (This Week)
1. Complete account signups for all platforms
2. Set up UAT environment (highest priority)
3. Configure GitHub Actions with all secrets
4. Deploy first application to UAT
5. Verify health checks passing

### Short-term (Next 2 Weeks)
1. Set up Beta and Pre-PROD environments
2. Implement automated monitoring dashboard
3. Run first performance comparison
4. Configure mobile app for all 3 environments
5. Document any platform-specific quirks discovered

### Medium-term (Next Month)
1. Collect 30 days of performance data across all environments
2. Analyze cost vs performance trade-offs
3. Decide on production hosting strategy based on data
4. Implement automated failover system
5. Create disaster recovery playbook

### Long-term (Production Launch)
1. Determine production platform based on UAT/Beta/Pre-PROD learnings
2. Implement production monitoring and alerting
3. Set up CDN and advanced caching strategies
4. Plan for scaling beyond free tiers
5. Establish SLAs and support processes

---

## 📊 Success Criteria

This triple-environment strategy will be considered successful when:

✅ All 45 deployments (15 apps × 3 environments) are live
✅ CI/CD automatically deploys to all environments on push
✅ Monitoring dashboard tracks performance across all platforms
✅ Zero critical errors in any environment for 7 consecutive days
✅ Performance comparison data collected for 30 days
✅ Failover testing demonstrates < 5 minute recovery time
✅ Total monthly cost remains under $10 across all environments
✅ Team can confidently choose production platform based on data

---

## 🏆 Expected Outcomes

### Technical Benefits
- **Platform Comparison Data** - Empirical evidence for production platform choice
- **Performance Benchmarks** - Real-world latency and throughput measurements
- **Cost Validation** - Actual usage vs free tier limits
- **Redundancy** - Natural disaster recovery with 3 independent infrastructures

### Business Benefits
- **Risk Mitigation** - No vendor lock-in, proven alternatives ready
- **Cost Savings** - $3,000-$3,400 annually vs traditional cloud
- **Faster Iteration** - Multiple test environments for parallel feature development
- **Confidence** - Data-driven production platform decision

### Operational Benefits
- **Automated Deployment** - Zero-touch CD pipeline
- **Environment Parity** - Consistent configurations across UAT/Beta/Pre-PROD
- **Easy Rollback** - Git-based deployments enable instant rollback
- **Monitoring** - Proactive alerts and comparison dashboards

---

**Document Version:** 1.0
**Last Updated:** 2025-01-23
**Next Review:** 2025-02-23
**Owner:** Engineering Team
**Status:** Ready for Implementation
