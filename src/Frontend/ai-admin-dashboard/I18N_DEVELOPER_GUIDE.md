# Internationalization (i18n) Developer Guide

Complete developer guide for implementing and maintaining internationalization in the WeedGo Admin Dashboard.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Adding New Languages](#adding-new-languages)
5. [Adding New Translation Keys](#adding-new-translation-keys)
6. [Using Translations in Components](#using-translations-in-components)
7. [Best Practices](#best-practices)
8. [Testing](#testing)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

## Overview

The WeedGo Admin Dashboard uses **react-i18next** for internationalization, supporting **28 languages** across multiple scripts and writing directions.

### Supported Languages

28 languages including:
- **LTR Languages**: English, Spanish, French, German, etc. (24 languages)
- **RTL Languages**: Arabic, Persian, Hebrew, Urdu (4 languages)

### Key Features

✅ Automatic language detection from browser
✅ Persistent language selection (localStorage)
✅ RTL language support with automatic layout flipping
✅ Namespaced translations for better organization
✅ Dynamic language switching without page reload
✅ Translation validation script for CI/CD

## Architecture

### Directory Structure

```
src/
├── i18n/
│   ├── config.ts              # i18next configuration
│   └── locales/
│       ├── en/                # English translations (baseline)
│       │   ├── common.json
│       │   ├── auth.json
│       │   ├── dashboard.json
│       │   └── ...
│       ├── es/                # Spanish translations
│       ├── fr/                # French translations
│       └── ...                # 25 more languages
├── utils/
│   ├── rtl.ts                 # RTL utilities
│   └── errorTranslation.ts   # Error message translation
├── components/
│   └── LanguageSelector.tsx  # Language switcher UI
└── scripts/
    └── validate-translations.js  # Validation script
```

### Translation Namespaces

Translations are organized into **21 namespaces**:

| Namespace | Purpose | Example Keys |
|-----------|---------|--------------|
| `common` | Shared UI elements | buttons, labels, messages, errors |
| `auth` | Authentication | login, signup, password reset |
| `dashboard` | Dashboard page | statistics, charts, widgets |
| `forms` | Form-related | field labels, placeholders |
| `errors` | Error messages | validation, network errors |
| `modals` | Modal dialogs | titles, confirmations |
| `tenants` | Tenant management | tenant CRUD, settings |
| `stores` | Store management | store CRUD, settings |
| `inventory` | Inventory | products, stock, adjustments |
| `orders` | Orders | order management, fulfillment |
| `pos` | Point of Sale | POS interface, checkout |
| `payments` | Payments | payment methods, transactions |
| `settings` | Settings | configuration, preferences |
| `communications` | Communications | email, SMS, notifications |
| `database` | Database management | schemas, migrations |
| `promotions` | Promotions | discounts, campaigns |
| `catalog` | Product catalog | categories, attributes |
| `apps` | Applications | app marketplace, integrations |
| `tools` | Tools | utilities, helpers |
| `signup` | Signup flow | tenant registration, onboarding |
| `landing` | Landing page | marketing content |

## Getting Started

### 1. Import i18n Configuration

The i18n configuration is automatically loaded in `App.tsx`:

```typescript
// src/App.tsx
import './i18n/config'; // Initialize i18n
```

This sets up:
- Language detection
- Translation loading
- RTL support
- Persistence

### 2. Use Translation Hook in Components

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation(['common', 'dashboard']);

  return (
    <div>
      <h1>{t('dashboard:title')}</h1>
      <button>{t('common:buttons.save')}</button>
    </div>
  );
}
```

### 3. Verify Translations Load

Check browser console on dev startup:

```
[i18next] Loaded namespace "common" for language "en"
[i18next] Loaded namespace "dashboard" for language "en"
```

## Adding New Languages

### Step 1: Add Language Configuration

Edit `src/i18n/config.ts`:

```typescript
export const SUPPORTED_LANGUAGES = [
  // ... existing languages
  { code: 'sw', name: 'Swahili', flag: '🇹🇿', nativeName: 'Kiswahili' },
];
```

### Step 2: Create Translation Directory

```bash
mkdir src/i18n/locales/sw
```

### Step 3: Copy English Templates

```bash
# Copy all English translations as templates
cp src/i18n/locales/en/*.json src/i18n/locales/sw/
```

### Step 4: Translate Files

Translate each JSON file:

```json
// src/i18n/locales/sw/common.json
{
  "buttons": {
    "save": "Hifadhi",        // Translated
    "cancel": "Ghairi",       // Translated
    "delete": "Futa"          // Translated
  }
}
```

### Step 5: Add RTL Support (if applicable)

If the language is RTL, add to `src/utils/rtl.ts`:

```typescript
export const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur', 'new-rtl-lang'] as const;
```

### Step 6: Validate Translations

```bash
npm run i18n:validate
```

## Adding New Translation Keys

### Step 1: Add to English (Baseline)

```json
// src/i18n/locales/en/common.json
{
  "buttons": {
    "save": "Save",
    "export": "Export",  // ← New key
    "import": "Import"   // ← New key
  }
}
```

### Step 2: Add to All Other Languages

Use the validation script to find missing keys:

```bash
npm run i18n:validate
```

Output will show:

```
MISSING TRANSLATION KEYS:
  Language: es (2 missing keys)
    common: 2 keys missing
      - buttons.export
      - buttons.import
```

### Step 3: Translate New Keys

Add translations to each language:

```json
// src/i18n/locales/es/common.json
{
  "buttons": {
    "save": "Guardar",
    "export": "Exportar",  // ← Added
    "import": "Importar"   // ← Added
  }
}
```

## Using Translations in Components

### Basic Usage

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();

  return <button>{t('common:buttons.save')}</button>;
}
```

### With Interpolation

```typescript
const { t } = useTranslation();

// Translation: "Hello, {{name}}!"
t('greeting', { name: 'John' }); // → "Hello, John!"

// Translation: "You have {{count}} messages"
t('messages.count', { count: 5 }); // → "You have 5 messages"
```

### With Pluralization

```json
// Translation file
{
  "items": "{{count}} item",
  "items_plural": "{{count}} items"
}
```

```typescript
t('items', { count: 1 }); // → "1 item"
t('items', { count: 5 }); // → "5 items"
```

### Multiple Namespaces

```typescript
const { t } = useTranslation(['common', 'dashboard', 'forms']);

<div>
  <h1>{t('dashboard:title')}</h1>
  <p>{t('common:messages.loading')}</p>
  <input placeholder={t('forms:placeholders.email')} />
</div>
```

### Default Namespace

```typescript
// Set default namespace
const { t } = useTranslation('dashboard');

// No need to prefix with namespace
t('title')           // Uses dashboard:title
t('common:buttons.save')  // Can still access other namespaces
```

### Conditional Translation

```typescript
const status = 'active';
t(`status.${status}`);  // → Translates "status.active"
```

### Array Translations

```json
{
  "steps": [
    "Create account",
    "Verify email",
    "Complete profile"
  ]
}
```

```typescript
const steps = t('steps', { returnObjects: true });
steps.map((step, index) => <li key={index}>{step}</li>);
```

## Best Practices

### 1. Use Descriptive Keys

❌ **Bad**: Generic keys

```json
{
  "label1": "Name",
  "label2": "Email"
}
```

✅ **Good**: Descriptive hierarchical keys

```json
{
  "user": {
    "name": "Name",
    "email": "Email"
  }
}
```

### 2. Group Related Translations

```json
{
  "product": {
    "name": "Product Name",
    "price": "Price",
    "stock": "Stock Level",
    "actions": {
      "edit": "Edit Product",
      "delete": "Delete Product"
    }
  }
}
```

### 3. Avoid Hardcoded Strings

❌ **Bad**:
```typescript
<button>Save Changes</button>
```

✅ **Good**:
```typescript
<button>{t('common:buttons.save')}</button>
```

### 4. Use Namespaces Appropriately

```typescript
// ✅ Component-specific translations
const { t } = useTranslation(['inventory', 'common']);

// ❌ Loading all namespaces unnecessarily
const { t } = useTranslation([
  'common', 'auth', 'dashboard', 'forms', 'errors'
]);
```

### 5. Handle Plurals Correctly

```json
{
  "cart": {
    "items": "{{count}} item",
    "items_plural": "{{count}} items",
    "items_zero": "No items"
  }
}
```

```typescript
t('cart.items', { count: 0 });  // → "No items"
t('cart.items', { count: 1 });  // → "1 item"
t('cart.items', { count: 5 });  // → "5 items"
```

### 6. Date & Number Formatting

Use `Intl` API for locale-aware formatting:

```typescript
// Numbers
new Intl.NumberFormat(i18n.language).format(1234.56);

// Currency
new Intl.NumberFormat(i18n.language, {
  style: 'currency',
  currency: 'USD'
}).format(1234.56);

// Dates
new Intl.DateTimeFormat(i18n.language).format(new Date());
```

### 7. Keep Translations Short

Avoid long paragraphs in translation keys. Break into smaller chunks:

```json
{
  "welcome": {
    "title": "Welcome to WeedGo",
    "description": "Manage your cannabis retail business with ease.",
    "getStarted": "Click the button below to get started."
  }
}
```

### 8. Use Context Parameters

```json
{
  "welcome": "Welcome, {{name}}!",
  "itemsInCart": "You have {{count}} items ({{currency}}{{total}})"
}
```

```typescript
t('welcome', { name: user.firstName });
t('itemsInCart', {
  count: 3,
  currency: '$',
  total: 45.99
});
```

### 9. Avoid Translation in Computation

❌ **Bad**:
```typescript
const message = "User " + t('user.name') + " has been deleted";
```

✅ **Good**:
```json
{
  "user": {
    "deleted": "User {{name}} has been deleted"
  }
}
```

```typescript
const message = t('user.deleted', { name: user.name });
```

### 10. RTL-Aware Styling

Use logical CSS properties for RTL compatibility:

```css
/* ❌ Bad: Direction-specific */
.element {
  margin-left: 1rem;
  text-align: left;
}

/* ✅ Good: Logical properties */
.element {
  margin-inline-start: 1rem;
  text-align: start;
}
```

Or use Tailwind RTL modifiers:

```jsx
<div className="ltr:ml-4 rtl:mr-4 ltr:text-left rtl:text-right">
  Content
</div>
```

## Testing

### 1. Run Validation Script

```bash
# Check all translations
npm run i18n:validate

# In CI/CD
npm run i18n:validate:ci
```

### 2. Manual Testing

1. Switch to target language
2. Navigate through all pages
3. Test forms and validation
4. Check modals and dialogs
5. Verify error messages

### 3. RTL Testing

For RTL languages (Arabic, Persian, Hebrew, Urdu):

1. Switch to RTL language
2. Verify layout flips correctly
3. Check text alignment
4. Test form inputs
5. Verify navigation

See [`RTL_TESTING_GUIDE.md`](./RTL_TESTING_GUIDE.md) for comprehensive RTL testing procedures.

### 4. Unit Testing Translations

```typescript
// Example test
import { renderWithTranslation } from './test-utils';
import MyComponent from './MyComponent';

test('renders translated text', () => {
  const { getByText } = renderWithTranslation(<MyComponent />, {
    lng: 'es'
  });

  expect(getByText('Guardar')).toBeInTheDocument();
});
```

## Common Patterns

### Pattern 1: Form Validation Messages

```typescript
const validateForm = () => {
  const errors = {};

  if (!email) {
    errors.email = t('common:errors.validation.required');
  } else if (!isValidEmail(email)) {
    errors.email = t('common:errors.invalidEmail');
  }

  return errors;
};
```

### Pattern 2: Toast Notifications

```typescript
import toast from 'react-hot-toast';

// Success
toast.success(t('common:toasts.save.success'));

// Error
toast.error(t('common:toasts.save.failed'));
```

### Pattern 3: Confirmation Dialogs

```typescript
if (window.confirm(t('common:confirmations.delete', { name }))) {
  await deleteItem(id);
}
```

### Pattern 4: Dynamic Status Labels

```json
{
  "status": {
    "active": "Active",
    "inactive": "Inactive",
    "pending": "Pending"
  }
}
```

```typescript
<span>{t(`common:status.${item.status}`)}</span>
```

### Pattern 5: Error Boundary Messages

```typescript
import { useTranslation } from 'react-i18next';

function ErrorFallback({ error }) {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('common:errors.title')}</h1>
      <p>{t('common:errors.description')}</p>
    </div>
  );
}
```

### Pattern 6: Loading States

```typescript
{isLoading ? (
  <p>{t('common:messages.loading')}</p>
) : (
  <ProductList products={products} />
)}
```

### Pattern 7: Empty States

```typescript
{items.length === 0 ? (
  <div>
    <p>{t('inventory:empty.title')}</p>
    <button>{t('inventory:empty.addFirst')}</button>
  </div>
) : (
  <ItemList items={items} />
)}
```

## Troubleshooting

### Issue: Translations Not Loading

**Symptoms**: Keys appear instead of translated text (e.g., "common:buttons.save")

**Solutions**:
1. Check i18n is initialized: `import './i18n/config'` in `App.tsx`
2. Verify translation file exists: `src/i18n/locales/{lang}/{namespace}.json`
3. Check console for loading errors
4. Ensure namespace is added to config: `namespaces` array in `config.ts`

### Issue: RTL Layout Not Working

**Symptoms**: RTL language selected but layout doesn't flip

**Solutions**:
1. Check RTL utility is imported in `config.ts`
2. Verify language code is in `RTL_LANGUAGES` array
3. Inspect HTML: `<html dir="rtl">` should be set
4. Check CSS uses logical properties (not `margin-left`, etc.)

### Issue: Language Not Persisting

**Symptoms**: Language resets on page refresh

**Solutions**:
1. Check localStorage: `localStorage.getItem('i18nextLng')`
2. Verify language detector is configured in `config.ts`
3. Ensure `caches: ['localStorage']` in detection config

### Issue: Missing Translations Showing in Production

**Symptoms**: Some keys untranslated despite existing in files

**Solutions**:
1. Run validation: `npm run i18n:validate`
2. Check translation file is properly formatted JSON
3. Rebuild app: `npm run build`
4. Clear browser cache

### Issue: Interpolation Not Working

**Symptoms**: "Hello, {{name}}!" appears literally

**Solutions**:
1. Check parameter is passed: `t('greeting', { name: 'John' })`
2. Ensure curly braces are in translation: `"Hello, {{name}}!"`
3. Verify no typos in parameter name

### Issue: Pluralization Not Working

**Symptoms**: Always shows singular or plural form

**Solutions**:
1. Check translation keys: `key`, `key_plural`, `key_zero`
2. Pass count parameter: `t('items', { count: 5 })`
3. Verify i18next pluralization is enabled (it is by default)

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/i18n-validation.yml
name: Validate Translations

on: [push, pull_request]

jobs:
  validate-i18n:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run i18n:validate:ci
```

### Pre-commit Hook

```bash
# .husky/pre-commit
#!/bin/sh
npm run i18n:validate
```

## Resources

### Documentation
- [react-i18next Documentation](https://react.i18next.com/)
- [i18next Documentation](https://www.i18next.com/)
- [MDN: Intl API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)

### Tools
- [i18n Ally](https://github.com/lokalise/i18n-ally) - VS Code extension
- [BabelEdit](https://www.codeandweb.com/babeledit) - Translation editor
- [Lokalise](https://lokalise.com/) - Translation management platform

### Internal Guides
- [`RTL_TESTING_GUIDE.md`](./RTL_TESTING_GUIDE.md) - RTL language testing
- [`I18N_TESTING_GUIDE.md`](./I18N_TESTING_GUIDE.md) - Comprehensive testing
- [`scripts/validate-translations.js`](./scripts/validate-translations.js) - Validation script

## Quick Reference

```typescript
// Import
import { useTranslation } from 'react-i18next';

// Hook
const { t, i18n } = useTranslation(['common', 'dashboard']);

// Translate
t('common:buttons.save')                          // Simple
t('greeting', { name: 'John' })                   // Interpolation
t('items', { count: 5 })                          // Pluralization
t(`status.${value}`)                              // Dynamic
t('steps', { returnObjects: true })               // Array

// Change language
i18n.changeLanguage('es');

// Current language
i18n.language;                                    // 'en', 'es', etc.

// Check RTL
import { isRTL } from './utils/rtl';
isRTL(i18n.language);                             // true/false
```

## Contributing

When adding new features:

1. ✅ Add translation keys to English first
2. ✅ Use `useTranslation` hook in components
3. ✅ Follow naming conventions (descriptive, hierarchical)
4. ✅ Run `npm run i18n:validate` before committing
5. ✅ Test in at least 2 languages (including 1 RTL if applicable)
6. ✅ Update this guide if adding new patterns

---

**Questions?** Contact the development team or create an issue in the repository.
