#!/usr/bin/env python3
"""
Display all tables and columns in the database
"""

import asyncio
import asyncpg
import os
from tabulate import tabulate

async def show_database_schema():
    """Show all tables and columns in the database"""
    
    # Database connection settings
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here')
    }
    
    # Connect to database
    conn = await asyncpg.connect(**db_config)
    
    try:
        # Query to get all tables and columns
        query = """
            SELECT 
                t.table_name,
                array_agg(
                    c.column_name || ' (' || 
                    c.data_type || 
                    CASE 
                        WHEN c.character_maximum_length IS NOT NULL 
                        THEN '(' || c.character_maximum_length || ')'
                        ELSE ''
                    END ||
                    CASE 
                        WHEN c.is_nullable = 'NO' THEN ' NOT NULL'
                        ELSE ''
                    END ||
                    CASE 
                        WHEN c.column_default IS NOT NULL 
                        THEN ' DEFAULT ' || 
                            CASE 
                                WHEN c.column_default LIKE 'nextval%' THEN 'AUTO'
                                WHEN c.column_default LIKE '%CURRENT%' THEN 'CURRENT_TIMESTAMP'
                                WHEN c.column_default LIKE '%uuid_generate%' THEN 'UUID'
                                ELSE substring(c.column_default, 1, 20)
                            END
                        ELSE ''
                    END ||
                    ')' 
                    ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name
            ORDER BY t.table_name;
        """
        
        results = await conn.fetch(query)
        
        print("\n" + "="*80)
        print("📊 DATABASE SCHEMA - All Tables and Columns")
        print("="*80)
        
        for row in results:
            table_name = row['table_name']
            columns = row['columns']
            
            print(f"\n📋 Table: {table_name}")
            print("-" * 60)
            
            for i, col in enumerate(columns, 1):
                print(f"  {i:2}. {col}")
        
        # Get counts
        count_query = """
            SELECT 
                (SELECT COUNT(*) FROM information_schema.tables 
                 WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as table_count,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_schema = 'public') as column_count,
                (SELECT COUNT(*) FROM information_schema.views 
                 WHERE table_schema = 'public') as view_count
        """
        
        counts = await conn.fetchrow(count_query)
        
        print("\n" + "="*80)
        print("📈 DATABASE STATISTICS")
        print("="*80)
        print(f"  • Total Tables: {counts['table_count']}")
        print(f"  • Total Columns: {counts['column_count']}")
        print(f"  • Total Views: {counts['view_count']}")
        
        # Show views
        view_query = """
            SELECT table_name as view_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        
        views = await conn.fetch(view_query)
        
        if views:
            print("\n📐 Views:")
            for view in views:
                print(f"  • {view['view_name']}")
        
        # Show table sizes
        size_query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """
        
        sizes = await conn.fetch(size_query)
        
        print("\n📦 Top Tables by Size:")
        print("-" * 60)
        
        table_data = []
        for size_row in sizes:
            table_data.append([
                size_row['tablename'],
                size_row['size'],
                f"{size_row['row_count']:,}" if size_row['row_count'] else "0"
            ])
        
        if table_data:
            print(tabulate(table_data, headers=["Table", "Size", "Rows"], tablefmt="simple"))
        
        print("\n" + "="*80)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(show_database_schema())