#!/usr/bin/env python3
"""
Multilingual Database Setup
Pre-translates product data for offline multilingual support
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
import asyncpg
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    PORTUGUESE = "pt"
    GERMAN = "de"
    ITALIAN = "it"
    RUSSIAN = "ru"

@dataclass
class TranslationCache:
    """Cache for common cannabis terms"""
    
    # Cannabis-specific translations
    CANNABIS_TERMS = {
        "Flower": {
            Language.SPANISH: "Flor",
            Language.FRENCH: "Fleur",
            Language.CHINESE: "大麻花",
            Language.JAPANESE: "フラワー",
            Language.KOREAN: "꽃",
            Language.PORTUGUESE: "Flor",
            Language.GERMAN: "Blüte",
            Language.ITALIAN: "Fiore",
            Language.RUSSIAN: "Цветок"
        },
        "Pre-Roll": {
            Language.SPANISH: "Pre-enrollado",
            Language.FRENCH: "Pré-roulé",
            Language.CHINESE: "预卷烟",
            Language.JAPANESE: "プリロール",
            Language.KOREAN: "프리롤",
            Language.PORTUGUESE: "Pré-enrolado",
            Language.GERMAN: "Vorgerollt",
            Language.ITALIAN: "Pre-rollato",
            Language.RUSSIAN: "Предварительно скрученный"
        },
        "Edibles": {
            Language.SPANISH: "Comestibles",
            Language.FRENCH: "Comestibles",
            Language.CHINESE: "食用品",
            Language.JAPANESE: "エディブル",
            Language.KOREAN: "식용품",
            Language.PORTUGUESE: "Comestíveis",
            Language.GERMAN: "Essbare",
            Language.ITALIAN: "Commestibili",
            Language.RUSSIAN: "Съедобные"
        },
        "Vapes": {
            Language.SPANISH: "Vaporizadores",
            Language.FRENCH: "Vaporisateurs",
            Language.CHINESE: "电子烟",
            Language.JAPANESE: "ベイプ",
            Language.KOREAN: "베이프",
            Language.PORTUGUESE: "Vaporizadores",
            Language.GERMAN: "Verdampfer",
            Language.ITALIAN: "Vaporizzatori",
            Language.RUSSIAN: "Вейпы"
        },
        "Extracts": {
            Language.SPANISH: "Extractos",
            Language.FRENCH: "Extraits",
            Language.CHINESE: "提取物",
            Language.JAPANESE: "エキストラクト",
            Language.KOREAN: "추출물",
            Language.PORTUGUESE: "Extratos",
            Language.GERMAN: "Extrakte",
            Language.ITALIAN: "Estratti",
            Language.RUSSIAN: "Экстракты"
        },
        "Shatter": {
            Language.SPANISH: "Fragmento",
            Language.FRENCH: "Éclat",
            Language.CHINESE: "碎片",
            Language.JAPANESE: "シャッター",
            Language.KOREAN: "샤터",
            Language.PORTUGUESE: "Estilhaço",
            Language.GERMAN: "Splitter",
            Language.ITALIAN: "Frantumi",
            Language.RUSSIAN: "Осколок"
        },
        "Wax": {
            Language.SPANISH: "Cera",
            Language.FRENCH: "Cire",
            Language.CHINESE: "蜡",
            Language.JAPANESE: "ワックス",
            Language.KOREAN: "왁스",
            Language.PORTUGUESE: "Cera",
            Language.GERMAN: "Wachs",
            Language.ITALIAN: "Cera",
            Language.RUSSIAN: "Воск"
        },
        "Oil": {
            Language.SPANISH: "Aceite",
            Language.FRENCH: "Huile",
            Language.CHINESE: "油",
            Language.JAPANESE: "オイル",
            Language.KOREAN: "오일",
            Language.PORTUGUESE: "Óleo",
            Language.GERMAN: "Öl",
            Language.ITALIAN: "Olio",
            Language.RUSSIAN: "Масло"
        },
        "Tincture": {
            Language.SPANISH: "Tintura",
            Language.FRENCH: "Teinture",
            Language.CHINESE: "酊剂",
            Language.JAPANESE: "チンキ",
            Language.KOREAN: "팅크처",
            Language.PORTUGUESE: "Tintura",
            Language.GERMAN: "Tinktur",
            Language.ITALIAN: "Tintura",
            Language.RUSSIAN: "Настойка"
        },
        "Capsules": {
            Language.SPANISH: "Cápsulas",
            Language.FRENCH: "Capsules",
            Language.CHINESE: "胶囊",
            Language.JAPANESE: "カプセル",
            Language.KOREAN: "캡슐",
            Language.PORTUGUESE: "Cápsulas",
            Language.GERMAN: "Kapseln",
            Language.ITALIAN: "Capsule",
            Language.RUSSIAN: "Капсулы"
        },
        "Topicals": {
            Language.SPANISH: "Tópicos",
            Language.FRENCH: "Topiques",
            Language.CHINESE: "外用药",
            Language.JAPANESE: "トピカル",
            Language.KOREAN: "국소용",
            Language.PORTUGUESE: "Tópicos",
            Language.GERMAN: "Topische",
            Language.ITALIAN: "Topici",
            Language.RUSSIAN: "Местные"
        }
    }
    
    # Strain type translations
    STRAIN_TYPES = {
        "Sativa": {
            Language.SPANISH: "Sativa",
            Language.FRENCH: "Sativa",
            Language.CHINESE: "萨蒂瓦",
            Language.JAPANESE: "サティバ",
            Language.KOREAN: "사티바",
            Language.PORTUGUESE: "Sativa",
            Language.GERMAN: "Sativa",
            Language.ITALIAN: "Sativa",
            Language.RUSSIAN: "Сатива"
        },
        "Indica": {
            Language.SPANISH: "Índica",
            Language.FRENCH: "Indica",
            Language.CHINESE: "印度大麻",
            Language.JAPANESE: "インディカ",
            Language.KOREAN: "인디카",
            Language.PORTUGUESE: "Índica",
            Language.GERMAN: "Indica",
            Language.ITALIAN: "Indica",
            Language.RUSSIAN: "Индика"
        },
        "Hybrid": {
            Language.SPANISH: "Híbrido",
            Language.FRENCH: "Hybride",
            Language.CHINESE: "混合",
            Language.JAPANESE: "ハイブリッド",
            Language.KOREAN: "하이브리드",
            Language.PORTUGUESE: "Híbrido",
            Language.GERMAN: "Hybrid",
            Language.ITALIAN: "Ibrido",
            Language.RUSSIAN: "Гибрид"
        }
    }
    
    # Common descriptors
    DESCRIPTORS = {
        "High THC": {
            Language.SPANISH: "Alto THC",
            Language.FRENCH: "THC élevé",
            Language.CHINESE: "高THC",
            Language.JAPANESE: "高THC",
            Language.KOREAN: "높은 THC",
            Language.PORTUGUESE: "Alto THC",
            Language.GERMAN: "Hoher THC",
            Language.ITALIAN: "Alto THC",
            Language.RUSSIAN: "Высокий THC"
        },
        "CBD Rich": {
            Language.SPANISH: "Rico en CBD",
            Language.FRENCH: "Riche en CBD",
            Language.CHINESE: "富含CBD",
            Language.JAPANESE: "CBD豊富",
            Language.KOREAN: "CBD 풍부",
            Language.PORTUGUESE: "Rico em CBD",
            Language.GERMAN: "CBD-reich",
            Language.ITALIAN: "Ricco di CBD",
            Language.RUSSIAN: "Богат CBD"
        }
    }


class ProductTranslator:
    """Handles product translation for offline multilingual support"""
    
    def __init__(self):
        self.cache = TranslationCache()
    
    def translate_product_name(self, name: str, target_language: Language) -> str:
        """
        Translate product name using cached translations and patterns
        """
        if target_language == Language.ENGLISH:
            return name
        
        # Check if it's a known cannabis term
        for term, translations in self.cache.CANNABIS_TERMS.items():
            if term.lower() in name.lower():
                if target_language in translations:
                    # Replace the term with translation
                    translated_term = translations[target_language]
                    return name.replace(term, translated_term)
        
        # Check strain types
        for strain, translations in self.cache.STRAIN_TYPES.items():
            if strain.lower() in name.lower():
                if target_language in translations:
                    translated_strain = translations[target_language]
                    return name.replace(strain, translated_strain)
        
        # If no translation found, return original with language marker
        return name
    
    def translate_category(self, category: str, target_language: Language) -> str:
        """Translate category name"""
        if target_language == Language.ENGLISH:
            return category
        
        if category in self.cache.CANNABIS_TERMS:
            translations = self.cache.CANNABIS_TERMS[category]
            return translations.get(target_language, category)
        
        return category
    
    def translate_description(self, description: str, target_language: Language) -> str:
        """
        Translate product description using pattern replacement
        """
        if not description or target_language == Language.ENGLISH:
            return description
        
        translated = description
        
        # Replace known terms
        for term, translations in self.cache.CANNABIS_TERMS.items():
            if term.lower() in translated.lower() and target_language in translations:
                translated = translated.replace(term, translations[target_language])
        
        for strain, translations in self.cache.STRAIN_TYPES.items():
            if strain.lower() in translated.lower() and target_language in translations:
                translated = translated.replace(strain, translations[target_language])
        
        for descriptor, translations in self.cache.DESCRIPTORS.items():
            if descriptor.lower() in translated.lower() and target_language in translations:
                translated = translated.replace(descriptor, translations[target_language])
        
        return translated
    
    def generate_translations(self, product: Dict) -> Dict:
        """
        Generate all translations for a product
        Returns JSONB-ready dictionary
        """
        name_translations = {}
        category_translations = {}
        description_translations = {}
        
        for language in Language:
            if language == Language.ENGLISH:
                continue
            
            # Translate each field
            name_translations[language.value] = self.translate_product_name(
                product.get('product_name', ''), language
            )
            
            category_translations[language.value] = self.translate_category(
                product.get('category', ''), language
            )
            
            if product.get('description'):
                description_translations[language.value] = self.translate_description(
                    product['description'], language
                )
        
        return {
            'name_translations': name_translations,
            'category_translations': category_translations,
            'description_translations': description_translations
        }


async def setup_multilingual_schema(conn):
    """Add multilingual columns to products table"""
    
    schema_sql = """
    -- Add translation columns if they don't exist
    ALTER TABLE products 
    ADD COLUMN IF NOT EXISTS name_translations JSONB DEFAULT '{}';
    
    ALTER TABLE products 
    ADD COLUMN IF NOT EXISTS category_translations JSONB DEFAULT '{}';
    
    ALTER TABLE products 
    ADD COLUMN IF NOT EXISTS description_translations JSONB DEFAULT '{}';
    
    ALTER TABLE products 
    ADD COLUMN IF NOT EXISTS sub_category_translations JSONB DEFAULT '{}';
    
    -- Create indexes for fast language-specific lookups
    CREATE INDEX IF NOT EXISTS idx_products_name_translations 
    ON products USING GIN (name_translations);
    
    CREATE INDEX IF NOT EXISTS idx_products_category_translations 
    ON products USING GIN (category_translations);
    
    -- Add language preference to customers table
    ALTER TABLE customers 
    ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(2) DEFAULT 'en';
    
    -- Create language usage tracking table
    CREATE TABLE IF NOT EXISTS language_usage (
        id SERIAL PRIMARY KEY,
        customer_id VARCHAR(255),
        session_id VARCHAR(255),
        language_code VARCHAR(2),
        detection_method VARCHAR(50),
        confidence FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_language_usage_customer 
    ON language_usage(customer_id, language_code);
    """
    
    try:
        await conn.execute(schema_sql)
        logger.info("✅ Multilingual schema created successfully")
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        raise


async def translate_existing_products(conn):
    """Translate all existing products in the database"""
    
    translator = ProductTranslator()
    
    # Fetch all products
    products = await conn.fetch("""
        SELECT product_id, product_name, category, sub_category, description
        FROM products
        WHERE name_translations IS NULL OR name_translations = '{}'
        LIMIT 1000
    """)
    
    logger.info(f"Found {len(products)} products to translate")
    
    # Translate each product
    for product in products:
        translations = translator.generate_translations(dict(product))
        
        # Update database with translations
        await conn.execute("""
            UPDATE products
            SET 
                name_translations = $1,
                category_translations = $2,
                description_translations = $3
            WHERE product_id = $4
        """, 
            json.dumps(translations['name_translations']),
            json.dumps(translations['category_translations']),
            json.dumps(translations['description_translations']),
            product['product_id']
        )
    
    logger.info(f"✅ Translated {len(products)} products")


async def demonstrate_multilingual_search(conn):
    """Demonstrate multilingual product search"""
    
    # Example: Search for "flor" (Spanish for flower)
    spanish_results = await conn.fetch("""
        SELECT product_name, category, 
               name_translations->>'es' as spanish_name,
               category_translations->>'es' as spanish_category
        FROM products
        WHERE category = 'Flower'
        LIMIT 5
    """)
    
    print("\n🌍 Multilingual Search Demo:")
    print("\nSpanish Results for 'Flower' category:")
    for product in spanish_results:
        print(f"  EN: {product['product_name']} ({product['category']})")
        print(f"  ES: {product['spanish_name']} ({product['spanish_category']})")
        print()
    
    # Example: Search in Chinese
    chinese_results = await conn.fetch("""
        SELECT product_name,
               name_translations->>'zh' as chinese_name,
               category_translations->>'zh' as chinese_category
        FROM products
        WHERE category = 'Edibles'
        LIMIT 3
    """)
    
    print("\nChinese Results for 'Edibles' category:")
    for product in chinese_results:
        print(f"  EN: {product['product_name']}")
        print(f"  ZH: {product['chinese_name']} ({product['chinese_category']})")
        print()


async def main():
    """Main setup function"""
    
    # Database connection
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='weedgo',
        password='your_password_here',
        database='ai_engine'
    )
    
    try:
        # Step 1: Setup schema
        await setup_multilingual_schema(conn)
        
        # Step 2: Translate existing products
        await translate_existing_products(conn)
        
        # Step 3: Demonstrate search
        await demonstrate_multilingual_search(conn)
        
        print("\n✅ Multilingual database setup complete!")
        print("\n📝 Key Features Implemented:")
        print("  • Pre-translated product names, categories, descriptions")
        print("  • JSONB storage for instant language switching")
        print("  • Zero-latency offline translation")
        print("  • Support for 10 languages")
        print("  • Cannabis-specific terminology")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())