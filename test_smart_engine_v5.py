#!/usr/bin/env python3
"""
Test script for Smart AI Engine V5
Demonstrates tool calling and context persistence capabilities
"""

import asyncio
import sys
sys.path.append('.')

from services.smart_ai_engine_v5 import get_smart_engine_v5

def test_basic_generation():
    """Test basic generation without tools"""
    print("\n=== Testing Basic Generation ===")
    engine = get_smart_engine_v5()
    
    # Load a small model for testing
    if engine.load_model("qwen2.5_0.5b_instruct_q4_k_m", 
                        role_folder="prompts/agents/dispensary",
                        personality_file="prompts/agents/dispensary/personality/zac.json"):
        
        # Test without prompts
        response = engine.generate("What is cannabis?", max_tokens=50)
        print(f"Response without prompts: {response.get('text', response.get('error'))[:200]}")
        
        # Test with prompts
        response = engine.generate("hey", prompt_type="greeting", max_tokens=50)
        print(f"Response with greeting prompt: {response.get('text', response.get('error'))[:200]}")
    else:
        print("Failed to load model")

def test_tool_detection():
    """Test tool call detection"""
    print("\n=== Testing Tool Detection ===")
    engine = get_smart_engine_v5()
    
    # Test tool extraction
    test_response = "I'll search for that product. [TOOL: search_products(query=\"blue dream\", category=\"flower\")]"
    tool_calls = engine._extract_tool_calls(test_response)
    print(f"Extracted tool calls: {tool_calls}")
    
    test_response2 = "Let me calculate the dosage. [TOOL: dosage_calculator(experience_level=\"beginner\", product_thc_mg=\"10\")]"
    tool_calls2 = engine._extract_tool_calls(test_response2)
    print(f"Extracted tool calls 2: {tool_calls2}")

async def test_tool_execution():
    """Test tool execution"""
    print("\n=== Testing Tool Execution ===")
    engine = get_smart_engine_v5()
    
    if engine.tool_manager:
        # Test search tool
        result = await engine.tool_manager.execute_tool(
            "search_products", 
            {"query": "blue", "category": "flower", "limit": 2}
        )
        print(f"Search tool result: {result.success}, Data: {result.data}")
        
        # Test calculator tool  
        result = await engine.tool_manager.execute_tool(
            "calculator",
            {"expression": "25 * 4"}
        )
        print(f"Calculator result: {result.success}, Data: {result.data}")
    else:
        print("Tool manager not initialized")

def test_context_storage():
    """Test context storage"""
    print("\n=== Testing Context Storage ===")
    engine = get_smart_engine_v5()
    
    if engine.context_manager:
        # Store some context
        session_id = engine.session_id or "test-session"
        
        # This would normally be async
        print(f"Context manager initialized with session: {session_id}")
        print(f"Max context length: {engine.context_manager.config.get('max_context_length', 4000)}")
    else:
        print("Context manager not initialized")

def test_agent_loading():
    """Test agent and personality loading"""
    print("\n=== Testing Agent Loading ===")
    engine = get_smart_engine_v5()
    
    # Load dispensary agent
    engine.current_agent = "dispensary"
    engine._load_agent_tools("dispensary")
    
    if engine.tool_manager:
        tools = engine.tool_manager.list_tools()
        print(f"Available tools after loading dispensary agent: {tools}")
    
    # List available agents and personalities
    agents = engine.list_available_agents()
    print(f"Available agents: {[a['name'] for a in agents]}")
    
    personalities = engine.list_available_personalities()
    print(f"Available personalities: {[p['name'] for p in personalities]}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Smart AI Engine V5 Test Suite")
    print("=" * 60)
    
    # Run synchronous tests
    test_basic_generation()
    test_tool_detection()
    test_agent_loading()
    test_context_storage()
    
    # Run async tests
    print("\n=== Running Async Tests ===")
    asyncio.run(test_tool_execution())
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()