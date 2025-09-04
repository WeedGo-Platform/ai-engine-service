#!/usr/bin/env python3
"""
Test Domain Switching
Demonstrates the domain-agnostic AI engine with multiple domains
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.ai_engine import DomainAgnosticAIEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_domain_switching():
    """Test switching between different domains"""
    
    # Initialize AI Engine
    engine = DomainAgnosticAIEngine()
    await engine.initialize()
    
    print("\n" + "="*60)
    print("🤖 DOMAIN-AGNOSTIC AI ENGINE DEMONSTRATION")
    print("="*60)
    
    # List available domains
    print("\n📚 Available Domains:")
    domains = engine.list_domains()
    for domain in domains:
        print(f"  • {domain['name']}: {domain['display_name']}")
        print(f"    {domain['description']}")
        print(f"    Languages: {', '.join(domain['languages'][:5])}...")
        print(f"    Tasks: {', '.join(domain['tasks'])}")
        print()
    
    # Test Budtender Domain
    print("\n" + "-"*60)
    print("🌿 TESTING BUDTENDER DOMAIN")
    print("-"*60)
    
    # Switch to budtender
    result = await engine.switch_domain("budtender")
    print(f"✓ Switched to: {result['display_name']}")
    
    # Test queries
    budtender_queries = [
        "Hello, I'm new to cannabis",
        "I need something for chronic pain",
        "What's the difference between THC and CBD?",
        "Recommend something for sleep"
    ]
    
    for query in budtender_queries:
        print(f"\n👤 User: {query}")
        response = await engine.process(
            message=query,
            session_id="test_session_1"
        )
        print(f"🤖 Budtender: {response.get('message', response)[:200]}...")
        if response.get('disclaimer'):
            print(f"⚠️  {response['disclaimer']}")
    
    # Test Healthcare Domain
    print("\n" + "-"*60)
    print("⚕️ TESTING HEALTHCARE DOMAIN")
    print("-"*60)
    
    # Switch to healthcare
    result = await engine.switch_domain("healthcare")
    if result['success']:
        print(f"✓ Switched to: {result['display_name']}")
        
        healthcare_queries = [
            "Hello, I have some health questions",
            "What are common symptoms of flu?",
            "How can I improve my sleep?",
            "I have persistent headaches"
        ]
        
        for query in healthcare_queries:
            print(f"\n👤 User: {query}")
            response = await engine.process(
                message=query,
                session_id="test_session_2"
            )
            print(f"👨‍⚕️ Healthcare: {response.get('message', response)[:200]}...")
            if response.get('disclaimer'):
                print(f"⚠️  {response['disclaimer']}")
    else:
        print(f"⚠️ Healthcare domain not available: {result.get('error')}")
    
    # Test Multi-language Support
    print("\n" + "-"*60)
    print("🌍 TESTING MULTILINGUAL SUPPORT")
    print("-"*60)
    
    # Switch back to budtender
    await engine.switch_domain("budtender")
    
    multilingual_queries = [
        ("Hola, necesito algo para el dolor", "es"),
        ("Bonjour, je cherche quelque chose pour dormir", "fr"),
        ("你好，我需要一些放松的东西", "zh"),
        ("Olá, preciso de algo para ansiedade", "pt")
    ]
    
    for query, lang in multilingual_queries:
        print(f"\n👤 User ({lang}): {query}")
        response = await engine.process(
            message=query,
            session_id=f"test_session_{lang}",
            metadata={"language": lang}
        )
        print(f"🤖 Response: {response.get('message', response)[:150]}...")
    
    # Test Domain Capabilities
    print("\n" + "-"*60)
    print("🔧 DOMAIN CAPABILITIES")
    print("-"*60)
    
    for domain_name in ["budtender", "healthcare"]:
        if domain_name in [d['name'] for d in domains]:
            print(f"\n{domain_name.upper()} Tools:")
            tools = await engine.get_tools(domain_name)
            for tool in tools:
                print(f"  • {tool['name']}: {tool['description']}")
    
    # Test Knowledge Search
    print("\n" + "-"*60)
    print("🔍 KNOWLEDGE BASE SEARCH")
    print("-"*60)
    
    search_queries = [
        ("Blue Dream", "budtender"),
        ("headache", "healthcare")
    ]
    
    for query, domain in search_queries:
        if domain in [d['name'] for d in domains]:
            print(f"\nSearching '{query}' in {domain} knowledge base:")
            results = await engine.search_knowledge(query, domain, limit=3)
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result}")
    
    # Test Session Context
    print("\n" + "-"*60)
    print("💬 SESSION CONTEXT TEST")
    print("-"*60)
    
    await engine.switch_domain("budtender")
    
    session_queries = [
        "I'm looking for something energizing",
        "But not too strong",
        "And preferably organic",
        "What do you recommend?"
    ]
    
    print("\nConversation with context:")
    for query in session_queries:
        print(f"👤: {query}")
        response = await engine.process(
            message=query,
            session_id="context_test"
        )
        print(f"🤖: {response.get('message', response)[:150]}...")
    
    # Summary
    print("\n" + "="*60)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("  ✓ Domain switching (budtender ↔ healthcare)")
    print("  ✓ Domain-specific responses and validations")
    print("  ✓ Multilingual support")
    print("  ✓ Knowledge base search")
    print("  ✓ Session context management")
    print("  ✓ Domain-specific tools and capabilities")
    print("\nThe AI Engine can easily be extended with new domains")
    print("by adding domain plugins without modifying core code!")
    
    # Cleanup
    await engine.cleanup()

async def main():
    """Main entry point"""
    try:
        await test_domain_switching()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())