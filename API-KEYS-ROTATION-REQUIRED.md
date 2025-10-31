# 🔐 API Keys Rotation Required - Action Plan

**Date**: 2025-10-30
**Priority**: 🚨 **URGENT - Immediate Action Required**
**Reason**: Real API keys were committed to git repository

---

## 📋 Executive Summary

**7 environment files** containing **real API keys and secrets** were committed to git and are now in the repository history. These secrets have been removed from git tracking, but **they must be rotated immediately** to prevent unauthorized access.

**Files affected**:
- `src/Backend/.env.test`
- `src/Backend/.env.uat`
- `src/Backend/.env.beta`
- `src/Backend/.env.prod`
- `src/Backend/.env.cloudrun`
- `src/Backend/.env.cloudrun.yaml`
- `src/Backend/.env.llm_router`

---

## 🔑 Exposed API Keys & Secrets

### Critical Priority (Rotate TODAY)

These keys grant direct access to paid services and can incur charges:

#### 1. **OpenRouter API Key**
- **Key**: `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`
- **Found in**: `.env.test`, `.env.uat`, `.env.llm_router`
- **Risk**: Unauthorized LLM usage, API charges
- **How to rotate**:
  ```bash
  # 1. Login to OpenRouter
  https://openrouter.ai/keys

  # 2. Revoke the old key:
  #    Find: sk-or-v1-dd91ea18082311f6...
  #    Click: "Revoke"

  # 3. Create new key:
  #    Click: "Create API Key"
  #    Name: "WeedGo Production" (or environment name)
  #    Copy the new key

  # 4. Update in your environment:
  #    - Local: Add to .env.test
  #    - UAT: Update in Koyeb Secrets
  #    - Production: Update in platform secrets
  ```

#### 2. **Groq API Key**
- **Key**: `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`
- **Found in**: `.env.test`, `.env.uat`, `.env.llm_router`
- **Risk**: Unauthorized LLM usage, rate limit abuse
- **How to rotate**:
  ```bash
  # 1. Login to Groq
  https://console.groq.com/keys

  # 2. Revoke the old key:
  #    Find: gsk_Cj0xwU3QdanTuCLMW477...
  #    Click "Delete" or "Revoke"

  # 3. Create new key:
  #    Click: "Create API Key"
  #    Name: "WeedGo Production"
  #    Copy the new key

  # 4. Update in your environment
  ```

#### 3. **Twilio Auth Token**
- **Key**: `927eabf31e8a7c214539964bdcd6d7ec`
- **Account SID**: `AC7fabaac1e3be386ed7aef21834f9805d`
- **Found in**: `.env.test`, `.env.uat`
- **Risk**: Unauthorized SMS sending (very expensive!)
- **How to rotate**:
  ```bash
  # 1. Login to Twilio
  https://console.twilio.com/

  # 2. Navigate to: Account → API Keys & Tokens

  # 3. Under "Auth Token":
  #    Click: "View" to see current token
  #    Click: "Refresh" to generate new token

  # 4. IMPORTANT: Old token will stop working immediately!
  #    Have the new token ready to update all environments

  # 5. Update in:
  #    - .env.test (local)
  #    - Koyeb Secrets (UAT)
  #    - Platform secrets (Production)
  ```

#### 4. **SendGrid API Key**
- **Key**: `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`
- **Found in**: `.env.test`, `.env.uat`
- **Risk**: Unauthorized email sending, spam abuse
- **How to rotate**:
  ```bash
  # 1. Login to SendGrid
  https://app.sendgrid.com/settings/api_keys

  # 2. Find the exposed key (look for creation date or name)

  # 3. Delete the old key:
  #    Click: "..." → "Delete"

  # 4. Create new key:
  #    Click: "Create API Key"
  #    Name: "WeedGo Production API Key"
  #    Permissions: "Full Access" or specific permissions
  #    Click: "Create & View"
  #    Copy the key (you'll only see it once!)

  # 5. Update in your environments
  ```

#### 5. **SMTP Password (Gmail App Password)**
- **Key**: `pkryohwdsfgbieyd`
- **Email**: `charrcy@gmail.com`
- **Found in**: `.env.test`, `.env.uat`
- **Risk**: Unauthorized email access
- **How to rotate**:
  ```bash
  # 1. Login to Google Account
  https://myaccount.google.com/security

  # 2. Navigate to: "2-Step Verification" → "App passwords"

  # 3. Find "Mail" or the app name you used
  #    Click: "Remove" or "Revoke"

  # 4. Create new app password:
  #    Click: "Generate"
  #    Select: "Mail" and your device
  #    Copy the new 16-character password

  # 5. Update SMTP_PASSWORD in your environments
  ```

---

### High Priority (Rotate This Week)

#### 6. **Mapbox API Key**
- **Key**: `pk.eyJ1IjoiY2hhcnJjeSIsImEiOiJja2llcXF5eXcxNWx4MnlxeHAzbmJnY3g2In0.FC98EHBZh2apYVTNiuyNKg`
- **Found in**: `.env.test`, `.env.uat`
- **Risk**: Unauthorized geocoding requests, API charges
- **How to rotate**:
  ```bash
  # 1. Login to Mapbox
  https://account.mapbox.com/access-tokens/

  # 2. Find the exposed token (check "Created" date)

  # 3. Revoke the old token:
  #    Click: token name → "Revoke"

  # 4. Create new token:
  #    Click: "Create a token"
  #    Name: "WeedGo Production"
  #    Scopes: Select what you need (usually just geocoding)
  #    Click: "Create token"

  # 5. Update MAPBOX_API_KEY in your environments
  ```

---

### Critical Secrets (Rotate Immediately)

#### 7. **Database Credentials (Neon PostgreSQL)**
- **Connection**: `postgresql://neondb_owner:npg_49xrIFTtaqym@ep-super-mouse-a4vwh6l6-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require`
- **Password**: `npg_49xrIFTtaqym`
- **Found in**: `.env.uat`, `.env.cloudrun`, `.env.cloudrun.yaml`
- **Risk**: Full database access, data breach
- **How to rotate**:
  ```bash
  # 1. Login to Neon
  https://console.neon.tech/

  # 2. Navigate to your project: "ep-super-mouse-a4vwh6l6"

  # 3. Go to: Settings → Reset password

  # 4. Generate new password:
  #    Click: "Reset password"
  #    Copy the new password

  # 5. Update DATABASE_URL in:
  #    - .env.uat (local)
  #    - Koyeb Secrets
  #    - Any Cloud Run configs

  # 6. IMPORTANT: Update DB_PASSWORD variable separately too!
  ```

#### 8. **Upstash Redis Token**
- **URL**: `https://powerful-ladybird-21805.upstash.io`
- **Token**: `AVUtAAIncDI2ZTg1M2FjOGQzY2M0ZjM0OGU4NTc0MTA3ODJjMGQ0MXAxMA`
- **Found in**: `.env.uat`, `.env.cloudrun`, `.env.cloudrun.yaml`
- **Risk**: Cache manipulation, session hijacking
- **How to rotate**:
  ```bash
  # 1. Login to Upstash
  https://console.upstash.com/redis

  # 2. Find your database: "powerful-ladybird-21805"

  # 3. Navigate to: Details → REST API

  # 4. Regenerate token:
  #    Click: "Regenerate Token"
  #    Confirm the action
  #    Copy the new UPSTASH_REDIS_REST_TOKEN

  # 5. Update in your environments

  # Note: URL stays the same, only token changes
  ```

#### 9. **JWT Secret Key**
- **Key**: `G5Z6z+VwaymtFvgzTDTMM8rhcUovzUG+AvRyKzlG/xc=`
- **Found in**: `.env.uat`, `.env.cloudrun`, `.env.cloudrun.yaml`
- **Risk**: Token forging, session hijacking
- **How to rotate**:
  ```bash
  # 1. Generate new JWT secret:
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"

  # 2. Copy the generated secret

  # 3. Update JWT_SECRET_KEY in your environment

  # 4. IMPORTANT: This will invalidate ALL existing user sessions!
  #    Users will need to log in again

  # 5. Consider announcing maintenance window to users
  ```

---

## 📅 Rotation Timeline

### Immediate (Today)
- [ ] OpenRouter API Key
- [ ] Groq API Key
- [ ] Twilio Auth Token
- [ ] SendGrid API Key
- [ ] Database Password
- [ ] Upstash Redis Token
- [ ] JWT Secret Key

### This Week
- [ ] Mapbox API Key
- [ ] SMTP App Password

---

## 🔄 Rotation Procedure

### For Each Service:

1. **Before Rotation**:
   - [ ] Note down the current key location
   - [ ] Prepare update procedure
   - [ ] Have access to all deployment platforms

2. **Rotation**:
   - [ ] Login to service dashboard
   - [ ] Generate new key/token
   - [ ] **Copy immediately** (some services show keys only once)
   - [ ] Save to password manager (1Password, LastPass, etc.)

3. **Update Environments**:

   **Local Development** (.env.test):
   ```bash
   # Edit your local .env.test file
   nano src/Backend/.env.test
   # Replace old key with new key
   ```

   **Koyeb (UAT)**:
   ```bash
   # Update secret via CLI
   koyeb secret update OPENROUTER_API_KEY --value "new-key-here"

   # Or via Dashboard:
   # Settings → Secrets → Find secret → Edit → Save

   # Redeploy service
   koyeb service redeploy weedgo-uat
   ```

   **Google Cloud Run**:
   ```bash
   # Update secret
   echo -n "new-key-here" | gcloud secrets versions add SECRET_NAME --data-file=-

   # Redeploy
   gcloud run deploy weedgo-uat --update-secrets=OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest
   ```

4. **After Rotation**:
   - [ ] Test the new key works
   - [ ] Revoke/delete the old key
   - [ ] Document the rotation in your team wiki
   - [ ] Update this checklist

---

## ✅ Verification Checklist

After rotating all keys:

### Functional Tests
- [ ] Can connect to database
- [ ] Can cache data in Redis
- [ ] Can send SMS (Twilio)
- [ ] Can send emails (SendGrid)
- [ ] Can geocode addresses (Mapbox)
- [ ] LLM inference works (OpenRouter)
- [ ] LLM inference works (Groq)
- [ ] User can log in (JWT)

### Security Tests
- [ ] Old keys are revoked/deleted
- [ ] Old keys no longer work
- [ ] No secrets in git history (or repo is private)
- [ ] All secrets in platform secret managers
- [ ] No secrets in deployment configs

---

## 📊 Impact Assessment

### Services Affected
- **Authentication**: JWT rotation invalidates all user sessions
- **Database**: Brief connection drop during password change
- **Cache**: Brief unavailability during token rotation
- **SMS/Email**: Immediate rotation, no downtime
- **LLM Services**: Immediate rotation, no downtime
- **Geocoding**: Immediate rotation, no downtime

### Downtime
- **Estimated**: 0-5 minutes per environment
- **User Impact**: Users need to log in again after JWT rotation
- **Recommendation**: Rotate during low-traffic hours

---

## 🛡️ Prevention Measures

### Implemented
- [x] Updated `.gitignore` to protect `.env` files
- [x] Created `.env.example` templates for all environments
- [x] Removed secret files from git tracking

### To Implement
- [ ] Set up git hooks to prevent committing secrets
- [ ] Use platform secret managers for all environments
- [ ] Implement secret scanning in CI/CD
- [ ] Set up secret rotation schedule (every 90 days)
- [ ] Add pre-commit hooks with `detect-secrets`
- [ ] Enable GitHub/GitLab secret scanning
- [ ] Document secret management process
- [ ] Train team on security best practices

---

## 🔗 Quick Links

- OpenRouter: https://openrouter.ai/keys
- Groq: https://console.groq.com/keys
- Twilio: https://console.twilio.com/
- SendGrid: https://app.sendgrid.com/settings/api_keys
- Mapbox: https://account.mapbox.com/access-tokens/
- Neon: https://console.neon.tech/
- Upstash: https://console.upstash.com/redis
- Koyeb: https://app.koyeb.com/secrets
- Google Cloud Secrets: https://console.cloud.google.com/security/secret-manager

---

## 📝 Rotation Log

Keep track of when keys were rotated:

| Service | Old Key Created | Rotated Date | Rotated By | New Key ID |
|---------|----------------|--------------|------------|------------|
| OpenRouter | Unknown | YYYY-MM-DD | Name | sk-or-v1-... |
| Groq | Unknown | YYYY-MM-DD | Name | gsk_... |
| Twilio | Unknown | YYYY-MM-DD | Name | Account SID |
| SendGrid | Unknown | YYYY-MM-DD | Name | SG.... |
| Mapbox | Unknown | YYYY-MM-DD | Name | pk.eyJ... |
| Database | Unknown | YYYY-MM-DD | Name | npg_... |
| Redis | Unknown | YYYY-MM-DD | Name | Token ID |
| JWT | Unknown | YYYY-MM-DD | Name | N/A |

---

## ⚠️ URGENT REMINDER

**These keys are in git history forever.** Even though we removed them from tracking, anyone who clones the repository can see them in git history.

**Actions**:
1. **Rotate all keys TODAY**
2. **Monitor usage** for any suspicious activity
3. **Consider making repository private** if it's currently public
4. **Set up alerts** for unusual API usage

**If you need to completely remove secrets from git history** (advanced):
```bash
# WARNING: This rewrites git history!
# Coordinate with your team first
git filter-repo --path src/Backend/.env.test --invert-paths
git filter-repo --path src/Backend/.env.uat --invert-paths
# ... repeat for all secret files

# Force push (destructive!)
git push origin --force --all
```

---

## 📞 Need Help?

If you encounter issues during rotation:
1. Check service status pages
2. Review service documentation
3. Contact service support
4. Reach out to team lead

**Remember**: Security first. When in doubt, rotate the key.
