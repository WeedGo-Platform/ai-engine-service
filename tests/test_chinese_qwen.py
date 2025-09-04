#!/usr/bin/env python3
"""
Test Chinese language processing with Qwen model
"""

import requests
import json

def test_chinese_queries():
    """Test various Chinese queries"""
    
    api_url = "http://localhost:5024/api/v1/chat"
    
    test_queries = [
        "最高THC含量的产品是什么?",
        "推荐一些适合新手的产品",
        "indica和sativa有什么区别？",
        "我想要放松的产品",
        "有CBD的产品吗？"
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Chinese queries with Qwen model")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        
        payload = {
            "message": query,
            "session_id": f"test_chinese_{i}",
            "customer_id": "test_user_zh",
            "language": "zh"
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: Success")
                print(f"🌐 Detected Language: {result.get('detected_language', 'N/A')}")
                print(f"📊 Confidence: {result.get('language_confidence', 'N/A')}")
                print(f"💬 Response: {result.get('message', 'No message')[:500]}")
                
                if result.get('products'):
                    print(f"📦 Products found: {len(result['products'])}")
                    for product in result['products'][:3]:
                        print(f"   - {product.get('product_name', 'Unknown')}")
                        if product.get('thc_percentage'):
                            print(f"     THC: {product['thc_percentage']}%")
                
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print("⏱️  Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_chinese_queries()