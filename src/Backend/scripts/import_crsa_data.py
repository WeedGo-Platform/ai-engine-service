#!/usr/bin/env python3
"""
Import Ontario CRSA Status Data from AGCO CSV
============================================

This script imports Cannabis Retail Store Authorization data from the AGCO CSV file
into the ontario_crsa_status table.

Usage:
    python import_crsa_data.py /path/to/csv/file.csv
    python import_crsa_data.py --download  # Downloads latest from AGCO (if available)
"""

import asyncio
import asyncpg
import csv
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123'),
    'database': os.getenv('DB_NAME', 'ai_engine'),
}

# CSV column mapping (AGCO format)
CSV_COLUMNS = {
    'License Number': 'license_number',
    'Municipality or First Nation': 'municipality_or_first_nation',
    'Store Name': 'store_name',
    'Address': 'address',
    'Store Application Status': 'store_application_status',
    'Website': 'website',
}


async def get_db_pool() -> asyncpg.Pool:
    """Create database connection pool"""
    return await asyncpg.create_pool(**DB_CONFIG)


def parse_municipality_first_nation(value: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse municipality or first nation field

    Returns: (municipality, first_nation)
    """
    if not value or value.strip() == '':
        return (None, None)

    value = value.strip()

    # Check if it's a First Nation (usually contains specific keywords)
    first_nation_keywords = ['First Nation', 'FN', 'Nation']
    is_first_nation = any(keyword in value for keyword in first_nation_keywords)

    if is_first_nation:
        return (None, value)
    else:
        return (value, None)


def clean_csv_value(value: str) -> Optional[str]:
    """Clean and normalize CSV values"""
    if not value or value.strip() == '':
        return None
    return value.strip()


async def upsert_crsa_record(
    pool: asyncpg.Pool,
    record: Dict[str, any],
    is_initial_load: bool = False
) -> str:
    """
    Insert or update a CRSA record

    Returns: 'inserted', 'updated', or 'skipped'
    """
    async with pool.acquire() as conn:
        # Check if record exists
        existing = await conn.fetchrow(
            "SELECT id, store_name, address, store_application_status FROM ontario_crsa_status WHERE license_number = $1",
            record['license_number']
        )

        if existing:
            # Check if data has changed
            has_changes = (
                existing['store_name'] != record['store_name'] or
                existing['address'] != record['address'] or
                existing['store_application_status'] != record['store_application_status']
            )

            if has_changes or not is_initial_load:
                # Update existing record
                await conn.execute("""
                    UPDATE ontario_crsa_status SET
                        municipality = $2,
                        first_nation = $3,
                        store_name = $4,
                        address = $5,
                        store_application_status = $6,
                        website = $7,
                        last_synced_at = NOW(),
                        is_active = TRUE
                    WHERE license_number = $1
                """,
                    record['license_number'],
                    record['municipality'],
                    record['first_nation'],
                    record['store_name'],
                    record['address'],
                    record['store_application_status'],
                    record['website']
                )
                return 'updated'
            else:
                # No changes, just update sync time
                await conn.execute(
                    "UPDATE ontario_crsa_status SET last_synced_at = NOW() WHERE license_number = $1",
                    record['license_number']
                )
                return 'skipped'
        else:
            # Insert new record
            await conn.execute("""
                INSERT INTO ontario_crsa_status (
                    license_number,
                    municipality,
                    first_nation,
                    store_name,
                    address,
                    store_application_status,
                    website,
                    first_seen_at,
                    last_synced_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """,
                record['license_number'],
                record['municipality'],
                record['first_nation'],
                record['store_name'],
                record['address'],
                record['store_application_status'],
                record['website']
            )
            return 'inserted'


async def mark_removed_stores(pool: asyncpg.Pool, current_licenses: List[str]):
    """Mark stores that are no longer in the CSV as inactive"""
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE ontario_crsa_status
            SET is_active = FALSE
            WHERE license_number NOT IN (SELECT unnest($1::text[]))
              AND is_active = TRUE
        """, current_licenses)

        count = int(result.split()[-1])
        if count > 0:
            logger.warning(f"Marked {count} stores as inactive (removed from AGCO list)")


async def import_csv(file_path: str, is_initial_load: bool = False):
    """Import CSV data into database"""

    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    logger.info(f"Starting import from: {file_path}")
    logger.info(f"Mode: {'Initial Load' if is_initial_load else 'Sync Update'}")

    # Read CSV
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate CSV headers
            expected_headers = set(CSV_COLUMNS.keys())
            actual_headers = set(reader.fieldnames or [])

            if not expected_headers.issubset(actual_headers):
                missing = expected_headers - actual_headers
                logger.error(f"CSV missing required columns: {missing}")
                logger.info(f"Found columns: {actual_headers}")
                return False

            # Parse rows
            for row_num, row in enumerate(reader, start=2):
                license_num = clean_csv_value(row.get('License Number'))
                store_name = clean_csv_value(row.get('Store Name'))
                address = clean_csv_value(row.get('Address'))
                status = clean_csv_value(row.get('Store Application Status'))

                # Skip rows without required fields
                # Note: "In Progress" and "Public Notice" applications may not have license numbers yet
                if not store_name or not address or not status:
                    logger.warning(f"Row {row_num}: Skipping incomplete record (missing store name, address, or status)")
                    continue
                
                # Generate placeholder license number for pending applications
                if not license_num:
                    if status in ['In Progress', 'Public Notice']:
                        # Use hash of store name + address as unique identifier
                        import hashlib
                        unique_str = f"{store_name}|{address}".lower()
                        hash_val = hashlib.md5(unique_str.encode()).hexdigest()[:12]
                        license_num = f"PENDING-{hash_val}"
                        logger.info(f"Row {row_num}: Generated placeholder license for {status} application: {license_num}")
                    else:
                        logger.warning(f"Row {row_num}: Skipping record without license number (status: {status})")
                        continue

                # Parse municipality/first nation
                muni_fn = clean_csv_value(row.get('Municipality or First Nation'))
                municipality, first_nation = parse_municipality_first_nation(muni_fn)

                records.append({
                    'license_number': license_num,
                    'municipality': municipality,
                    'first_nation': first_nation,
                    'store_name': store_name,
                    'address': address,
                    'store_application_status': status,
                    'website': clean_csv_value(row.get('Website')),
                })

        logger.info(f"Parsed {len(records)} valid records from CSV")

    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return False

    if not records:
        logger.error("No valid records found in CSV")
        return False

    # Import to database
    pool = await get_db_pool()

    try:
        stats = {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        for idx, record in enumerate(records, start=1):
            try:
                result = await upsert_crsa_record(pool, record, is_initial_load)
                stats[result] += 1

                # Progress indicator
                if idx % 100 == 0:
                    logger.info(f"Progress: {idx}/{len(records)} records processed")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error importing {record['license_number']}: {e}")

        # Mark removed stores as inactive
        if not is_initial_load:
            all_licenses = [r['license_number'] for r in records]
            await mark_removed_stores(pool, all_licenses)

        # Final statistics
        logger.info("=" * 60)
        logger.info("Import Summary:")
        logger.info(f"  ✅ Inserted: {stats['inserted']}")
        logger.info(f"  🔄 Updated:  {stats['updated']}")
        logger.info(f"  ⏭️  Skipped:  {stats['skipped']}")
        logger.info(f"  ❌ Errors:   {stats['errors']}")
        logger.info(f"  📊 Total:    {len(records)}")
        logger.info("=" * 60)

        # Query database statistics
        async with pool.acquire() as conn:
            db_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE store_application_status = 'Authorized') as authorized,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active,
                    COUNT(*) FILTER (WHERE linked_tenant_id IS NOT NULL) as linked
                FROM ontario_crsa_status
            """)

            logger.info("Database Statistics:")
            logger.info(f"  Total records: {db_stats['total']}")
            logger.info(f"  Authorized: {db_stats['authorized']}")
            logger.info(f"  Active: {db_stats['active']}")
            logger.info(f"  Linked to tenants: {db_stats['linked']}")

        return True

    finally:
        await pool.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import Ontario CRSA data from CSV')
    parser.add_argument('csv_file', nargs='?', help='Path to CSV file')
    parser.add_argument('--initial', action='store_true', help='Initial load (skips unchanged records)')
    parser.add_argument('--download', action='store_true', help='Download latest CSV from AGCO (not yet implemented)')

    args = parser.parse_args()

    if args.download:
        logger.error("Download feature not yet implemented")
        logger.info("Please download CSV manually from:")
        logger.info("https://www.agco.ca/en/cannabis/status-current-cannabis-retail-store-applications")
        sys.exit(1)

    if not args.csv_file:
        logger.error("CSV file path required")
        parser.print_help()
        sys.exit(1)

    # Run import
    success = asyncio.run(import_csv(args.csv_file, is_initial_load=args.initial))

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
