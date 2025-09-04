#!/usr/bin/env python3
"""
Test script to verify stability fixes for AI Engine Service
Tests model swapping, WebSocket connection, and decision tree analysis
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5024"

class StabilityTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test basic health check endpoint"""
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/ai/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['status']}")
                    return True
                else:
                    print(f"❌ Health check failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_decision_tree_analysis(self) -> bool:
        """Test decision tree analysis endpoint"""
        test_queries = [
            "What strains do you have for pain relief?",
            "I need something for anxiety",
            "Show me your strongest indica"
        ]
        
        all_passed = True
        for query in test_queries:
            try:
                payload = {
                    "query": query,
                    "session_id": f"test_{int(time.time())}"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/v1/chat/analyze-decision",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Decision tree analysis passed for: '{query[:50]}...'")
                        print(f"   - Intent: {data.get('intent', 'N/A')}")
                        print(f"   - Model: {data.get('model_used', 'N/A')}")
                        print(f"   - Processing time: {data.get('processing_time_ms', 'N/A')}ms")
                    else:
                        print(f"❌ Decision tree analysis failed for '{query[:50]}...' with status {response.status}")
                        text = await response.text()
                        print(f"   Error: {text}")
                        all_passed = False
            except Exception as e:
                print(f"❌ Decision tree analysis error for '{query[:50]}...': {e}")
                all_passed = False
                
        return all_passed
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection stability"""
        try:
            ws_url = f"ws://localhost:5024/api/v1/models/ws"
            async with self.session.ws_connect(ws_url) as ws:
                print("✅ WebSocket connection established")
                
                # Test receiving status updates
                messages_received = 0
                start_time = time.time()
                
                while time.time() - start_time < 5:  # Test for 5 seconds
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("type") == "model_status":
                                messages_received += 1
                                print(f"   Received status update #{messages_received}")
                                print(f"   - Current model: {data.get('current_model', 'N/A')}")
                                print(f"   - Memory available: {data.get('memory_available_gb', 0):.2f}GB")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"❌ WebSocket error: {msg}")
                            return False
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await ws.send_str("ping")
                
                # Close connection gracefully
                await ws.send_str("close")
                await ws.close()
                
                if messages_received > 0:
                    print(f"✅ WebSocket test passed - received {messages_received} status updates")
                    return True
                else:
                    print("❌ WebSocket test failed - no status updates received")
                    return False
                    
        except Exception as e:
            print(f"❌ WebSocket connection error: {e}")
            return False
    
    async def test_model_swap_stability(self) -> bool:
        """Test model swapping doesn't cause crashes"""
        test_prompts = [
            {"message": "Hello, how are you?", "session_id": "swap_test_1"},
            {"message": "Explain quantum physics", "session_id": "swap_test_2"},
            {"message": "Write a poem about cannabis", "session_id": "swap_test_3"}
        ]
        
        all_passed = True
        for i, prompt in enumerate(test_prompts):
            try:
                # Force different models by varying request patterns
                async with self.session.post(
                    f"{BASE_URL}/api/v1/chat",
                    json=prompt
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Model swap test {i+1} passed")
                        print(f"   Response length: {len(data.get('message', ''))}")
                    else:
                        print(f"❌ Model swap test {i+1} failed with status {response.status}")
                        all_passed = False
                        
                # Small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Model swap test {i+1} error: {e}")
                all_passed = False
                
        return all_passed
    
    async def run_all_tests(self):
        """Run all stability tests"""
        print("\n" + "="*60)
        print("AI ENGINE STABILITY TEST SUITE")
        print("="*60 + "\n")
        
        await self.setup()
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Decision Tree Analysis", self.test_decision_tree_analysis),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Model Swap Stability", self.test_model_swap_stability)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            print("-" * 40)
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ Test crashed: {e}")
                results[test_name] = False
            print()
        
        await self.cleanup()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All stability tests passed! The fixes are working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
            return 1

async def main():
    """Main entry point"""
    tester = StabilityTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    print("Starting AI Engine Stability Tests...")
    print("Make sure the API server is running on http://localhost:5024")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)