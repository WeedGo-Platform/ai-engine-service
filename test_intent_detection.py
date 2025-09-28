#!/usr/bin/env python3
"""
Test script for V5 Engine Intent Detection System
Tests the fixes applied to intent detection
"""

import sys
import os

# Set working directory to Backend
backend_path = '/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend'
os.chdir(backend_path)
sys.path.append(backend_path)

from services.smart_ai_engine_v5 import SmartAIEngineV5
from services.intent_detector import LLMIntentDetector
import json

def test_intent_detection():
    """Test intent detection with various messages"""

    print("="*50)
    print("V5 Engine Intent Detection Test")
    print("="*50)

    # Initialize V5 engine
    print("\n1. Initializing V5 engine...")
    v5_engine = SmartAIEngineV5()

    # Check if _detecting_intent flag exists
    if hasattr(v5_engine, '_detecting_intent'):
        print("✅ _detecting_intent flag initialized:", v5_engine._detecting_intent)
    else:
        print("❌ _detecting_intent flag not found!")

    # Check if _generate_internal method exists
    if hasattr(v5_engine, '_generate_internal'):
        print("✅ _generate_internal method exists")
    else:
        print("❌ _generate_internal method not found!")

    # Initialize intent detector
    print("\n2. Initializing intent detector...")
    if v5_engine.intent_detector:
        print("✅ Intent detector initialized:", type(v5_engine.intent_detector).__name__)
    else:
        print("❌ Intent detector not initialized!")

    # Load dispensary agent intents
    print("\n3. Loading dispensary agent intents...")
    if v5_engine.intent_detector:
        loaded = v5_engine.intent_detector.load_intents("dispensary")
        if loaded:
            print("✅ Intents loaded successfully")
            if hasattr(v5_engine.intent_detector, 'intent_config'):
                intents = v5_engine.intent_detector.intent_config.get('intents', {})
                print(f"   Available intents: {list(intents.keys())}")
        else:
            print("⚠️  Using default intents")

    # Test messages
    test_messages = [
        "Hello there!",
        "I'm looking for Blue Dream",
        "What do you recommend for sleep?",
        "How much THC is in this?",
        "I want to buy some edibles",
        "Can you help with anxiety?",
        "What's the dosage for beginners?",
        "Is Blue Dream in stock?",
        "Random conversation here"
    ]

    print("\n4. Testing intent detection...")
    print("-"*40)

    for message in test_messages:
        try:
            # Detect intent
            result = v5_engine.detect_intent(message)

            # Check if result is properly formatted
            if isinstance(result, dict):
                intent = result.get('intent', 'unknown')
                confidence = result.get('confidence', 0)
                prompt_type = result.get('prompt_type', 'none')
                method = result.get('method', 'unknown')

                print(f"\nMessage: '{message}'")
                print(f"  Intent: {intent} (confidence: {confidence:.2f})")
                print(f"  Prompt Type: {prompt_type}")
                print(f"  Method: {method}")
            else:
                print(f"\n❌ Invalid result type for '{message}': {type(result)}")

        except Exception as e:
            print(f"\n❌ Error detecting intent for '{message}': {e}")

    # Test cache statistics
    print("\n" + "-"*40)
    print("\n5. Cache Statistics:")
    if hasattr(v5_engine.intent_detector, 'get_stats'):
        stats = v5_engine.intent_detector.get_stats()
        print(f"  Total requests: {stats.get('total_requests', 0)}")
        print(f"  Cache hits: {stats.get('cache_hits', 0)}")
        print(f"  Cache misses: {stats.get('cache_misses', 0)}")
        print(f"  Cache hit rate: {stats.get('cache_hit_rate', '0%')}")
        print(f"  Average latency: {stats.get('avg_latency_ms', 0):.2f}ms")

    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)

if __name__ == "__main__":
    test_intent_detection()