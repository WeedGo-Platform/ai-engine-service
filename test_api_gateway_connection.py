#!/usr/bin/env python3
"""
Test API Gateway Connection to Product Catalog Service
Tests various endpoints and authentication methods
"""

import requests
import json
from datetime import datetime

# Configuration
GATEWAY_URL = "http://localhost:8000"
DIRECT_SERVICE_URL = "http://localhost:5013"
IDENTITY_SERVICE_URL = "http://localhost:5011"

def test_connection(name, url, headers=None):
    """Test a connection and return status"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    if headers:
        print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"Response (text): {response.text[:500]}")
        else:
            print(f"Response: {response.text[:500]}")
        
        return {
            "name": name,
            "url": url,
            "status": response.status_code,
            "success": response.status_code in [200, 201],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }

def main():
    print("="*60)
    print("Product Catalog Service API Gateway Connection Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    results = []
    
    # Test 1: Direct service access
    results.append(test_connection(
        "Direct Product Catalog Service",
        f"{DIRECT_SERVICE_URL}/api/v1/products"
    ))
    
    # Test 2: Gateway access without auth
    results.append(test_connection(
        "Gateway - Products (No Auth)",
        f"{GATEWAY_URL}/api/v1/products"
    ))
    
    # Test 3: Gateway with API key
    results.append(test_connection(
        "Gateway - Products (API Key)",
        f"{GATEWAY_URL}/api/v1/products",
        headers={"X-API-Key": "test-api-key"}
    ))
    
    # Test 4: Try barcode endpoint
    results.append(test_connection(
        "Gateway - Barcode Lookup",
        f"{GATEWAY_URL}/api/v1/BarcodeLookup/123456789"
    ))
    
    # Test 5: Check health endpoint
    results.append(test_connection(
        "Direct Service Health",
        f"{DIRECT_SERVICE_URL}/health"
    ))
    
    # Test 6: Check Swagger
    results.append(test_connection(
        "Direct Service Swagger",
        f"{DIRECT_SERVICE_URL}/swagger/v1/swagger.json"
    ))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\nTotal tests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    print("\nSuccessful connections:")
    for r in successful:
        print(f"  ✓ {r['name']} - Status: {r['status']}")
    
    print("\nFailed connections:")
    for r in failed:
        print(f"  ✗ {r['name']} - Status: {r.get('status', 'error')}")
        if 'error' in r:
            print(f"    Error: {r['error']}")
    
    # Write results to file
    with open("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/api_gateway_test_results.json", "w") as f:
        json.dump({
            "test_time": datetime.now().isoformat(),
            "gateway_url": GATEWAY_URL,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed)
            }
        }, f, indent=2)
    
    print("\nResults saved to: api_gateway_test_results.json")
    
    # Connection status for DispensarySearchTool
    print("\n" + "="*60)
    print("RECOMMENDATION FOR DISPENSARYSEARCHTOOL")
    print("="*60)
    
    if any(r['name'] == "Direct Product Catalog Service" and r['success'] for r in results):
        print("✓ Direct connection to Product Catalog Service is available")
        print("  Endpoint: http://localhost:5013/api/v1/products")
    elif any(r['name'].startswith("Gateway") and r['success'] for r in results):
        print("✓ Gateway connection is available")
        print("  Endpoint: http://localhost:8000/api/v1/products")
    else:
        print("✗ No successful API connections")
        print("  The DispensarySearchTool should use direct database connection")
        print("  Connection: postgresql://weedgo:your_password_here@localhost:5434/ai_engine")
        print("  Table: cannabis_data.products")

if __name__ == "__main__":
    main()