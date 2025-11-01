# Tenant Signup Status - 2025-10-31

## ✅ Completed Fixes

### 1. Email OTP Auto-Verification on Paste
- **Issue**: Pasting 6-digit code showed "Please enter a 6-digit code" error briefly
- **Fix**: Made paste verification immediate (removed setTimeout delay)
- **Status**: ✅ Fixed in commit 864ffda

### 2. Exact Domain Matching (Including TLD)
- **Issue**: Email domain validation was too loose - `support@potpalace.ca` matched `www.potpalace.cc`
- **Fix**: Changed from substring matching to exact domain match including TLD
- **Status**: ✅ Fixed in commit 864ffda

## Current State

### Environment Configuration
```bash
DATABASE_URL=postgresql://weedgo:your_password_here@localhost:5434/ai_engine
SMTP_USERNAME=admin@weedgo.ca  
SMTP_PASSWORD="zsox fzaz zjlg jxgj"  # Gmail app password (NOT in git)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Signup Flow Features
1. ✅ Multi-step wizard (5 steps)
2. ✅ Email verification with OTP
3. ✅ Phone verification (optional)
4. ✅ Ontario CRSA license validation
5. ✅ Checkbox to auto-create first store from CRSA data (default: checked)
6. ✅ Email domain must match website domain (exact TLD match)
7. ✅ Atomic transaction (tenant + user + store created together or all rolled back)
8. ✅ Terms of Service and Privacy Policy acceptance with audit trail
9. ✅ Duplicate prevention (check by email, tenant code, website domain)

### Known Issues from Testing
- Some orphaned database records from incomplete signup attempts
- These cause "user already exists" or "tenant already exists" errors
- **Solution**: Clear test data or use different email/website for testing

## Testing the Signup Flow

1. Use unique email that hasn't been used before
2. Use unique website domain
3. Verify CRSA license for Ontario
4. Check/uncheck "auto-create store" as needed
5. Complete all 5 steps

## Recent Fixes Applied (Last 24 Hours)
- Transaction isolation for atomic signup
- Store schema fixes (JSONB address field)  
- Province territory foreign key handling
- Missing import fixes (HTTPStatus)
- Subscription repository connection parameter
- Audit log foreign key constraints
- User repository transaction support
- Password reset flow
- Login page translations
- Free tier billing cycle hiding
- OTP paste auto-verify
- Domain validation exactness

