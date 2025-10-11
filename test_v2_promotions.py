#!/usr/bin/env python3
"""Test V2 Promotions CRUD Endpoints with Repository"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5024"

def test_create_promotion():
    """Test creating a promotion"""
    print("\n🧪 Test 1: Create Promotion")
    print("=" * 50)

    payload = {
        "store_id": "ce2d57bc-b3ba-4801-b229-889a9fe9626d",
        "promotion_name": "Test Summer Sale",
        "description": "20% off all products",
        "discount_type": "percentage",
        "discount_value": 20,
        "start_date": "2025-06-01T00:00:00",
        "end_date": "2025-08-31T23:59:59",
        "applicable_to": "all_products",
        "customer_segment": "all",
        "can_stack": False,
        "priority": 1
    }

    response = requests.post(
        f"{BASE_URL}/api/v2/pricing-promotions/promotions",
        json=payload
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Promotion created successfully")
        print(f"   ID: {data['id']}")
        print(f"   Name: {data['promotion_name']}")
        print(f"   Status: {data['status']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.text}")
        return None

def test_list_promotions():
    """Test listing promotions"""
    print("\n🧪 Test 2: List Promotions")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/api/v2/pricing-promotions/promotions?page=1&page_size=10"
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} promotions")
        print(f"   Active: {data.get('active_count', 0)}")
        print(f"   Scheduled: {data.get('scheduled_count', 0)}")
        for promo in data['promotions']:
            print(f"   - {promo['promotion_name']} ({promo['status']})")
    else:
        print(f"❌ Failed: {response.text}")

def test_get_promotion(promotion_id):
    """Test getting a promotion by ID"""
    print("\n🧪 Test 3: Get Promotion by ID")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/api/v2/pricing-promotions/promotions/{promotion_id}"
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Promotion found")
        print(f"   Name: {data['promotion_name']}")
        print(f"   Discount: {data['discount_value']}% off")
        print(f"   Status: {data['status']}")
    else:
        print(f"❌ Failed: {response.text}")

def test_update_status(promotion_id):
    """Test updating promotion status"""
    print("\n🧪 Test 4: Update Promotion Status")
    print("=" * 50)

    response = requests.post(
        f"{BASE_URL}/api/v2/pricing-promotions/promotions/{promotion_id}/status",
        json={"action": "activate"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Promotion status updated")
        print(f"   New status: {data['status']}")
    else:
        print(f"❌ Failed: {response.text}")

def test_stats():
    """Test getting promotion statistics"""
    print("\n🧪 Test 5: Get Promotion Statistics")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/api/v2/pricing-promotions/stats"
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Statistics retrieved")
        print(f"   Total Promotions: {data['promotions']['total']}")
        print(f"   Active: {data['promotions']['active']}")
        print(f"   Discount Codes: {data['discount_codes']['total']}")
    else:
        print(f"❌ Failed: {response.text}")

if __name__ == "__main__":
    print("\n🚀 Starting V2 Promotions CRUD Tests")
    print("=" * 50)

    # Test the full CRUD cycle
    promotion_id = test_create_promotion()

    if promotion_id:
        test_get_promotion(promotion_id)
        test_update_status(promotion_id)
        test_list_promotions()
        test_stats()

        print("\n✨ All tests completed!")
    else:
        print("\n❌ Tests failed - could not create promotion")
