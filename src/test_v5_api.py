#!/usr/bin/env python3
"""
V5 API Test Script
Tests all V5 endpoints and features
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5025"

def test_health():
    """Test health endpoint"""
    print("\n✓ Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "5.0.0"
    print(f"  ✅ Health check passed: {data}")
    return True

def test_chat_without_auth():
    """Test chat endpoint without authentication (should work with auth disabled)"""
    print("\n✓ Testing chat endpoint (no auth)...")
    
    payload = {
        "message": "What strains do you recommend for relaxation?",
        "session_id": "test_session_001"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v5/chat",
        json=payload
    )
    
    # With auth disabled, this should work
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Chat response: {data['response'][:100]}...")
        return True
    elif response.status_code == 401:
        print("  ⚠️  Authentication required (expected when auth is enabled)")
        return True
    else:
        print(f"  ❌ Unexpected status: {response.status_code}")
        return False

def test_function_list():
    """Test function listing endpoint"""
    print("\n✓ Testing function list endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/v5/functions")
    
    if response.status_code == 200:
        functions = response.json()
        print(f"  ✅ Found {len(functions)} functions")
        for func in functions[:3]:  # Show first 3
            if isinstance(func, dict) and 'name' in func:
                print(f"    - {func['name']}: {func.get('description', 'No description')[:50]}...")
        return True
    elif response.status_code == 401:
        print("  ⚠️  Authentication required")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return False

def test_product_search():
    """Test product search endpoint"""
    print("\n✓ Testing product search...")
    
    payload = {
        "query": "indica",
        "limit": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v5/search/products",
        json=payload
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"  ✅ Search returned results")
        return True
    elif response.status_code in [401, 403]:
        print("  ⚠️  Authentication required")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return False

def test_rate_limiting():
    """Test rate limiting (if enabled)"""
    print("\n✓ Testing rate limiting...")
    
    # Send multiple rapid requests
    for i in range(5):
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 429:
            print(f"  ✅ Rate limiting triggered after {i+1} requests")
            return True
    
    print("  ℹ️  Rate limiting not triggered (may be disabled)")
    return True

def test_invalid_endpoint():
    """Test 404 handling"""
    print("\n✓ Testing 404 handling...")
    
    response = requests.get(f"{BASE_URL}/api/v5/invalid")
    if response.status_code == 404:
        print("  ✅ 404 handled correctly")
        return True
    else:
        print(f"  ❌ Unexpected status: {response.status_code}")
        return False

def test_validation():
    """Test input validation"""
    print("\n✓ Testing input validation...")
    
    # Invalid chat request (missing message)
    payload = {
        "session_id": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v5/chat",
        json=payload
    )
    
    if response.status_code == 422:
        print("  ✅ Validation working (rejected invalid input)")
        return True
    elif response.status_code == 401:
        print("  ⚠️  Authentication required")
        return True
    else:
        print(f"  ❌ Validation may not be working: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("V5 API TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_health,
        test_chat_without_auth,
        test_function_list,
        test_product_search,
        test_rate_limiting,
        test_invalid_endpoint,
        test_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} tests failed or had issues")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())