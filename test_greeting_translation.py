#!/usr/bin/env python3
"""
Quick test script to verify greeting translation works for the sales chat widget
"""

import asyncio
import aiohttp
import json

# The greeting message from SalesChatWidget.tsx
DEFAULT_GREETING = """Hi! I'm Carlos, your WeedGo sales assistant. 👋

I'm here to help you discover how WeedGo can transform your cannabis retail business. Whether you're curious about pricing, features, or just getting started - I'm here to answer any questions.

What would you like to know about WeedGo?"""

async def test_translation(target_language: str, language_name: str):
    """Test translating the greeting to a specific language"""
    url = "http://localhost:5024/api/translate/"
    
    payload = {
        "text": DEFAULT_GREETING,
        "target_language": target_language,
        "source_language": "en",
        "context": "sales_chat_greeting",
        "namespace": "sales_widget",
        "use_cache": True
    }
    
    print(f"\n{'='*80}")
    print(f"Testing {language_name} ({target_language}) translation...")
    print(f"{'='*80}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"\n✅ Success!")
                    print(f"   Cache Hit: {result.get('cache_hit', False)}")
                    print(f"   Source: {result.get('source', 'unknown')}")
                    print(f"\n📝 Original (English):")
                    print(f"   {DEFAULT_GREETING[:80]}...")
                    print(f"\n🌍 Translated ({language_name}):")
                    translated = result.get('translated', '')
                    # Show first 200 chars
                    print(f"   {translated[:200]}...")
                    
                    return True
                else:
                    print(f"\n❌ Error: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"\n❌ Exception: {type(e).__name__}")
        print(f"   {str(e)}")
        return False

async def main():
    """Run translation tests for multiple languages"""
    
    print("\n" + "="*80)
    print("MULTILINGUAL GREETING TRANSLATION TEST")
    print("Testing the sales chat widget greeting translation")
    print("="*80)
    
    # Test languages that the widget might encounter
    test_languages = [
        ('en', 'English'),         # Baseline (should skip translation)
        ('zh', 'Chinese'),         # Simplified Chinese
        ('es', 'Spanish'),         # Spanish
        ('fr', 'French'),          # French
        ('de', 'German'),          # German
        ('ja', 'Japanese'),        # Japanese
        ('ko', 'Korean'),          # Korean
        ('ar', 'Arabic'),          # Arabic (RTL language)
        ('pt', 'Portuguese'),      # Portuguese
        ('ru', 'Russian'),         # Russian (Cyrillic)
    ]
    
    results = []
    
    for lang_code, lang_name in test_languages:
        success = await test_translation(lang_code, lang_name)
        results.append((lang_name, success))
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    for lang_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {lang_name}")
    
    print(f"\n   Total: {total} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All translations working! The sales chat widget will greet users in their language.")
    else:
        print(f"\n⚠️  {failed} translation(s) failed. Check server logs for details.")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
