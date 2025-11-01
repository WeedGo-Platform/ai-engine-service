# Super Admin User Created ✅

**Date:** November 1, 2025  
**Status:** Successfully Created

---

## 🔐 Credentials

```
Email:    admin@weedgo.ca
Password: Password1$
Role:     super_admin
User ID:  0598a900-1991-4d15-bab9-66d834f3ea17
```

---

## ✅ Verification

- ✅ User exists in database
- ✅ Email verified: `true`
- ✅ Role: `super_admin`
- ✅ Password hashed with bcrypt

---

## 📝 User Details

| Field | Value |
|-------|-------|
| **Email** | admin@weedgo.ca |
| **Role** | super_admin |
| **Email Verified** | ✅ Yes |
| **User ID** | 0598a900-1991-4d15-bab9-66d834f3ea17 |
| **Database** | ai_engine |
| **Created By** | scripts/create_super_admin.py |

---

## 🚀 Usage

### Login to Admin Dashboard

1. Navigate to admin dashboard: `http://localhost:3003` (or your deployed URL)
2. Click "Login"
3. Enter credentials:
   - Email: `admin@weedgo.ca`
   - Password: `Password1$`
4. Access all super admin features

### What Super Admin Can Do

✅ Manage all tenants  
✅ Create/edit/delete tenants  
✅ View all users  
✅ Manage system settings  
✅ Access all features  
✅ Override tenant restrictions  

---

## ⚠️ Security Recommendations

1. **Change Password After First Login**
   - Current password is default for setup
   - Use a strong, unique password

2. **Enable 2FA** (if available)
   - Add extra security layer

3. **Limit Access**
   - Only share credentials with authorized personnel
   - Don't commit credentials to git

4. **Rotate Password Regularly**
   - Change password every 90 days
   - Use password manager

---

## 🔧 Script Used

**Location:** `src/Backend/scripts/create_super_admin.py`

**Environment Variables Required:**
- `DB_PASSWORD` - Database password
- `ADMIN_EMAIL` - Admin email (default: admin@weedgo.ca)
- `ADMIN_PASSWORD` - Admin password (default: Password1$)

**Command:**
```bash
cd src/Backend
DB_PASSWORD=weedgo123 \
ADMIN_EMAIL=admin@weedgo.ca \
ADMIN_PASSWORD='Password1$' \
python3 scripts/create_super_admin.py
```

---

## 📊 Database Details

**Connection Info:**
- Host: localhost
- Port: 5434
- Database: ai_engine
- User: weedgo

**Table:** `users`

**Record:**
```sql
SELECT * FROM users WHERE email = 'admin@weedgo.ca';
```

---

**Status:** ✅ READY FOR USE
