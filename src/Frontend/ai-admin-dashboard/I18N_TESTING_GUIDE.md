# Internationalization (i18n) Testing Guide

Comprehensive testing guide for all 28 supported languages in the WeedGo Admin Dashboard.

## Supported Languages

The dashboard supports **28 languages** across multiple scripts and writing systems:

| Language | Code | Script | Direction | Native Name |
|----------|------|--------|-----------|-------------|
| English | en | Latin | LTR | English |
| Spanish | es | Latin | LTR | Español |
| French | fr | Latin | LTR | Français |
| Mandarin | zh | Han | LTR | 中文 |
| Cantonese | yue | Han | LTR | 廣東話 |
| Punjabi | pa | Gurmukhi | LTR | ਪੰਜਾਬੀ |
| **Arabic** | **ar** | **Arabic** | **RTL** | **العربية** |
| Tagalog | tl | Latin | LTR | Tagalog |
| German | de | Latin | LTR | Deutsch |
| Italian | it | Latin | LTR | Italiano |
| Portuguese | pt | Latin | LTR | Português |
| Polish | pl | Latin | LTR | Polski |
| Russian | ru | Cyrillic | LTR | Русский |
| Vietnamese | vi | Latin | LTR | Tiếng Việt |
| Hindi | hi | Devanagari | LTR | हिन्दी |
| Ukrainian | uk | Cyrillic | LTR | Українська |
| **Persian** | **fa** | **Arabic** | **RTL** | **فارسی** |
| Korean | ko | Hangul | LTR | 한국어 |
| Tamil | ta | Tamil | LTR | தமிழ் |
| **Urdu** | **ur** | **Arabic** | **RTL** | **اردو** |
| Gujarati | gu | Gujarati | LTR | ગુજરાતી |
| Romanian | ro | Latin | LTR | Română |
| Dutch | nl | Latin | LTR | Nederlands |
| Cree | cr | Canadian Aboriginal | LTR | ᓀᐦᐃᔭᐍᐏᐣ |
| Inuktitut | iu | Canadian Aboriginal | LTR | ᐃᓄᒃᑎᑐᑦ |
| Bengali | bn | Bengali | LTR | বাংলা |
| **Hebrew** | **he** | **Hebrew** | **RTL** | **עברית** |
| Somali | so | Latin | LTR | Soomaali |
| Japanese | ja | Japanese | LTR | 日本語 |

**Bold** indicates RTL languages requiring special testing.

## Testing Matrix

### 1. Character Encoding Tests

Test that all characters display correctly for each script type:

#### Latin Scripts (17 languages)
- [ ] English, Spanish, French, German, Italian, Portuguese
- [ ] Polish, Vietnamese, Tagalog, Romanian, Dutch, Somali
- Character tests: á, é, í, ó, ú, ñ, ç, ü, ø, å, ă, ș, ț

#### Cyrillic Scripts (2 languages)
- [ ] Russian (Русский)
- [ ] Ukrainian (Українська)
- Character tests: А, Б, В, Г, Д, Е, Ё, Ж, З, И, Й, І, Ї, Є

#### CJK (Chinese-Japanese-Korean) (3 languages)
- [ ] Mandarin (中文)
- [ ] Cantonese (廣東話)
- [ ] Japanese (日本語)
- [ ] Korean (한국어)
- Character tests: 中文字符, ひらがな, カタカナ, 한글

#### Indic Scripts (5 languages)
- [ ] Hindi (हिन्दी) - Devanagari
- [ ] Punjabi (ਪੰਜਾਬੀ) - Gurmukhi
- [ ] Tamil (தமிழ்) - Tamil
- [ ] Gujarati (ગુજરાતી) - Gujarati
- [ ] Bengali (বাংলা) - Bengali
- Complex character tests: Combined glyphs, diacritics, ligatures

#### Arabic Scripts (3 languages)
- [ ] Arabic (العربية)
- [ ] Persian (فارسی)
- [ ] Urdu (اردو)
- Character tests: Initial, medial, final, isolated forms
- Ligature tests: لا، ها، با

#### Hebrew Script (1 language)
- [ ] Hebrew (עברית)
- Character tests: א ב ג ד ה ו ז ח ט
- Nikud (vowel points) if applicable

#### Canadian Aboriginal Syllabics (2 languages)
- [ ] Cree (ᓀᐦᐃᔭᐍᐏᐣ)
- [ ] Inuktitut (ᐃᓄᒃᑎᑐᑦ)
- Syllabics tests: ᐁ ᐃ ᐅ ᐊ ᑫ ᑭ ᑯ ᑲ

### 2. Font Rendering Tests

Verify appropriate fonts are loaded for each script:

```css
/* Expected font stacks */
- Latin: 'Inter', sans-serif
- Cyrillic: 'Inter', sans-serif (has Cyrillic support)
- CJK: System fonts (e.g., 'Noto Sans CJK', 'PingFang SC')
- Arabic: System fonts (e.g., 'Noto Sans Arabic', 'Arial')
- Devanagari: System fonts (e.g., 'Noto Sans Devanagari')
- Tamil: System fonts (e.g., 'Noto Sans Tamil')
```

### 3. Text Layout Tests

#### Line Height & Spacing
- [ ] Latin scripts: Normal line height (1.5)
- [ ] CJK scripts: Adequate vertical spacing for tall characters
- [ ] Indic scripts: Extra height for diacritics above/below
- [ ] Arabic scripts: Adequate spacing for connecting characters

#### Word Wrapping
- [ ] English: Breaks at spaces and hyphens
- [ ] German: Handles compound words (Zusammengesetztewörter)
- [ ] CJK: Line breaks between characters (no spaces)
- [ ] Thai/Vietnamese: Proper word breaking
- [ ] Arabic/Hebrew: Correct RTL word wrapping

#### Text Alignment
- [ ] LTR languages: Default left alignment
- [ ] RTL languages: Default right alignment
- [ ] Mixed content: Embedded LTR in RTL (URLs, emails, numbers)

### 4. Number & Date Formatting Tests

Test number and date formatting for each language:

#### Numbers
```javascript
// Test values
1234.56  → "1,234.56" (en)
         → "1 234,56" (fr)
         → "1.234,56" (de)
         → "1,234.56" (zh)
         → "١٬٢٣٤٫٥٦" (ar)  // Note: Eastern Arabic numerals
```

#### Dates
```javascript
// Test date: 2024-03-15
"March 15, 2024"     (en)
"15 mars 2024"       (fr)
"15. März 2024"      (de)
"2024年3月15日"       (zh)
"15 مارس 2024"      (ar)
"۱۵ مارس ۲۰۲۴"      (fa)  // Persian numerals
```

#### Currency
```javascript
// Test amount: 1234.56
"$1,234.56"          (en-US)
"1 234,56 $"         (fr-CA)
"€1.234,56"          (de)
"¥1,235"             (zh)
"﷼‏1,234.56"         (ar)  // Rial symbol
```

### 5. Language Switching Tests

#### Immediate Switching
1. [ ] Switch from English to any language → UI updates immediately
2. [ ] No page refresh required
3. [ ] Current page state persists (form data, scroll position)

#### Persistence Tests
1. [ ] Select language → Refresh page → Language persists
2. [ ] Select language → Close browser → Reopen → Language persists
3. [ ] Select language → Navigate pages → Language persists
4. [ ] Clear cache → Language falls back to browser default or English

#### Mixed Sessions
1. [ ] Open in Tab 1 (English) → Tab 2 (Spanish) → Both work correctly
2. [ ] Language selection independent per session (if desired)

### 6. Component-Specific Tests

Test each major component in multiple languages:

#### Forms
- [ ] **Login Form**: Test in English, Spanish, Arabic, Mandarin
- [ ] **Signup Form**: Test in French, German, Japanese, Hebrew
- [ ] **Settings Forms**: Test in Russian, Korean, Hindi, Punjabi

#### Tables
- [ ] **Inventory Table**: Test column headers in 5 languages
- [ ] **Orders Table**: Test date/currency formatting
- [ ] **Customer Table**: Test sorting with different character sets

#### Modals & Dialogs
- [ ] **Confirmation Dialogs**: Test button order (RTL reversal)
- [ ] **Form Modals**: Test validation messages in multiple scripts
- [ ] **Password Modal**: Test complex script password entry

#### Navigation
- [ ] **Sidebar**: Test navigation items in long languages (German, Punjabi)
- [ ] **Breadcrumbs**: Test separator direction in RTL
- [ ] **Tabs**: Test tab overflow with long labels

### 7. Accessibility Tests

Test screen reader support for each script:

- [ ] **English**: NVDA/JAWS/VoiceOver
- [ ] **Arabic**: NVDA Arabic support
- [ ] **Mandarin**: NVDA Chinese support
- [ ] **Hindi**: NVDA Hindi support
- [ ] **Japanese**: PC-Talker/NVDA Japanese

### 8. Performance Tests

Measure performance impact of different scripts:

```javascript
// Bundle size test
- Latin languages: ~50KB (base)
- + CJK fonts: +500KB-1MB (system fonts recommended)
- + Arabic/Indic: +200-400KB (system fonts recommended)

// Rendering performance
- Measure FCP (First Contentful Paint) for each language
- Measure TTI (Time to Interactive) with different fonts
- Check for font loading FOUT/FOIT issues
```

### 9. Error Handling Tests

Test error messages in each language:

```javascript
// Common errors to test
- "Required field" → All languages
- "Invalid email" → All languages
- "Password too short" → All languages
- Network errors → All languages
- 404/500 error pages → All languages
```

### 10. Browser Compatibility Matrix

Test language rendering across browsers:

| Browser | Latin | Cyrillic | CJK | Arabic | Indic | Notes |
|---------|-------|----------|-----|--------|-------|-------|
| Chrome 120+ | ✓ | ✓ | ✓ | ✓ | ✓ | Excellent |
| Firefox 121+ | ✓ | ✓ | ✓ | ✓ | ✓ | Excellent |
| Safari 17+ | ✓ | ✓ | ✓ | ✓ | ~✓ | Some Indic rendering quirks |
| Edge 120+ | ✓ | ✓ | ✓ | ✓ | ✓ | Chromium-based, excellent |

## Manual Testing Procedures

### Procedure 1: Quick Language Smoke Test (5 min per language)

1. Select target language
2. Navigate to Dashboard
3. Check: Header, sidebar, main content render correctly
4. Open one form (e.g., Product creation)
5. Trigger one validation error
6. Check: Error message displays in target language
7. Refresh page
8. Check: Language persists

### Procedure 2: Comprehensive Language Test (15 min per language)

1. Select target language
2. Test all primary navigation items
3. Fill out a complete form (with validation errors)
4. Test table sorting and filtering
5. Open and interact with modals
6. Test search functionality
7. Verify date pickers, dropdowns, tooltips
8. Check responsive behavior (mobile/tablet/desktop)
9. Test language switching mid-session
10. Verify all error states

### Procedure 3: Script-Specific Tests

#### For CJK Languages (Mandarin, Cantonese, Japanese, Korean)
- [ ] Verify full-width vs half-width characters
- [ ] Test input method editors (IME) compatibility
- [ ] Check vertical text rendering (if applicable)
- [ ] Verify character counting for text limits

#### For RTL Languages (Arabic, Persian, Hebrew, Urdu)
- [ ] Follow RTL_TESTING_GUIDE.md procedures
- [ ] Test bidirectional text (LTR embedded in RTL)
- [ ] Verify number directionality
- [ ] Check mirror-image icons and layouts

#### For Indic Languages (Hindi, Punjabi, Tamil, Gujarati, Bengali)
- [ ] Test complex glyph rendering (conjuncts, ligatures)
- [ ] Verify diacritic placement
- [ ] Check character reordering
- [ ] Test input method support

## Automated Testing

### Unit Tests for i18n Functions

```typescript
// Example test suite
describe('i18n Translation Tests', () => {
  const languages = SUPPORTED_LANGUAGES.map(lang => lang.code);

  languages.forEach(lang => {
    describe(`Language: ${lang}`, () => {
      test('has all required translation keys', () => {
        // Load translation file
        const translations = require(`./locales/${lang}/common.json`);

        // Verify critical keys exist
        expect(translations.buttons.save).toBeDefined();
        expect(translations.errors.required).toBeDefined();
        expect(translations.labels.email).toBeDefined();
      });

      test('has no untranslated English fallbacks', () => {
        const translations = require(`./locales/${lang}/common.json`);
        const english = require(`./locales/en/common.json`);

        // Check if translations are different from English
        // (This helps catch copy-paste without actual translation)
        if (lang !== 'en') {
          const translationValues = JSON.stringify(translations);
          const englishValues = JSON.stringify(english);
          expect(translationValues).not.toBe(englishValues);
        }
      });
    });
  });
});
```

### Integration Tests

```typescript
// Test language switching in components
describe('Language Switching Integration', () => {
  test('updates UI when language changes', () => {
    render(<Dashboard />);

    // Switch to Spanish
    i18n.changeLanguage('es');

    // Verify text updates
    expect(screen.getByText('Panel de Control')).toBeInTheDocument();
  });

  test('persists language across navigation', () => {
    // Set language
    i18n.changeLanguage('fr');

    // Navigate
    navigate('/dashboard/inventory');

    // Verify language persisted
    expect(i18n.language).toBe('fr');
    expect(screen.getByText('Inventaire')).toBeInTheDocument();
  });
});
```

## Translation Quality Checks

### Completeness Check

```bash
# Run this script to check translation completeness
npm run i18n:check-completeness
```

This should check:
- All translation keys exist in all languages
- No empty string values
- No untranslated placeholders like "TODO" or "TRANSLATE ME"

### Consistency Check

- [ ] Terminology consistency within each language
- [ ] Button labels follow convention (Save vs Submit)
- [ ] Error messages use consistent tone
- [ ] Date/time formats match locale conventions

### Context Appropriateness

- [ ] Formal vs informal tone appropriate for language
- [ ] Gender-neutral language where applicable
- [ ] Cultural sensitivity (colors, symbols, idioms)
- [ ] No machine translation artifacts

## Common Issues & Solutions

### Issue 1: Missing Glyphs
**Symptom**: Square boxes (□) or question marks (?) appear
**Solution**: Ensure system fonts support the script, or add web font fallbacks

### Issue 2: Text Overflow
**Symptom**: Long German/Finnish words break layout
**Solution**: Use CSS `word-break: break-word` or `overflow-wrap: break-word`

### Issue 3: RTL Layout Breaks
**Symptom**: UI elements misaligned in Arabic/Hebrew
**Solution**: Use logical CSS properties (margin-inline-start instead of margin-left)

### Issue 4: Font Loading Delay (FOIT/FOUT)
**Symptom**: Text invisible or styled incorrectly during font load
**Solution**: Use `font-display: swap` in CSS

### Issue 5: Number Formatting Inconsistency
**Symptom**: Numbers display wrong format for locale
**Solution**: Use `Intl.NumberFormat` API consistently

## Testing Checklist Summary

- [ ] All 28 languages load without errors
- [ ] Characters render correctly for all scripts
- [ ] Fonts are appropriate for each script
- [ ] Text layout (alignment, wrapping) works correctly
- [ ] Numbers, dates, currency format per locale
- [ ] Language switching works immediately
- [ ] Language selection persists across sessions
- [ ] Forms validate with localized messages
- [ ] Modals and dialogs display correctly
- [ ] Tables sort and filter with different character sets
- [ ] RTL languages flip layout appropriately
- [ ] No console errors when switching languages
- [ ] Performance acceptable with all languages
- [ ] Accessibility (screen readers) works for supported languages

## Next Steps

After completing these tests:

1. ✅ Document any issues found
2. ✅ Create tickets for bugs/improvements
3. ✅ Add visual regression tests for each language
4. ✅ Set up automated translation coverage monitoring
5. ✅ Create developer documentation for i18n best practices

## Resources

- [i18next Documentation](https://www.i18next.com/)
- [react-i18next Documentation](https://react.i18next.com/)
- [Unicode CLDR](https://cldr.unicode.org/) - Locale data
- [Google Noto Fonts](https://fonts.google.com/noto) - Comprehensive font coverage
- [MDN: Internationalization API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
