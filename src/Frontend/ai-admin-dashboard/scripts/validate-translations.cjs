#!/usr/bin/env node

/**
 * Translation Coverage Validation Script
 *
 * This script validates that all translation files are complete and consistent
 * across all 28 supported languages in the WeedGo Admin Dashboard.
 *
 * Usage:
 *   node scripts/validate-translations.js
 *   npm run i18n:validate
 *
 * Exit codes:
 *   0 - All translations valid
 *   1 - Validation errors found
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Supported languages (must match i18n/config.ts)
const SUPPORTED_LANGUAGES = [
  'en', 'es', 'fr', 'zh', 'yue', 'pa', 'ar', 'tl', 'de', 'it',
  'pt', 'pl', 'ru', 'vi', 'hi', 'uk', 'fa', 'ko', 'ta', 'ur',
  'gu', 'ro', 'nl', 'cr', 'iu', 'bn', 'he', 'so', 'ja'
];

// Translation namespaces (must match i18n/config.ts)
const NAMESPACES = [
  'common', 'auth', 'dashboard', 'landing', 'forms', 'errors',
  'modals', 'tenants', 'stores', 'inventory', 'orders', 'pos',
  'payments', 'settings', 'communications', 'database',
  'promotions', 'catalog', 'apps', 'tools', 'signup'
];

// Base directory for translations
const LOCALES_DIR = path.join(__dirname, '../src/i18n/locales');

// Validation results
const results = {
  totalFiles: 0,
  validFiles: 0,
  missingFiles: [],
  emptyFiles: [],
  invalidJson: [],
  missingKeys: {},
  emptyValues: {},
  suspiciousValues: {},
  errors: [],
  warnings: [],
};

/**
 * Log with color
 */
function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * Load and parse JSON file
 */
function loadJsonFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    return null;
  }
}

/**
 * Get all keys from nested object
 */
function getAllKeys(obj, prefix = '') {
  let keys = [];

  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;

    if (value && typeof value === 'object' && !Array.isArray(value)) {
      keys = keys.concat(getAllKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }

  return keys;
}

/**
 * Get value from nested object using dot notation
 */
function getNestedValue(obj, keyPath) {
  return keyPath.split('.').reduce((current, key) => current?.[key], obj);
}

/**
 * Check if string looks like it's untranslated (contains English words)
 */
function looksUntranslated(value, language) {
  if (language === 'en') return false; // English is the base language

  // Common English words that shouldn't appear in other languages
  const englishIndicators = [
    'TODO', 'TRANSLATE', 'FIXME', 'TBD',
    'please', 'click', 'enter', 'submit', 'cancel',
    'error', 'success', 'warning', 'required'
  ];

  const lowerValue = value.toLowerCase();
  return englishIndicators.some(word => lowerValue.includes(word.toLowerCase()));
}

/**
 * Validate single translation file
 */
function validateTranslationFile(language, namespace) {
  results.totalFiles++;

  const filePath = path.join(LOCALES_DIR, language, `${namespace}.json`);

  // Check if file exists
  if (!fs.existsSync(filePath)) {
    results.missingFiles.push({ language, namespace, path: filePath });
    return null;
  }

  // Load JSON
  const translations = loadJsonFile(filePath);

  if (!translations) {
    results.invalidJson.push({ language, namespace, path: filePath });
    return null;
  }

  // Check if file is empty
  const keys = getAllKeys(translations);
  if (keys.length === 0) {
    results.emptyFiles.push({ language, namespace, path: filePath });
    return null;
  }

  results.validFiles++;
  return translations;
}

/**
 * Compare translations against English (baseline)
 */
function compareTranslations(language, namespace, translations, englishTranslations) {
  const englishKeys = getAllKeys(englishTranslations);
  const translationKeys = getAllKeys(translations);

  // Find missing keys
  const missingKeys = englishKeys.filter(key => !translationKeys.includes(key));
  if (missingKeys.length > 0) {
    if (!results.missingKeys[language]) {
      results.missingKeys[language] = {};
    }
    results.missingKeys[language][namespace] = missingKeys;
  }

  // Find empty values
  const emptyValues = translationKeys.filter(key => {
    const value = getNestedValue(translations, key);
    return value === '' || value === null || value === undefined;
  });

  if (emptyValues.length > 0) {
    if (!results.emptyValues[language]) {
      results.emptyValues[language] = {};
    }
    results.emptyValues[language][namespace] = emptyValues;
  }

  // Find suspicious values (look untranslated)
  if (language !== 'en') {
    const suspicious = translationKeys.filter(key => {
      const value = getNestedValue(translations, key);
      return typeof value === 'string' && looksUntranslated(value, language);
    });

    if (suspicious.length > 0) {
      if (!results.suspiciousValues[language]) {
        results.suspiciousValues[language] = {};
      }
      results.suspiciousValues[language][namespace] = suspicious.map(key => ({
        key,
        value: getNestedValue(translations, key)
      }));
    }
  }
}

/**
 * Main validation function
 */
function validateAllTranslations() {
  log('\n╔════════════════════════════════════════════════════════════════╗', 'cyan');
  log('║     WeedGo Admin Dashboard - Translation Validation           ║', 'cyan');
  log('╚════════════════════════════════════════════════════════════════╝\n', 'cyan');

  log(`Validating ${SUPPORTED_LANGUAGES.length} languages × ${NAMESPACES.length} namespaces = ${SUPPORTED_LANGUAGES.length * NAMESPACES.length} files\n`, 'blue');

  // Load English translations as baseline
  const englishTranslations = {};
  NAMESPACES.forEach(namespace => {
    englishTranslations[namespace] = validateTranslationFile('en', namespace);
  });

  // Validate all other languages
  SUPPORTED_LANGUAGES.forEach(language => {
    if (language === 'en') return; // Skip English (already loaded)

    log(`Validating ${language}...`, 'bright');

    NAMESPACES.forEach(namespace => {
      const translations = validateTranslationFile(language, namespace);

      if (translations && englishTranslations[namespace]) {
        compareTranslations(language, namespace, translations, englishTranslations[namespace]);
      }
    });
  });
}

/**
 * Print validation results
 */
function printResults() {
  log('\n' + '═'.repeat(70), 'cyan');
  log('VALIDATION RESULTS', 'cyan');
  log('═'.repeat(70) + '\n', 'cyan');

  // Summary
  log(`✓ Valid files:   ${results.validFiles} / ${results.totalFiles}`, 'green');

  if (results.missingFiles.length > 0) {
    log(`✗ Missing files: ${results.missingFiles.length}`, 'red');
  }

  if (results.invalidJson.length > 0) {
    log(`✗ Invalid JSON:  ${results.invalidJson.length}`, 'red');
  }

  if (results.emptyFiles.length > 0) {
    log(`✗ Empty files:   ${results.emptyFiles.length}`, 'red');
  }

  // Missing files
  if (results.missingFiles.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('MISSING FILES:', 'yellow');
    log('─'.repeat(70), 'yellow');
    results.missingFiles.forEach(({ language, namespace }) => {
      log(`  • ${language}/${namespace}.json`, 'red');
    });
  }

  // Invalid JSON
  if (results.invalidJson.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('INVALID JSON FILES:', 'yellow');
    log('─'.repeat(70), 'yellow');
    results.invalidJson.forEach(({ language, namespace }) => {
      log(`  • ${language}/${namespace}.json`, 'red');
    });
  }

  // Empty files
  if (results.emptyFiles.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('EMPTY FILES:', 'yellow');
    log('─'.repeat(70), 'yellow');
    results.emptyFiles.forEach(({ language, namespace }) => {
      log(`  • ${language}/${namespace}.json`, 'red');
    });
  }

  // Missing keys
  const languagesWithMissingKeys = Object.keys(results.missingKeys);
  if (languagesWithMissingKeys.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('MISSING TRANSLATION KEYS:', 'yellow');
    log('─'.repeat(70), 'yellow');

    languagesWithMissingKeys.forEach(language => {
      const namespaces = Object.keys(results.missingKeys[language]);
      const totalMissing = namespaces.reduce((sum, ns) =>
        sum + results.missingKeys[language][ns].length, 0);

      log(`\n  Language: ${language} (${totalMissing} missing keys)`, 'red');

      namespaces.forEach(namespace => {
        const keys = results.missingKeys[language][namespace];
        log(`    ${namespace}: ${keys.length} keys missing`, 'yellow');

        if (keys.length <= 5) {
          keys.forEach(key => log(`      - ${key}`, 'red'));
        } else {
          keys.slice(0, 3).forEach(key => log(`      - ${key}`, 'red'));
          log(`      ... and ${keys.length - 3} more`, 'red');
        }
      });
    });
  }

  // Empty values
  const languagesWithEmptyValues = Object.keys(results.emptyValues);
  if (languagesWithEmptyValues.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('EMPTY VALUES:', 'yellow');
    log('─'.repeat(70), 'yellow');

    languagesWithEmptyValues.forEach(language => {
      const namespaces = Object.keys(results.emptyValues[language]);
      const totalEmpty = namespaces.reduce((sum, ns) =>
        sum + results.emptyValues[language][ns].length, 0);

      log(`\n  Language: ${language} (${totalEmpty} empty values)`, 'yellow');

      namespaces.forEach(namespace => {
        const keys = results.emptyValues[language][namespace];
        log(`    ${namespace}: ${keys.length} empty values`, 'yellow');
        keys.slice(0, 5).forEach(key => log(`      - ${key}`, 'yellow'));
        if (keys.length > 5) {
          log(`      ... and ${keys.length - 5} more`, 'yellow');
        }
      });
    });
  }

  // Suspicious values
  const languagesWithSuspicious = Object.keys(results.suspiciousValues);
  if (languagesWithSuspicious.length > 0) {
    log('\n' + '─'.repeat(70), 'yellow');
    log('SUSPICIOUS VALUES (possibly untranslated):', 'yellow');
    log('─'.repeat(70), 'yellow');

    languagesWithSuspicious.forEach(language => {
      const namespaces = Object.keys(results.suspiciousValues[language]);
      const totalSuspicious = namespaces.reduce((sum, ns) =>
        sum + results.suspiciousValues[language][ns].length, 0);

      log(`\n  Language: ${language} (${totalSuspicious} suspicious values)`, 'yellow');

      namespaces.forEach(namespace => {
        const items = results.suspiciousValues[language][namespace];
        log(`    ${namespace}: ${items.length} suspicious values`, 'yellow');
        items.slice(0, 3).forEach(({ key, value }) => {
          log(`      - ${key}: "${value}"`, 'yellow');
        });
        if (items.length > 3) {
          log(`      ... and ${items.length - 3} more`, 'yellow');
        }
      });
    });
  }

  // Final summary
  log('\n' + '═'.repeat(70), 'cyan');

  const hasErrors = results.missingFiles.length > 0 ||
                    results.invalidJson.length > 0 ||
                    results.emptyFiles.length > 0 ||
                    languagesWithMissingKeys.length > 0;

  const hasWarnings = languagesWithEmptyValues.length > 0 ||
                      languagesWithSuspicious.length > 0;

  if (!hasErrors && !hasWarnings) {
    log('✅ ALL TRANSLATIONS VALID!', 'green');
    log('All ' + results.validFiles + ' translation files passed validation.', 'green');
  } else if (hasErrors) {
    log('❌ VALIDATION FAILED', 'red');
    log('Critical errors found. Please fix before deployment.', 'red');
  } else if (hasWarnings) {
    log('⚠️  VALIDATION PASSED WITH WARNINGS', 'yellow');
    log('No critical errors, but some warnings to review.', 'yellow');
  }

  log('═'.repeat(70) + '\n', 'cyan');

  return hasErrors ? 1 : 0;
}

// Run validation
try {
  validateAllTranslations();
  const exitCode = printResults();
  process.exit(exitCode);
} catch (error) {
  log('\n❌ VALIDATION SCRIPT ERROR:', 'red');
  log(error.message, 'red');
  log(error.stack, 'red');
  process.exit(1);
}
