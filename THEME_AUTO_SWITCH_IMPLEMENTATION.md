# Theme Auto-Switch Implementation

## Overview
Implemented automatic theme switching based on OS/browser preferences while preserving user manual override capability.

## Implementation Date
December 2024

## Changes Made

### 1. Enhanced Theme Hook (`src/Frontend/ai-admin-dashboard/src/hooks/useTheme.ts`)

**Priority Order:**
1. **User's manual preference** (stored in localStorage)
2. **System preference** (`prefers-color-scheme` media query)
3. **Default theme** (light)

**Key Features:**
- ✅ Detects system theme on initial load
- ✅ Listens for system theme changes in real-time
- ✅ Only auto-switches if user hasn't set manual preference
- ✅ Manual toggle always takes priority
- ✅ New `useSystemTheme()` function to clear override

**Implementation:**
```typescript
export function useTheme() {
  // Priority 1: User's manual preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || savedTheme === 'light') {
    return savedTheme === 'dark';
  }
  
  // Priority 2: System preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}
```

**System Change Listener:**
```typescript
useEffect(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  
  const handleSystemThemeChange = (e: MediaQueryListEvent) => {
    // Only auto-switch if no manual preference
    if (!localStorage.getItem('theme')) {
      setIsDark(e.matches);
    }
  };
  
  mediaQuery.addEventListener('change', handleSystemThemeChange);
  return () => mediaQuery.removeEventListener('change', handleSystemThemeChange);
}, []);
```

### 2. Prevent FOUC (`src/Frontend/ai-admin-dashboard/index.html`)

Added inline script in `<head>` to apply theme **before React loads**:

```html
<script>
  (function() {
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme ? savedTheme === 'dark' : systemPrefersDark;
    
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
  })();
</script>
```

**Why This Matters:**
- Prevents white flash when loading in dark mode
- Applies theme before any CSS is rendered
- Uses same priority logic as React hook

## User Behavior Scenarios

### Scenario 1: Fresh User (No Manual Preference)
**OS Setting:** Dark Mode  
**Result:** App opens in dark mode  
**OS Changes to Light:** App auto-switches to light mode ✅

### Scenario 2: User With Manual Preference
**User Clicks Toggle:** Sets light mode manually  
**Stored:** `localStorage.theme = 'light'`  
**OS Changes to Dark:** App **stays in light mode** (manual override) ✅

### Scenario 3: Clearing Manual Override
**User Calls:** `useSystemTheme()`  
**Effect:** Removes localStorage preference  
**Result:** App reverts to system theme ✅

### Scenario 4: Cross-Device Sync (Future Enhancement)
**Current:** Manual preference stored in browser localStorage only  
**Future:** Could sync theme preference via backend user settings

## API Reference

### `useTheme()` Hook

**Returns:**
```typescript
{
  isDark: boolean,           // Current theme state
  toggleTheme: () => void,   // Manual toggle (stores preference)
  useSystemTheme: () => void // Clear override, use system
}
```

**Usage:**
```tsx
import { useTheme } from './hooks/useTheme';

function MyComponent() {
  const { isDark, toggleTheme, useSystemTheme } = useTheme();
  
  return (
    <>
      <button onClick={toggleTheme}>
        {isDark ? 'Light Mode' : 'Dark Mode'}
      </button>
      <button onClick={useSystemTheme}>
        Use System Theme
      </button>
    </>
  );
}
```

## Industry Best Practices Followed

### ✅ 1. Priority Order
```
Manual Preference > System Preference > Default
```

### ✅ 2. localStorage Usage
- **Key:** `theme`
- **Values:** `'light'` | `'dark'` | `null` (system)
- **Persistence:** Across sessions, single device

### ✅ 3. Media Query
```javascript
window.matchMedia('(prefers-color-scheme: dark)')
```

### ✅ 4. Event Listener
- Listens for system changes
- Respects manual override
- Cleans up on unmount

### ✅ 5. FOUC Prevention
- Inline script in `<head>`
- Executes before CSS/React
- No visible flash

### ✅ 6. Accessibility
- Maintains user choice
- Respects system preferences
- Clear toggle UI

## Testing Checklist

### Manual Testing

**macOS:**
- [ ] System Preferences → General → Appearance → Dark
- [ ] Change while app is open
- [ ] Verify app auto-switches (if no manual preference)
- [ ] Toggle manually, change system, verify no auto-switch

**Windows:**
- [ ] Settings → Personalization → Colors → Dark
- [ ] Same test as macOS

**Linux:**
- [ ] System settings (varies by distro)
- [ ] Same test as above

**iOS/Android Browser:**
- [ ] System dark mode toggle
- [ ] Verify mobile Safari/Chrome respects preference

### Automated Testing (Future)

```typescript
describe('useTheme', () => {
  it('should use system preference on first load', () => {
    window.matchMedia = jest.fn().mockImplementation(query => ({
      matches: true, // System is dark
      media: query,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }));
    
    const { result } = renderHook(() => useTheme());
    expect(result.current.isDark).toBe(true);
  });
  
  it('should respect manual override', () => {
    localStorage.setItem('theme', 'light');
    // Even if system is dark
    window.matchMedia = jest.fn().mockImplementation(query => ({
      matches: true,
      media: query,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }));
    
    const { result } = renderHook(() => useTheme());
    expect(result.current.isDark).toBe(false); // Manual light wins
  });
});
```

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 76+ | ✅ Full |
| Firefox | 67+ | ✅ Full |
| Safari | 12.1+ | ✅ Full |
| Edge | 79+ | ✅ Full |
| Opera | 62+ | ✅ Full |
| iOS Safari | 13+ | ✅ Full |
| Android Chrome | 76+ | ✅ Full |

**Legacy Fallback:**
If `prefers-color-scheme` not supported:
- Falls back to light mode
- Manual toggle still works

## Performance

**Overhead:** Negligible
- Single media query listener
- localStorage read (synchronous, <1ms)
- No network requests
- No polling

**Memory:** ~1KB
- Media query listener
- useState hook
- 2 useEffect hooks

## Future Enhancements

### 1. Three-State Toggle (Optional)
```typescript
type ThemeMode = 'light' | 'dark' | 'auto';

// UI could show:
// ☀️ Light | 🌙 Dark | 🔄 Auto (System)
```

### 2. Backend Sync
```typescript
// Save preference to user settings
await updateUserSettings({ theme: 'dark' });

// Load on login
const { theme } = await getUserSettings();
```

### 3. Scheduled Theme Switching
```typescript
// Auto dark mode 8pm-6am
const hour = new Date().getHours();
const shouldBeDark = hour >= 20 || hour < 6;
```

### 4. Per-Device Preferences
```typescript
// Use device fingerprint or user agent
const deviceId = getDeviceId();
localStorage.setItem(`theme_${deviceId}`, 'dark');
```

### 5. Contrast Modes
```typescript
// Respect prefers-contrast media query
const highContrast = window.matchMedia('(prefers-contrast: high)').matches;
```

## Troubleshooting

### Issue: Theme not auto-switching
**Check:**
1. Is `darkMode: 'class'` in `tailwind.config.js`? ✅ (Already present)
2. Is localStorage `theme` key set? (Clear it to test auto)
3. Does browser support `prefers-color-scheme`?

**Fix:**
```javascript
localStorage.removeItem('theme'); // Clear manual override
location.reload(); // Should now follow system
```

### Issue: Flash of white on dark mode load
**Check:**
1. Is inline script in `index.html` `<head>`? ✅ (Added)
2. Is script **before** any CSS?

**Fix:**
Ensure script is first thing in `<head>` after `<meta>` tags.

### Issue: System change not detected
**Check:**
1. Does browser fire `change` event on media query?
2. Is event listener attached?

**Debug:**
```javascript
const mq = window.matchMedia('(prefers-color-scheme: dark)');
mq.addEventListener('change', (e) => {
  console.log('System theme changed:', e.matches ? 'dark' : 'light');
});
```

## Related Files

**Modified:**
- `src/Frontend/ai-admin-dashboard/src/hooks/useTheme.ts` ✅
- `src/Frontend/ai-admin-dashboard/index.html` ✅

**Uses Hook:**
- `src/Frontend/ai-admin-dashboard/src/App.tsx` (Line 16, Line 91, Line 358)

**Configuration:**
- `src/Frontend/ai-admin-dashboard/tailwind.config.js` (Already has `darkMode: 'class'`)

## References

**MDN Documentation:**
- [prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
- [Window.matchMedia()](https://developer.mozilla.org/en-US/docs/Web/API/Window/matchMedia)
- [MediaQueryList: change event](https://developer.mozilla.org/en-US/docs/Web/API/MediaQueryList/change_event)

**Industry Examples:**
- GitHub: Auto-switches with manual override
- Twitter/X: Three-state toggle (light/dark/auto)
- Discord: Manual toggle only
- macOS Mail: Follows system preference

**Best Practices:**
- [Web.dev: prefers-color-scheme](https://web.dev/prefers-color-scheme/)
- [CSS-Tricks: Dark Mode](https://css-tricks.com/a-complete-guide-to-dark-mode-on-the-web/)
- [Tailwind CSS: Dark Mode](https://tailwindcss.com/docs/dark-mode)

## Summary

✅ **Implemented:**
- System preference detection on load
- Real-time system change listener
- Manual override capability
- FOUC prevention
- localStorage persistence
- Clean API with `useSystemTheme()`

✅ **Benefits:**
- Better UX (respects user's OS preference)
- No jarring theme changes on load
- Manual control preserved
- Industry-standard behavior
- Zero breaking changes

✅ **Result:**
Users now get automatic theme switching that respects their OS/browser settings while maintaining full manual control. The implementation follows industry best practices and provides a smooth, flash-free experience.
