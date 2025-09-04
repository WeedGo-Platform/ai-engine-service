#!/usr/bin/env python3
"""
Comprehensive Integration Test for AI Admin Portal
Tests all API endpoints to ensure real data is being served (no mock data)
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Tuple
from datetime import datetime

API_BASE_URL = "http://localhost:8080/api/v1"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class APIIntegrationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def test_endpoint(self, session: aiohttp.ClientSession, name: str, endpoint: str, method: str = "GET", data: Dict = None) -> Tuple[bool, str]:
        """Test a single API endpoint"""
        self.total_tests += 1
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                async with session.get(url) as response:
                    status = response.status
                    content = await response.text()
                    
                    if status == 200:
                        # Parse JSON and check for mock data indicators
                        json_data = json.loads(content)
                        
                        # Check for common mock data patterns
                        content_str = json.dumps(json_data).lower()
                        mock_indicators = ['mock', 'dummy', 'fake', 'test', 'example', 'demo']
                        has_mock = any(indicator in content_str for indicator in mock_indicators)
                        
                        if has_mock:
                            self.failed_tests += 1
                            return False, f"Possible mock data detected"
                        
                        # Check if response has real data structure
                        if isinstance(json_data, dict):
                            if not json_data or all(v is None or v == [] or v == {} for v in json_data.values()):
                                self.failed_tests += 1
                                return False, "Empty or null response"
                        
                        self.passed_tests += 1
                        return True, f"Status {status}, Real data returned"
                    else:
                        self.failed_tests += 1
                        return False, f"Status {status}"
                        
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    status = response.status
                    content = await response.text()
                    
                    if status in [200, 201]:
                        self.passed_tests += 1
                        return True, f"Status {status}"
                    else:
                        self.failed_tests += 1
                        return False, f"Status {status}: {content[:100]}"
                        
        except Exception as e:
            self.failed_tests += 1
            return False, f"Error: {str(e)}"
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{BLUE}    AI Admin Portal - Complete Integration Test Suite{RESET}")
        print(f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}\n")
        print(f"Testing against: {API_BASE_URL}\n")
        
        async with aiohttp.ClientSession() as session:
            # Core AI Engine Endpoints
            print(f"{BOLD}Core AI Engine:{RESET}")
            endpoints = [
                ("AI Stats", "/ai/stats"),
                ("AI Decision Stream", "/ai/decision-stream"),
                ("AI Context Factors", "/ai/context-factors"),
                ("AI Decision Paths", "/ai/decision-paths?input_text=test"),
                ("AI Training Examples", "/ai/training-examples"),
                ("AI Personalities", "/ai/personalities"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            print(f"\n{BOLD}Knowledge Base:{RESET}")
            endpoints = [
                ("Cannabis Strains", "/knowledge/strains"),
                ("Terpenes", "/knowledge/terpenes"),
                ("Medical Intents", "/medical-intents"),
                ("Intents", "/intents"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            print(f"\n{BOLD}Conversation Management:{RESET}")
            endpoints = [
                ("Conversation History", "/conversations/history"),
                ("Conversation Flows", "/conversation-flows"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            print(f"\n{BOLD}Training & Analytics:{RESET}")
            endpoints = [
                ("Training Accuracy", "/training/accuracy"),
                ("Training Metrics", "/admin/training-metrics"),
                ("Analytics Dashboard", "/analytics/dashboard"),
                ("Analytics Performance", "/analytics/performance"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            print(f"\n{BOLD}Model & Service Management:{RESET}")
            endpoints = [
                ("Model Versions", "/models/versions"),
                ("Service Health", "/services/health"),
                ("AI Datasets", "/ai/datasets"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            print(f"\n{BOLD}Admin Operations:{RESET}")
            endpoints = [
                ("Cache Status", "/admin/cache/status"),
            ]
            
            for name, endpoint in endpoints:
                success, message = await self.test_endpoint(session, name, endpoint)
                self.print_result(name, success, message)
            
            # Test POST endpoints
            print(f"\n{BOLD}Testing Write Operations:{RESET}")
            
            # Test chat endpoint
            chat_data = {
                "message": "What strains help with anxiety?",
                "session_id": "test_session"
            }
            success, message = await self.test_endpoint(session, "Chat API", "/chat", "POST", chat_data)
            self.print_result("Chat API", success, message)
            
            # Test training example creation
            training_data = {
                "input": "I need help with pain relief",
                "output": "I can recommend several strains known for pain relief properties.",
                "category": "medical"
            }
            success, message = await self.test_endpoint(session, "Add Training Example", "/ai/training-examples", "POST", training_data)
            self.print_result("Add Training Example", success, message)
        
        # Print summary
        self.print_summary()
    
    def print_result(self, name: str, success: bool, message: str):
        """Print test result with color coding"""
        status_symbol = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        status_color = GREEN if success else RED
        print(f"  {status_symbol} {name:<30} {status_color}{message}{RESET}")
        self.results.append((name, success, message))
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}Test Summary:{RESET}")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  {GREEN}Passed: {self.passed_tests}{RESET}")
        print(f"  {RED}Failed: {self.failed_tests}{RESET}")
        
        if self.failed_tests == 0:
            print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! No mock data detected.{RESET}")
            print(f"{GREEN}The AI Admin Portal is fully integrated with real APIs.{RESET}")
        else:
            print(f"\n{YELLOW}⚠️  Some tests failed. Review the results above.{RESET}")
            
            # List failed tests
            failed = [(name, msg) for name, success, msg in self.results if not success]
            if failed:
                print(f"\n{BOLD}Failed Tests:{RESET}")
                for name, msg in failed:
                    print(f"  {RED}• {name}: {msg}{RESET}")
        
        print(f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}\n")

async def main():
    """Main function"""
    tester = APIIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print(f"Starting integration tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(main())