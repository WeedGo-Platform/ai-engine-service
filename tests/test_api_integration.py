#!/usr/bin/env python3
"""
Test script to verify API endpoints are working correctly
"""

import urllib.request
import urllib.error
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description or endpoint}")
    print(f"Method: {method} {url}")
    
    try:
        request = urllib.request.Request(url, method=method)
        request.add_header('Content-Type', 'application/json')
        
        if data and method in ["POST", "PUT"]:
            request.data = json.dumps(data).encode('utf-8')
            
        try:
            response = urllib.request.urlopen(request)
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')
            
            print(f"Status: {status_code}")
            print("✅ Success")
            
            if response_data:
                try:
                    data = json.loads(response_data)
                    print(f"Response preview: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"Response: {response_data[:200]}...")
            return True
            
        except urllib.error.HTTPError as e:
            print(f"❌ Failed: {e.code}")
            error_data = e.read().decode('utf-8')
            print(f"Error: {error_data[:200]}")
            return False
            
    except urllib.error.URLError:
        print("❌ Connection failed - Is the API server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("WeedGo AI Admin API Integration Test")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test core endpoints
    tests = [
        # Health & Stats
        ("GET", "/api/v1/ai/health", None, "AI Health Check"),
        ("GET", "/api/v1/ai/stats", None, "AI Statistics"),
        
        # Service Management (New)
        ("GET", "/api/v1/services/health", None, "All Services Health"),
        ("GET", "/api/v1/services/ai-engine/logs?limit=5", None, "Service Logs"),
        
        # Knowledge Base (New)
        ("GET", "/api/v1/knowledge/strains?limit=5", None, "Strain Database"),
        ("GET", "/api/v1/knowledge/terpenes", None, "Terpene Profiles"),
        ("GET", "/api/v1/knowledge/effects?limit=5", None, "Effects Database"),
        ("GET", "/api/v1/knowledge/education?limit=3", None, "Educational Content"),
        
        # Personalities
        ("GET", "/api/v1/ai/personalities", None, "AI Personalities"),
        
        # Analytics
        ("GET", "/api/v1/analytics/dashboard", None, "Analytics Dashboard"),
        
        # Training
        ("GET", "/api/v1/ai/datasets", None, "Training Datasets"),
        ("GET", "/api/v1/ai/training-examples", None, "Training Examples"),
        
        # Models
        ("GET", "/api/v1/models/versions", None, "Model Versions"),
        ("GET", "/api/v1/models/base", None, "Base Models"),
    ]
    
    for method, endpoint, data, description in tests:
        if test_endpoint(method, endpoint, data, description):
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Test POST endpoints with sample data
    print("\n" + "="*60)
    print("Testing POST Endpoints")
    
    # Test adding a strain
    strain_data = {
        "name": "Test Strain",
        "type": "Hybrid",
        "thc_content": 20.5,
        "cbd_content": 1.2,
        "effects": ["relaxed", "happy"],
        "medical": ["stress", "anxiety"]
    }
    if test_endpoint("POST", "/api/v1/knowledge/strains", strain_data, "Add New Strain"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test service restart
    if test_endpoint("POST", "/api/v1/services/ai-engine/restart", None, "Restart Service"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test service scaling
    scale_data = {"replicas": 3}
    if test_endpoint("POST", "/api/v1/services/ai-engine/scale", scale_data, "Scale Service"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! API integration is working correctly.")
    else:
        print(f"\n⚠️  {tests_failed} tests failed. Please check the API server.")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)