# Your ACTUAL Environment Strategy - WeedGo Admin

**Last Updated**: 2025-10-30
**Important**: This reflects what's ACTUALLY on disk RIGHT NOW

---

## 📁 Files That EXIST (5 files)

```bash
$ ls -la .env*

.env         4,184 bytes   Base/Development (default)
.env.beta      467 bytes   Beta environment (Render)
.env.prod      234 bytes   Production
.env.test      420 bytes   Test environment
.env.uat       664 bytes   UAT environment (Koyeb)
```

---

## 🎯 Your Strategy (Simpler Than Expected!)

### **1. `.env` = Base Configuration AND Development Default**

**Size**: 4.1 KB (140+ configuration values)

**Purpose**:
- Single source of truth for all settings
- Used directly for local development (no `.env.development` needed!)
- Contains comprehensive configuration

**Key Settings**:
```bash
# API Configuration (FOR LOCAL DEV)
VITE_API_URL=http://localhost:6024
VITE_API_BASE_URL=http://localhost:6024/api
VITE_WS_API_URL=ws://localhost:6024

# Plus ALL other config:
- 14 API/Auth settings
- 10 UI configuration values
- 10 Feature flags
- 8 Business rules
- 8 Upload/validation rules
- 90+ other settings
```

**Used When**:
```bash
npm run dev
# Loads ONLY .env (no .env.development!)
# Frontend: localhost:3003
# Backend: localhost:6024
```

---

### **2. `.env.test` = Test Environment Overrides**

**Size**: 420 bytes (minimal overrides)

**Purpose**: Parallel testing with different frontend port

**Overrides from `.env`**:
```bash
VITE_API_URL=http://localhost:6024        # Same backend
VITE_API_BASE_URL=http://localhost:6024/api
VITE_ENV=test                              # Identifier
```

**Used When**:
```bash
npm run dev:test
# Loads: .env + .env.test
# Frontend: localhost:6003 (different!)
# Backend: localhost:6024 (same!)
```

**Why It Works**: Different frontend ports means you can run both:
- `npm run dev` → port 3003
- `npm run dev:test` → port 6003

Both hit same backend (6024) simultaneously!

---

### **3. `.env.uat` = UAT on Koyeb**

**Size**: 664 bytes

**Purpose**: User Acceptance Testing environment

**Overrides from `.env`**:
```bash
VITE_API_URL=https://weedgo-uat-weedgo-c07d9ce5.koyeb.app
VITE_API_BASE_URL=https://weedgo-uat-weedgo-c07d9ce5.koyeb.app/api
VITE_WS_URL=wss://weedgo-uat-weedgo-c07d9ce5.koyeb.app
VITE_ENVIRONMENT=uat
VITE_ENV_LABEL=UAT
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_VOICE=true
VITE_ENABLE_RAG=true
```

**Used When**:
```bash
# Build for UAT
npm run build -- --mode uat
# Vite loads: .env + .env.uat
# Deploy to: Koyeb, Cloudflare Pages, etc.
```

---

### **4. `.env.beta` = Beta on Render**

**Size**: 467 bytes

**Purpose**: Beta testing environment

**Overrides from `.env`**:
```bash
VITE_API_URL=https://weedgo-beta.onrender.com
VITE_API_BASE_URL=https://weedgo-beta.onrender.com/api
VITE_WS_URL=wss://weedgo-beta.onrender.com
VITE_ENVIRONMENT=beta
VITE_ENV_LABEL=BETA
```

**Used When**:
```bash
npm run build -- --mode beta
# Vite loads: .env + .env.beta
# Deploy to: Render
```

---

### **5. `.env.prod` = Production**

**Size**: 234 bytes (minimal, only what's different)

**Purpose**: Live production

**Overrides from `.env`**:
```bash
VITE_API_URL=https://api.weedgo.com
VITE_API_BASE_URL=https://api.weedgo.com/api
VITE_TRANSLATION_API_URL=https://api.weedgo.com/api/translate
VITE_ENV=production
```

**Used When**:
```bash
npm run build
# OR explicitly:
npm run build -- --mode prod
# Vite loads: .env + .env.prod
# Deploy to: Production servers
```

---

## 🔄 How Vite Loads These Files

### Loading Order (What Actually Happens)

```
┌─────────────────────────────────────┐
│  Development (npm run dev)          │
├─────────────────────────────────────┤
│  1. Load .env (4.1 KB)              │
│  2. No .env.development exists!     │
│  3. Use .env values directly        │
│                                     │
│  Result:                            │
│  - Frontend: localhost:3003         │
│  - Backend:  localhost:6024         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Test (npm run dev:test)            │
├─────────────────────────────────────┤
│  1. Load .env (base)                │
│  2. Load .env.test (overrides)      │
│  3. Merge (test values win)         │
│                                     │
│  Result:                            │
│  - Frontend: localhost:6003         │
│  - Backend:  localhost:6024         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  UAT (npm run build --mode uat)     │
├─────────────────────────────────────┤
│  1. Load .env (base)                │
│  2. Load .env.uat (overrides)       │
│  3. Merge (uat values win)          │
│                                     │
│  Result:                            │
│  - All URLs point to Koyeb          │
└─────────────────────────────────────┘
```

---

## 💡 Why This Strategy is BETTER

### ✅ **Simplicity**
- Only 5 files total
- No `.env.development` needed
- `.env` IS your development config

### ✅ **Clarity**
- `.env` = comprehensive default (140+ settings)
- `.env.{mode}` = minimal overrides (just what's different)
- Easy to see what changes per environment

### ✅ **Maintainability**
- Add new setting? → Put in `.env` once
- All environments inherit it automatically
- Only override if environment needs something different

### ✅ **No Duplication**
- Settings defined once in `.env`
- Override files are tiny (234-664 bytes!)
- DRY principle applied

---

## 🔍 Example: How a Setting Flows

Let's trace `VITE_ENABLE_ANALYTICS`:

```bash
# In .env (base)
VITE_ENABLE_ANALYTICS=true

# Development (npm run dev)
# Uses: .env
# Value: true ✅

# Test (npm run dev:test)
# Uses: .env + .env.test
# .env.test doesn't override it
# Value: true ✅ (inherited)

# UAT (build --mode uat)
# Uses: .env + .env.uat
# .env.uat explicitly sets it to true
# Value: true ✅

# Beta (build --mode beta)
# Uses: .env + .env.beta
# .env.beta sets it to true
# Value: true ✅

# Production (build --mode prod)
# Uses: .env + .env.prod
# .env.prod doesn't mention it
# Value: true ✅ (inherited from .env!)
```

**One setting in `.env` works everywhere!**

---

## 📊 Comparison: Before My Cleanup vs After

### Before (Hardcoded URLs)
```typescript
// Scattered across 25+ files:
const url1 = 'http://localhost:5024';  // File 1
const url2 = 'http://localhost:5024';  // File 2
const url3 = 'http://localhost:5024';  // File 3
// ... 22 more files

// Problems:
// - What if backend moves to different port?
// - Have to update 25 files manually
// - Easy to miss one
// - No environment awareness
```

### After (Environment-Driven)
```typescript
// All files use:
import { appConfig } from './config/app.config';
const url = appConfig.api.baseUrl;  // From .env!

// Benefits:
// - Change .env → affects all 25 files
// - Environment-aware (dev vs uat vs prod)
// - Deploy anywhere (just set VITE_API_URL)
// - Single source of truth
```

---

## 🚦 Common Commands

```bash
# Local Development
npm run dev
# Uses: .env only
# Port: 3003

# Local Test Mode
npm run dev:test
# Uses: .env + .env.test
# Port: 6003

# Build for UAT
npm run build -- --mode uat
# Uses: .env + .env.uat
# Output: dist/ with UAT config

# Build for Beta
npm run build -- --mode beta
# Uses: .env + .env.beta
# Output: dist/ with Beta config

# Build for Production
npm run build
# OR: npm run build -- --mode prod
# Uses: .env + .env.prod
# Output: dist/ with prod config

# Preview a build locally
npm run build -- --mode uat
npm run preview
# See UAT config running locally
```

---

## ⚠️ IMPORTANT: Port Configuration

### Backend Ports (from Backend/.env files)

```bash
.env (base)    → PORT=6024  ✅
.env.local     → PORT=5024  (different local setup)
.env.test      → PORT=6024  ✅
.env.uat       → Cloud port
.env.beta      → Cloud port
.env.prod      → Cloud port
```

### Frontend Expects Backend On:

```bash
Development → localhost:6024 (from .env)
Test        → localhost:6024 (from .env.test)
UAT         → weedgo-uat-weedgo-c07d9ce5.koyeb.app
Beta        → weedgo-beta.onrender.com
Production  → api.weedgo.com
```

**Make sure your backend is actually running on the port the frontend expects!**

---

## ✅ Verification Checklist

Before committing my cleanup:

### Backend Check
```bash
cd src/Backend
source .env  # or .env.test
python api_server.py
# Should see: "Server running on http://0.0.0.0:6024"
```

### Frontend Check
```bash
cd src/Frontend/ai-admin-dashboard
npm run dev
# Should start on port 3003
# Browser console: check VITE_API_URL points to localhost:6024
```

### API Call Check
```bash
# With frontend running, open browser DevTools → Network tab
# Look at any API call
# Should show: Request URL: http://localhost:6024/api/...
# ✅ If it shows 6024 → correct!
# ❌ If it shows 5024 → backend/frontend mismatch!
```

---

## 🎯 Summary

Your environment strategy is **clean and effective**:

1. **`.env`** = Comprehensive base (4.1 KB with 140+ settings)
2. **`.env.test`** = Test overrides (420 bytes)
3. **`.env.uat`** = UAT overrides (664 bytes)
4. **`.env.beta`** = Beta overrides (467 bytes)
5. **`.env.prod`** = Production overrides (234 bytes)

**No `.env.development` needed** - you use `.env` directly for development!

**My cleanup aligns with this strategy perfectly** - all 25 files now read from these environment variables instead of hardcoded URLs.

