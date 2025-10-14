# Admin Review Workflow Guide

**WeedGo AI Engine - Tenant Account Review System**

---

## Table of Contents

1. [Overview](#overview)
2. [Access Requirements](#access-requirements)
3. [Getting Started](#getting-started)
4. [Reviewing Pending Accounts](#reviewing-pending-accounts)
5. [Approval Process](#approval-process)
6. [Rejection Process](#rejection-process)
7. [Real-Time Notifications](#real-time-notifications)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Admin Review Workflow allows administrators to review and approve new tenant account signups that require manual verification. This typically includes:

- **Manual Review Tier**: Accounts where email domain doesn't match CRSA website
- **High-Risk Signups**: Unusual patterns or suspicious activity
- **Bulk Signups**: Multiple accounts from same organization

### Verification Tiers

| Tier | Description | Review Required |
|------|-------------|----------------|
| **Auto-Approved** | Email domain matches CRSA website | ❌ No |
| **Manual Review** | Email domain doesn't match or suspicious | ✅ Yes |

---

## Access Requirements

### Required Role

To access the Admin Review Dashboard, you must have one of the following roles:

- `super_admin` - Full access to all features
- `tenant_admin` - Access to review tenants
- `admin` - Basic admin access

### Login

1. Navigate to the admin dashboard: `https://admin.weedgo.com`
2. Click **Sign In**
3. Enter your admin credentials
4. You'll be redirected to the dashboard

---

## Getting Started

### Accessing the Review Dashboard

1. Log in to the admin dashboard
2. Click on **Tenants** in the left sidebar
3. Select **Review** from the dropdown menu
4. Or directly navigate to: `https://admin.weedgo.com/dashboard/tenants/review`

### Dashboard Overview

The Tenant Review page displays:

**Stats Cards (Top)**
- 📊 Total Pending - All accounts awaiting review
- 📅 Pending This Week - New accounts this week
- ⏱️ Avg Review Time - Average time to review
- ✅ Approval Rate - % of approved accounts

**Accounts Table (Main)**
- Store name and CRSA license number
- Contact email and name
- Submission date
- Verification tier
- Action buttons

---

## Reviewing Pending Accounts

### Step 1: Select an Account

Click on any row in the pending accounts table to view details.

### Step 2: Review Account Information

The detail modal displays:

**Store Information**
- Store name from CRSA registry
- CRSA license number (verified)
- Physical address
- Municipality
- Store status (from CRSA)

**Contact Information**
- Contact person name and role
- Email address
- Phone number (if provided)
- Submission date

**Verification Context**
- ✅ Email domain (e.g., @candream.ca)
- ✅ CRSA website (e.g., https://candream.ca)
- ✅/❌ Domain match status

### Step 3: Verification Checks

Perform the following checks:

1. **CRSA License Validation**
   - Verify license number matches CRSA registry
   - Confirm store status is "Authorized" or "Active"
   - Check address matches CRSA records

2. **Contact Verification**
   - Email domain should relate to business
   - Phone number should be in correct format
   - Contact name and role seem legitimate

3. **Domain Matching** (if failed)
   - Check if email domain relates to business
   - Look up website to verify legitimacy
   - Consider if using personal email is acceptable

4. **Red Flags** ⚠️
   - Generic email addresses (gmail, yahoo, etc.)
   - Mismatched business information
   - Recently created domains
   - Multiple signups with similar patterns

---

## Approval Process

### When to Approve

Approve an account when:
- ✅ CRSA license is valid and active
- ✅ Contact information appears legitimate
- ✅ No red flags identified
- ✅ Domain mismatch has valid explanation (e.g., personal email for small business)

### How to Approve

1. Click the **View Details** button for the account
2. Review all information carefully
3. (Optional) Add **Admin Notes** explaining approval rationale
4. Click **Approve Account**
5. Confirm the action

### What Happens After Approval

1. **Account Activated**
   - Account status changes from "pending_review" to "active"
   - Tenant can now access full platform features

2. **Password Setup Email Sent**
   - Automatic email sent to contact email
   - Contains secure password setup link (24-hour expiry)
   - Instructions for completing account setup

3. **Welcome Email** (Optional)
   - Additional welcome message
   - Getting started guide
   - Support contact information

4. **Real-Time Notification**
   - Other admins receive notification of approval
   - Notification includes admin who approved and timestamp

### Email Template Example

```
Subject: Your WeedGo Account Has Been Approved! 🎉

Hi [Contact Name],

Great news! Your WeedGo account for [Store Name] has been approved.

To complete your setup, please create your password:
[Password Setup Link - Expires in 24 hours]

Once you've set your password, you'll have full access to:
✅ AI-powered customer support
✅ Inventory management
✅ Analytics and reporting
✅ Multi-channel communication

Need help? Contact us at support@weedgo.com

Welcome aboard!
The WeedGo Team
```

---

## Rejection Process

### When to Reject

Reject an account when:
- ❌ CRSA license is invalid or suspended
- ❌ Obvious fraudulent activity
- ❌ Contact information is fake or misleading
- ❌ Multiple failed verification checks
- ❌ Duplicate signup (same business/person)

### How to Reject

1. Click the **View Details** button for the account
2. Review all information carefully
3. Click **Reject** button
4. **Enter rejection reason** (required, min 10 characters)
   - Be specific and professional
   - Include actionable feedback if applicable
5. Choose whether to **Send Notification**
6. Click **Confirm Rejection**

### Rejection Reason Examples

**Good Examples:**
```
❌ "CRSA license 1234567 shows as 'Suspended' in the registry. Please resolve license status and reapply."

❌ "Email address (john@example.com) does not appear to be associated with CanDream Inc. Please use business email or provide additional verification."

❌ "Multiple signup attempts detected with conflicting information. Please contact support to resolve."
```

**Bad Examples:**
```
❌ "Suspicious" (too vague)
❌ "Not approved" (no explanation)
❌ "Fake" (unprofessional)
```

### What Happens After Rejection

1. **Account Cancelled**
   - Account status changes to "cancelled"
   - Tenant cannot access platform

2. **Notification Email** (If enabled)
   - Rejection reason sent to contact email
   - Instructions for reapplication (if applicable)
   - Support contact information

3. **Admin Log**
   - Rejection recorded with admin ID, reason, and timestamp
   - Available for audit purposes

---

## Real-Time Notifications

### Notification Bell

The notification bell (🔔) in the top-right corner displays:

- **Green Dot**: Connected to real-time updates
- **Red Dot**: Disconnected (will reconnect automatically)
- **Badge Number**: Unread notification count

### Notification Types

1. **New Account Pending Review**
   ```
   👤 New account pending review: CanDream Inc.
   ```

2. **Account Approved**
   ```
   ✅ Account approved by admin@weedgo.com
   ```

3. **Account Rejected**
   ```
   ❌ Account rejected by admin@weedgo.com
   ```

### Managing Notifications

- **View All**: Click the bell icon
- **Mark as Read**: Click on individual notification
- **Mark All Read**: Click "Mark all read" button
- **Clear All**: Click "Clear all" button

### Browser Notifications

Enable browser notifications for desktop alerts:

1. Click the bell icon when prompted
2. Select "Allow" in browser permission dialog
3. Receive notifications even when tab is inactive

---

## Best Practices

### Review Timing

- ⏱️ **Aim for 24-hour turnaround** on all reviews
- 🚨 **Prioritize same-day reviews** during business hours
- 📊 **Monitor Avg Review Time** stat card

### Documentation

- ✍️ **Always add admin notes** for borderline cases
- 📝 **Document verification steps taken**
- 💡 **Provide clear rejection reasons**

### Communication

- 💬 **Be professional and helpful** in rejection messages
- 📧 **Provide actionable feedback** when possible
- 🤝 **Offer support contacts** for questions

### Security

- 🔒 **Verify CRSA license** in official registry
- 🔍 **Check domain age** for new websites
- ⚠️ **Report patterns** of suspicious activity
- 🛡️ **Never approve** without proper verification

### Efficiency

- ⚡ **Use keyboard shortcuts** (coming soon)
- 📋 **Sort by submission date** to handle oldest first
- 🎯 **Filter by verification tier** to batch similar reviews
- 🔔 **Enable notifications** to stay updated

---

## FAQ

### Q: How long does the password setup link last?

**A:** Password setup links expire after 24 hours. If expired, the tenant can request a new link from the login page.

### Q: Can I undo an approval or rejection?

**A:** Currently, no. Contact super_admin to manually update account status if needed.

### Q: What if I'm unsure about approving an account?

**A:**
1. Add admin notes with your concerns
2. Request additional verification from tenant
3. Consult with super_admin or team lead
4. When in doubt, reject with clear reason and instructions

### Q: How do I handle duplicate signups?

**A:**
1. Check if existing account already approved
2. If duplicate, reject new signup with reason: "Account already exists for [store name]. Please contact support."
3. If different stores, approve as separate accounts

### Q: What if CRSA license is pending?

**A:** Reject with reason: "CRSA license status shows as 'Pending'. Please reapply once license is approved by AGCO."

### Q: Can tenants reapply after rejection?

**A:** Yes, tenants can start a new signup flow. Previous rejections are logged for reference.

---

## Troubleshooting

### Issue: Can't access Review page

**Solutions:**
- Verify you have admin role (super_admin, tenant_admin, or admin)
- Clear browser cache and refresh
- Check with super_admin about role permissions
- Try logging out and back in

### Issue: Notifications not working

**Solutions:**
- Check green dot on notification bell (connection status)
- Enable browser notifications in browser settings
- Refresh the page to reconnect WebSocket
- Check browser console for WebSocket errors

### Issue: Can't see pending accounts

**Solutions:**
- Verify accounts exist by checking stats card
- Try clearing any applied filters
- Refresh the page (Cmd/Ctrl + R)
- Check browser console for API errors

### Issue: Approval/Rejection failing

**Solutions:**
- Check internet connection
- Verify JWT token hasn't expired (refresh page)
- Ensure rejection reason is at least 10 characters
- Contact technical support if persists

### Issue: Email not being sent

**Solutions:**
- Verify email service is configured
- Check spam folder
- Confirm email address is valid
- Review email logs in admin panel

---

## Support

### Technical Support

- **Email**: support@weedgo.com
- **Slack**: #admin-support channel
- **Phone**: 1-800-WEEDGO-1 (ext. 2)

### Escalation

For urgent issues or security concerns:
- **Security**: security@weedgo.com
- **On-Call**: Use PagerDuty escalation

---

## Appendix

### Verification Tier Decision Tree

```
Is email domain from CRSA website?
├─ Yes → Auto-Approved ✅
└─ No → Check email domain
    ├─ Business domain (e.g., @store.com) → Manual Review 🔍
    ├─ Generic (e.g., @gmail.com) → Manual Review 🔍
    └─ Suspicious → Flag for investigation 🚨
```

### Common Domain Patterns

**Auto-Approved Patterns:**
- `@candream.ca` ✅ (matches candream.ca website)
- `@torontocannabis.com` ✅
- `@greendispensary.ca` ✅

**Manual Review Patterns:**
- `@gmail.com` 🔍 (generic email)
- `@companyname.com` 🔍 (verify domain ownership)
- `@newdomain.xyz` 🔍 (recently registered)

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Document Owner**: WeedGo Admin Team
