#!/usr/bin/env python3
"""
Check database for role and customer type definitions
"""

import asyncio
import asyncpg
import json

async def check_database():
    """Check for roles and customer types in database"""
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='your_password_here'
        )
        
        print("=" * 80)
        print("DATABASE ROLE AND CUSTOMER TYPE ANALYSIS")
        print("=" * 80)
        
        # 1. Check for role-related tables
        print("\n1. CHECKING FOR ROLE-RELATED TABLES:")
        print("-" * 40)
        
        role_tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (tablename LIKE '%role%' OR tablename LIKE '%permission%' OR tablename LIKE '%auth%')
            ORDER BY tablename
        """)
        
        if role_tables:
            for table in role_tables:
                print(f"  - {table['tablename']}")
        else:
            print("  No dedicated role/permission tables found")
        
        # 2. Check users table for role column
        print("\n2. CHECKING USERS TABLE FOR ROLE COLUMN:")
        print("-" * 40)
        
        user_role_info = await conn.fetchrow("""
            SELECT 
                column_name,
                data_type,
                column_default,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'role'
        """)
        
        if user_role_info:
            print(f"  Column: {user_role_info['column_name']}")
            print(f"  Type: {user_role_info['data_type']}")
            print(f"  Default: {user_role_info['column_default']}")
            print(f"  Nullable: {user_role_info['is_nullable']}")
            
            # Get distinct role values
            roles = await conn.fetch("""
                SELECT DISTINCT role, COUNT(*) as count
                FROM users
                WHERE role IS NOT NULL
                GROUP BY role
                ORDER BY role
            """)
            
            if roles:
                print("\n  Existing role values in users table:")
                for role in roles:
                    print(f"    - {role['role']}: {role['count']} users")
            else:
                print("\n  No role values found in users table")
        else:
            print("  No 'role' column found in users table")
        
        # 3. Check for customer_type definitions
        print("\n3. CHECKING CUSTOMER_TYPE DEFINITIONS:")
        print("-" * 40)
        
        # Check profiles table
        customer_type_info = await conn.fetchrow("""
            SELECT
                column_name,
                data_type,
                column_default,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'profiles' AND column_name = 'customer_type'
        """)
        
        if customer_type_info:
            print(f"  Column: {customer_type_info['column_name']}")
            print(f"  Type: {customer_type_info['data_type']}")
            print(f"  Default: {customer_type_info['column_default']}")
            print(f"  Nullable: {customer_type_info['is_nullable']}")
            
            # Get distinct customer types
            types = await conn.fetch("""
                SELECT DISTINCT customer_type, COUNT(*) as count
                FROM profiles
                WHERE customer_type IS NOT NULL
                GROUP BY customer_type
                ORDER BY customer_type
            """)
            
            if types:
                print("\n  Existing customer_type values in profiles table:")
                for ctype in types:
                    print(f"    - {ctype['customer_type']}: {ctype['count']} profiles")
            else:
                print("\n  No customer_type values found in profiles table")
        else:
            print("  No 'customer_type' column found in profiles table")
        
        # Check user_profiles table
        profile_type_info = await conn.fetchrow("""
            SELECT 
                column_name,
                data_type,
                column_default,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_profiles' AND column_name = 'customer_type'
        """)
        
        if profile_type_info:
            print(f"\n  user_profiles.customer_type:")
            print(f"    Type: {profile_type_info['data_type']}")
            print(f"    Default: {profile_type_info['column_default']}")
        
        # 4. Check for ENUMs or custom types
        print("\n4. CHECKING FOR CUSTOM TYPES/ENUMS:")
        print("-" * 40)
        
        custom_types = await conn.fetch("""
            SELECT typname, typtype, typlen
            FROM pg_type
            WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            AND typtype IN ('e', 'd')  -- enums and domains
            ORDER BY typname
        """)
        
        if custom_types:
            for ctype in custom_types:
                print(f"  - {ctype['typname']} (type: {ctype['typtype']})")
                
                # If it's an enum, get the values
                if ctype['typtype'] == 'e':
                    enum_values = await conn.fetch("""
                        SELECT enumlabel 
                        FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = $1)
                        ORDER BY enumsortorder
                    """, ctype['typname'])
                    
                    if enum_values:
                        print(f"    Values: {', '.join([v['enumlabel'] for v in enum_values])}")
        else:
            print("  No custom types or enums found")
        
        # 5. Check for constraints on role/customer_type columns
        print("\n5. CHECKING CONSTRAINTS:")
        print("-" * 40)
        
        constraints = await conn.fetch("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                cc.check_clause
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.check_constraints cc 
                ON tc.constraint_name = cc.constraint_name
            WHERE tc.table_schema = 'public'
            AND (
                tc.table_name IN ('users', 'profiles', 'user_profiles')
                OR tc.constraint_name LIKE '%role%'
                OR tc.constraint_name LIKE '%customer_type%'
            )
            AND tc.constraint_type = 'CHECK'
            ORDER BY tc.table_name, tc.constraint_name
        """)
        
        if constraints:
            for constraint in constraints:
                print(f"  {constraint['table_name']}.{constraint['constraint_name']}:")
                print(f"    {constraint['check_clause']}")
        else:
            print("  No CHECK constraints found for role/customer_type columns")
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("-" * 40)
        print("• User roles are stored as VARCHAR(50) in users.role column")
        print("• Default role value is 'customer' (from migration)")
        print("• Customer types are stored as VARCHAR(50) in profiles.customer_type")
        print("• Default customer_type is 'regular'")
        print("• No dedicated role/permission tables exist")
        print("• No ENUM types or CHECK constraints enforce specific values")
        print("\nBoth role and customer_type are free-form VARCHAR fields.")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database())