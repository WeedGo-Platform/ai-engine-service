# Environment Management Strategy

## Overview

This document describes how environment configurations are managed across different deployment environments to prevent configuration mix-ups and ensure smooth branch merges.

## 📋 Table of Contents

- [Environment File Hierarchy](#environment-file-hierarchy)
- [Environment Types](#environment-types)
- [File Structure](#file-structure)
- [Git Handling](#git-handling)
- [Branch Strategy](#branch-strategy)
- [Automated Workflows](#automated-workflows)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Environment File Hierarchy

WeedGo uses a **hierarchical environment configuration system** where files override each other in a specific order:

```
.env (base config)
  ↓ overridden by
.env.[mode] (environment-specific)
  ↓ overridden by
.env.local (developer-specific, not tracked in git)
```

### How It Works

1. **`.env`** - Base configuration with defaults for local/dev environment
   - Contains common settings used across all environments
   - Defines local development ports (5024/3003)
   - **Tracked in git** ✅

2. **`.env.[mode]`** - Environment-specific overrides (test, uat, beta, preprod, production)
   - Only contains values that differ from base .env
   - Each branch may have its own .env.[mode]
   - **Tracked in git** ✅

3. **`.env.local`** - Developer-specific overrides (highest priority)
   - Personal settings that override everything
   - **NOT tracked in git** ❌
   - Useful for local API keys, debug settings, etc.

---

## 🌍 Environment Types

### Local Development
- **Ports**: Backend 5024, Frontend 3003
- **Config**: `.env` (base) + `.env.local` (optional)
- **Run**: `npm run dev` (backend), `npm run dev` (frontend)

### Test Environment
- **Branch**: `test`
- **Ports**: Backend 6024, Frontend 6003
- **Config**: `.env` (base) + `.env.test` (overrides)
- **Run**: `npm run dev:test` (uses `--mode test` flag)
- **Infrastructure**: Shares local PostgreSQL (5434) and Redis (6379)

### UAT (User Acceptance Testing)
- **Branch**: `main`
- **Config**: `.env` (base) + `.env.uat` (overrides)
- **Deployment**: Cloudflare Pages + Koyeb
- **Database**: Neon PostgreSQL

### Beta Environment
- **Branch**: `staging`
- **Config**: `.env` (base) + `.env.beta` (overrides)
- **Deployment**: Netlify + Render
- **Database**: Supabase

### Pre-PROD Environment
- **Branch**: `release`
- **Config**: `.env` (base) + `.env.preprod` (overrides)
- **Deployment**: Vercel + Railway

---

## 📁 File Structure

### Backend (`src/Backend/`)
```
src/Backend/
├── .env                    # Base config (local: 5024)
├── .env.test              # Test overrides (port: 6024)
├── .env.uat               # UAT cloud config
├── .env.beta              # Beta cloud config
├── .env.preprod           # Pre-PROD cloud config
├── .env.local             # Developer overrides (NOT in git)
└── validate_env.py        # Environment validation script
```

### Frontend (`src/Frontend/ai-admin-dashboard/`)
```
src/Frontend/ai-admin-dashboard/
├── .env                    # Base config (API: localhost:5024)
├── .env.test              # Test overrides (API: localhost:6024)
├── .env.uat               # UAT cloud config
├── .env.beta              # Beta cloud config
├── .env.preprod           # Pre-PROD cloud config
├── .env.local             # Developer overrides (NOT in git)
└── package.json           # Contains mode-specific scripts
```

### Package.json Scripts (Frontend)
```json
{
  "scripts": {
    "dev": "vite --port 3003",                    // Local dev (uses .env)
    "dev:test": "vite --port 6003 --mode test",   // Test (uses .env + .env.test)
    "build": "vite build",                         // Production build
    "build:uat": "vite build --mode uat",         // UAT build
    "build:beta": "vite build --mode beta",       // Beta build
    "build:preprod": "vite build --mode preprod"  // Pre-PROD build
  }
}
```

---

## 🔀 Git Handling

### What's Tracked in Git

✅ **Tracked** (committed to repository):
- `.env` - Base configuration
- `.env.test` - Test environment config
- `.env.uat` - UAT environment config
- `.env.beta` - Beta environment config
- `.env.preprod` - Pre-PROD environment config
- `.env.production` - Production environment config

❌ **NOT Tracked** (ignored by git):
- `.env.local` - Developer-specific overrides
- `.env.*.local` - Any .local files
- `.env.backup`, `.env.original` - Backup files

### `.gitignore` Configuration

```gitignore
# Environment files
# .env and .env.[mode] are tracked (contain non-secret config)
# Only .env.local and .env.*.local are ignored
.env.local
.env.*.local
*.local.env
.env.backup
.env.original
```

### `.gitattributes` Configuration

Defines merge strategies for environment files to prevent conflicts:

```gitattributes
# Environment files use union merge to preserve both versions
src/Backend/.env.test        merge=union
src/Backend/.env.uat         merge=union
src/Frontend/*/.env.test     merge=union
src/Frontend/*/.env.uat      merge=union

# Package.json may have environment-specific scripts
src/Frontend/*/package.json  merge=union
```

**Union merge strategy** combines changes from both branches, which works well for environment files since they typically have non-overlapping keys.

---

## 🌳 Branch Strategy

### Branch → Environment Mapping

```
dev branch        → Local development
  ↓ (auto-sync)
test branch       → Test environment (localhost:6024/6003)
  ↓ (manual)
staging branch    → Beta environment (staging servers)
  ↓ (manual)
release branch    → Pre-PROD environment (pre-production)
  ↓ (manual)
main branch       → UAT environment (production-like)
  ↓ (manual)
production branch → Production environment (NOT YET IMPLEMENTED)
```

### Automated Syncing: Dev → Test

When you push to `dev`, the **auto-sync workflow** automatically:
1. Detects push to dev branch
2. Merges dev into test branch
3. Preserves test-specific configurations (.env.test, package.json scripts)
4. Pushes to test branch
5. Triggers test-deploy workflow

**Workflow file**: `.github/workflows/auto-sync-dev-to-test.yml`

---

## ⚙️ Automated Workflows

### 1. Auto-Sync Dev to Test
**File**: `.github/workflows/auto-sync-dev-to-test.yml`

**Triggers**: Push to `dev` branch

**Actions**:
- Merges dev into test automatically
- Resolves conflicts in favor of test for env files
- Verifies test-specific configurations
- Pushes to test branch

### 2. Test Environment CI/CD
**File**: `.github/workflows/test-deploy.yml`

**Triggers**: Push to `test` branch

**Actions**:
- Validates .env.test configuration
- Runs unit and integration tests
- Builds Docker image
- Provides deployment artifacts

### 3. Multi-Environment Deployment
**File**: `.github/workflows/deploy-multi-env.yml`

**Triggers**: Push to `main`, `staging`, or `release` branches

**Actions**:
- main → UAT deployment (Cloudflare + Koyeb)
- staging → Beta deployment (Netlify + Render)
- release → Pre-PROD deployment (Vercel + Railway)

---

## ✅ Best Practices

### 1. Never Modify `.env` for Environment-Specific Changes

❌ **Wrong**:
```bash
# Editing .env directly to change ports for test
VITE_API_URL=http://localhost:6024  # Don't do this!
```

✅ **Correct**:
```bash
# Create/edit .env.test instead
# .env.test
VITE_API_URL=http://localhost:6024
VITE_API_BASE_URL=http://localhost:6024/api
VITE_ENV=test
```

### 2. Use Mode-Specific Scripts

❌ **Wrong**:
```bash
# Manually passing environment variables
VITE_API_BASE_URL=http://localhost:6024 npm run dev --port 6003
```

✅ **Correct**:
```bash
# Use the mode-specific script
npm run dev:test
```

### 3. Keep Secrets Out of Git

**Never commit**:
- API keys
- Database passwords
- Private tokens
- Encryption keys

**Instead**:
- Use GitHub Secrets for CI/CD
- Use .env.local for local development
- Use secret management services for production

### 4. Document Environment Variables

Each .env file should include comments:
```bash
# ===========================================
# API Configuration
# ===========================================
VITE_API_URL=http://localhost:6024
VITE_API_TIMEOUT=30000  # milliseconds

# ===========================================
# Feature Flags
# ===========================================
VITE_FEATURE_ANALYTICS=true
```

### 5. Validate Environment Files

Before committing, validate your environment files:
```bash
cd src/Backend
cp .env.test .env
python3 validate_env.py
```

---

## 🔧 Troubleshooting

### Issue: Frontend connecting to wrong API port

**Problem**: Frontend is connecting to port 5024 instead of 6024 in test environment.

**Solution**:
1. Verify `.env.test` exists with correct configuration
2. Run with correct mode: `npm run dev:test` (not `npm run dev`)
3. Check Vite is loading the right config:
   ```bash
   # Should show VITE_API_URL=http://localhost:6024
   npm run dev:test | grep VITE_API
   ```

### Issue: Environment variables not updating

**Problem**: Changed .env but app still uses old values.

**Solution**:
1. Restart the dev server
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Ensure you're editing the right file (.env vs .env.test vs .env.local)

### Issue: Merge conflicts in .env files

**Problem**: Git merge creates conflicts in environment files.

**Solution**:
1. The auto-sync workflow handles this automatically
2. For manual merges, keep the target branch's environment configs:
   ```bash
   git checkout test
   git merge dev
   # If conflicts in .env.test
   git checkout --ours src/Backend/.env.test
   git checkout --ours src/Frontend/*/.env.test
   git add .
   git commit
   ```

### Issue: "Cannot find module" after switching branches

**Problem**: Dependencies missing after branch switch.

**Solution**:
```bash
# Backend
cd src/Backend
pip install -r requirements.txt

# Frontend
cd src/Frontend/ai-admin-dashboard
npm install
```

### Issue: Database connection refused in test environment

**Problem**: Test environment can't connect to PostgreSQL.

**Solution**:
1. Verify local PostgreSQL is running on port 5434
2. Check `.env.test` has correct DB_PORT:
   ```bash
   grep DB_PORT src/Backend/.env.test
   # Should show: DB_PORT=5434
   ```
3. Ensure database exists:
   ```bash
   psql -h localhost -p 5434 -U weedgo -l | grep ai_engine
   ```

---

## 📚 Related Documentation

- [Deployment Guide](./DEPLOYMENT.md)
- [Docker Setup](./DOCKER.md)
- [CI/CD Workflows](../.github/workflows/README.md)
- [Testing Strategy](./TESTING.md)

---

## 🤝 Contributing

When adding a new environment:
1. Create `.env.[mode]` file with environment-specific overrides
2. Update `.gitattributes` to include new environment file
3. Add build/deploy scripts to `package.json`
4. Create corresponding GitHub Actions workflow
5. Document the environment in this file

---

**Last Updated**: 2025-01-29
**Maintained By**: WeedGo DevOps Team
