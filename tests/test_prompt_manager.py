#!/usr/bin/env python3
"""
Test the new JSON-based prompt management system
"""

import sys
import json
from services.centralized_prompt_manager import CentralizedPromptManager

def test_prompt_loading():
    """Test loading prompts from JSON files"""
    print("=" * 60)
    print("Testing Prompt Manager with JSON Files")
    print("=" * 60)
    
    # Initialize the manager
    manager = CentralizedPromptManager(prompts_dir="prompts")
    
    # Test 1: Check categories loaded
    print("\n1. Available Categories:")
    categories = manager.get_all_categories()
    for cat in categories:
        print(f"   - {cat}")
    
    # Test 2: Check prompt types loaded
    print(f"\n2. Total Prompts Loaded: {len(manager.get_all_prompt_types())}")
    print("   Sample prompts:")
    for prompt_type in manager.get_all_prompt_types()[:5]:
        info = manager.get_prompt_info(prompt_type)
        print(f"   - {prompt_type} (category: {info['category']})")
    
    # Test 3: Test intent detection prompt
    print("\n3. Testing Intent Detection:")
    intent_prompt = manager.get_prompt(
        "intent_detection",
        conversation_context="Customer just entered the store",
        message="do you have tiger blood preroll?"
    )
    print(f"   Prompt length: {len(intent_prompt)} chars")
    print(f"   Contains 'tiger blood': {'tiger blood' in intent_prompt.lower()}")
    
    # Test 4: Test search extraction
    print("\n4. Testing Search Extraction:")
    search_prompt = manager.get_prompt(
        "search_extraction",
        query="I want pink kush half ounce"
    )
    print(f"   Prompt includes size conversions: {'14g' in search_prompt}")
    
    # Test 5: Test analytics query type
    print("\n5. Testing Analytics Query Type:")
    analytics_prompt = manager.get_prompt(
        "query_type",
        message="what is the max thc in your gummies"
    )
    print(f"   Prompt mentions analytics_query: {'analytics_query' in analytics_prompt}")
    
    # Test 6: Test prompt validation
    print("\n6. Testing Response Validation:")
    
    # Test valid single word response
    validation = manager.validate_prompt_response("intent_detection", "search")
    print(f"   'search' for intent_detection: {validation}")
    
    # Test invalid response
    validation = manager.validate_prompt_response("intent_detection", "invalid intent")
    print(f"   'invalid intent' for intent_detection: {validation}")
    
    # Test JSON validation
    json_response = '{"product": "pink kush", "size": "14g"}'
    validation = manager.validate_prompt_response("search_extraction", json_response)
    print(f"   JSON for search_extraction: {validation}")
    
    # Test 7: Get prompts by category
    print("\n7. Prompts by Category:")
    for category in ["intent", "search", "conversation", "analytics"]:
        prompts = manager.get_prompts_by_category(category)
        print(f"   {category}: {len(prompts)} prompts")
    
    # Test 8: Add custom prompt at runtime
    print("\n8. Adding Custom Prompt:")
    manager.add_custom_prompt(
        name="test_custom",
        template="This is a test prompt for {item}",
        category="testing",
        variables=["item"],
        output_format="text"
    )
    
    custom_result = manager.get_prompt("test_custom", item="validation")
    print(f"   Custom prompt result: {custom_result}")
    
    # Test 9: Reload prompts
    print("\n9. Testing Reload:")
    manager.reload_prompts()
    print(f"   Prompts after reload: {len(manager.get_all_prompt_types())}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_prompt_loading()