#!/usr/bin/env python3
"""
Script to create a super admin user in the database
"""

import bcrypt
import asyncpg
import asyncio
import os
from uuid import uuid4

async def create_super_admin():
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }

    # User details
    email = 'admin@weedgo.ca'
    password = 'Password1$'

    # Hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    # Connect to database
    conn = await asyncpg.connect(**db_config)

    try:
        # Check if user already exists
        existing = await conn.fetchrow(
            "SELECT id, email FROM users WHERE email = $1",
            email
        )

        if existing:
            print(f"User {email} already exists with ID: {existing['id']}")
            # Update the user to be super_admin
            await conn.execute(
                """
                UPDATE users
                SET role = 'super_admin',
                    password_hash = $1,
                    tenant_id = NULL,
                    store_id = NULL,
                    first_name = 'Super',
                    last_name = 'Admin',
                    active = true,
                    email_verified = true,
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = $2
                """,
                password_hash,
                email
            )
            print(f"Updated user {email} to super_admin role with new password")
        else:
            # Create new user
            user_id = await conn.fetchval(
                """
                INSERT INTO users (
                    id,
                    email,
                    password_hash,
                    first_name,
                    last_name,
                    role,
                    tenant_id,
                    store_id,
                    active,
                    email_verified,
                    terms_accepted,
                    created_at,
                    updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING id
                """,
                uuid4(),
                email,
                password_hash,
                'Super',
                'Admin',
                'super_admin',
                None,  # tenant_id is NULL for super_admin
                None,  # store_id is NULL for super_admin
                True,  # active
                True,  # email_verified
                True   # terms_accepted
            )
            print(f"Created super admin user: {email} with ID: {user_id}")

        # Verify the user was created/updated correctly
        user = await conn.fetchrow(
            """
            SELECT id, email, role, tenant_id, store_id, active
            FROM users
            WHERE email = $1
            """,
            email
        )

        print("\nUser details:")
        print(f"  ID: {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        print(f"  Tenant ID: {user['tenant_id']}")
        print(f"  Store ID: {user['store_id']}")
        print(f"  Active: {user['active']}")
        print(f"\nCredentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_super_admin())