# RTL (Right-to-Left) Language Testing Guide

This guide provides comprehensive instructions for testing RTL language rendering in the WeedGo Admin Dashboard.

## Overview

The dashboard supports **4 RTL languages**:
- **Arabic (ar)** - العربية
- **Persian (fa)** - فارسی
- **Hebrew (he)** - עברית
- **Urdu (ur)** - اردو

## Automatic RTL Detection

The application automatically detects RTL languages and applies appropriate styling:

1. **HTML `dir` attribute** - Sets `<html dir="rtl">` for RTL languages
2. **Body class** - Adds `.rtl` class to `<body>` for CSS targeting
3. **Text direction persistence** - Stores direction in localStorage
4. **Language-specific handling** - Automatically switches on language change

## Testing Checklist

### 1. Basic RTL Layout (✓ Priority: High)

Test these fundamental RTL behaviors:

- [ ] **Text Alignment**: Text should align to the right
- [ ] **Layout Flip**: Sidebars, navigation should flip to right side
- [ ] **Icon Position**: Icons should appear on the right side of text
- [ ] **Scroll Direction**: Horizontal scrolling should start from right
- [ ] **Form Fields**: Labels should appear on the right of inputs
- [ ] **Dropdown Menus**: Should open from right to left
- [ ] **Tooltips**: Should position correctly for RTL context

### 2. Component-Specific Testing

#### Navigation & Sidebar
```
Component: src/App.tsx (Lines 170-262)
```
- [ ] Sidebar should flip to right side
- [ ] Navigation icons should appear on right
- [ ] Collapse/expand buttons should flip direction
- [ ] User profile section should flip

#### Forms
```
Components: All forms in src/components/ and src/pages/
```
- [ ] Input labels align right
- [ ] Required asterisks (*) appear on left
- [ ] Error messages align right
- [ ] Validation icons appear on left
- [ ] Submit buttons align correctly

#### Modals & Dialogs
```
Components: src/components/*Modal.tsx
```
- [ ] Modal close button (X) appears on left
- [ ] Modal content aligns right
- [ ] Action buttons (Cancel/OK) order reverses
- [ ] Form fields within modals align right

#### Tables
```
Components: Inventory.tsx, Orders.tsx, etc.
```
- [ ] Table headers align right
- [ ] Column order remains logical
- [ ] Action columns appear on left
- [ ] Pagination controls flip direction
- [ ] Sorting arrows position correctly

#### Cards & Lists
- [ ] Card content aligns right
- [ ] List bullets/numbers appear on right
- [ ] Status badges position correctly
- [ ] Timestamps align right

### 3. Typography & Text

- [ ] **Font Rendering**: Arabic/Persian/Hebrew glyphs render correctly
- [ ] **Line Height**: Adequate spacing for RTL scripts
- [ ] **Word Wrapping**: Text wraps naturally in RTL
- [ ] **Numbers**: Numbers remain LTR (e.g., "123" not "321")
- [ ] **Mixed Content**: LTR text (like URLs, emails) embedded correctly

### 4. Interactive Elements

#### Buttons
- [ ] Icon-text buttons: Icon appears on correct side
- [ ] Button groups: Order makes sense in RTL
- [ ] Dropdown buttons: Chevron/arrow flips

#### Input Fields
- [ ] Search boxes: Search icon position
- [ ] Password reveal: Eye icon position
- [ ] Clear buttons (X): Position on left
- [ ] Date pickers: Calendar opens correctly
- [ ] Select dropdowns: Arrow position

#### Navigation Elements
- [ ] Breadcrumbs: Separators (>) flip to (<)
- [ ] Pagination: Previous/Next labels flip
- [ ] Carousels: Arrow direction flips
- [ ] Tabs: Tab order remains intuitive

### 5. Data Display

- [ ] **Currency**: $ symbol position (before or after)
- [ ] **Dates**: Format appropriate for RTL language
- [ ] **Times**: Display correctly (e.g., "10:30 PM")
- [ ] **Percentages**: Position and spacing
- [ ] **Phone Numbers**: Display LTR even in RTL context

### 6. Responsive Design

Test RTL layout at different screen sizes:

- [ ] **Desktop** (1920×1080): Full layout with sidebar
- [ ] **Laptop** (1366×768): Medium layout
- [ ] **Tablet** (768×1024): Tablet-optimized layout
- [ ] **Mobile** (375×667): Mobile menu behavior

### 7. Known RTL Issues to Check

Common RTL layout issues to watch for:

1. **Margin/Padding**: Check for `ml-*`, `mr-*` classes that need direction-aware alternatives
2. **Positioning**: Absolute/fixed positioned elements
3. **Borders**: Border-left/border-right specificity
4. **Transforms**: `translateX` values may need reversal
5. **Animations**: Slide-in animations should slide from appropriate side
6. **Shadows**: Drop shadows should flip direction

## Manual Testing Steps

### Step 1: Switch to RTL Language

1. Open the dashboard
2. Click the language selector in the header
3. Select an RTL language (Arabic, Persian, Hebrew, or Urdu)
4. Observe immediate direction change

### Step 2: Navigate Through Pages

Visit each major page and verify RTL layout:

1. **Dashboard** - `/dashboard`
2. **Inventory** - `/dashboard/inventory`
3. **Orders** - `/dashboard/orders`
4. **POS** - `/dashboard/pos`
5. **Settings** - Various settings pages
6. **Forms** - Tenant signup, user registration

### Step 3: Test Interactions

Perform common actions in RTL mode:

1. Fill out forms (signup, login, product creation)
2. Open and close modals
3. Navigate menus and dropdowns
4. Sort and filter tables
5. Switch between tabs
6. Use search functionality

### Step 4: Test Edge Cases

1. **Switch language during interaction**
   - Open a modal in LTR, switch to RTL → Modal should re-layout

2. **Refresh page in RTL**
   - Direction should persist after refresh

3. **Mixed LTR/RTL content**
   - Type English text in Arabic UI → Should embed correctly

### Step 5: Verify Persistence

1. Select RTL language
2. Refresh browser → Direction should persist
3. Clear localStorage → Should detect from browser language
4. Switch to LTR, then back to RTL → Should apply correctly

## Browser Testing Matrix

Test RTL rendering in multiple browsers:

| Browser | Version | RTL Support | Notes |
|---------|---------|-------------|-------|
| Chrome  | Latest  | ✓ Excellent | Best RTL support |
| Firefox | Latest  | ✓ Excellent | Native RTL handling |
| Safari  | Latest  | ✓ Good      | Some rendering quirks |
| Edge    | Latest  | ✓ Excellent | Chromium-based |

## Testing Tools

### Browser DevTools

1. **Inspect HTML**:
   ```bash
   # Check if dir attribute is set
   <html dir="rtl" lang="ar">
   ```

2. **Check Body Class**:
   ```bash
   # Body should have .rtl class
   <body class="rtl">
   ```

3. **Verify localStorage**:
   ```javascript
   localStorage.getItem('textDirection') // Should return 'rtl'
   localStorage.getItem('i18nextLng') // Should return 'ar', 'fa', 'he', or 'ur'
   ```

### CSS Inspection

Look for these RTL-aware patterns in computed styles:

```css
/* Direction-based properties */
direction: rtl;
text-align: right;

/* Tailwind RTL modifiers (if used) */
.rtl\:text-right { text-align: right; }
.rtl\:mr-4 { margin-right: 1rem; }
```

## Automated Testing

### Unit Tests (Future Enhancement)

```typescript
// Example test for RTL utility
import { isRTL, getTextDirection } from './utils/rtl';

describe('RTL Utils', () => {
  test('detects RTL languages correctly', () => {
    expect(isRTL('ar')).toBe(true);
    expect(isRTL('en')).toBe(false);
  });

  test('returns correct text direction', () => {
    expect(getTextDirection('ar')).toBe('rtl');
    expect(getTextDirection('en')).toBe('ltr');
  });
});
```

### Visual Regression Testing (Future Enhancement)

Consider using tools like:
- **Percy** - Visual comparison testing
- **Chromatic** - Storybook visual testing
- **BackstopJS** - Screenshot comparison

## Common RTL Fixes

If you find RTL layout issues, here are common fixes:

### 1. Margin/Padding Fixes

```css
/* Before (LTR-specific) */
.element { margin-left: 1rem; }

/* After (Direction-aware) */
.element { margin-inline-start: 1rem; }
```

### 2. Text Alignment

```css
/* Before */
.text { text-align: left; }

/* After */
.text { text-align: start; }
```

### 3. Flexbox Direction

```css
/* Before */
.flex-container { flex-direction: row; }

/* After - Let RTL handle it */
.flex-container { flex-direction: row; } /* Still row, browser flips for RTL */
```

### 4. Tailwind RTL Modifiers

```html
<!-- Use direction-specific classes -->
<div class="ltr:mr-4 rtl:ml-4">Content</div>
<div class="ltr:text-left rtl:text-right">Text</div>
```

## Reporting RTL Issues

When reporting RTL layout issues, include:

1. **Language**: Which RTL language (ar, fa, he, ur)
2. **Browser**: Browser name and version
3. **Component**: Specific component/page with issue
4. **Screenshot**: Visual proof of the issue
5. **Expected vs Actual**: What should happen vs what happens
6. **Console Errors**: Any JavaScript errors

## Resources

- [MDN: CSS Logical Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Logical_Properties)
- [W3C: Structural Markup and Right-to-Left Text](https://www.w3.org/International/questions/qa-html-dir)
- [Tailwind CSS RTL Support](https://tailwindcss.com/docs/hover-focus-and-other-states#rtl-support)
- [Material-UI RTL Guide](https://mui.com/material-ui/guides/right-to-left/)

## Quick Reference

```javascript
// RTL Language Codes
const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur'];

// Check if current language is RTL
import { isRTL } from './utils/rtl';
const isRTLMode = isRTL(currentLanguage);

// Apply RTL programmatically
import { applyTextDirection } from './utils/rtl';
applyTextDirection('ar'); // Switches to RTL
```

## Status

- ✅ RTL detection implemented
- ✅ HTML dir attribute handling
- ✅ localStorage persistence
- ✅ Language change listener
- ⏳ Component-by-component testing needed
- ⏳ Visual regression tests needed
