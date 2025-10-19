#!/usr/bin/env python3
"""
Add charts.revenueLabel translation to all languages
"""

import json
from pathlib import Path

# Translations for "Revenue" in all languages
REVENUE_TRANSLATIONS = {
    "en": "Revenue",
    "es": "Ingresos",
    "fr": "Revenu",
    "zh": "收入",
    "ar": "الإيرادات",
    "hi": "राजस्व",
    "pa": "ਆਮਦਨ",
    "tl": "Kita",
    "it": "Entrate",
    "de": "Umsatz",
    "pt": "Receita",
    "fa": "درآمد",
    "uk": "Дохід",
    "pl": "Przychody",
    "vi": "Doanh thu",
    "ko": "수익",
    "ja": "収益",
    "he": "הכנסות",
    "ur": "آمدنی",
    "ru": "Доход",
    "el": "Έσοδα",
    "ro": "Venit",
    "nl": "Omzet",
    "hu": "Bevétel",
    "cs": "Výnosy",
    "sv": "Intäkter",
    "fi": "Tulot",
    "tr": "Gelir",
    "da": "Omsætning",
    "no": "Inntekter",
    "cr": "ᑭᒋ ᐱᒥᐯᐦᐄᑫᐎᓇ"
}

def add_chart_labels():
    """Add charts.revenueLabel to all dashboard.json files"""

    base_dir = Path(__file__).parent.parent / "src" / "i18n" / "locales"

    for lang_code, translation in REVENUE_TRANSLATIONS.items():
        dashboard_file = base_dir / lang_code / "dashboard.json"

        if not dashboard_file.exists():
            print(f"⚠️  Skipping {lang_code} - dashboard.json not found")
            continue

        try:
            # Read existing file
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add charts section if it doesn't exist
            if 'charts' not in data:
                data['charts'] = {}

            # Add revenueLabel
            data['charts']['revenueLabel'] = translation

            # Write back with pretty formatting
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')

            print(f"✅ Updated {lang_code}/dashboard.json")

        except Exception as e:
            print(f"❌ Error processing {lang_code}: {e}")

    print(f"\n{'='*80}")
    print(f"Chart label propagation complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    add_chart_labels()
