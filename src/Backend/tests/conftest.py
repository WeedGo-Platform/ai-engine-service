"""
Pytest Configuration and Shared Fixtures
Provides database setup, test data factories, and common utilities
"""

import pytest
import asyncio
import asyncpg
from uuid import uuid4
from typing import AsyncGenerator
import json

# Database configuration for testing
TEST_DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine_test',  # Separate test database
    'user': 'weedgo',
    'password': 'your_password_here',
}


@pytest.fixture
async def db_connection():
    """
    Provide database connection with automatic transaction rollback
    Each test runs in a transaction that's rolled back after test completes
    """
    # Create a new connection for each test
    conn = await asyncpg.connect(**TEST_DB_CONFIG)

    # Start transaction
    transaction = conn.transaction()
    await transaction.start()

    yield conn

    # Rollback transaction (cleanup)
    try:
        await transaction.rollback()
    except Exception:
        pass  # Already rolled back

    # Close connection
    await conn.close()


@pytest.fixture
async def test_user(db_connection):
    """Create test user and profile"""
    user_id = uuid4()

    # Create user
    await db_connection.execute("""
        INSERT INTO users (id, email, phone, first_name, last_name, password_hash, active, role)
        VALUES ($1, $2, $3, $4, $5, $6, true, 'customer')
    """, user_id, f'test_{user_id}@example.com', '4161234567', 'Test', 'User', 'hashed')

    # Create profile with payment method
    payment_method = {
        'id': str(uuid4()),
        'type': 'card',
        'nickname': 'Test Card',
        'card_brand': 'Visa',
        'last4': '4242',
        'is_default': True,
        'created_at': '2024-01-01T00:00:00Z'
    }

    await db_connection.execute("""
        INSERT INTO profiles (user_id, first_name, last_name, phone, payment_methods)
        VALUES ($1, $2, $3, $4, $5::jsonb)
    """, user_id, 'Test', 'User', '4161234567', json.dumps([payment_method]))

    return {
        'user_id': user_id,
        'email': f'test_{user_id}@example.com',
        'payment_method_id': payment_method['id']
    }


@pytest.fixture
async def test_store(db_connection):
    """Create test store"""
    # First get or create tenant
    tenant_id = await db_connection.fetchval("""
        INSERT INTO tenants (id, name, code)
        VALUES ($1, 'Test Tenant', 'test-tenant')
        ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
        RETURNING id
    """, uuid4())

    store_id = uuid4()
    await db_connection.execute("""
        INSERT INTO stores (id, tenant_id, name, store_code, status)
        VALUES ($1, $2, $3, $4, 'active')
        ON CONFLICT (store_code) DO NOTHING
    """, store_id, tenant_id, 'Test Store', 'test-store-001')

    return {'store_id': store_id, 'tenant_id': tenant_id}


@pytest.fixture
async def test_inventory(db_connection, test_store):
    """Create test inventory items"""
    items = []

    for i in range(5):
        sku = f'TEST-SKU-{i:03d}'
        await db_connection.execute("""
            INSERT INTO ocs_inventory (
                sku, product_name, price, quantity_available,
                quantity_reserved, is_available, store_id
            )
            VALUES ($1, $2, $3, $4, $5, true, $6)
            ON CONFLICT (sku, store_id) DO UPDATE
            SET quantity_available = EXCLUDED.quantity_available
        """, sku, f'Test Product {i}', 19.99 + i, 100, 0, test_store['store_id'])

        items.append({
            'sku': sku,
            'name': f'Test Product {i}',
            'price': 19.99 + i,
            'quantity_available': 100
        })

    return items


@pytest.fixture
async def test_cart(db_connection, test_user, test_store, test_inventory):
    """Create test cart session with items"""
    cart_id = uuid4()

    # Prepare cart items
    cart_items = [
        {
            'sku': test_inventory[0]['sku'],
            'name': test_inventory[0]['name'],
            'quantity': 2,
            'price': test_inventory[0]['price']
        },
        {
            'sku': test_inventory[1]['sku'],
            'name': test_inventory[1]['name'],
            'quantity': 1,
            'price': test_inventory[1]['price']
        }
    ]

    await db_connection.execute("""
        INSERT INTO cart_sessions (
            id, user_id, store_id, items, status
        )
        VALUES ($1, $2, $3, $4::jsonb, 'active')
    """, cart_id, test_user['user_id'], test_store['store_id'], json.dumps(cart_items))

    return {
        'cart_id': cart_id,
        'items': cart_items,
        'user_id': test_user['user_id'],
        'store_id': test_store['store_id']
    }


# Markers for different test categories
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "concurrency: Concurrency/race condition tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
