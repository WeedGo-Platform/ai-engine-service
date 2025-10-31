# Environment Files Explained - WeedGo Admin Dashboard

## 📋 Overview

Your frontend uses **Vite's environment file system** to manage configuration across different deployment environments.

---

## 🗂️ Available Environment Files

```
.env                 (4.1 KB) - Base/Default configuration
.env.development     (234 B)  - Local development overrides
.env.test            (420 B)  - Test environment overrides
.env.uat             (664 B)  - UAT environment (Koyeb)
.env.beta            (467 B)  - Beta environment (Render)
.env.preprod         (500 B)  - Pre-production (Railway)
.env.prod            (234 B)  - Production environment
```

---

## 🔄 How Vite Loads Environment Files

### Loading Priority (Highest to Lowest)

```
1. .env.[mode].local     (ignored by git - for local overrides)
2. .env.[mode]           (environment-specific)
3. .env.local            (ignored by git - for all modes)
4. .env                  (base configuration)
```

**Key Point**: Files with higher priority **override** values from lower priority files.

---

## 📍 Your Current Configuration

### 1. **`.env` (Base Configuration)**

**Purpose**: Default values for ALL environments

**Used When**: Always loaded first, then overridden by mode-specific files

**Key Values**:
```bash
VITE_API_URL=http://localhost:6024
VITE_API_BASE_URL=http://localhost:6024/api
VITE_WS_API_URL=ws://localhost:6024

# Plus 130+ other config values:
- Feature flags
- UI timeouts
- Business rules
- Upload limits
- Validation rules
- etc.
```

**Think of it as**: "The template that everything else builds on"

---

### 2. **`.env.development` (Local Dev)**

**Purpose**: Overrides for local development

**Used When**:
- Running `npm run dev` (default mode is "development")
- Working on your local machine

**Key Values**:
```bash
VITE_API_URL=http://localhost:6024        # ✅ Now aligned with base
VITE_API_BASE_URL=http://localhost:6024/api
VITE_ENV=development
```

**Why It Exists**:
- Lightweight override file
- Only contains values that differ from `.env`
- Keeps local dev configuration separate

**Command**:
```bash
npm run dev
# Vite loads: .env + .env.development
# Frontend runs on: localhost:3003
# Talks to backend on: localhost:6024
```

---

### 3. **`.env.test` (Test Environment)**

**Purpose**: Local test mode with different ports to avoid conflicts

**Used When**:
- Running `npm run dev:test`
- Running automated tests
- Testing new features in isolation

**Key Values**:
```bash
VITE_API_URL=http://localhost:6024
VITE_API_BASE_URL=http://localhost:6024/api
VITE_ENV=test
```

**Why Different Port**:
- Frontend: port **6003** (vs 3003 in dev)
- Backend: port **6024** (same)
- Allows dev and test to run simultaneously!

**Command**:
```bash
npm run dev:test
# Vite loads: .env + .env.test (note --mode test)
# Frontend runs on: localhost:6003
# Talks to backend on: localhost:6024
```

---

### 4. **`.env.uat` (UAT Environment)**

**Purpose**: User Acceptance Testing on Koyeb

**Used When**:
- Deploying to UAT environment
- QA team testing
- Stakeholder demos

**Key Values**:
```bash
VITE_API_URL=https://weedgo-uat-weedgo-c07d9ce5.koyeb.app
VITE_API_BASE_URL=https://weedgo-uat-weedgo-c07d9ce5.koyeb.app/api
VITE_WS_URL=wss://weedgo-uat-weedgo-c07d9ce5.koyeb.app
VITE_ENVIRONMENT=uat
VITE_ENV_LABEL=UAT
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_VOICE=true
VITE_ENABLE_RAG=true
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_... (test mode)
```

**Deployment**:
```bash
# On your CI/CD or locally:
npm run build -- --mode uat
# Vite loads: .env + .env.uat
# Builds with UAT configuration
# Deploy to: Koyeb, Cloudflare Pages, etc.
```

---

### 5. **`.env.beta` (Beta Environment)**

**Purpose**: Beta testing on Render

**Used When**:
- Beta releases
- Early adopter testing
- Feature previews

**Key Values**:
```bash
VITE_API_URL=https://weedgo-beta.onrender.com
VITE_API_BASE_URL=https://weedgo-beta.onrender.com/api
VITE_WS_URL=wss://weedgo-beta.onrender.com
VITE_ENVIRONMENT=beta
VITE_ENV_LABEL=BETA
```

**Deployment**:
```bash
npm run build -- --mode beta
# Vite loads: .env + .env.beta
# Deploy to: Render
```

---

### 6. **`.env.preprod` (Pre-Production)**

**Purpose**: Final testing before production on Railway

**Used When**:
- Final validation before prod release
- Production-like environment
- Load testing

**Key Values**:
```bash
VITE_API_URL=https://weedgo-preprod.up.railway.app
VITE_API_BASE_URL=https://weedgo-preprod.up.railway.app/api
VITE_WS_URL=wss://weedgo-preprod.up.railway.app
VITE_ENVIRONMENT=preprod
```

**Deployment**:
```bash
npm run build -- --mode preprod
# Vite loads: .env + .env.preprod
# Deploy to: Railway
```

---

### 7. **`.env.prod` (Production)**

**Purpose**: Live production environment

**Used When**:
- Production builds
- Live customer-facing application

**Key Values**:
```bash
VITE_API_URL=https://api.weedgo.com
VITE_API_BASE_URL=https://api.weedgo.com/api
VITE_TRANSLATION_API_URL=https://api.weedgo.com/api/translate
VITE_ENV=production
```

**Deployment**:
```bash
npm run build -- --mode prod
# OR just:
npm run build  # production is default for build
# Vite loads: .env + .env.prod
# Deploy to: Production hosting
```

---

## 🎯 Visual Flow Diagram

```
┌─────────────────────────────────────────────────┐
│            Developer's Machine                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  npm run dev                                     │
│  ├─ Loads: .env + .env.development              │
│  ├─ Frontend: localhost:3003                    │
│  └─ Backend:  localhost:6024                    │
│                                                  │
│  npm run dev:test                                │
│  ├─ Loads: .env + .env.test                     │
│  ├─ Frontend: localhost:6003                    │
│  └─ Backend:  localhost:6024                    │
│                                                  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│             Cloud Deployments                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  UAT (Koyeb)                                     │
│  ├─ Build: npm run build -- --mode uat          │
│  ├─ Loads: .env + .env.uat                      │
│  └─ URL: weedgo-uat-weedgo-c07d9ce5.koyeb.app  │
│                                                  │
│  Beta (Render)                                   │
│  ├─ Build: npm run build -- --mode beta         │
│  ├─ Loads: .env + .env.beta                     │
│  └─ URL: weedgo-beta.onrender.com              │
│                                                  │
│  Pre-Prod (Railway)                              │
│  ├─ Build: npm run build -- --mode preprod      │
│  ├─ Loads: .env + .env.preprod                  │
│  └─ URL: weedgo-preprod.up.railway.app         │
│                                                  │
│  Production                                      │
│  ├─ Build: npm run build -- --mode prod         │
│  ├─ Loads: .env + .env.prod                     │
│  └─ URL: api.weedgo.com                         │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 🔍 How to Check Which Env is Active

### In Your Code:
```typescript
console.log('Mode:', import.meta.env.MODE);           // 'development', 'test', 'uat', etc.
console.log('Dev?:', import.meta.env.DEV);            // true in dev mode
console.log('Prod?:', import.meta.env.PROD);          // true in prod mode
console.log('API URL:', import.meta.env.VITE_API_URL);
console.log('Env:', import.meta.env.VITE_ENV);        // Custom env identifier
```

### In The Browser:
Open DevTools Console and run:
```javascript
window.location.origin         // Current frontend URL
import.meta.env.VITE_API_URL  // Backend API URL being used
```

---

## 🚦 Common Scenarios

### Scenario 1: "I want to run dev and test at the same time"

```bash
# Terminal 1 - Development
npm run dev
# Frontend: http://localhost:3003
# Backend: http://localhost:6024

# Terminal 2 - Test
npm run dev:test
# Frontend: http://localhost:6003
# Backend: http://localhost:6024 (same backend!)
```

Both can run simultaneously because they use different frontend ports!

---

### Scenario 2: "I want to test UAT config locally"

```bash
# Option 1: Use UAT backend but local frontend
npm run dev -- --mode uat
# Frontend: localhost:3003
# Backend: weedgo-uat-weedgo-c07d9ce5.koyeb.app (cloud)

# Option 2: Full UAT build locally
npm run build -- --mode uat
npm run preview
# Builds with UAT config, preview locally
```

---

### Scenario 3: "I need to add a new environment variable"

**For all environments:**
1. Add to `.env` (base file)
2. Will be available everywhere

**For specific environment only:**
1. Add to `.env.uat` (or whichever environment)
2. Only available in that environment

**Example:**
```bash
# In .env (available everywhere)
VITE_FEATURE_NEW_DASHBOARD=false

# In .env.uat (override for UAT only)
VITE_FEATURE_NEW_DASHBOARD=true
```

---

### Scenario 4: "Deploy to new environment"

1. Create new file: `.env.staging`
```bash
VITE_API_URL=https://staging.weedgo.com
VITE_ENVIRONMENT=staging
```

2. Add build command to package.json:
```json
"build:staging": "vite build --mode staging"
```

3. Deploy:
```bash
npm run build:staging
# Uploads dist/ to staging server
```

That's it! No code changes needed.

---

## ⚠️ Important Rules

### 1. **Never commit `.env.local` or `.env.[mode].local`**
- These are in `.gitignore`
- Use for personal overrides
- Example: Your local database credentials

### 2. **Always prefix with `VITE_`**
```bash
# ✅ Exposed to client
VITE_API_URL=...

# ❌ NOT exposed to client (security!)
SECRET_KEY=...
DATABASE_URL=...
```

Only `VITE_*` variables are available in browser code!

### 3. **Environment files are NOT secrets**
- `.env.uat`, `.env.beta`, etc. are committed to git
- They contain public URLs, not secrets
- Secrets go in platform env vars (Koyeb, Vercel UI)

### 4. **Mode vs Environment**
- **Mode**: Vite's build mode (development, production, test, uat, beta)
- **Environment**: Where it's deployed (local, cloud)
- One mode can be used in multiple environments

---

## 📚 Your Current Port Strategy

| Environment | Frontend Port | Backend Port | Purpose |
|------------|--------------|--------------|---------|
| **Development** | 3003 | 6024 | Daily development |
| **Test** | 6003 | 6024 | Testing in isolation |
| **UAT** | 443 (HTTPS) | 443 | Cloud - Koyeb |
| **Beta** | 443 (HTTPS) | 443 | Cloud - Render |
| **Pre-Prod** | 443 (HTTPS) | 443 | Cloud - Railway |
| **Production** | 443 (HTTPS) | 443 | Cloud - Production |

**Why 6024?**
- Test backend port (vs 5024 for main dev)
- Allows multiple backend instances
- Aligned across all local `.env` files

---

## 🔧 Troubleshooting

### "My changes aren't showing up"

**Solution 1**: Restart dev server
```bash
# Vite caches .env files, need to restart
npm run dev
```

**Solution 2**: Clear cache
```bash
rm -rf node_modules/.vite
npm run dev
```

---

### "Wrong environment loaded"

**Check**:
```bash
# Which mode is active?
vite --help  # Shows current mode

# Force specific mode:
npm run dev -- --mode test
npm run build -- --mode uat
```

---

### "Environment variable is undefined"

**Checklist**:
1. ✅ Does it start with `VITE_`?
2. ✅ Is it in the correct `.env.[mode]` file?
3. ✅ Did you restart the dev server?
4. ✅ Are you checking in the right place (browser vs node)?

```typescript
// ✅ In browser/frontend code
console.log(import.meta.env.VITE_API_URL);

// ❌ Won't work - not available in frontend
console.log(process.env.DATABASE_URL);
```

---

## 📖 Further Reading

- [Vite Environment Variables Docs](https://vitejs.dev/guide/env-and-mode.html)
- [Environment Modes](https://vitejs.dev/guide/env-and-mode.html#modes)
- [Environment Files Priority](https://vitejs.dev/guide/env-and-mode.html#env-files)

---

## ✅ Summary

**Your setup is well-organized!** You have:

1. ✅ **Base configuration** (`.env`) - 140+ settings
2. ✅ **Local dev** (`.env.development`) - Quick local work
3. ✅ **Test mode** (`.env.test`) - Isolated testing
4. ✅ **Multiple cloud environments** (uat, beta, preprod, prod)
5. ✅ **Clear separation** - Each environment has its own file
6. ✅ **Port strategy** - Consistent 6024 for local, 443 for cloud

**The strategy**:
- `.env` = comprehensive base template
- `.env.[mode]` = lightweight overrides for specific needs
- No hardcoded values in code ✅
- Deploy anywhere by just changing mode ✅
