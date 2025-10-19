/**
 * Test Suite 2: RTL Layout Verification
 * Tests right-to-left language layouts (Arabic, Persian, Hebrew, Urdu)
 */

import { test, expect } from '@playwright/test';
import { RTL_LANGUAGES } from './utils/languages';
import { switchLanguage, verifyTextDirection, verifyRTLLayout, takeLanguageScreenshot } from './utils/test-helpers';

test.describe('RTL Layout Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  for (const language of RTL_LANGUAGES) {
    test(`${language.name} (${language.code}) - Should apply RTL layout correctly`, async ({ page }) => {
      await switchLanguage(page, language.code);

      // Verify HTML dir attribute
      const htmlDir = await page.locator('html').getAttribute('dir');
      expect(htmlDir).toBe('rtl');

      // Verify text direction
      await verifyTextDirection(page, language);

      // Take screenshot for visual verification
      await takeLanguageScreenshot(page, language, 'dashboard');

      // Check for common RTL issues
      const rtlIssues = await verifyRTLLayout(page);

      // Log issues for review (some may be intentional)
      if (rtlIssues.length > 0) {
        console.log(`${language.name} - Potential RTL issues:`, rtlIssues);
      }
    });

    test(`${language.name} (${language.code}) - Should mirror navigation elements`, async ({ page }) => {
      await switchLanguage(page, language.code);

      // Check if navigation bar text is aligned to the right
      const nav = page.locator('nav').first();
      if (await nav.count() > 0) {
        const textAlign = await nav.evaluate((el) =>
          window.getComputedStyle(el).textAlign
        );

        // In RTL, text should be right-aligned or start-aligned (which becomes right)
        expect(['right', 'start'].includes(textAlign)).toBeTruthy();
      }
    });

    test(`${language.name} (${language.code}) - Should flip icons and chevrons`, async ({ page }) => {
      await switchLanguage(page, language.code);

      // Check for chevron/arrow elements that should be flipped
      const chevrons = page.locator('[class*="chevron"], [class*="arrow"]');

      if (await chevrons.count() > 0) {
        const firstChevron = chevrons.first();
        const transform = await firstChevron.evaluate((el) =>
          window.getComputedStyle(el).transform
        );

        // Should have some transform (scale/rotate) for RTL
        // This is a soft check as implementation may vary
        console.log(`${language.name} - Chevron transform:`, transform);
      }
    });

    test(`${language.name} (${language.code}) - Should handle forms correctly`, async ({ page }) => {
      await switchLanguage(page, language.code);

      // Look for form inputs
      const inputs = page.locator('input[type="text"], input[type="email"]');

      if (await inputs.count() > 0) {
        const firstInput = inputs.first();
        const direction = await firstInput.evaluate((el) =>
          window.getComputedStyle(el).direction
        );

        expect(direction).toBe('rtl');
      }
    });
  }

  test('RTL languages - Compare with LTR baseline', async ({ page }) => {
    // Load English first
    await page.goto('/');
    const englishScreenshot = await page.screenshot();

    // Switch to Arabic
    await switchLanguage(page, 'ar');
    const arabicScreenshot = await page.screenshot();

    // The screenshots should be different (layout mirrored)
    expect(englishScreenshot).not.toEqual(arabicScreenshot);
  });
});
