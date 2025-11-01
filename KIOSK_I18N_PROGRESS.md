# Kiosk & Menu Display Internationalization - Progress Report

**Branch:** `dashboard-fixes`  
**Date:** November 1, 2025  
**Status:** 🟡 In Progress (Phase 1 Complete - WelcomeScreen migrated)

---

## 📊 Summary

Systematic internationalization of all hardcoded text in the `/apps` page (POS, Kiosk, Menu Display tabs).

**Phase 1 Complete:**
- ✅ Created `kiosk.json` translation structure (70+ keys)
- ✅ Deployed to all 29 supported languages  
- ✅ EN & FR translations complete
- ✅ WelcomeScreen.tsx migrated to i18next

**Remaining:** 8 kiosk components + MenuDisplay components

---

## ✅ Phase 1: WelcomeScreen (COMPLETE)

### Changes Made:
1. **Removed** custom `translations` object (lines 22-51)
2. **Added** `useTranslation` hook from react-i18next
3. **Integrated** with i18n.changeLanguage() for language switching
4. **Removed** hardcoded "Select Store" text

### Translation Keys Used:
```typescript
kiosk:welcome.title              // "Welcome to"
kiosk:welcome.selectStore        // "Select Store"
kiosk:welcome.selectLanguage     // "Select Your Language"
kiosk:welcome.or                 // "OR"
kiosk:welcome.scanQR             // "Scan QR to Sign In"
kiosk:welcome.signIn             // "Sign In with Phone/Email"
kiosk:welcome.continueAsGuest    // "Continue as Guest"
kiosk:welcome.touchToStart       // "Touch to Start Shopping"
```

---

## 🔄 Phase 2: Remaining Kiosk Components (PENDING)

### Priority: HIGH

#### 1. Cart.tsx
**Hardcoded Strings:** 8  
**Keys Ready:** kiosk:cart.* (8 keys)

#### 2. Checkout.tsx  
**Hardcoded Strings:** 10  
**Keys Ready:** kiosk:checkout.* (10 keys)  
**Placeholders:** namePlaceholder, emailPlaceholder, phonePlaceholder

#### 3. ProductBrowsing.tsx
**Hardcoded Strings:** 15+  
**Keys Ready:** kiosk:browse.*, kiosk:sort.* (15 keys)

#### 4. OrderConfirmation.tsx
**Hardcoded Strings:** 7  
**Keys Ready:** kiosk:confirmation.* (7 keys)  
⚠️ **CRITICAL:** Contains hardcoded French text: "Retour à l'accueil dans" (line 73)

### Priority: MEDIUM

#### 5. ProductDetailsModal.tsx
**Hardcoded Strings:** 20+  
**Keys Ready:** kiosk:productDetails.* (20 keys)

### Priority: LOW

#### 6. ProductRecommendations.tsx
**Hardcoded Strings:** 3  
**Keys Ready:** kiosk:recommendations.* (3 keys)

#### 7. AIAssistant.tsx
**Hardcoded Strings:** 3  
**Keys Ready:** kiosk:assistant.* (3 keys)

---

## 📁 Files Created

### Translation Files (29 languages)
```
✅ src/i18n/locales/en/kiosk.json  (Complete - 70+ keys)
✅ src/i18n/locales/fr/kiosk.json  (Complete - 70+ keys)
⏳ src/i18n/locales/{ar,bn,cr,de,es,fa,gu,he,hi,it,iu,ja,ko,nl,pa,pl,pt,ro,ru,so,ta,tl,uk,ur,vi,yue,zh}/kiosk.json
   (English placeholders - need translation)
```

### Modified Files
```
✅ src/components/kiosk/WelcomeScreen.tsx
```

---

## 🎯 Next Steps

1. Update Cart.tsx - add `useTranslation`, replace hardcoded strings
2. Update Checkout.tsx - add `useTranslation`, replace placeholders
3. Update ProductBrowsing.tsx - add `useTranslation`, replace sort options
4. **FIX** OrderConfirmation.tsx - remove hardcoded French!
5. Update ProductDetailsModal.tsx - extensive replacements needed
6. Update remaining low-priority components
7. Analyze MenuDisplay components (not yet done)
8. Test all flows in EN and FR
9. Professional translation for 27 remaining languages

---

## 💡 Implementation Pattern

```typescript
// 1. Import
import { useTranslation } from 'react-i18next';

// 2. Hook
const { t } = useTranslation(['kiosk']);

// 3. Use
<h1>{t('kiosk:cart.title')}</h1>
<input placeholder={t('kiosk:checkout.namePlaceholder')} />
```

---

## ⚠️ Known Issues

1. **Hardcoded French** in OrderConfirmation.tsx (line 73)
2. **Tax Rate** "HST 13%" is Ontario-specific - should be dynamic
3. **27 Languages** need professional translation (currently English placeholders)

---

**Progress:** 1/9 components migrated (11%)  
**Translation Keys:** 74 keys defined  
**Languages:** 2/29 complete (7%)
