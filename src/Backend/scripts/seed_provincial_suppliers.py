#!/usr/bin/env python3
"""
Seed Provincial Suppliers for all Canadian Provinces/Territories
"""
import asyncio
import asyncpg
import os
from uuid import uuid4
from datetime import datetime

# Provincial supplier data for all provinces/territories
PROVINCIAL_SUPPLIERS = {
    'ON': {'name': 'Ontario Cannabis Store (OCS)', 'code': 'OCS'},
    'BC': {'name': 'BC Cannabis Stores', 'code': 'BCCS'},
    'AB': {'name': 'Alberta Gaming, Liquor & Cannabis (AGLC)', 'code': 'AGLC'},
    'SK': {'name': 'Saskatchewan Liquor & Gaming Authority (SLGA)', 'code': 'SLGA'},
    'MB': {'name': 'Manitoba Liquor & Lotteries (MBLL)', 'code': 'MBLL'},
    'QC': {'name': 'Société québécoise du cannabis (SQDC)', 'code': 'SQDC'},
    'NB': {'name': 'Cannabis NB', 'code': 'CNB'},
    'NS': {'name': 'Nova Scotia Liquor Corporation (NSLC)', 'code': 'NSLC'},
    'PE': {'name': 'Prince Edward Island Cannabis Management Corporation', 'code': 'PEICMC'},
    'NL': {'name': 'Newfoundland and Labrador Liquor Corporation', 'code': 'NLC'},
    'YT': {'name': 'Yukon Liquor Corporation', 'code': 'YLC'},
    'NT': {'name': 'Northwest Territories Liquor & Cannabis Commission', 'code': 'NTLCC'},
    'NU': {'name': 'Nunavut Liquor & Cannabis Commission', 'code': 'NLCC'},
}

async def seed_provincial_suppliers():
    """Seed provincial suppliers for all provinces/territories"""
    
    # Database connection
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    print("🚀 Seeding Provincial Suppliers\n")
    print(f"🔌 Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to database\n")
        
        # Get all provinces/territories
        provinces = await conn.fetch(
            "SELECT id, code, name FROM provinces_territories ORDER BY name"
        )
        
        province_map = {p['code']: p for p in provinces}
        
        # Insert or update suppliers
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for province_code, supplier_data in PROVINCIAL_SUPPLIERS.items():
            if province_code not in province_map:
                print(f"⚠️  Province {province_code} not found in database, skipping...")
                skipped_count += 1
                continue
            
            province = province_map[province_code]
            
            # Check if supplier already exists
            existing = await conn.fetchrow(
                """SELECT id FROM provincial_suppliers 
                   WHERE province_territory_id = $1 AND is_provincial_supplier = true""",
                province['id']
            )
            
            if existing:
                # Update existing supplier
                await conn.execute(
                    """UPDATE provincial_suppliers 
                       SET name = $1, supplier_code = $2, is_active = true,
                           provinces_territories_id = $3, updated_at = $4
                       WHERE id = $5""",
                    supplier_data['name'],
                    supplier_data['code'],
                    province['id'],
                    datetime.utcnow(),
                    existing['id']
                )
                print(f"✅ Updated: {supplier_data['name']} for {province['name']}")
                updated_count += 1
            else:
                # Insert new supplier
                supplier_id = uuid4()
                await conn.execute(
                    """INSERT INTO provincial_suppliers (
                        id, province_territory_id, provinces_territories_id,
                        name, supplier_code, is_provincial_supplier,
                        is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    supplier_id,
                    province['id'],
                    province['id'],
                    supplier_data['name'],
                    supplier_data['code'],
                    True,  # is_provincial_supplier
                    True,  # is_active
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                print(f"✅ Created: {supplier_data['name']} for {province['name']}")
                created_count += 1
        
        await conn.close()
        
        print(f"\n{'='*60}")
        print(f"✅ SEEDING COMPLETE")
        print(f"{'='*60}")
        print(f"Created: {created_count}")
        print(f"Updated: {updated_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {created_count + updated_count + skipped_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_provincial_suppliers())
