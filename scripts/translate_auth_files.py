#!/usr/bin/env python3
"""
Auto-translate all [TRANSLATE] marked strings in auth.json files
Uses the backend translation service
"""
import asyncio
import json
import os
import sys
from pathlib import Path
import asyncpg
import redis.asyncio as redis

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'Backend'))

from services.translation_service import TranslationService

# Language codes
LANGUAGES = [
    'ar', 'bn', 'cr', 'de', 'es', 'fa', 'fr', 'gu', 'he', 'hi',
    'it', 'iu', 'ja', 'ko', 'nl', 'pa', 'pl', 'pt', 'ro', 'ru',
    'so', 'ta', 'tl', 'uk', 'ur', 'vi', 'yue', 'zh'
]

async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )

async def get_redis_client():
    try:
        client = await redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            encoding="utf-8",
            decode_responses=True
        )
        await client.ping()
        return client
    except:
        return None

async def translate_dict(data, lang_code, service, path=""):
    """Recursively translate all [TRANSLATE] marked strings"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                result[key] = await translate_dict(value, lang_code, service, current_path)
            elif isinstance(value, str) and value.startswith("[TRANSLATE] "):
                # Extract English text
                english_text = value.replace("[TRANSLATE] ", "")
                
                # Translate
                translation_result = await service.translate_single(
                    text=english_text,
                    target_language=lang_code,
                    source_language='en',
                    context=f'Authentication/Address management - {current_path}',
                    namespace='auth',
                    use_cache=True
                )
                
                translated_text = translation_result.get('translated_text', english_text)
                result[key] = translated_text
                
                cache_status = "💾" if translation_result.get('cache_hit') else "🆕"
                print(f"  {cache_status} {current_path}: {english_text[:40]}... → {translated_text[:40]}...")
            else:
                result[key] = value
        return result
    return data

async def main():
    print("=" * 80)
    print("AUTO-TRANSLATE AUTH.JSON FILES")
    print("=" * 80)
    print(f"\nTranslating {len(LANGUAGES)} languages\n")
    
    # Initialize services
    db_conn = await get_db_connection()
    redis_client = await get_redis_client()
    service = TranslationService(db_conn, redis_client)
    
    locales_dir = Path(__file__).parent.parent / 'src' / 'Frontend' / 'ai-admin-dashboard' / 'src' / 'i18n' / 'locales'
    
    translated_count = 0
    total_count = 0
    
    for lang in LANGUAGES:
        print(f"\n{'=' * 80}")
        print(f"Translating {lang.upper()}")
        print(f"{'=' * 80}")
        
        auth_file = locales_dir / lang / 'auth.json'
        
        if not auth_file.exists():
            print(f"⚠️  Skipping - file not found")
            continue
        
        # Load file
        with open(auth_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count [TRANSLATE] markers
        json_str = json.dumps(data)
        to_translate = json_str.count('[TRANSLATE]')
        total_count += to_translate
        
        if to_translate == 0:
            print(f"✓ Already complete")
            continue
        
        print(f"Found {to_translate} strings to translate")
        
        # Translate
        translated_data = await translate_dict(data, lang, service)
        
        # Save
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        
        translated_count += to_translate
        print(f"\n✅ Saved {lang}/auth.json")
    
    # Close connections
    await db_conn.close()
    if redis_client:
        await redis_client.close()
    
    print("\n" + "=" * 80)
    print("✅ TRANSLATION COMPLETE!")
    print("=" * 80)
    print(f"Translated {translated_count} strings across {len(LANGUAGES)} languages")

if __name__ == '__main__':
    asyncio.run(main())
