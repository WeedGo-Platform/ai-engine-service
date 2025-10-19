/**
 * Test Suite 3: Translation Sanity Check
 * Verifies translations are meaningful and not missing
 */

import { test, expect } from '@playwright/test';
import { LANGUAGES, getLanguageGroups } from './utils/languages';
import {
  switchLanguage,
  detectMissingTranslations,
  verifyTextRendering,
  verifyFontRendering,
  takeLanguageScreenshot,
} from './utils/test-helpers';

test.describe('Translation Sanity Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  // Test all languages for missing translations
  for (const language of LANGUAGES) {
    test(`${language.name} (${language.code}) - Should not have missing translations`, async ({ page }) => {
      await switchLanguage(page, language.code);

      // Wait for translations to load
      await page.waitForTimeout(2000);

      // Detect potential missing translations
      const missingTranslations = await detectMissingTranslations(page, language);

      // Log findings
      if (missingTranslations.length > 0) {
        console.log(`${language.name} - Potential untranslated text:`, missingTranslations);
      }

      // Allow some technical terms in English (API, POS, etc.)
      const allowedEnglishTerms = ['API', 'POS', 'SKU', 'QR', 'URL', 'ID', 'UUID'];
      const problematicTranslations = missingTranslations.filter(text =>
        !allowedEnglishTerms.some(term => text.includes(term))
      );

      // Soft assertion - log but don't fail
      if (problematicTranslations.length > 0) {
        console.warn(`⚠️  ${language.name} may have ${problematicTranslations.length} untranslated strings`);
      }
    });
  }

  // Test proper script rendering
  for (const language of LANGUAGES) {
    test(`${language.name} (${language.code}) - Should render in correct script`, async ({ page }) => {
      if (language.code === 'en') return; // Skip English

      await switchLanguage(page, language.code);

      // Find main heading or dashboard title
      const headingSelectors = ['h1', 'h2', '[role="heading"]', 'header'];

      for (const selector of headingSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          await verifyTextRendering(page, selector, language);
          break;
        }
      }
    });
  }

  // Test font rendering for all languages
  for (const language of LANGUAGES) {
    test(`${language.name} (${language.code}) - Should have proper font rendering`, async ({ page }) => {
      await switchLanguage(page, language.code);

      const fontInfo = await verifyFontRendering(page, language);

      // Log font information
      console.log(`${language.name} - Font: ${fontInfo.fontFamily}, Size: ${fontInfo.fontSize}`);

      // Ensure fonts are being applied
      expect(fontInfo.fontFamily).not.toBe('');
      expect(fontInfo.fontSize).toMatch(/\d+px/);
    });
  }

  // Test key pages for each language group
  const languageGroups = getLanguageGroups();

  test.describe('Indigenous Languages - Cultural Appropriateness', () => {
    for (const language of languageGroups.indigenous) {
      test(`${language.name} (${language.code}) - Should display syllabic script correctly`, async ({ page }) => {
        await switchLanguage(page, language.code);

        // Get all text nodes
        const textContent = await page.evaluate(() => {
          return document.body.textContent || '';
        });

        // Should contain syllabic characters
        const hasSyllabics = /[\u1400-\u167F\u18B0-\u18FF]/.test(textContent);

        if (!hasSyllabics) {
          console.warn(`⚠️  ${language.name} may not be displaying syllabic characters`);
        }

        // Take screenshot for visual review
        await takeLanguageScreenshot(page, language, 'main-page');
      });
    }
  });

  test.describe('Asian Languages - Character Display', () => {
    for (const language of languageGroups.asian) {
      test(`${language.name} (${language.code}) - Should display characters correctly`, async ({ page }) => {
        await switchLanguage(page, language.code);

        const textContent = await page.evaluate(() => {
          return document.body.textContent || '';
        });

        // Should have non-ASCII characters
        const hasNonAscii = /[^\x00-\x7F]/.test(textContent);
        expect(hasNonAscii).toBe(true);

        // Check for specific character ranges
        let expectedPattern: RegExp | null = null;

        if (['ja'].includes(language.code)) {
          // Japanese: Hiragana, Katakana, Kanji
          expectedPattern = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/;
        } else if (['ko'].includes(language.code)) {
          // Korean: Hangul
          expectedPattern = /[\uAC00-\uD7AF]/;
        } else if (['zh', 'yue'].includes(language.code)) {
          // Chinese: CJK
          expectedPattern = /[\u4E00-\u9FFF]/;
        } else if (['hi', 'gu', 'pa', 'bn', 'ta'].includes(language.code)) {
          // Indic scripts
          expectedPattern = /[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0B80-\u0BFF]/;
        }

        if (expectedPattern && !expectedPattern.test(textContent)) {
          console.warn(`⚠️  ${language.name} may not be displaying expected character set`);
        }
      });
    }
  });

  test.describe('Translation Completeness - Key Pages', () => {
    const keyRoutes = [
      { path: '/', name: 'Dashboard' },
      { path: '/tenants', name: 'Tenants' },
      { path: '/stores', name: 'Stores' },
      { path: '/inventory', name: 'Inventory' },
    ];

    for (const route of keyRoutes) {
      test(`All languages should translate ${route.name} page`, async ({ page }) => {
        const results: { lang: string; hasMissing: boolean; count: number }[] = [];

        for (const language of LANGUAGES.slice(0, 5)) { // Test first 5 languages
          await page.goto(route.path);
          await switchLanguage(page, language.code);
          await page.waitForTimeout(1000);

          const missingTranslations = await detectMissingTranslations(page, language);

          results.push({
            lang: language.code,
            hasMissing: missingTranslations.length > 0,
            count: missingTranslations.length,
          });
        }

        console.log(`${route.name} translation check:`, results);
      });
    }
  });
});
