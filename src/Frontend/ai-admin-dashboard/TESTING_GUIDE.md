# Multilingual Translation Testing Guide

## Overview

This guide describes the comprehensive testing suite for the AI Admin Dashboard's multilingual implementation across 28 languages.

---

## 🎯 Testing Goals

1. **Functional Correctness** - Verify language switching works reliably
2. **RTL Layout Verification** - Ensure right-to-left languages display properly
3. **Translation Completeness** - Check that all translations are present and meaningful
4. **Performance** - Verify language switching is fast and efficient
5. **Visual Consistency** - Ensure UI renders correctly in all languages

---

## 📋 Test Suites

### 1. Language Switching Tests (`01-language-switching.spec.ts`)

**Purpose:** Verify basic language switching functionality

**Tests:**
- Default language loads correctly (English)
- All 28 languages can be switched to successfully
- Language preference persists on page reload
- Language persists across navigation
- Text direction (LTR/RTL) applies correctly

**Run:** `npm run test:language`

---

### 2. RTL Layout Tests (`02-rtl-layout.spec.ts`)

**Purpose:** Verify right-to-left language layouts

**Languages Tested:** Arabic, Persian, Hebrew, Urdu

**Tests:**
- HTML `dir` attribute set to 'rtl'
- Navigation elements mirrored correctly
- Icons and chevrons flipped appropriately
- Form inputs have RTL text direction
- Layout comparison with LTR baseline

**Run:** `npm run test:rtl`

---

### 3. Translation Sanity Tests (`03-translation-sanity.spec.ts`)

**Purpose:** Verify translation quality and completeness

**Tests:**
- No missing translations (detect untranslated English)
- Correct script rendering (Arabic, Cyrillic, CJK, etc.)
- Font rendering for all scripts
- Indigenous languages display syllabic characters
- Asian languages display correct character sets
- Key pages translated across all languages

**Run:** `npm run test:sanity`

---

### 4. Performance Tests (`04-performance.spec.ts`)

**Purpose:** Verify language switching performance

**Tests:**
- Language switch completes within 2 seconds
- Rapid switching doesn't cause errors
- Language assets are cached after first load
- No memory leaks during repeated switching
- All 28 languages load without network errors
- UI remains responsive during switching

**Run:** `npm run test:performance`

---

### 5. Comprehensive UI Tests (`05-comprehensive.spec.ts`)

**Purpose:** Full page testing with visual verification

**Tests:**
- Key pages render correctly in all languages
- Layout issues detection (overflow, clipping)
- Visual comparison between RTL and LTR
- Navigation menu functionality
- Language selector accessibility
- Login page in multiple languages
- Form input handling in different scripts

**Run:** `npm run test:comprehensive`

---

## 🚀 Running Tests

### Quick Test (Recommended for Development)

```bash
./run-translation-tests.sh quick
```

Runs language switching + RTL tests (~5 minutes)

### Full Test Suite

```bash
./run-translation-tests.sh all
```

Runs all test suites (~20-30 minutes)

### Individual Test Suites

```bash
npm run test:language      # Language switching
npm run test:rtl           # RTL layouts
npm run test:sanity        # Translation sanity
npm run test:performance   # Performance
npm run test:comprehensive # Full UI tests
```

### Interactive UI Mode

```bash
npm run test:ui
```

Opens Playwright's interactive test UI for debugging

---

## 📊 Test Reports

After running tests, several reports are generated:

### HTML Report
```bash
npm run test:report
```

Opens interactive HTML report with:
- Test results for each suite
- Screenshots of failures
- Execution timeline
- Detailed error logs

**Location:** `playwright-report/index.html`

### JSON Report

Machine-readable test results for CI/CD integration

**Location:** `test-results/results.json`

### Screenshots

Visual captures of UI in different languages

**Location:** `test-results/screenshots/`

**Naming:** `{language-code}-{page-name}.png`

Examples:
- `ar-dashboard.png` - Arabic dashboard
- `zh-inventory.png` - Chinese inventory page
- `he-tenants.png` - Hebrew tenants page

---

## 🔍 Test Configuration

### Playwright Configuration

**File:** `playwright.config.ts`

Key settings:
- **Base URL:** `http://localhost:3003`
- **Timeout:** 60 seconds per test
- **Retries:** 2 on CI, 0 locally
- **Browser:** Chromium
- **Dev Server:** Auto-starts Vite

### Language Configuration

**File:** `tests/utils/languages.ts`

Defines all 28 languages with:
- Language code (ISO 639-1)
- Native name
- English name
- RTL flag
- Script type
- Test phrase for verification

### Test Helpers

**File:** `tests/utils/test-helpers.ts`

Utility functions:
- `switchLanguage()` - Change UI language
- `verifyTextDirection()` - Check RTL/LTR
- `detectMissingTranslations()` - Find untranslated text
- `verifyRTLLayout()` - Check RTL-specific UI
- `measureLanguageSwitchTime()` - Performance measurement
- `checkLayoutIssues()` - Detect overflow/clipping
- `takeLanguageScreenshot()` - Capture UI screenshots

---

## 🎨 Test Scenarios by Language Group

### Indigenous Languages (2)
- **Cree (cr)**, **Inuktitut (iu)**
- Focus: Syllabic character rendering
- Test: `test.describe('Indigenous Languages - Cultural Appropriateness')`

### Asian Languages (11)
- **Bengali, Gujarati, Hindi, Japanese, Korean, Punjabi, Tamil, Tagalog, Vietnamese, Cantonese, Mandarin**
- Focus: Complex scripts, character display
- Test: `test.describe('Asian Languages - Character Display')`

### Middle Eastern Languages (4)
- **Arabic, Persian, Hebrew, Urdu**
- Focus: RTL layout, text alignment
- Test: `test.describe('RTL Layout Tests')`

### European Languages (11)
- **German, Spanish, French, Italian, Dutch, Polish, Portuguese, Romanian, Russian, Ukrainian, Somali**
- Focus: Latin/Cyrillic script rendering
- Test: Standard comprehensive tests

---

## 🐛 Debugging Failed Tests

### View Test Results

```bash
npm run test:report
```

### Run Specific Test

```bash
npx playwright test tests/02-rtl-layout.spec.ts --headed
```

`--headed` opens browser window to see what's happening

### Debug Mode

```bash
npx playwright test --debug
```

Opens Playwright Inspector for step-by-step debugging

### Screenshots on Failure

All failures automatically capture:
- Screenshot of the page
- HTML snapshot
- Console logs
- Network requests

Location: `test-results/`

---

## ✅ Acceptance Criteria

Tests pass when:

1. **Language Switching**
   - All 28 languages load successfully
   - Language persists across navigation
   - No JavaScript errors during switching

2. **RTL Layouts**
   - `dir="rtl"` applied to HTML element
   - Text alignment flipped
   - Navigation mirrored

3. **Translation Quality**
   - < 5 untranslated strings per language
   - Correct script rendering
   - Proper font loading

4. **Performance**
   - Language switch < 2 seconds
   - Average switch time < 1 second
   - No memory leaks (< 50% memory increase)

5. **Visual Consistency**
   - No layout overflow issues
   - Key UI elements visible
   - Forms functional in all languages

---

## 🔧 Troubleshooting

### Dev Server Not Starting

```bash
# Check if port 3003 is in use
lsof -ti:3003 | xargs kill -9

# Restart tests
npm run test
```

### Language Not Switching in Tests

1. Check `LanguageSelector.tsx` is rendering
2. Verify language files exist in `src/i18n/locales/{code}/`
3. Check browser console for errors (use `--headed` mode)

### RTL Tests Failing

1. Verify `applyTextDirection()` is called in `src/i18n/config.ts`
2. Check `src/utils/rtl.ts` has correct RTL language codes
3. Ensure CSS supports RTL (check for `[dir="rtl"]` selectors)

### Performance Tests Timing Out

1. Increase timeout in `playwright.config.ts`
2. Check network requests in dev tools
3. Verify translation files aren't too large

---

## 📚 Resources

### Playwright Documentation
- [Playwright Testing](https://playwright.dev/docs/intro)
- [Test Configuration](https://playwright.dev/docs/test-configuration)
- [Locators](https://playwright.dev/docs/locators)

### i18next Documentation
- [react-i18next](https://react.i18next.com/)
- [i18next Configuration](https://www.i18next.com/overview/configuration-options)

### RTL Best Practices
- [RTL Styling Guide](https://rtlstyling.com/)
- [Material Design RTL](https://material.io/design/usability/bidirectionality.html)

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Translation Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 📝 Adding New Languages

When adding a new language:

1. Add translation files to `src/i18n/locales/{code}/`
2. Update `src/i18n/config.ts` SUPPORTED_LANGUAGES
3. If RTL, add to `src/utils/rtl.ts` RTL_LANGUAGES
4. Update `tests/utils/languages.ts` LANGUAGES array
5. Run `npm run test` to verify

---

## 🎯 Test Coverage

Current test coverage:

- **Languages:** 28/28 (100%)
- **Namespaces:** 21/21 (100%)
- **Test Suites:** 5 comprehensive suites
- **Test Cases:** ~150+ individual tests
- **Screenshots:** Visual verification for all languages

---

**Last Updated:** October 18, 2025
**Maintained By:** WeedGo Development Team
