#!/usr/bin/env python3
"""
Seed Admin Users Script
Creates test admin users for development and testing
Run: python scripts/seed_admin_users.py
"""

import asyncio
import asyncpg
import bcrypt
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5434)),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123')
}

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

async def create_admin_users():
    """Create test admin users"""
    
    # Connect to database
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        print("🚀 Starting admin user seed process...")
        
        # Test users to create
        test_users = [
            {
                'email': 'admin@potpalace.ca',
                'password': 'Admin123!',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'super_admin',
                'description': 'Super Admin - Full system access'
            },
            {
                'email': 'manager@potpalace.ca',
                'password': 'Manager123!',
                'first_name': 'John',
                'last_name': 'Manager',
                'role': 'admin',
                'description': 'Platform Admin - Manage multiple tenants'
            },
            {
                'email': 'tenant.admin@leafygreens.ca',
                'password': 'Tenant123!',
                'first_name': 'Sarah',
                'last_name': 'Green',
                'role': 'manager',
                'description': 'Tenant Admin - Leafy Greens dispensary'
            },
            {
                'email': 'store.manager@downtown.ca',
                'password': 'Store123!',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'role': 'manager',
                'description': 'Store Manager - Downtown location'
            }
        ]
        
        # Create or update users
        for user_data in test_users:
            # Check if user exists
            existing = await conn.fetchrow(
                "SELECT id, email FROM users WHERE email = $1",
                user_data['email']
            )
            
            if existing:
                # Update password
                await conn.execute("""
                    UPDATE users 
                    SET password_hash = $1,
                        first_name = $2,
                        last_name = $3,
                        role = $4,
                        active = true,
                        email_verified = true,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE email = $5
                """, hash_password(user_data['password']),
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['role'],
                    user_data['email'])
                
                print(f"✅ Updated: {user_data['email']} - {user_data['description']}")
            else:
                # Create new user
                user_id = await conn.fetchval("""
                    INSERT INTO users (
                        email, password_hash, first_name, last_name,
                        role, active, email_verified, created_at
                    ) VALUES ($1, $2, $3, $4, $5, true, true, CURRENT_TIMESTAMP)
                    RETURNING id
                """, user_data['email'],
                    hash_password(user_data['password']),
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['role'])
                
                print(f"✅ Created: {user_data['email']} - {user_data['description']}")
        
        # Create sample tenant if not exists
        tenant_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM tenants WHERE code = 'LEAFY001')"
        )
        
        if not tenant_exists:
            tenant_id = await conn.fetchval("""
                INSERT INTO tenants (
                    name, code, status, contact_email, contact_phone,
                    address, currency, subscription_tier, 
                    company_name, settings, created_at
                ) VALUES (
                    'Leafy Greens Cannabis',
                    'LEAFY001',
                    'active',
                    'info@leafygreens.ca',
                    '+1-416-555-0100',
                    jsonb_build_object(
                        'street', '123 Cannabis Street',
                        'city', 'Toronto',
                        'province', 'ON',
                        'postal_code', 'M5V 3A8',
                        'country', 'CA'
                    ),
                    'CAD',
                    'enterprise',
                    'Leafy Greens Cannabis Inc.',
                    jsonb_build_object(
                        'timezone', 'America/Toronto',
                        'language', 'en'
                    ),
                    CURRENT_TIMESTAMP
                ) RETURNING id
            """)
            print(f"✅ Created test tenant: Leafy Greens Cannabis")
            
            # Link tenant admin to tenant
            tenant_admin = await conn.fetchrow(
                "SELECT id FROM users WHERE email = 'tenant.admin@leafygreens.ca'"
            )
            
            if tenant_admin:
                # Removed tenant_users table reference
                # User-tenant association handled differently now
                print(f"✅ Tenant admin user exists for Leafy Greens")
            
            # Get Ontario province ID
            ontario_id = await conn.fetchval(
                "SELECT id FROM provinces_territories WHERE code = 'ON'"
            )
            
            # Create sample store
            store_id = await conn.fetchval("""
                INSERT INTO stores (
                    tenant_id, province_territory_id, name, store_code, 
                    address, phone, email, timezone, status, created_at
                ) VALUES (
                    $1,
                    $2,
                    'Downtown Location',
                    'DT001',
                    jsonb_build_object(
                        'street', '456 Queen Street West',
                        'city', 'Toronto',
                        'province', 'ON',
                        'postal_code', 'M5V 2B2',
                        'country', 'CA'
                    ),
                    '+1-416-555-0101',
                    'downtown@leafygreens.ca',
                    'America/Toronto',
                    'active',
                    CURRENT_TIMESTAMP
                ) RETURNING id
            """, tenant_id, ontario_id)
            print(f"✅ Created test store: Downtown Location")
            
            # Link store manager to store
            store_manager = await conn.fetchrow(
                "SELECT id FROM users WHERE email = 'store.manager@downtown.ca'"
            )
            
            if store_manager:
                # Removed store_users table reference
                # User-store association handled differently now
                print(f"✅ Store manager user exists for Downtown Location")
        
        print("\n" + "="*60)
        print("🎉 Admin users seed completed successfully!")
        print("="*60)
        print("\n📝 Test Credentials:")
        print("-"*40)
        for user in test_users:
            print(f"Email: {user['email']}")
            print(f"Password: {user['password']}")
            print(f"Role: {user['description']}")
            print("-"*40)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

async def run_migrations():
    """Run the admin auth migrations first"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Read and execute migration
        migration_path = Path(__file__).parent.parent / 'migrations' / '012_admin_auth_tables.sql'
        
        if migration_path.exists():
            print("📦 Running admin auth migrations...")
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration
            await conn.execute(migration_sql)
            print("✅ Migrations completed")
        else:
            print("⚠️  Migration file not found, skipping...")
    
    except Exception as e:
        print(f"⚠️  Migration error (may already exist): {e}")
    finally:
        await conn.close()

async def main():
    """Main function"""
    # Run migrations first
    await run_migrations()
    
    # Create admin users
    await create_admin_users()

if __name__ == '__main__':
    asyncio.run(main())