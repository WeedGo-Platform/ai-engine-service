#!/usr/bin/env python3
"""
Create Super Admin User
Creates a super admin user in the database with the specified credentials
"""

import asyncio
import asyncpg
import bcrypt
import os
import sys
from datetime import datetime
from uuid import uuid4

# Configuration
ADMIN_EMAIL = "admin@weedgo.ca"
ADMIN_PASSWORD = "Password1$"
ADMIN_ROLE = "super_admin"

async def create_super_admin():
    """Create super admin user in database"""

    # Get database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }

    print(f"🔌 Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to database")

        # Check if user already exists
        existing_user = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE email = $1",
            ADMIN_EMAIL
        )

        if existing_user:
            print(f"⚠️  User {ADMIN_EMAIL} already exists:")
            print(f"   ID: {existing_user['id']}")
            print(f"   Role: {existing_user['role']}")

            # Update role to super_admin if needed
            if existing_user['role'] != ADMIN_ROLE:
                print(f"🔄 Updating role from '{existing_user['role']}' to '{ADMIN_ROLE}'...")
                await conn.execute(
                    """
                    UPDATE users
                    SET role = $1::user_role_simple,
                        tenant_id = NULL,
                        updated_at = $2
                    WHERE id = $3
                    """,
                    ADMIN_ROLE,
                    datetime.utcnow(),
                    existing_user['id']
                )
                print("✅ Role updated to super_admin")

            # Update password
            print("🔐 Updating password...")
            password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = $2 WHERE id = $3",
                password_hash,
                datetime.utcnow(),
                existing_user['id']
            )
            print("✅ Password updated")

            user_id = existing_user['id']
        else:
            # Hash the password
            print("🔐 Hashing password...")
            password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Create new user
            print(f"👤 Creating new super admin user: {ADMIN_EMAIL}")
            user_id = str(uuid4())

            await conn.execute(
                """
                INSERT INTO users (
                    id,
                    email,
                    password_hash,
                    role,
                    active,
                    email_verified,
                    tenant_id,
                    created_at,
                    updated_at
                ) VALUES (
                    $1::uuid,
                    $2,
                    $3,
                    $4::user_role_simple,
                    true,
                    true,
                    NULL,
                    $5,
                    $5
                )
                """,
                user_id,
                ADMIN_EMAIL,
                password_hash,
                ADMIN_ROLE,
                datetime.utcnow()
            )
            print("✅ Super admin user created successfully!")

        print("\n" + "="*60)
        print("✅ SUPER ADMIN CREDENTIALS")
        print("="*60)
        print(f"Email:    {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        print(f"Role:     {ADMIN_ROLE}")
        print(f"User ID:  {user_id}")
        print("="*60)
        print("\n⚠️  Please change the password after first login!")

        await conn.close()
        print("\n✅ Database connection closed")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n🚀 Creating Super Admin User\n")
    asyncio.run(create_super_admin())
