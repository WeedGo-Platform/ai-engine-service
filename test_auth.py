#!/usr/bin/env python3
import requests
import json

# Test authentication flow
print("Testing Authentication Flow...")

# 1. Login to get JWT tokens
print("\n1. Testing login endpoint...")
login_response = requests.post(
    "http://localhost:5024/api/v2/identity-access/auth/login?tenant_id=ce2d57bc-b3ba-4801-b229-889a9fe9626d",
    json={"email": "admin@weedgo.ca", "password": "admin123"}
)

if login_response.status_code == 200:
    print("✅ Login successful")
    tokens = login_response.json()
    access_token = tokens["access_token"]
    print(f"   Access token: {access_token[:50]}...")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    exit(1)

# 2. Test admin endpoints with JWT token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print("\n2. Testing admin endpoints with JWT token...")

# Test /api/admin/models
models_response = requests.get("http://localhost:5024/api/admin/models", headers=headers)
if models_response.status_code == 200:
    models = models_response.json()
    print(f"✅ /api/admin/models - {len(models.get('models', []))} models found")
else:
    print(f"❌ /api/admin/models - Status: {models_response.status_code}")

# Test /api/admin/agents
agents_response = requests.get("http://localhost:5024/api/admin/agents", headers=headers)
if agents_response.status_code == 200:
    agents = agents_response.json()
    print(f"✅ /api/admin/agents - {len(agents.get('agents', []))} agents found")
else:
    print(f"❌ /api/admin/agents - Status: {agents_response.status_code}")

# Test /api/admin/stats
stats_response = requests.get("http://localhost:5024/api/admin/stats", headers=headers)
if stats_response.status_code == 200:
    print(f"✅ /api/admin/stats - Stats retrieved")
else:
    print(f"❌ /api/admin/stats - Status: {stats_response.status_code}")

# Test /api/stores/tenant/active (previously failing)
stores_response = requests.get("http://localhost:5024/api/stores/tenant/active", headers=headers)
if stores_response.status_code == 200:
    print(f"✅ /api/stores/tenant/active - Active stores retrieved")
else:
    print(f"❌ /api/stores/tenant/active - Status: {stores_response.status_code}")

print("\n3. Testing user profile endpoint...")
# Test /api/v2/identity-access/users/me
me_response = requests.get(
    "http://localhost:5024/api/v2/identity-access/users/me?tenant_id=ce2d57bc-b3ba-4801-b229-889a9fe9626d",
    headers=headers
)
if me_response.status_code == 200:
    user_data = me_response.json()
    print(f"✅ /users/me - User: {user_data['user']['email']}")
else:
    print(f"❌ /users/me - Status: {me_response.status_code}")

print("\n✨ Authentication test complete!")