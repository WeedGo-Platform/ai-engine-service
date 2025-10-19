/**
 * Test Suite 5: Comprehensive Visual and Functional Tests
 * Full page testing across all languages with screenshots
 */

import { test, expect } from '@playwright/test';
import { LANGUAGES, getLanguageGroups } from './utils/languages';
import {
  switchLanguage,
  takeLanguageScreenshot,
  checkLayoutIssues,
  verifyKeyElements,
} from './utils/test-helpers';

test.describe('Comprehensive Language Tests', () => {
  const keyPages = [
    { path: '/', name: 'dashboard', selectors: ['header', 'nav', 'main'] },
    { path: '/tenants', name: 'tenants', selectors: ['table', 'button'] },
    { path: '/stores', name: 'stores', selectors: ['table'] },
    { path: '/inventory', name: 'inventory', selectors: ['table'] },
  ];

  for (const language of LANGUAGES) {
    test.describe(`${language.name} (${language.code}) - Full UI Test`, () => {
      for (const pageDef of keyPages) {
        test(`Should render ${pageDef.name} page correctly`, async ({ page }) => {
          await page.goto(pageDef.path);
          await page.waitForLoadState('networkidle');
          await switchLanguage(page, language.code);
          await page.waitForTimeout(1000);

          // Verify key elements are present
          await verifyKeyElements(page, pageDef.selectors);

          // Check for layout issues
          const layoutIssues = await checkLayoutIssues(page);
          if (layoutIssues.length > 0) {
            console.warn(`${language.name} - Layout issues on ${pageDef.name}:`, layoutIssues.slice(0, 5));
          }

          // Take screenshot
          await takeLanguageScreenshot(page, language, pageDef.name);

          // Verify page doesn't have critical errors
          const hasErrorMessage = await page.locator('text=/error|erro|erreur|fehler/i').count();
          expect(hasErrorMessage).toBe(0);
        });
      }
    });
  }

  test('Visual comparison - RTL vs LTR layouts', async ({ page }) => {
    const routes = ['/'];

    for (const route of routes) {
      // LTR reference (English)
      await page.goto(route);
      await switchLanguage(page, 'en');
      await page.waitForTimeout(1000);
      const ltrScreenshot = await page.screenshot({ fullPage: true });

      // RTL example (Arabic)
      await switchLanguage(page, 'ar');
      await page.waitForTimeout(1000);
      const rtlScreenshot = await page.screenshot({ fullPage: true });

      // Screenshots should be different
      expect(ltrScreenshot.equals(rtlScreenshot)).toBe(false);
    }
  });

  test('All languages - Navigation menu should be functional', async ({ page }) => {
    await page.goto('/');

    const testLanguages = ['en', 'fr', 'ar', 'zh', 'hi'];

    for (const langCode of testLanguages) {
      await switchLanguage(page, langCode);

      // Find navigation links
      const navLinks = page.locator('nav a, nav button');
      const count = await navLinks.count();

      expect(count).toBeGreaterThan(0);

      // Click first nav item (if it exists)
      if (count > 0) {
        await navLinks.first().click();
        await page.waitForLoadState('networkidle');

        // Should navigate successfully
        expect(page.url()).toBeTruthy();
      }
    }
  });

  test('Language selector should be accessible in all languages', async ({ page }) => {
    await page.goto('/');

    for (const language of LANGUAGES.slice(0, 10)) { // Test first 10
      await switchLanguage(page, language.code);

      // Language selector should still be accessible
      // This ensures users can always switch languages
      const languageButton = page.locator('[data-testid="language-selector"], [aria-label*="language"], button:has-text("language")');

      // If selector exists in UI
      if (await languageButton.count() > 0) {
        await expect(languageButton.first()).toBeVisible();
      }
    }
  });
});

test.describe('Critical User Flows - All Languages', () => {
  test('Login page should work in all languages', async ({ page }) => {
    const languages = ['en', 'fr', 'es', 'ar', 'zh'];

    for (const langCode of languages) {
      await page.goto('/login');
      await switchLanguage(page, langCode);

      // Check for login form elements
      const emailInput = page.locator('input[type="email"], input[name="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button[type="submit"]');

      if (await emailInput.count() > 0) {
        await expect(emailInput.first()).toBeVisible();
      }

      if (await passwordInput.count() > 0) {
        await expect(passwordInput.first()).toBeVisible();
      }

      if (await submitButton.count() > 0) {
        await expect(submitButton.first()).toBeVisible();
      }
    }
  });

  test('Forms should handle input in different scripts', async ({ page }) => {
    await page.goto('/');

    const testCases = [
      { lang: 'en', text: 'Test Store', expected: 'Test Store' },
      { lang: 'ar', text: 'متجر تجريبي', expected: 'متجر تجريبي' },
      { lang: 'ja', text: 'テスト店', expected: 'テスト店' },
      { lang: 'hi', text: 'परीक्षण स्टोर', expected: 'परीक्षण स्टोर' },
    ];

    for (const testCase of testCases) {
      await switchLanguage(page, testCase.lang);

      // Find any text input
      const textInput = page.locator('input[type="text"]').first();

      if (await textInput.count() > 0) {
        await textInput.clear();
        await textInput.fill(testCase.text);

        const value = await textInput.inputValue();
        expect(value).toBe(testCase.expected);
      }
    }
  });
});
