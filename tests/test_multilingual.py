"""
Test script for multilingual AI engine
Tests all 6 languages: English, Spanish, French, Portuguese, Chinese, Arabic
"""

import asyncio
import asyncpg
import json
from services.smart_multilingual_engine import SmartMultilingualEngine

# Test messages in different languages
TEST_MESSAGES = {
    'en': [
        "What do you have?",
        "Show me sativa strains",
        "I want something relaxing",
        "Do you have Pink Kush?"
    ],
    'es': [
        "¿Qué tienes?",
        "Muéstrame cepas sativa",
        "Quiero algo relajante",
        "¿Tienes Pink Kush?"
    ],
    'fr': [
        "Qu'est-ce que vous avez?",
        "Montrez-moi les variétés sativa",
        "Je veux quelque chose de relaxant",
        "Avez-vous Pink Kush?"
    ],
    'pt': [
        "O que você tem?",
        "Mostre-me cepas sativa",
        "Quero algo relaxante",
        "Você tem Pink Kush?"
    ],
    'zh': [
        "你们有什么？",
        "给我看看sativa品种",
        "我想要一些放松的东西",
        "你们有Pink Kush吗？"
    ],
    'ar': [
        "ماذا لديك؟",
        "أرني سلالات ساتيفا",
        "أريد شيئا مريحا",
        "هل لديك Pink Kush؟"
    ]
}

async def test_language(engine: SmartMultilingualEngine, language: str, messages: list):
    """Test a specific language"""
    print(f"\n{'='*60}")
    print(f"Testing {language.upper()} Language")
    print('='*60)
    
    session_id = f"test-{language}-session"
    customer_id = f"test-{language}-customer"
    
    for i, message in enumerate(messages, 1):
        print(f"\n[Test {i}] Input: {message}")
        
        try:
            # Process message
            response = await engine.process_message(
                message=message,
                session_id=session_id,
                customer_id=customer_id,
                preferred_language=language
            )
            
            # Display results
            print(f"Response: {response['message']}")
            print(f"Language: {response.get('detected_language', 'unknown')}")
            print(f"Quality Score: {response.get('quality_score', 0):.2f}")
            print(f"Processing Time: {response.get('processing_time_ms', 0)}ms")
            
            if response.get('products'):
                print(f"Products Found: {len(response['products'])}")
                for product in response['products'][:2]:
                    print(f"  - {product.get('product_name', 'Unknown')}")
            
            if response.get('translation_used'):
                print("  [Translation was used]")
            
            if response.get('fallback'):
                print("  [Fallback strategy applied]")
                
        except Exception as e:
            print(f"ERROR: {e}")
        
        # Small delay between tests
        await asyncio.sleep(0.5)

async def test_cross_language_conversation():
    """Test conversation with language switching"""
    print(f"\n{'='*60}")
    print("Testing Cross-Language Conversation")
    print('='*60)
    
    # Create engine
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    engine = SmartMultilingualEngine(db_pool)
    await engine.initialize()
    
    session_id = "test-multilingual-session"
    customer_id = "test-multilingual-customer"
    
    # Conversation mixing languages
    conversation = [
        ("Hello, what do you have?", "en"),
        ("Quiero algo para relajarme", "es"),  # Spanish: I want something to relax
        ("Montrez-moi vos meilleures fleurs", "fr"),  # French: Show me your best flowers
        ("你们有食用品吗？", "zh"),  # Chinese: Do you have edibles?
        ("Back to English, add Pink Kush to cart", "en")
    ]
    
    for message, expected_lang in conversation:
        print(f"\n[{expected_lang}] User: {message}")
        
        response = await engine.process_message(
            message=message,
            session_id=session_id,
            customer_id=customer_id
        )
        
        print(f"[{response.get('detected_language', '??')}] Bot: {response['message'][:200]}...")
        print(f"Quality: {response.get('quality_score', 0):.2f}")
    
    await db_pool.close()

async def test_product_translation():
    """Test product information translation"""
    print(f"\n{'='*60}")
    print("Testing Product Translation")
    print('='*60)
    
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    engine = SmartMultilingualEngine(db_pool)
    
    # Test product in different languages
    test_product = {
        'id': 1,
        'product_name': 'Pink Kush',
        'description': 'A potent indica strain known for its relaxing effects',
        'effects': ['relaxing', 'euphoric', 'sleepy'],
        'price': 45.00,
        'size': '3.5g'
    }
    
    languages = ['es', 'fr', 'zh', 'ar']
    
    for lang in languages:
        print(f"\n[{lang.upper()}] Translating product...")
        
        translated = await engine.multilingual.translate_products(
            [test_product], lang
        )
        
        if translated:
            product = translated[0]
            print(f"Name: {product['product_name']}")
            print(f"Description: {product.get('description', 'N/A')[:100]}...")
            print(f"Effects: {product.get('effects', [])}")
    
    await db_pool.close()

async def main():
    """Main test function"""
    
    # Setup database connection
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    # Create engine
    engine = SmartMultilingualEngine(db_pool)
    await engine.initialize()
    
    # Test each language
    for language, messages in TEST_MESSAGES.items():
        await test_language(engine, language, messages)
    
    # Get analytics
    print(f"\n{'='*60}")
    print("Language Analytics")
    print('='*60)
    
    analytics = await engine.get_language_analytics()
    
    print("\nLanguage Distribution:")
    for lang in analytics['language_distribution']:
        print(f"  {lang['message_language']}: {lang['count']} messages")
    
    print("\nToday's Metrics:")
    for metric in analytics['today_metrics']:
        print(f"  {metric['language_code']}: {metric['total_requests']} requests, "
              f"Quality: {metric['avg_quality_score']:.2f}")
    
    print("\nCache Statistics:")
    print(f"  Cache Size: {analytics['cache_stats']['size']}")
    print(f"  Cached Languages: {', '.join(analytics['cache_stats']['languages'])}")
    
    # Cleanup
    await db_pool.close()
    
    # Run additional tests
    await test_cross_language_conversation()
    await test_product_translation()

if __name__ == "__main__":
    asyncio.run(main())