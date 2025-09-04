#!/usr/bin/env python3
"""
Test script for Model Deployment Enhanced Features
Verifies all endpoints are working correctly on port 5028
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5024/api/v1/models"

def test_endpoint(name, method, endpoint, data=None):
    """Test a single endpoint"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ {name}: SUCCESS")
            return True
        else:
            print(f"❌ {name}: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Testing Model Deployment Enhanced Features")
    print(f"API Base: {API_BASE}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    tests = [
        # System Health
        ("System Metrics", "GET", "/system/metrics"),
        
        # Configuration Presets
        ("Get Config Presets", "GET", "/config-presets"),
        
        # Model Health
        ("Model Health Check", "GET", "/test-model/health"),
        
        # Deployment Status
        ("Deployment Status", "GET", "/deployments/test_deploy_1"),
        
        # Model Testing
        ("Test Model", "POST", "/test", {"model_id": "test-model", "test_cases": []}),
        
        # Model Benchmarks
        ("Get Benchmarks", "GET", "/test-model/benchmarks"),
        ("Run Benchmark", "POST", "/test-model/benchmark", {}),
        
        # Model Comparison
        ("Compare Models", "POST", "/compare", {"model_ids": ["model1", "model2"]}),
        
        # Deployment Logs
        ("Get Deployment Logs", "GET", "/deployments/test_deploy_1/logs?limit=10"),
        
        # Deployment Actions
        ("Rollback Deployment", "POST", "/deployments/test_deploy_1/rollback"),
        ("Retry Deployment", "POST", "/deployments/test_deploy_1/retry"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, method, endpoint, *args in tests:
        data = args[0] if args else None
        if test_endpoint(test_name, method, endpoint, data):
            passed += 1
        else:
            failed += 1
        time.sleep(0.1)  # Small delay between tests
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! Model Deployment Enhanced features are working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the endpoints.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)