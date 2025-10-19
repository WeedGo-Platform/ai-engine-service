#!/usr/bin/env python3
"""
Comprehensive Translation Completeness Analysis
Analyzes all 29 languages across 21 namespaces for the AI Admin Dashboard
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Base directory
BASE_DIR = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/ai-admin-dashboard/src/i18n/locales")

# All languages
LANGUAGES = [
    'ar', 'bn', 'cr', 'de', 'es', 'fa', 'fr', 'gu', 'he', 'hi',
    'it', 'iu', 'ja', 'ko', 'nl', 'pa', 'pl', 'pt', 'ro', 'ru',
    'so', 'ta', 'tl', 'uk', 'ur', 'vi', 'yue', 'zh'
]

# All namespaces (based on English directory)
NAMESPACES = [
    'apps', 'auth', 'catalog', 'common', 'communications', 'dashboard',
    'database', 'errors', 'forms', 'inventory', 'landing', 'modals',
    'orders', 'payments', 'pos', 'promotions', 'settings', 'signup',
    'stores', 'tenants', 'tools'
]

def count_keys(obj, prefix=''):
    """Recursively count all keys in a nested JSON object"""
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, dict):
                count += count_keys(value, f"{prefix}.{key}" if prefix else key)
            elif isinstance(value, list):
                # Lists are counted as one key
                count += 1
            else:
                count += 1
    return count

def get_all_keys(obj, prefix=''):
    """Get all key paths in a nested JSON object"""
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.update(get_all_keys(value, full_key))
            else:
                keys.add(full_key)
    return keys

def load_json_safe(file_path):
    """Load JSON file safely, return None if error"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def analyze_namespace(namespace: str, lang: str) -> Dict:
    """Analyze a single namespace file for a language"""
    en_file = BASE_DIR / 'en' / f'{namespace}.json'
    lang_file = BASE_DIR / lang / f'{namespace}.json'

    result = {
        'exists': False,
        'valid_json': False,
        'key_count': 0,
        'en_key_count': 0,
        'completeness': 0.0,
        'missing_keys': [],
        'extra_keys': []
    }

    # Check if file exists
    if not lang_file.exists():
        return result

    result['exists'] = True

    # Load English reference
    en_data = load_json_safe(en_file)
    if not en_data:
        return result

    result['en_key_count'] = count_keys(en_data)
    en_keys = get_all_keys(en_data)

    # Load language file
    lang_data = load_json_safe(lang_file)
    if not lang_data:
        return result

    result['valid_json'] = True
    result['key_count'] = count_keys(lang_data)
    lang_keys = get_all_keys(lang_data)

    # Calculate completeness
    if result['en_key_count'] > 0:
        result['completeness'] = (result['key_count'] / result['en_key_count']) * 100

    # Find missing and extra keys
    result['missing_keys'] = sorted(list(en_keys - lang_keys))
    result['extra_keys'] = sorted(list(lang_keys - en_keys))

    return result

def main():
    print("=" * 80)
    print("MULTILINGUAL TRANSLATION COMPLETENESS ANALYSIS")
    print("AI Admin Dashboard - 29 Languages × 21 Namespaces")
    print("=" * 80)
    print()

    # Master tracking
    fully_translated = []
    incomplete = defaultdict(list)
    missing_files = defaultdict(list)

    # Track by namespace
    namespace_stats = defaultdict(lambda: {'complete': 0, 'incomplete': 0, 'missing': 0})

    # Analyze each language
    for lang in LANGUAGES:
        print(f"\n{'─' * 80}")
        print(f"Language: {lang.upper()}")
        print(f"{'─' * 80}")

        lang_complete = True
        lang_stats = []

        for namespace in NAMESPACES:
            result = analyze_namespace(namespace, lang)

            status = "❌ MISSING"
            if result['exists']:
                if result['valid_json']:
                    if result['completeness'] >= 100:
                        status = "✅ COMPLETE"
                        namespace_stats[namespace]['complete'] += 1
                    else:
                        status = f"⚠️  INCOMPLETE ({result['completeness']:.1f}%)"
                        namespace_stats[namespace]['incomplete'] += 1
                        lang_complete = False
                        incomplete[lang].append({
                            'namespace': namespace,
                            'completeness': result['completeness'],
                            'missing_keys': result['missing_keys'][:5]  # First 5
                        })
                else:
                    status = "❌ INVALID JSON"
                    lang_complete = False
                    namespace_stats[namespace]['incomplete'] += 1
            else:
                lang_complete = False
                namespace_stats[namespace]['missing'] += 1
                missing_files[lang].append(namespace)

            lang_stats.append({
                'namespace': namespace,
                'status': status,
                'keys': f"{result['key_count']}/{result['en_key_count']}"
            })

        # Print language summary
        for stat in lang_stats:
            print(f"  {stat['namespace']:20s} {stat['status']:30s} {stat['keys']}")

        if lang_complete:
            fully_translated.append(lang)
            print(f"\n  🎉 {lang.upper()} is FULLY TRANSLATED!")

    # Summary Report
    print("\n\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total Languages: {len(LANGUAGES)}")
    print(f"  Total Namespaces: {len(NAMESPACES)}")
    print(f"  Total Translation Files: {len(LANGUAGES) * len(NAMESPACES)}")

    print(f"\n✅ FULLY TRANSLATED LANGUAGES ({len(fully_translated)}):")
    if fully_translated:
        for lang in fully_translated:
            print(f"  • {lang}")
    else:
        print("  None yet - all languages have incomplete translations")

    print(f"\n⚠️  INCOMPLETE TRANSLATIONS ({len(incomplete)}):")
    for lang, issues in incomplete.items():
        print(f"\n  {lang.upper()}: {len(issues)} namespaces incomplete")
        for issue in issues[:3]:  # Show first 3
            print(f"    • {issue['namespace']}: {issue['completeness']:.1f}% complete")
            if issue['missing_keys']:
                print(f"      Missing keys: {', '.join(issue['missing_keys'][:3])}...")

    print(f"\n❌ MISSING FILES ({sum(len(v) for v in missing_files.values())} total):")
    for lang, namespaces in missing_files.items():
        if namespaces:
            print(f"  {lang.upper()}: {', '.join(namespaces)}")

    print(f"\n📈 NAMESPACE COMPLETION STATS:")
    for namespace in NAMESPACES:
        stats = namespace_stats[namespace]
        total = len(LANGUAGES)
        complete_pct = (stats['complete'] / total) * 100
        print(f"  {namespace:20s} ✅ {stats['complete']:2d}  ⚠️  {stats['incomplete']:2d}  ❌ {stats['missing']:2d}  ({complete_pct:.0f}% complete)")

    # Save detailed report
    report_path = BASE_DIR.parent / "translation_report.json"
    report = {
        'fully_translated': fully_translated,
        'incomplete': dict(incomplete),
        'missing_files': dict(missing_files),
        'namespace_stats': dict(namespace_stats)
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed report saved to: {report_path}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()