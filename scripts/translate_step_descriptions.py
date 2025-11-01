#!/usr/bin/env python3
"""Translate step descriptions for Ontario licensing across all languages"""

import json
import os

STEP_DESCRIPTIONS = {
    "ar": "التحقق من تراخيص بيع القنب بالتجزئة في أونتاريو (CROL و CRSA)",
    "bn": "আপনার অন্টারিও ক্যানাবিস খুচরা লাইসেন্স যাচাই করুন (CROL এবং CRSA)",
    "cr": "kwayaskîtam ki Ontario askîhkâna atâwêwin oyôhkêmakana (CROL êkwa CRSA)",
    "de": "Validieren Sie Ihre Ontario Cannabis-Einzelhandelslizenzen (CROL und CRSA)",
    "en": "Validate your Ontario cannabis retail licenses (CROL and CRSA)",
    "es": "Valide sus licencias minoristas de cannabis de Ontario (CROL y CRSA)",
    "fa": "مجوزهای خرده‌فروشی شاهدانه انتاریو خود را اعتبارسنجی کنید (CROL و CRSA)",
    "fr": "Validez vos licences de vente au détail de cannabis de l'Ontario (CROL et CRSA)",
    "gu": "તમારા ઑન્ટારિયો કેનાબીસ રિટેલ લાઇસન્સ માન્ય કરો (CROL અને CRSA)",
    "he": "אמת את רישיונות הקמעונאות קנאביס באונטריו שלך (CROL ו-CRSA)",
    "hi": "अपने ओंटारियो कैनबिस खुदरा लाइसेंस को मान्य करें (CROL और CRSA)",
    "it": "Convalida le tue licenze al dettaglio di cannabis dell'Ontario (CROL e CRSA)",
    "iu": "kwayaskîtam ki Ontario Cannabis atâwêwin oyôhkêmakana (CROL êkwa CRSA)",
    "ja": "オンタリオの大麻小売ライセンスを検証（CROLおよびCRSA）",
    "ko": "온타리오 대마초 소매 라이센스 검증 (CROL 및 CRSA)",
    "nl": "Valideer uw Ontario cannabis detailhandelslicenties (CROL en CRSA)",
    "pa": "ਆਪਣੇ ਓਨਟਾਰੀਓ ਕੈਨਾਬਿਸ ਰਿਟੇਲ ਲਾਇਸੰਸ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ (CROL ਅਤੇ CRSA)",
    "pl": "Zweryfikuj swoje licencje detaliczne na sprzedaż konopi w Ontario (CROL i CRSA)",
    "pt": "Valide suas licenças de varejo de cannabis de Ontário (CROL e CRSA)",
    "ro": "Validați licențele dvs. de vânzare cu amănuntul de canabis din Ontario (CROL și CRSA)",
    "ru": "Подтвердите свои лицензии на розничную продажу каннабиса в Онтарио (CROL и CRSA)",
    "so": "Xaqiiji shatiyada tafaariiqda cannabis ee Ontario (CROL iyo CRSA)",
    "ta": "உங்கள் ஒன்டாரியோ கன்னாபிஸ் சில்லறை உரிமங்களை சரிபார்க்கவும் (CROL மற்றும் CRSA)",
    "tl": "I-validate ang iyong mga lisensya ng cannabis retail sa Ontario (CROL at CRSA)",
    "uk": "Підтвердіть свої ліцензії на роздрібну торгівлю канабісом в Онтаріо (CROL та CRSA)",
    "ur": "اپنے اونٹاریو کینابس ریٹیل لائسنس کی تصدیق کریں (CROL اور CRSA)",
    "vi": "Xác thực giấy phép bán lẻ cần sa Ontario của bạn (CROL và CRSA)",
    "yue": "驗證你嘅安大略省大麻零售牌照（CROL同CRSA）",
    "zh": "验证您的安大略省大麻零售许可证（CROL和CRSA）"
}

def update_step_description(lang_code, translation):
    """Update stepDescriptions.ontario in signup.json"""
    file_path = f"src/Frontend/ai-admin-dashboard/src/i18n/locales/{lang_code}/signup.json"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'tenant' in data and 'stepDescriptions' in data['tenant']:
            data['tenant']['stepDescriptions']['ontario'] = translation
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Updated {lang_code}")
            return True
        else:
            print(f"✗ Missing stepDescriptions in {lang_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error updating {lang_code}: {e}")
        return False

def main():
    print("=" * 80)
    print("TRANSLATING ONTARIO STEP DESCRIPTIONS")
    print("=" * 80)
    
    completed = 0
    for lang_code, translation in STEP_DESCRIPTIONS.items():
        if update_step_description(lang_code, translation):
            completed += 1
    
    print("=" * 80)
    print(f"✅ COMPLETE! Updated {completed}/{len(STEP_DESCRIPTIONS)} languages")
    print("=" * 80)

if __name__ == "__main__":
    main()
