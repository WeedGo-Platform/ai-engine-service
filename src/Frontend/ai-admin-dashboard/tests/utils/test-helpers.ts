/**
 * Test Helper Functions for Multilingual Testing
 */

import { Page, expect } from '@playwright/test';
import { LanguageConfig } from './languages';

/**
 * Switch language in the UI
 */
export async function switchLanguage(page: Page, languageCode: string) {
  // Look for language selector button (Globe icon)
  const languageButton = page.locator('button[aria-label="Select Language"]');

  if (await languageButton.count() > 0) {
    // Click to open dropdown
    await languageButton.click();
    await page.waitForTimeout(300);

    // Find and click the language option
    const languageOption = page.locator(`button[role="menuitem"]`).filter({
      has: page.locator(`text="${languageCode}"`)
    }).first();

    if (await languageOption.count() > 0) {
      await languageOption.click();
      await page.waitForTimeout(1000); // Wait for language to load
    } else {
      // If option not found, use localStorage fallback
      await page.evaluate((code) => {
        localStorage.setItem('i18nextLng', code);
      }, languageCode);
      await page.reload();
      await page.waitForLoadState('networkidle');
    }
  } else {
    // Fallback: use localStorage
    await page.evaluate((code) => {
      localStorage.setItem('i18nextLng', code);
    }, languageCode);
    await page.reload();
    await page.waitForLoadState('networkidle');
  }
}

/**
 * Check if text direction matches language RTL setting
 */
export async function verifyTextDirection(page: Page, language: LanguageConfig) {
  const htmlDir = await page.locator('html').getAttribute('dir');
  const expectedDir = language.isRTL ? 'rtl' : 'ltr';

  expect(htmlDir).toBe(expectedDir);
}

/**
 * Check if text is rendered in correct script
 */
export async function verifyTextRendering(page: Page, selector: string, language: LanguageConfig) {
  const element = page.locator(selector).first();
  const text = await element.textContent();

  if (!text) {
    throw new Error(`No text found in selector: ${selector}`);
  }

  // Basic check: text should not be empty and should contain non-ASCII for non-Latin scripts
  expect(text.trim()).not.toBe('');

  if (!['Latin'].includes(language.script)) {
    // Should contain non-ASCII characters for non-Latin scripts
    const hasNonAscii = /[^\x00-\x7F]/.test(text);
    expect(hasNonAscii).toBe(true);
  }
}

/**
 * Measure language switching performance
 */
export async function measureLanguageSwitchTime(page: Page, fromLang: string, toLang: string): Promise<number> {
  const startTime = Date.now();
  await switchLanguage(page, toLang);
  const endTime = Date.now();
  return endTime - startTime;
}

/**
 * Check for layout issues (overflow, clipping)
 */
export async function checkLayoutIssues(page: Page) {
  const overflowIssues = await page.evaluate(() => {
    const issues: string[] = [];
    const elements = document.querySelectorAll('*');

    elements.forEach((el) => {
      const htmlEl = el as HTMLElement;
      if (htmlEl.scrollWidth > htmlEl.clientWidth + 5) {
        issues.push(`Horizontal overflow: ${htmlEl.tagName}.${htmlEl.className}`);
      }
    });

    return issues;
  });

  return overflowIssues;
}

/**
 * Verify that key UI elements are present
 */
export async function verifyKeyElements(page: Page, selectors: string[]) {
  for (const selector of selectors) {
    const element = page.locator(selector);
    await expect(element).toBeVisible({ timeout: 10000 });
  }
}

/**
 * Take screenshot with language context
 */
export async function takeLanguageScreenshot(page: Page, language: LanguageConfig, pageName: string) {
  await page.screenshot({
    path: `test-results/screenshots/${language.code}-${pageName}.png`,
    fullPage: false,
  });
}

/**
 * Check for missing translations (English text in non-English pages)
 */
export async function detectMissingTranslations(page: Page, language: LanguageConfig): Promise<string[]> {
  if (language.code === 'en') return [];

  const suspiciousTexts = await page.evaluate(() => {
    const issues: string[] = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null
    );

    let node;
    const commonEnglishWords = ['login', 'email', 'password', 'dashboard', 'settings', 'logout', 'save', 'cancel', 'delete', 'edit'];

    while (node = walker.nextNode()) {
      const text = node.textContent?.trim() || '';
      if (text.length > 3) {
        // Check if it's purely ASCII and matches common English words
        const isAscii = /^[\x00-\x7F]+$/.test(text);
        const hasCommonWord = commonEnglishWords.some(word =>
          text.toLowerCase().includes(word)
        );

        if (isAscii && hasCommonWord && text.split(' ').length <= 5) {
          issues.push(text);
        }
      }
    }

    return [...new Set(issues)]; // Remove duplicates
  });

  return suspiciousTexts;
}

/**
 * Verify RTL-specific UI elements (icons, chevrons, etc.)
 */
export async function verifyRTLLayout(page: Page) {
  const rtlIssues = await page.evaluate(() => {
    const issues: string[] = [];

    // Check if flex direction is reversed
    const flexContainers = document.querySelectorAll('[style*="flex"]');
    flexContainers.forEach((el) => {
      const htmlEl = el as HTMLElement;
      const direction = window.getComputedStyle(htmlEl).direction;
      if (direction !== 'rtl') {
        issues.push(`Flex container not RTL: ${htmlEl.tagName}.${htmlEl.className}`);
      }
    });

    return issues;
  });

  return rtlIssues;
}

/**
 * Check font rendering and readability
 */
export async function verifyFontRendering(page: Page, language: LanguageConfig) {
  const fontInfo = await page.evaluate((script) => {
    const body = document.body;
    const computedStyle = window.getComputedStyle(body);
    const fontFamily = computedStyle.fontFamily;
    const fontSize = computedStyle.fontSize;

    return { fontFamily, fontSize, script };
  }, language.script);

  // Ensure fonts are loaded
  expect(fontInfo.fontFamily).toBeTruthy();
  expect(fontInfo.fontSize).toBeTruthy();

  return fontInfo;
}
