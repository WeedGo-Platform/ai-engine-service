#!/usr/bin/env python3
"""
Mobile App V2 API Endpoint Testing Script
Tests all mobile app endpoints against the backend running on port 5024
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Backend configuration
BASE_URL = "http://localhost:5024"
TENANT_ID = "ce2d57bc-b3ba-4801-b229-889a9fe9626d"  # Pot Palace tenant

# Test user credentials
TEST_USER = {
    "email": "test.mobile@weedgo.ca",
    "password": "TestPass123!",
    "first_name": "Mobile",
    "last_name": "Tester",
    "phone": "+14165551234",
    "date_of_birth": "1990-01-01"
}

# Global token storage
tokens = {
    "access_token": None,
    "refresh_token": None
}

class EndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        self.results = []
        self.test_data = {}  # Store IDs for testing

    def log_result(self, category: str, endpoint: str, method: str, status: str,
                   status_code: Optional[int] = None, message: str = ""):
        """Log test result with color coding"""
        if status == "PASS":
            status_str = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}"
        elif status == "FAIL":
            status_str = f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
        elif status == "SKIP":
            status_str = f"{Fore.YELLOW}⊘ SKIP{Style.RESET_ALL}"
        else:
            status_str = f"{Fore.BLUE}ℹ INFO{Style.RESET_ALL}"

        print(f"  [{status_str}] {method:6} {endpoint:50} {f'[{status_code}]' if status_code else '':7} {message}")

        self.results.append({
            "category": category,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[Optional[int], Optional[Dict]]:
        """Make HTTP request and return status code and response data"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            try:
                data = response.json() if response.text else {}
            except:
                data = {"text": response.text}
            return response.status_code, data
        except requests.exceptions.ConnectionError:
            return None, {"error": "Connection refused"}
        except Exception as e:
            return None, {"error": str(e)}

    def test_identity_access(self):
        """Test Identity & Access Management endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Identity & Access Management ═══{Style.RESET_ALL}")

        # 1. Check phone (should not exist initially)
        status_code, data = self.make_request("POST", "/api/v2/identity-access/auth/check-phone",
                                             json={"phone": TEST_USER["phone"]})
        if status_code == 200:
            self.log_result("Auth", "/api/v2/identity-access/auth/check-phone", "POST", "PASS", status_code)
        elif status_code == 404:
            self.log_result("Auth", "/api/v2/identity-access/auth/check-phone", "POST", "INFO", status_code, "Phone not found (expected)")
        else:
            self.log_result("Auth", "/api/v2/identity-access/auth/check-phone", "POST", "FAIL", status_code, str(data))

        # 2. Register new user
        status_code, data = self.make_request("POST", "/api/v2/identity-access/users", json=TEST_USER)
        if status_code == 201:
            self.log_result("Auth", "/api/v2/identity-access/users", "POST", "PASS", status_code, "User registered")
            if "id" in data:
                self.test_data["user_id"] = data["id"]
            if "access_token" in data:
                tokens["access_token"] = data["access_token"]
                tokens["refresh_token"] = data.get("refresh_token")
                self.session.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        elif status_code == 409:
            self.log_result("Auth", "/api/v2/identity-access/users", "POST", "INFO", status_code, "User already exists")
        else:
            self.log_result("Auth", "/api/v2/identity-access/users", "POST", "FAIL", status_code, str(data))

        # 3. Login
        login_data = {"email": TEST_USER["email"], "password": TEST_USER["password"]}
        status_code, data = self.make_request("POST", "/api/v2/identity-access/auth/login", json=login_data)
        if status_code == 200:
            self.log_result("Auth", "/api/v2/identity-access/auth/login", "POST", "PASS", status_code, "Login successful")
            if "access_token" in data:
                tokens["access_token"] = data["access_token"]
                tokens["refresh_token"] = data.get("refresh_token")
                self.session.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        else:
            self.log_result("Auth", "/api/v2/identity-access/auth/login", "POST", "FAIL", status_code, str(data))

        # 4. Validate token
        status_code, data = self.make_request("GET", "/api/v2/identity-access/auth/validate")
        if status_code == 200:
            self.log_result("Auth", "/api/v2/identity-access/auth/validate", "GET", "PASS", status_code)
        else:
            self.log_result("Auth", "/api/v2/identity-access/auth/validate", "GET", "FAIL", status_code, str(data))

        # 5. Refresh token
        if tokens["refresh_token"]:
            headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
            status_code, data = self.make_request("POST", "/api/v2/identity-access/auth/refresh", headers=headers)
            if status_code == 200:
                self.log_result("Auth", "/api/v2/identity-access/auth/refresh", "POST", "PASS", status_code)
                if "access_token" in data:
                    tokens["access_token"] = data["access_token"]
                    self.session.headers["Authorization"] = f"Bearer {tokens['access_token']}"
            else:
                self.log_result("Auth", "/api/v2/identity-access/auth/refresh", "POST", "FAIL", status_code, str(data))

        # 6. OTP endpoints
        status_code, data = self.make_request("POST", "/api/v2/identity-access/auth/verify-otp",
                                             json={"phone": TEST_USER["phone"], "code": "123456"})
        if status_code in [400, 401]:
            self.log_result("Auth", "/api/v2/identity-access/auth/verify-otp", "POST", "PASS", status_code, "Invalid OTP rejected")
        else:
            self.log_result("Auth", "/api/v2/identity-access/auth/verify-otp", "POST", "INFO", status_code, str(data))

        # 7. Password reset flow
        status_code, data = self.make_request("POST", "/api/v2/identity-access/auth/password-reset",
                                             json={"identifier": TEST_USER["email"]})
        if status_code == 200:
            self.log_result("Auth", "/api/v2/identity-access/auth/password-reset", "POST", "PASS", status_code)
        else:
            self.log_result("Auth", "/api/v2/identity-access/auth/password-reset", "POST", "INFO", status_code, str(data))

    def test_products(self):
        """Test Product Catalog endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Product Catalog ═══{Style.RESET_ALL}")

        # 1. Search products
        status_code, data = self.make_request("GET", "/api/v2/products/search", params={"q": "flower"})
        if status_code == 200:
            self.log_result("Products", "/api/v2/products/search", "GET", "PASS", status_code)
            if isinstance(data, list) and len(data) > 0:
                self.test_data["product_id"] = data[0].get("id")
        else:
            self.log_result("Products", "/api/v2/products/search", "GET", "INFO", status_code, "No products found")

        # 2. Get product by ID
        if self.test_data.get("product_id"):
            status_code, data = self.make_request("GET", f"/api/v2/products/{self.test_data['product_id']}")
            if status_code == 200:
                self.log_result("Products", f"/api/v2/products/{{id}}", "GET", "PASS", status_code)
            else:
                self.log_result("Products", f"/api/v2/products/{{id}}", "GET", "FAIL", status_code, str(data))
        else:
            self.log_result("Products", "/api/v2/products/{id}", "GET", "SKIP", None, "No product ID available")

        # 3. Get product categories
        status_code, data = self.make_request("GET", "/api/v2/products/categories")
        if status_code == 200:
            self.log_result("Products", "/api/v2/products/categories", "GET", "PASS", status_code)
        else:
            self.log_result("Products", "/api/v2/products/categories", "GET", "INFO", status_code, str(data))

    def test_inventory(self):
        """Test Inventory Management endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Inventory Management ═══{Style.RESET_ALL}")

        # 1. Search inventory
        status_code, data = self.make_request("GET", "/api/v2/inventory/search")
        if status_code == 200:
            self.log_result("Inventory", "/api/v2/inventory/search", "GET", "PASS", status_code)
            if isinstance(data, list) and len(data) > 0:
                self.test_data["inventory_id"] = data[0].get("id")
        else:
            self.log_result("Inventory", "/api/v2/inventory/search", "GET", "INFO", status_code, "No inventory found")

        # 2. Check stock by product
        if self.test_data.get("product_id"):
            status_code, data = self.make_request("GET", f"/api/v2/inventory/product/{self.test_data['product_id']}")
            if status_code == 200:
                self.log_result("Inventory", "/api/v2/inventory/product/{id}", "GET", "PASS", status_code)
            else:
                self.log_result("Inventory", "/api/v2/inventory/product/{id}", "GET", "INFO", status_code, str(data))

        # 3. Low stock alerts
        status_code, data = self.make_request("GET", "/api/v2/inventory/low-stock")
        if status_code == 200:
            self.log_result("Inventory", "/api/v2/inventory/low-stock", "GET", "PASS", status_code)
        else:
            self.log_result("Inventory", "/api/v2/inventory/low-stock", "GET", "INFO", status_code, str(data))

    def test_cart_orders(self):
        """Test Cart and Order Management endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Cart & Orders ═══{Style.RESET_ALL}")

        # 1. Get cart
        status_code, data = self.make_request("GET", "/api/v2/orders/cart")
        if status_code == 200:
            self.log_result("Cart", "/api/v2/orders/cart", "GET", "PASS", status_code)
            if "id" in data:
                self.test_data["cart_id"] = data["id"]
        else:
            self.log_result("Cart", "/api/v2/orders/cart", "GET", "INFO", status_code, "Cart not found")

        # 2. Add item to cart
        if self.test_data.get("product_id"):
            cart_item = {
                "product_id": self.test_data["product_id"],
                "quantity": 1
            }
            status_code, data = self.make_request("POST", "/api/v2/orders/cart/items", json=cart_item)
            if status_code in [200, 201]:
                self.log_result("Cart", "/api/v2/orders/cart/items", "POST", "PASS", status_code)
            else:
                self.log_result("Cart", "/api/v2/orders/cart/items", "POST", "INFO", status_code, str(data))

        # 3. Apply promo code
        status_code, data = self.make_request("POST", "/api/v2/pricing-promotions/apply",
                                             json={"code": "WELCOME10"})
        if status_code == 200:
            self.log_result("Cart", "/api/v2/pricing-promotions/apply", "POST", "PASS", status_code)
        else:
            self.log_result("Cart", "/api/v2/pricing-promotions/apply", "POST", "INFO", status_code, "Promo code not found")

        # 4. List orders
        status_code, data = self.make_request("GET", "/api/v2/orders")
        if status_code == 200:
            self.log_result("Orders", "/api/v2/orders", "GET", "PASS", status_code)
            if isinstance(data, list) and len(data) > 0:
                self.test_data["order_id"] = data[0].get("id")
        else:
            self.log_result("Orders", "/api/v2/orders", "GET", "INFO", status_code, str(data))

        # 5. Get order details
        if self.test_data.get("order_id"):
            status_code, data = self.make_request("GET", f"/api/v2/orders/{self.test_data['order_id']}")
            if status_code == 200:
                self.log_result("Orders", "/api/v2/orders/{id}", "GET", "PASS", status_code)
            else:
                self.log_result("Orders", "/api/v2/orders/{id}", "GET", "FAIL", status_code, str(data))

    def test_stores_tenants(self):
        """Test Store/Tenant Management endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Stores & Tenants ═══{Style.RESET_ALL}")

        # 1. List stores
        status_code, data = self.make_request("GET", "/api/v2/tenants/stores")
        if status_code == 200:
            self.log_result("Stores", "/api/v2/tenants/stores", "GET", "PASS", status_code)
            if isinstance(data, list) and len(data) > 0:
                self.test_data["store_id"] = data[0].get("id")
        else:
            self.log_result("Stores", "/api/v2/tenants/stores", "GET", "INFO", status_code, str(data))

        # 2. Get store details
        if self.test_data.get("store_id"):
            status_code, data = self.make_request("GET", f"/api/v2/tenants/stores/{self.test_data['store_id']}")
            if status_code == 200:
                self.log_result("Stores", "/api/v2/tenants/stores/{id}", "GET", "PASS", status_code)
            else:
                self.log_result("Stores", "/api/v2/tenants/stores/{id}", "GET", "FAIL", status_code, str(data))

        # 3. Get store hours
        if self.test_data.get("store_id"):
            status_code, data = self.make_request("GET", f"/api/v2/tenants/stores/{self.test_data['store_id']}/hours")
            if status_code == 200:
                self.log_result("Stores", "/api/v2/tenants/stores/{id}/hours", "GET", "PASS", status_code)
            else:
                self.log_result("Stores", "/api/v2/tenants/stores/{id}/hours", "GET", "INFO", status_code, str(data))

    def test_delivery(self):
        """Test Delivery Management endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Delivery Management ═══{Style.RESET_ALL}")

        # 1. Get delivery zones
        status_code, data = self.make_request("GET", "/api/v2/delivery/zones")
        if status_code == 200:
            self.log_result("Delivery", "/api/v2/delivery/zones", "GET", "PASS", status_code)
            if isinstance(data, list) and len(data) > 0:
                self.test_data["zone_id"] = data[0].get("id")
        else:
            self.log_result("Delivery", "/api/v2/delivery/zones", "GET", "INFO", status_code, str(data))

        # 2. Check delivery availability
        address = {
            "address": "123 Main St",
            "city": "Toronto",
            "postal_code": "M5V 2T6"
        }
        status_code, data = self.make_request("POST", "/api/v2/delivery/check-availability", json=address)
        if status_code == 200:
            self.log_result("Delivery", "/api/v2/delivery/check-availability", "POST", "PASS", status_code)
        else:
            self.log_result("Delivery", "/api/v2/delivery/check-availability", "POST", "INFO", status_code, str(data))

        # 3. Calculate delivery fee
        status_code, data = self.make_request("POST", "/api/v2/delivery/calculate-fee", json=address)
        if status_code == 200:
            self.log_result("Delivery", "/api/v2/delivery/calculate-fee", "POST", "PASS", status_code)
        else:
            self.log_result("Delivery", "/api/v2/delivery/calculate-fee", "POST", "INFO", status_code, str(data))

        # 4. Track delivery (if order exists)
        if self.test_data.get("order_id"):
            status_code, data = self.make_request("GET", f"/api/v2/delivery/track/{self.test_data['order_id']}")
            if status_code == 200:
                self.log_result("Delivery", "/api/v2/delivery/track/{order_id}", "GET", "PASS", status_code)
            else:
                self.log_result("Delivery", "/api/v2/delivery/track/{order_id}", "GET", "INFO", status_code, str(data))

    def test_customer_engagement(self):
        """Test Customer Engagement endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Customer Engagement ═══{Style.RESET_ALL}")

        # 1. Get reviews for product
        if self.test_data.get("product_id"):
            status_code, data = self.make_request("GET", f"/api/v2/customer-engagement/reviews/product/{self.test_data['product_id']}")
            if status_code == 200:
                self.log_result("Reviews", "/api/v2/customer-engagement/reviews/product/{id}", "GET", "PASS", status_code)
            else:
                self.log_result("Reviews", "/api/v2/customer-engagement/reviews/product/{id}", "GET", "INFO", status_code, str(data))

        # 2. Submit review
        if self.test_data.get("product_id"):
            review = {
                "product_id": self.test_data["product_id"],
                "rating": 5,
                "title": "Great product!",
                "comment": "Really enjoyed this product."
            }
            status_code, data = self.make_request("POST", "/api/v2/customer-engagement/reviews", json=review)
            if status_code in [200, 201]:
                self.log_result("Reviews", "/api/v2/customer-engagement/reviews", "POST", "PASS", status_code)
                if "id" in data:
                    self.test_data["review_id"] = data["id"]
            else:
                self.log_result("Reviews", "/api/v2/customer-engagement/reviews", "POST", "INFO", status_code, str(data))

    def test_ai_conversation(self):
        """Test AI Conversation endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing AI Conversation ═══{Style.RESET_ALL}")

        # 1. Send message
        message = {
            "message": "What products do you have?",
            "session_id": "test-session-123"
        }
        status_code, data = self.make_request("POST", "/api/v2/ai-conversation/messages", json=message)
        if status_code == 200:
            self.log_result("Chat", "/api/v2/ai-conversation/messages", "POST", "PASS", status_code)
            if "conversation_id" in data:
                self.test_data["conversation_id"] = data["conversation_id"]
        else:
            self.log_result("Chat", "/api/v2/ai-conversation/messages", "POST", "INFO", status_code, str(data))

        # 2. Get conversation history
        if self.test_data.get("conversation_id"):
            status_code, data = self.make_request("GET", f"/api/v2/ai-conversation/conversations/{self.test_data['conversation_id']}")
            if status_code == 200:
                self.log_result("Chat", "/api/v2/ai-conversation/conversations/{id}", "GET", "PASS", status_code)
            else:
                self.log_result("Chat", "/api/v2/ai-conversation/conversations/{id}", "GET", "INFO", status_code, str(data))

    def test_pricing_promotions(self):
        """Test Pricing & Promotions endpoints"""
        print(f"\n{Fore.CYAN}═══ Testing Pricing & Promotions ═══{Style.RESET_ALL}")

        # 1. Get active promotions
        status_code, data = self.make_request("GET", "/api/v2/pricing-promotions/active")
        if status_code == 200:
            self.log_result("Promotions", "/api/v2/pricing-promotions/active", "GET", "PASS", status_code)
        else:
            self.log_result("Promotions", "/api/v2/pricing-promotions/active", "GET", "INFO", status_code, str(data))

        # 2. Validate promo code
        status_code, data = self.make_request("POST", "/api/v2/pricing-promotions/validate",
                                             json={"code": "WELCOME10"})
        if status_code == 200:
            self.log_result("Promotions", "/api/v2/pricing-promotions/validate", "POST", "PASS", status_code)
        else:
            self.log_result("Promotions", "/api/v2/pricing-promotions/validate", "POST", "INFO", status_code, "Invalid code")

    def generate_report(self):
        """Generate test report"""
        print(f"\n{Fore.CYAN}═══ Test Results Summary ═══{Style.RESET_ALL}")

        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        skipped = len([r for r in self.results if r["status"] == "SKIP"])
        info = len([r for r in self.results if r["status"] == "INFO"])

        print(f"\nTotal Endpoints Tested: {total}")
        print(f"  {Fore.GREEN}✓ Passed: {passed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}✗ Failed: {failed}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}⊘ Skipped: {skipped}{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}ℹ Info: {info}{Style.RESET_ALL}")

        if passed > 0:
            success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
            print(f"\nSuccess Rate: {Fore.GREEN if success_rate >= 80 else Fore.YELLOW}{success_rate:.1f}%{Style.RESET_ALL}")

        # List failed endpoints
        if failed > 0:
            print(f"\n{Fore.RED}Failed Endpoints:{Style.RESET_ALL}")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['method']} {r['endpoint']}: {r['message']}")

        # Save detailed report
        report_path = "mobile_v2_test_report.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "info": info,
                    "success_rate": (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
                },
                "results": self.results,
                "test_data": self.test_data
            }, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")

    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}     Mobile App V2 API Endpoint Testing{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"Backend URL: {BASE_URL}")
        print(f"Tenant ID: {TENANT_ID}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check backend connectivity
        print(f"\n{Fore.CYAN}═══ Checking Backend Connectivity ═══{Style.RESET_ALL}")
        status_code, data = self.make_request("GET", "/health")
        if status_code == 200:
            print(f"  {Fore.GREEN}✓ Backend is running and healthy{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Backend is not responding on {BASE_URL}{Style.RESET_ALL}")
            print(f"  Please ensure the backend is running: cd src/Backend && python main_server.py")
            return

        # Run test categories
        self.test_identity_access()
        self.test_products()
        self.test_inventory()
        self.test_cart_orders()
        self.test_stores_tenants()
        self.test_delivery()
        self.test_customer_engagement()
        self.test_ai_conversation()
        self.test_pricing_promotions()

        # Generate report
        self.generate_report()

        # Cleanup - logout
        if tokens["access_token"]:
            print(f"\n{Fore.CYAN}═══ Cleanup ═══{Style.RESET_ALL}")
            status_code, _ = self.make_request("POST", "/api/v2/identity-access/auth/logout")
            if status_code == 200:
                print(f"  {Fore.GREEN}✓ Logged out successfully{Style.RESET_ALL}")

def main():
    tester = EndpointTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()