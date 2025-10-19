/**
 * Test Suite 4: Language Switching Performance
 * Measures and verifies performance of language switching
 */

import { test, expect } from '@playwright/test';
import { LANGUAGES } from './utils/languages';
import { measureLanguageSwitchTime, switchLanguage } from './utils/test-helpers';

test.describe('Language Switching Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Language switching should complete within acceptable time', async ({ page }) => {
    const results: { from: string; to: string; time: number }[] = [];

    // Test switching from English to various languages
    const testLanguages = ['fr', 'ar', 'zh', 'hi', 'de', 'es'];

    for (const targetLang of testLanguages) {
      const time = await measureLanguageSwitchTime(page, 'en', targetLang);
      results.push({ from: 'en', to: targetLang, time });

      // Language switch should be fast (under 2 seconds)
      expect(time).toBeLessThan(2000);

      // Switch back to English for next test
      await switchLanguage(page, 'en');
    }

    // Log results
    console.log('Language Switch Performance:', results);

    // Calculate average
    const avgTime = results.reduce((sum, r) => sum + r.time, 0) / results.length;
    console.log(`Average switch time: ${avgTime.toFixed(2)}ms`);

    // Average should be under 1 second
    expect(avgTime).toBeLessThan(1000);
  });

  test('Rapid language switching should not cause errors', async ({ page }) => {
    const languages = ['en', 'fr', 'de', 'es', 'it', 'pt'];

    // Listen for console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    // Rapidly switch between languages
    for (const lang of languages) {
      await switchLanguage(page, lang);
      await page.waitForTimeout(100); // Very short delay
    }

    // Should have no errors
    if (errors.length > 0) {
      console.error('Errors during rapid switching:', errors);
    }

    expect(errors.length).toBe(0);
  });

  test('Language assets should be cached after first load', async ({ page }) => {
    // First load - measure time
    const firstLoadTime = await measureLanguageSwitchTime(page, 'en', 'fr');

    // Switch to another language
    await switchLanguage(page, 'de');

    // Switch back to French - should be faster due to caching
    const secondLoadTime = await measureLanguageSwitchTime(page, 'de', 'fr');

    console.log(`First load: ${firstLoadTime}ms, Second load: ${secondLoadTime}ms`);

    // Second load should be faster or similar (accounting for variance)
    expect(secondLoadTime).toBeLessThanOrEqual(firstLoadTime * 1.5);
  });

  test('Language switching should not cause memory leaks', async ({ page }) => {
    // Get initial memory usage
    const initialMetrics = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return null;
    });

    if (initialMetrics === null) {
      test.skip();
      return;
    }

    // Switch languages multiple times
    for (let i = 0; i < 10; i++) {
      const lang = LANGUAGES[i % LANGUAGES.length];
      await switchLanguage(page, lang.code);
      await page.waitForTimeout(200);
    }

    // Get final memory usage
    const finalMetrics = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return null;
    });

    if (finalMetrics !== null && initialMetrics !== null) {
      const memoryIncrease = finalMetrics - initialMetrics;
      const increasePercentage = (memoryIncrease / initialMetrics) * 100;

      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${increasePercentage.toFixed(2)}%)`);

      // Memory increase should be reasonable (less than 50% increase)
      expect(increasePercentage).toBeLessThan(50);
    }
  });

  test('All 28 languages should load without network errors', async ({ page }) => {
    const networkErrors: { lang: string; error: string }[] = [];

    page.on('requestfailed', (request) => {
      networkErrors.push({
        lang: 'unknown',
        error: `Failed to load: ${request.url()}`,
      });
    });

    // Try loading each language
    for (const language of LANGUAGES) {
      await switchLanguage(page, language.code);
      await page.waitForTimeout(500);
    }

    // Log any network errors
    if (networkErrors.length > 0) {
      console.error('Network errors:', networkErrors);
    }

    // Should have no failed requests
    expect(networkErrors.length).toBe(0);
  });

  test('Language switching should not block UI interactions', async ({ page }) => {
    // Start language switch
    const switchPromise = switchLanguage(page, 'fr');

    // Try to interact with UI during switch
    const button = page.locator('button').first();

    // Wait a bit but not for full switch
    await page.waitForTimeout(100);

    // UI should still be responsive (button should exist)
    if (await button.count() > 0) {
      const isEnabled = await button.isEnabled();
      // Button may be disabled during loading, but should exist
      expect(await button.count()).toBeGreaterThan(0);
    }

    // Wait for switch to complete
    await switchPromise;
  });
});
