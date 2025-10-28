# Email & Phone Verification - Quick Test Guide

## Testing the Implementation

### Prerequisites
1. Backend API server running
2. SendGrid configured for email OTP
3. Twilio configured for SMS OTP (optional, for phone verification)
4. Frontend development server running

### Test Scenario 1: Email Verification (Happy Path)

**Steps:**
1. Navigate to signup page: `http://localhost:5173/signup`
2. Complete Step 1 (Company Information)
3. In Step 2, enter email: `test@example.com`
4. Click "Verify" button next to email field
5. OTP component should appear
6. Check email inbox for 6-digit code
7. Enter the 6-digit code
8. Should auto-verify when 6th digit entered
9. Green checkmark should appear
10. OTP component should close
11. Email field should have green border
12. Click "Next" - should proceed to Step 3

**Expected Result:**
✅ Email verified successfully, can proceed

### Test Scenario 2: Phone Verification (Happy Path)

**Steps:**
1. After email verification in Step 2
2. Enter phone: `+15551234567` (with country code)
3. Click "Verify" button next to phone field
4. OTP component should appear
5. Check phone for SMS with 6-digit code
6. Enter the 6-digit code
7. Should auto-verify when 6th digit entered
8. Green checkmark should appear
9. Phone field should have green border

**Expected Result:**
✅ Phone verified successfully

### Test Scenario 3: Skip Phone Verification

**Steps:**
1. After email verification
2. Leave phone field empty
3. Click "Next"

**Expected Result:**
✅ Can proceed without phone verification (phone is optional)

### Test Scenario 4: Invalid Email (Error Handling)

**Steps:**
1. Enter invalid email: `notanemail`
2. Click "Verify"

**Expected Result:**
❌ Error: "Please enter a valid email address"
Should NOT show OTP component

### Test Scenario 5: Wrong OTP Code

**Steps:**
1. Initiate email verification
2. Enter wrong code: `000000`
3. Press enter or click verify

**Expected Result:**
❌ Error: "Verification failed. Please check your code."
Code fields should clear
Should allow retry

### Test Scenario 6: Resend OTP

**Steps:**
1. Initiate verification
2. Wait for countdown (or manually wait)
3. Click "Resend Code"

**Expected Result:**
✅ New code sent
✅ 60-second countdown resets
✅ Previous code invalidated

### Test Scenario 7: Paste OTP Code

**Steps:**
1. Initiate verification
2. Copy 6-digit code: `123456`
3. Click in first OTP input box
4. Paste (Cmd/Ctrl + V)

**Expected Result:**
✅ All 6 digits fill in automatically
✅ Auto-verify triggered

### Test Scenario 8: Change Email After Verification

**Steps:**
1. Verify email successfully (green checkmark)
2. Change email to different address
3. Observe verification status

**Expected Result:**
✅ Verified status resets (no more green checkmark)
✅ Must re-verify new email

### Test Scenario 9: Try to Proceed Without Email Verification

**Steps:**
1. Enter email but don't verify
2. Complete other fields
3. Click "Next"

**Expected Result:**
❌ Error: "Email must be verified before proceeding"
Should NOT proceed to next step

### Test Scenario 10: Cancel Verification

**Steps:**
1. Click "Verify" to show OTP component
2. Click "Cancel" button

**Expected Result:**
✅ OTP component closes
✅ Can re-initiate verification

## Testing Backend Integration

### Test OTP Send Endpoint
```bash
curl -X POST http://localhost:5024/api/v1/auth/otp/send \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "identifier_type": "email",
    "purpose": "signup"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "expires_in": 600
}
```

### Test OTP Verify Endpoint
```bash
curl -X POST http://localhost:5024/api/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "identifier_type": "email",
    "code": "123456",
    "purpose": "signup"
  }'
```

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "Verification successful",
  "access_token": "jwt_token_here",
  "user": { ... }
}
```

**Expected Response (Failure):**
```json
{
  "detail": "Invalid or expired verification code"
}
```

## Browser Console Checks

### Success Case
```
✅ OTP sent successfully
✅ Verification successful
✅ Email verified: true
```

### Error Case
```
❌ Failed to send OTP: <error message>
❌ Verification failed: Invalid code
```

## Visual Indicators

### Email Verified
- ✅ Green checkmark icon
- ✅ Green border on email input
- ✅ "Verified ✓" text

### Email Not Verified
- ⚠️ No checkmark
- ⚠️ "Verify" button visible
- ⚠️ Gray border on input

### During Verification
- 🔄 OTP component visible
- 🔄 6-digit input boxes
- 🔄 "Verifying..." text (when submitting)

## Rate Limiting Tests

### Test Rate Limit
1. Send 6 OTP requests in quick succession
2. 6th request should fail with rate limit error

**Expected:**
❌ "Too many requests. Please wait before trying again."

## Mobile Responsive Testing

Test on various screen sizes:
- ✅ iPhone SE (375px)
- ✅ iPad (768px)
- ✅ Desktop (1920px)

Check:
- OTP input boxes are properly sized
- Buttons are touchable (min 44px)
- Text is readable
- No horizontal scroll

## Accessibility Testing

### Keyboard Navigation
1. Tab through form fields
2. Verify tab order is logical
3. Can navigate through OTP boxes with arrows
4. Can submit with Enter key

### Screen Reader
1. Test with VoiceOver (Mac) or JAWS (Windows)
2. Verify labels are announced
3. Verify error messages are announced
4. Verify success states are announced

## Common Issues & Solutions

### Issue: OTP Email Not Received
**Solutions:**
1. Check spam folder
2. Verify SendGrid API key in backend
3. Check backend logs for errors
4. Try different email address

### Issue: SMS Not Received
**Solutions:**
1. Verify phone format includes country code (+1...)
2. Check Twilio credentials in backend
3. Verify Twilio phone number is SMS-enabled
4. Check backend logs

### Issue: "Verify" Button Not Appearing
**Solutions:**
1. Ensure email/phone field has value
2. Check browser console for errors
3. Clear browser cache
4. Verify OTPVerification component imported

### Issue: Code Verification Fails
**Solutions:**
1. Ensure code entered within 10 minutes
2. Check for extra spaces in code
3. Try resend to get fresh code
4. Verify backend OTP service running

## Test Data

### Valid Test Emails
```
test@example.com
user@domain.com
admin@test.org
```

### Valid Test Phones (with country code)
```
+15551234567
+14165551234
+17785551234
```

### Invalid Test Data
```
Email: notanemail (missing @)
Email: @domain.com (missing local part)
Phone: 5551234567 (missing country code)
```

## Success Criteria

All tests should result in:
- ✅ Email verification required and working
- ✅ Phone verification optional and working
- ✅ Error handling graceful
- ✅ UI responsive on all devices
- ✅ Accessibility compliant
- ✅ No console errors
- ✅ Proper validation blocking progression
- ✅ State management working correctly

---

**Test Status:** Ready for QA
**Last Updated:** January 2025
