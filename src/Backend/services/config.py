"""
Configuration module for service endpoints
All API endpoints are loaded from environment variables
"""
import os

# Load base URL from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5024")

# Construct service endpoints
PRODUCTS_API = f"{API_BASE_URL}/api/products"
USER_API = f"{API_BASE_URL}/api/user"
CONVERSATION_API = f"{API_BASE_URL}/api/conversation"

# Specific endpoints (use .format() for dynamic parameters)
PRODUCTS_CATEGORIES_ENDPOINT = f"{PRODUCTS_API}/categories"
PRODUCTS_SUBCATEGORIES_ENDPOINT = f"{PRODUCTS_API}/sub-categories"
PRODUCTS_SEARCH_ENDPOINT = PRODUCTS_API

USER_PURCHASES_ENDPOINT = f"{USER_API}/{{user_id}}/purchases"
USER_PREFERENCES_ENDPOINT = f"{USER_API}/{{user_id}}/preferences"

CONVERSATION_HISTORY_ENDPOINT = f"{CONVERSATION_API}/history/{{session_id}}"
