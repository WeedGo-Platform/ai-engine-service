/**
 * Test Suite 1: Language Switching and Basic Functionality
 * Tests language switching mechanism and verifies UI updates correctly
 */

import { test, expect } from '@playwright/test';
import { LANGUAGES } from './utils/languages';
import { switchLanguage, verifyTextDirection } from './utils/test-helpers';

test.describe('Language Switching Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should load default language (English)', async ({ page }) => {
    const htmlLang = await page.locator('html').getAttribute('lang');
    expect(htmlLang).toBe('en');
  });

  test('should successfully switch between all 28 languages', async ({ page }) => {
    for (const language of LANGUAGES) {
      await test.step(`Switching to ${language.name} (${language.code})`, async () => {
        await switchLanguage(page, language.code);

        // Verify language changed in localStorage or HTML attribute
        const currentLang = await page.evaluate(() =>
          localStorage.getItem('i18nextLng') || document.documentElement.lang
        );

        expect(currentLang).toContain(language.code);

        // Verify text direction
        await verifyTextDirection(page, language);

        // Small delay to avoid overwhelming the system
        await page.waitForTimeout(500);
      });
    }
  });

  test('should persist language preference on page reload', async ({ page }) => {
    // Switch to French
    await switchLanguage(page, 'fr');

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify French is still selected
    const currentLang = await page.evaluate(() =>
      localStorage.getItem('i18nextLng') || document.documentElement.lang
    );

    expect(currentLang).toContain('fr');
  });

  test('should maintain language across navigation', async ({ page }) => {
    // Switch to Spanish
    await switchLanguage(page, 'es');

    // Navigate to different pages (adjust routes based on your app)
    const routes = ['/', '/tenants', '/stores', '/inventory'];

    for (const route of routes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      const currentLang = await page.evaluate(() =>
        localStorage.getItem('i18nextLng')
      );

      expect(currentLang).toBe('es');
    }
  });
});
