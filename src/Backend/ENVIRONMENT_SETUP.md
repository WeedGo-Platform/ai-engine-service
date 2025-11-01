# Environment Configuration Guide

Complete guide for managing environment configurations in WeedGo AI Backend.

## Table of Contents
- [Environment Structure](#environment-structure)
- [Quick Start](#quick-start)
- [Environment Files](#environment-files)
- [Switching Environments](#switching-environments)
- [Validation](#validation)
- [Variable Reference](#variable-reference)
- [Deployment](#deployment)

---

## Environment Structure

We maintain **5 separate environment configurations**:

| Environment | File | Ports | Use Case |
|-------------|------|-------|----------|
| **Local** | `.env.local` | Backend: 5024<br>Frontend: 3000-3007 | Daily development |
| **Test** | `.env.test` | Backend: 6024<br>Frontend: 6003, 600* | Testing & QA |
| **UAT** | `.env.uat` | Cloud Run (PORT env) | User acceptance testing |
| **Beta** | `.env.beta` | Cloud Run (PORT env) | Beta releases |
| **Production** | `.env.prod` | Cloud Run (PORT env) | Live production |

---

## Quick Start

### 1. Choose Your Environment

**For local development:**
```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service-main/src/Backend
cp .env.local .env
```

**For testing:**
```bash
cp .env.test .env
```

### 2. Validate Configuration

```bash
# Install python-dotenv if not already installed
pip install python-dotenv

# Run validation
python3 validate_env.py
```

### 3. Start the Server

```bash
python3 api_server.py
```

---

## Environment Files

### `.env.local` - Local Development
- **Port**: 5024
- **Database**: Local PostgreSQL (localhost:5434)
- **CORS**: localhost ports 3000-3007
- **Secrets**: Development keys (safe to commit template)
- **Use When**: Daily development work

### `.env.test` - Testing Environment
- **Port**: 6024
- **Database**: Local PostgreSQL (localhost:5434, different DB name)
- **CORS**: localhost ports 6003, 600*
- **Secrets**: Test keys (shared with local)
- **Use When**: Running tests, QA validation

### `.env.uat` - User Acceptance Testing
- **Port**: 8080 (Cloud Run sets automatically)
- **Database**: Cloud PostgreSQL (Neon, Cloud SQL)
- **CORS**: https://weedgo-uat-*.pages.dev
- **Secrets**: UAT-specific keys
- **Use When**: Deploying to UAT environment

### `.env.beta` - Beta Environment
- **Port**: 8080 (Cloud Run)
- **Database**: Cloud PostgreSQL (dedicated instance)
- **CORS**: https://weedgo-beta-*.netlify.app
- **Secrets**: Beta-specific keys
- **Use When**: Beta releases for early adopters

### `.env.prod` - Production
- **Port**: 8080 (Cloud Run)
- **Database**: Cloud SQL (production instance)
- **CORS**: https://weedgo.com, https://www.weedgo.com
- **Secrets**: **Production keys** (managed via Secret Manager)
- **Use When**: Production deployments only

---

## Switching Environments

### Manual Method

```bash
# Switch to test environment
cp .env.test .env

# Switch to local environment
cp .env.local .env

# Validate
python3 validate_env.py
```

### Quick Switcher Script

Create `switch_env.sh`:

```bash
#!/bin/bash
# Quick environment switcher

ENV=$1

if [ -z "$ENV" ]; then
    echo "Usage: ./switch_env.sh [local|test|uat|beta|prod]"
    exit 1
fi

ENV_FILE=".env.$ENV"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

cp "$ENV_FILE" .env
echo "✓ Switched to $ENV environment"

# Validate
python3 validate_env.py
```

**Usage:**
```bash
chmod +x switch_env.sh
./switch_env.sh test    # Switch to test
./switch_env.sh local   # Switch to local
```

---

## Validation

### Automatic Validation

The `validate_env.py` script checks:

✅ **Required Variables**: Ensures all critical env vars are set
✅ **CORS Configuration**: Validates origins are configured
✅ **Port Configuration**: Checks ports match environment expectations
✅ **Database Configuration**: Validates DB settings per environment
✅ **Secrets**: Ensures no placeholder values in production
✅ **Environment-Specific**: Validates requirements per environment

### Run Validation

```bash
python3 validate_env.py
```

**Example output:**
```
============================================================
WeedGo Backend - Environment Configuration Validator
============================================================

Validating environment: test

Checking required variables...
  ✓ ENVIRONMENT: test
  ✓ DB_HOST: localhost
  ✓ DB_PORT: 5434
  ✓ DB_NAME: ai_engine_test
  ✓ DB_USER: weedgo
  ✓ DB_PASSWORD: ***3123
  ✓ JWT_SECRET_KEY: ***tion
  ✓ CORS_ALLOWED_ORIGINS: http://localhost:6003,...

Checking CORS configuration...
  ✓ CORS_ALLOWED_ORIGINS: 8 origins configured
    - http://localhost:6003
    - http://localhost:6024
    ...

============================================================
✓ Environment validation PASSED
============================================================
```

---

## Variable Reference

### Core Variables (All Environments)

| Variable | Type | Description |
|----------|------|-------------|
| `ENVIRONMENT` | String | Environment identifier (development, test, uat, beta, production) |
| `PORT` | Integer | Server port (Cloud Run sets this) |
| `V5_PORT` | Integer | Fallback port if PORT not set |
| `V5_HOST` | String | Bind address (0.0.0.0) |

### Database Variables

| Variable | Type | Description |
|----------|------|-------------|
| `DB_HOST` | String | Database host |
| `DB_PORT` | Integer | Database port (5434 local, 5432 cloud) |
| `DB_NAME` | String | Database name |
| `DB_USER` | String | Database username |
| `DB_PASSWORD` | **SECRET** | Database password |
| `DATABASE_URL` | String | Full PostgreSQL connection string |

### CORS Variables (REQUIRED)

| Variable | Type | Description |
|----------|------|-------------|
| `CORS_ALLOWED_ORIGINS` | String | Comma or semicolon-separated origins |
| `CORS_ORIGIN_REGEX` | String | Optional regex for dynamic origins |

**Examples:**
```bash
# Local
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3003

# UAT (semicolon for Cloud Run YAML)
CORS_ALLOWED_ORIGINS=https://weedgo-uat-admin.pages.dev;https://weedgo-uat-commerce.pages.dev

# Production
CORS_ALLOWED_ORIGINS=https://weedgo.com;https://www.weedgo.com
```

### Security Variables (REQUIRED)

| Variable | Type | Description |
|----------|------|-------------|
| `SECRET_KEY` | **SECRET** | Application secret key |
| `JWT_SECRET_KEY` | **SECRET** | JWT signing key |
| `JWT_ALGORITHM` | String | JWT algorithm (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | Token expiry (30) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Integer | Refresh token expiry (7) |

**Generate secrets:**
```bash
# Generate a secure random secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Third-Party APIs

| Variable | Type | Description |
|----------|------|-------------|
| `MAPBOX_API_KEY` | SECRET | Mapbox geocoding API key |
| `OPENROUTER_API_KEY` | SECRET | OpenRouter LLM API key |
| `GROQ_API_KEY` | SECRET | Groq inference API key |

### Payment (Stripe)

| Variable | Type | Description |
|----------|------|-------------|
| `STRIPE_SECRET_KEY` | **SECRET** | Stripe secret key |
| `STRIPE_PUBLISHABLE_KEY` | String | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | **SECRET** | Stripe webhook secret |

⚠️ **WARNING**: Use **test keys** for local/test/UAT/beta. Use **LIVE keys** ONLY in production.

### Communication (OTP/SMS/Email)

| Variable | Type | Description |
|----------|------|-------------|
| `TWILIO_ACCOUNT_SID` | String | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | **SECRET** | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | String | Twilio phone number |
| `SENDGRID_API_KEY` | **SECRET** | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | String | Sender email address |
| `SENDGRID_FROM_NAME` | String | Sender name |
| `SMTP_HOST` | String | SMTP server host |
| `SMTP_PORT` | Integer | SMTP server port (587) |
| `SMTP_USER` | String | SMTP username |
| `SMTP_PASSWORD` | **SECRET** | SMTP password |

### OTP Configuration (Standard Defaults)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OTP_LENGTH` | Integer | 6 | OTP code length |
| `OTP_EXPIRY_MINUTES` | Integer | 10 | OTP validity |
| `OTP_MAX_ATTEMPTS` | Integer | 3 | Failed attempts before lockout |
| `OTP_RATE_LIMIT_MAX` | Integer | 5 | Max OTPs per window |
| `OTP_RATE_LIMIT_WINDOW` | Integer | 60 | Rate limit window (seconds) |

---

## Deployment

### Local/Test Deployment

1. **Choose environment:**
   ```bash
   cp .env.local .env  # or .env.test
   ```

2. **Validate:**
   ```bash
   python3 validate_env.py
   ```

3. **Start server:**
   ```bash
   python3 api_server.py
   ```

### Cloud Run Deployment (UAT/Beta/Prod)

1. **Prepare environment file:**
   ```bash
   # For UAT
   cp .env.uat .env.cloudrun.yaml
   ```

2. **Convert to YAML format** (if not already):
   ```yaml
   ENVIRONMENT: "uat"
   DB_HOST: "your-db-host"
   # ... other variables
   ```

3. **Deploy to Cloud Run:**
   ```bash
   ./deploy-cloudrun.sh
   ```

### Environment Variables in Cloud Run

Cloud Run sets these automatically:
- `PORT`: The port your container should listen on (usually 8080)
- `K_SERVICE`: Service name
- `K_REVISION`: Revision name

Your `.env.uat`, `.env.beta`, or `.env.prod` should NOT hardcode PORT—let Cloud Run set it.

---

## Security Best Practices

### ✅ DO:
- ✅ Use different secrets for each environment
- ✅ Generate strong random secrets (`python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- ✅ Use Google Cloud Secret Manager for production secrets
- ✅ Validate environment before deployment (`python3 validate_env.py`)
- ✅ Use test Stripe keys for non-production environments
- ✅ Review CORS origins carefully

### ❌ DON'T:
- ❌ Commit real production secrets to Git
- ❌ Use production database in local/test
- ❌ Use test Stripe keys in production
- ❌ Use `localhost` database in cloud deployments
- ❌ Leave placeholder values in production

---

## Troubleshooting

### CORS Errors

**Problem**: Frontend gets CORS errors

**Solution**:
1. Check `CORS_ALLOWED_ORIGINS` includes your frontend URL
2. Run validation: `python3 validate_env.py`
3. Verify backend logs show CORS origins loaded
4. For local dev, ensure frontend port matches CORS config

### Database Connection Errors

**Problem**: Can't connect to database

**Solution**:
1. Verify `DB_HOST`, `DB_PORT`, `DB_NAME` are correct
2. Check `DB_PASSWORD` is set (not placeholder)
3. For cloud: Ensure database allows connections from Cloud Run
4. Test connection string manually

### Port Already in Use

**Problem**: `Port 5024 already in use`

**Solution**:
```bash
# Find process using the port
lsof -i :5024

# Kill the process
kill -9 <PID>

# Or switch to test environment (port 6024)
cp .env.test .env
```

### Missing Environment Variables

**Problem**: Validation fails with missing variables

**Solution**:
1. Check which environment you're using: `cat .env | grep ENVIRONMENT`
2. Compare with example: `diff .env .env.example`
3. Copy missing variables from appropriate env file

---

## Summary

### Environment Ports

- **Local** → 5024, 300*
- **Test** → 6024, 60**
- **UAT/Beta/Prod** → 8080 (Cloud Run)

### Quick Commands

```bash
# Switch to local
cp .env.local .env && python3 validate_env.py

# Switch to test
cp .env.test .env && python3 validate_env.py

# Validate current environment
python3 validate_env.py

# Start server
python3 api_server.py
```

### Files to .gitignore

```gitignore
.env          # Active environment (never commit)
.env.local    # May commit template
.env.test     # May commit template
.env.uat      # Commit with placeholders
.env.beta     # Commit with placeholders
.env.prod     # Commit with placeholders
```

---

**Need Help?** Check validation output or review this guide.

**Last Updated**: 2025-10-29
