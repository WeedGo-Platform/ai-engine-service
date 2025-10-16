#!/usr/bin/env node

/**
 * Translation Key Propagation Script
 *
 * This script propagates new translation keys from English to all other languages.
 * It preserves existing translations and only adds missing keys with English placeholders.
 *
 * Usage:
 *   node scripts/propagate-translations.cjs
 *   npm run i18n:propagate
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
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

// Translation namespaces
const NAMESPACES = [
  'common', 'auth', 'dashboard', 'landing', 'forms', 'errors',
  'modals', 'tenants', 'stores', 'inventory', 'orders', 'pos',
  'payments', 'settings', 'communications', 'database',
  'promotions', 'catalog', 'apps', 'tools', 'signup'
];

// Base directory for translations
const LOCALES_DIR = path.join(__dirname, '../src/i18n/locales');

// Statistics
const stats = {
  filesProcessed: 0,
  keysAdded: 0,
  languagesUpdated: 0,
  errors: []
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
 * Save JSON file with pretty formatting
 */
function saveJsonFile(filePath, data) {
  try {
    const content = JSON.stringify(data, null, 2) + '\n';
    fs.writeFileSync(filePath, content, 'utf-8');
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Deep merge two objects, preserving existing values
 * @param {Object} target - Existing translations
 * @param {Object} source - English translations (template)
 * @returns {Object} Merged object
 */
function deepMerge(target, source) {
  const result = { ...target };

  for (const [key, value] of Object.entries(source)) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      // Recursively merge nested objects
      result[key] = deepMerge(result[key] || {}, value);
    } else if (!(key in result)) {
      // Add missing key with English value as placeholder
      result[key] = value;
      stats.keysAdded++;
    }
    // If key exists, keep existing translation (don't overwrite)
  }

  return result;
}

/**
 * Propagate keys from English to a target language
 */
function propagateNamespace(language, namespace) {
  const englishPath = path.join(LOCALES_DIR, 'en', `${namespace}.json`);
  const targetPath = path.join(LOCALES_DIR, language, `${namespace}.json`);

  // Load English translations (source of truth for structure)
  const englishTranslations = loadJsonFile(englishPath);
  if (!englishTranslations) {
    stats.errors.push(`Failed to load English: ${namespace}.json`);
    return false;
  }

  // Load target language translations
  let targetTranslations = loadJsonFile(targetPath);
  if (!targetTranslations) {
    // File doesn't exist, create it with English as template
    targetTranslations = {};
  }

  // Count keys before merge
  const keysBefore = JSON.stringify(targetTranslations).length;

  // Merge English keys into target language
  const mergedTranslations = deepMerge(targetTranslations, englishTranslations);

  // Count keys after merge
  const keysAfter = JSON.stringify(mergedTranslations).length;

  // Only save if there were changes
  if (keysBefore !== keysAfter) {
    if (saveJsonFile(targetPath, mergedTranslations)) {
      stats.filesProcessed++;
      return true;
    } else {
      stats.errors.push(`Failed to save: ${language}/${namespace}.json`);
      return false;
    }
  }

  return true; // No changes needed
}

/**
 * Main propagation function
 */
function propagateAllTranslations() {
  log('\n╔════════════════════════════════════════════════════════════════╗', 'cyan');
  log('║     WeedGo Admin Dashboard - Translation Propagation          ║', 'cyan');
  log('╚════════════════════════════════════════════════════════════════╝\n', 'cyan');

  log(`Propagating keys from English to ${SUPPORTED_LANGUAGES.length - 1} languages\n`, 'blue');

  // Process each language (skip English)
  SUPPORTED_LANGUAGES.forEach(language => {
    if (language === 'en') return; // Skip English

    log(`Processing ${language}...`, 'bright');

    let updatedCount = 0;

    NAMESPACES.forEach(namespace => {
      const keysBefore = stats.keysAdded;
      const success = propagateNamespace(language, namespace);

      if (success && stats.keysAdded > keysBefore) {
        updatedCount++;
      }
    });

    if (updatedCount > 0) {
      stats.languagesUpdated++;
      log(`  ✓ Updated ${updatedCount} namespaces`, 'green');
    } else {
      log(`  ✓ No changes needed`, 'green');
    }
  });
}

/**
 * Print results
 */
function printResults() {
  log('\n' + '═'.repeat(70), 'cyan');
  log('PROPAGATION RESULTS', 'cyan');
  log('═'.repeat(70) + '\n', 'cyan');

  log(`✓ Files processed:     ${stats.filesProcessed}`, 'green');
  log(`✓ Keys added:          ${stats.keysAdded}`, 'green');
  log(`✓ Languages updated:   ${stats.languagesUpdated}`, 'green');

  if (stats.errors.length > 0) {
    log(`\n✗ Errors encountered:  ${stats.errors.length}`, 'red');
    stats.errors.forEach(error => {
      log(`  • ${error}`, 'red');
    });
  }

  log('\n' + '═'.repeat(70), 'cyan');

  if (stats.errors.length === 0) {
    log('✅ PROPAGATION COMPLETED SUCCESSFULLY!', 'green');
    log(`Added ${stats.keysAdded} missing translation keys (English placeholders)`, 'green');
    log('Next step: Run "npm run i18n:validate" to verify coverage', 'blue');
  } else {
    log('⚠️  PROPAGATION COMPLETED WITH ERRORS', 'yellow');
    log('Please review errors above and fix manually', 'yellow');
  }

  log('═'.repeat(70) + '\n', 'cyan');

  return stats.errors.length === 0 ? 0 : 1;
}

// Run propagation
try {
  propagateAllTranslations();
  const exitCode = printResults();
  process.exit(exitCode);
} catch (error) {
  log('\n❌ PROPAGATION SCRIPT ERROR:', 'red');
  log(error.message, 'red');
  log(error.stack, 'red');
  process.exit(1);
}
