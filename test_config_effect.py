#!/usr/bin/env python3
"""Test script to verify system configuration effects"""

import asyncio
import websockets
import json

async def test_config_effects():
    """Test if system config affects model behavior"""
    
    # Connect to WebSocket
    uri = "ws://localhost:5024/api/v1/test-engine/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Test configurations
        test_cases = [
            {
                "name": "No Configuration",
                "config": {
                    "action": "load_model",
                    "model": "tinyllama_1.1b_chat_v1.0.q4_k_m",
                    "base_folder": None,
                    "role_folder": None,
                    "personality_file": None
                }
            },
            {
                "name": "With System Config Only",
                "config": {
                    "action": "load_model",
                    "model": "tinyllama_1.1b_chat_v1.0.q4_k_m",
                    "base_folder": "prompts/system",
                    "role_folder": None,
                    "personality_file": None
                }
            },
            {
                "name": "System + Dispensary Agent",
                "config": {
                    "action": "load_model",
                    "model": "tinyllama_1.1b_chat_v1.0.q4_k_m",
                    "base_folder": "prompts/system",
                    "role_folder": "prompts/agents/dispensary",
                    "personality_file": None
                }
            },
            {
                "name": "System + Dispensary + Friendly",
                "config": {
                    "action": "load_model",
                    "model": "tinyllama_1.1b_chat_v1.0.q4_k_m",
                    "base_folder": "prompts/system",
                    "role_folder": "prompts/agents/dispensary",
                    "personality_file": "prompts/agents/dispensary/personality/friendly.json"
                }
            }
        ]
        
        # Test each configuration
        for test_case in test_cases:
            print(f"\n{'='*60}")
            print(f"Testing: {test_case['name']}")
            print(f"{'='*60}")
            
            # Load model with config
            await websocket.send(json.dumps(test_case['config']))
            
            # Wait for loading confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Load response: {data.get('message', data)}")
            
            # Test prompts
            test_prompts = [
                "hello",
                "What is 2+2?",
                "I need cannabis for pain relief"
            ]
            
            for prompt in test_prompts:
                # Send test prompt
                await websocket.send(json.dumps({
                    "action": "generate",
                    "prompt": prompt,
                    "max_tokens": 100
                }))
                
                # Get response
                response = await websocket.recv()
                data = json.loads(response)
                
                print(f"\nPrompt: '{prompt}'")
                print(f"Response: {data.get('text', 'ERROR')[:100]}...")
                
                # Check for system config info
                if 'system_config_loaded' in data:
                    print(f"System Config Applied: {data['system_config_loaded']}")
                    print(f"Response Style: {data.get('response_style', 'N/A')}")
                    print(f"Applied Temperature: {data.get('applied_temperature', 'N/A')}")
                    print(f"Safety Guidelines: {data.get('safety_guidelines_enabled', False)}")
                
                if data.get('prompt_template'):
                    print(f"Used Template: {data['prompt_template']}")
                    
            # Also test the "list prompts" command
            await websocket.send(json.dumps({
                "action": "generate",
                "prompt": "list prompts",
                "max_tokens": 100
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\nLoaded Prompts: {data.get('loaded_files', [])}")

if __name__ == "__main__":
    asyncio.run(test_config_effects())