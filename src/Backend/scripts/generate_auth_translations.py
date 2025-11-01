#!/usr/bin/env python3
"""
Generate translations for auth/signup flow across all 28 supported languages
"""
import asyncio
import json
import os
import sys
import asyncpg
import redis.asyncio as redis
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.translation_service import TranslationService

# 28 supported languages for Canada
SUPPORTED_LANGUAGES = [
    'ar',  # Arabic
    'bn',  # Bengali
    'cr',  # Cree
    'de',  # German
    'es',  # Spanish
    'fa',  # Persian
    'fr',  # French
    'gu',  # Gujarati
    'he',  # Hebrew
    'hi',  # Hindi
    'it',  # Italian
    'iu',  # Inuktitut
    'ja',  # Japanese
    'ko',  # Korean
    'nl',  # Dutch
    'pa',  # Punjabi
    'pl',  # Polish
    'pt',  # Portuguese
    'ro',  # Romanian
    'ru',  # Russian
    'so',  # Somali
    'ta',  # Tamil
    'tl',  # Tagalog
    'uk',  # Ukrainian
    'ur',  # Urdu
    'vi',  # Vietnamese
    'yue', # Cantonese
    'zh',  # Mandarin
]

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )

async def get_redis_client():
    """Get Redis client"""
    try:
        client = await redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            encoding="utf-8",
            decode_responses=True
        )
        await client.ping()
        return client
    except Exception:
        return None

async def translate_namespace(service: TranslationService, namespace: str, translations: dict, lang_code: str):
    """Translate all strings in a namespace"""
    translated = {}
    
    for key, value in translations.items():
        # Handle nested dictionaries
        if isinstance(value, dict):
            translated[key] = await translate_namespace(service, f"{namespace}.{key}", value, lang_code)
        else:
            # Translate the string
            result = await service.translate_single(
                text=value,
                target_language=lang_code,
                source_language='en',
                context=f'Authentication and signup flow - {namespace}',
                namespace='auth_signup',
                use_cache=True
            )
            translated[key] = result.get('translated_text', value)
            
            # Log progress
            print(f"  [{lang_code}] {namespace}.{key}: {value[:50]}... -> {translated[key][:50]}...")
    
    return translated

async def main():
    """Main translation generation function"""
    print("=" * 80)
    print("AUTH/SIGNUP TRANSLATION GENERATOR")
    print("=" * 80)
    print(f"\nGenerating translations for {len(SUPPORTED_LANGUAGES)} languages\n")
    
    # Load source English keys
    keys_file = Path(__file__).parent.parent / 'data' / 'translations' / 'auth_signup_keys.json'
    with open(keys_file, 'r') as f:
        source_keys = json.load(f)
    
    print(f"Loaded {len(source_keys)} namespaces from {keys_file}")
    
    # Initialize services
    db_conn = await get_db_connection()
    redis_client = await get_redis_client()
    
    translation_service = TranslationService(db_conn, redis_client)
    
    # Output directory
    output_dir = Path(__file__).parent.parent / 'data' / 'translations' / 'generated'
    output_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {output_dir}\n")
    
    # Track statistics
    total_keys = sum(len(v) if isinstance(v, dict) else 1 for v in source_keys.values())
    total_translations = total_keys * len(SUPPORTED_LANGUAGES)
    completed = 0
    
    # Translate for each language
    for lang_code in SUPPORTED_LANGUAGES:
        print(f"\n{'=' * 80}")
        print(f"Translating to {lang_code.upper()}")
        print(f"{'=' * 80}")
        
        lang_translations = {}
        
        # Translate each namespace
        for namespace, translations in source_keys.items():
            print(f"\nNamespace: {namespace}")
            lang_translations[namespace] = await translate_namespace(
                translation_service,
                namespace,
                translations,
                lang_code
            )
            completed += len(translations) if isinstance(translations, dict) else 1
        
        # Save to file
        output_file = output_dir / f'auth_signup_{lang_code}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(lang_translations, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved: {output_file}")
        print(f"Progress: {completed}/{total_translations} ({completed/total_translations*100:.1f}%)")
    
    # Close connections
    await db_conn.close()
    if redis_client:
        await redis_client.close()
    
    print("\n" + "=" * 80)
    print("✅ TRANSLATION GENERATION COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated {len(SUPPORTED_LANGUAGES)} translation files")
    print(f"Total translations: {total_translations}")
    print(f"Output: {output_dir}")

if __name__ == '__main__':
    asyncio.run(main())
