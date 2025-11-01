#!/usr/bin/env python3
"""
Data Migration Script: Provinces/Territories & Provincial Suppliers
Migrates reference data from legacy database to current database

Date: October 12, 2025
"""

import psycopg2
import psycopg2.extras
import json
import sys
from typing import List, Dict, Tuple

# Database configurations
LEGACY_DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # Legacy database
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

CURRENT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,  # Current database
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

class DataMigrator:
    """Handles data migration between databases"""

    def __init__(self):
        self.legacy_conn = None
        self.current_conn = None
        self.stats = {
            'provinces_migrated': 0,
            'suppliers_migrated': 0,
            'provinces_skipped': 0,
            'suppliers_skipped': 0,
            'errors': []
        }

    def connect(self):
        """Connect to both databases"""
        print("🔌 Connecting to databases...")
        try:
            self.legacy_conn = psycopg2.connect(**LEGACY_DB_CONFIG)
            print(f"  ✅ Connected to legacy database (port {LEGACY_DB_CONFIG['port']})")

            self.current_conn = psycopg2.connect(**CURRENT_DB_CONFIG)
            print(f"  ✅ Connected to current database (port {CURRENT_DB_CONFIG['port']})")

            return True
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    def close(self):
        """Close database connections"""
        if self.legacy_conn:
            self.legacy_conn.close()
        if self.current_conn:
            self.current_conn.close()
        print("🔌 Database connections closed")

    def fetch_provinces_territories(self) -> List[Dict]:
        """Fetch all provinces/territories from legacy database"""
        print("\n📊 Fetching provinces/territories from legacy database...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("""
            SELECT
                id, code, name, type, tax_rate, min_age,
                regulatory_body, license_prefix, delivery_allowed,
                pickup_allowed, settings, created_at, updated_at
            FROM provinces_territories
            ORDER BY code
        """)

        columns = [desc[0] for desc in cursor.description]
        provinces = []

        for row in cursor.fetchall():
            province = dict(zip(columns, row))
            provinces.append(province)

        cursor.close()
        print(f"  ✅ Found {len(provinces)} provinces/territories")

        return provinces

    def fetch_provincial_suppliers(self) -> List[Dict]:
        """Fetch all provincial suppliers from legacy database"""
        print("\n📊 Fetching provincial suppliers from legacy database...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("""
            SELECT
                id, name, contact_person, email, phone, address,
                payment_terms, is_active, provinces_territories_id,
                is_provincial_supplier, tenant_id,
                created_at, updated_at
            FROM provincial_suppliers
            ORDER BY name
        """)

        columns = [desc[0] for desc in cursor.description]
        suppliers = []

        for row in cursor.fetchall():
            supplier = dict(zip(columns, row))
            suppliers.append(supplier)

        cursor.close()
        print(f"  ✅ Found {len(suppliers)} provincial suppliers")

        return suppliers

    def migrate_provinces_territories(self, provinces: List[Dict]) -> bool:
        """Migrate provinces/territories to current database"""
        print("\n🔄 Migrating provinces/territories...")

        cursor = self.current_conn.cursor()

        for province in provinces:
            try:
                # Check if province already exists
                cursor.execute(
                    "SELECT id FROM provinces_territories WHERE id = %s",
                    (province['id'],)
                )

                if cursor.fetchone():
                    print(f"  ⏭️  Skipping {province['code']} - {province['name']} (already exists)")
                    self.stats['provinces_skipped'] += 1
                    continue

                # Convert settings dict to JSON string if needed
                settings = province['settings']
                if isinstance(settings, dict):
                    settings = json.dumps(settings)

                # Insert province
                cursor.execute("""
                    INSERT INTO provinces_territories (
                        id, code, name, type, tax_rate, min_age,
                        regulatory_body, license_prefix, delivery_allowed,
                        pickup_allowed, settings, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s
                    )
                """, (
                    province['id'],
                    province['code'],
                    province['name'],
                    province['type'],
                    province['tax_rate'],
                    province['min_age'],
                    province['regulatory_body'],
                    province['license_prefix'],
                    province['delivery_allowed'],
                    province['pickup_allowed'],
                    settings,
                    province['created_at'],
                    province['updated_at']
                ))

                print(f"  ✅ Migrated: {province['code']} - {province['name']}")
                self.stats['provinces_migrated'] += 1

            except Exception as e:
                error_msg = f"Failed to migrate province {province['code']}: {str(e)}"
                print(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                # Rollback this transaction and continue
                self.current_conn.rollback()

        # Commit all province changes
        self.current_conn.commit()
        cursor.close()

        print(f"\n✅ Provinces migration complete: {self.stats['provinces_migrated']} migrated, {self.stats['provinces_skipped']} skipped")
        return True

    def migrate_provincial_suppliers(self, suppliers: List[Dict]) -> bool:
        """Migrate provincial suppliers to current database"""
        print("\n🔄 Migrating provincial suppliers...")

        cursor = self.current_conn.cursor()

        for supplier in suppliers:
            try:
                # Check if supplier already exists
                cursor.execute(
                    "SELECT id FROM provincial_suppliers WHERE id = %s",
                    (supplier['id'],)
                )

                if cursor.fetchone():
                    print(f"  ⏭️  Skipping {supplier['name']} (already exists)")
                    self.stats['suppliers_skipped'] += 1
                    continue

                # The current database has province_territory_id as NOT NULL
                # Use provinces_territories_id if it exists
                province_id = supplier['provinces_territories_id']

                # Insert supplier - using province_territory_id which is NOT NULL in current schema
                cursor.execute("""
                    INSERT INTO provincial_suppliers (
                        id, name, contact_person, email, phone, address,
                        payment_terms, is_active, province_territory_id,
                        provinces_territories_id,
                        is_provincial_supplier, tenant_id,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    supplier['id'],
                    supplier['name'],
                    supplier['contact_person'],
                    supplier['email'],
                    supplier['phone'],
                    supplier['address'],
                    supplier['payment_terms'],
                    supplier['is_active'],
                    province_id,  # province_territory_id (NOT NULL)
                    province_id,  # provinces_territories_id (legacy column)
                    supplier['is_provincial_supplier'],
                    supplier['tenant_id'],
                    supplier['created_at'],
                    supplier['updated_at']
                ))

                print(f"  ✅ Migrated: {supplier['name']}")
                self.stats['suppliers_migrated'] += 1

            except Exception as e:
                error_msg = f"Failed to migrate supplier {supplier['name']}: {str(e)}"
                print(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                # Rollback this transaction and continue
                self.current_conn.rollback()

        # Commit all supplier changes
        self.current_conn.commit()
        cursor.close()

        print(f"\n✅ Suppliers migration complete: {self.stats['suppliers_migrated']} migrated, {self.stats['suppliers_skipped']} skipped")
        return True

    def verify_migration(self) -> bool:
        """Verify the migration was successful"""
        print("\n🔍 Verifying migration...")

        cursor_legacy = self.legacy_conn.cursor()
        cursor_current = self.current_conn.cursor()

        # Verify provinces count
        cursor_legacy.execute("SELECT COUNT(*) FROM provinces_territories")
        legacy_provinces = cursor_legacy.fetchone()[0]

        cursor_current.execute("SELECT COUNT(*) FROM provinces_territories")
        current_provinces = cursor_current.fetchone()[0]

        print(f"  📊 Provinces: Legacy={legacy_provinces}, Current={current_provinces}")

        if current_provinces < legacy_provinces:
            print(f"  ⚠️  Warning: Current database has fewer provinces than legacy")

        # Verify suppliers count
        cursor_legacy.execute("SELECT COUNT(*) FROM provincial_suppliers")
        legacy_suppliers = cursor_legacy.fetchone()[0]

        cursor_current.execute("SELECT COUNT(*) FROM provincial_suppliers")
        current_suppliers = cursor_current.fetchone()[0]

        print(f"  📊 Suppliers: Legacy={legacy_suppliers}, Current={current_suppliers}")

        if current_suppliers < legacy_suppliers:
            print(f"  ⚠️  Warning: Current database has fewer suppliers than legacy")

        # Verify foreign key relationships
        cursor_current.execute("""
            SELECT COUNT(*)
            FROM provincial_suppliers ps
            LEFT JOIN provinces_territories pt ON ps.provinces_territories_id = pt.id
            WHERE ps.provinces_territories_id IS NOT NULL
            AND pt.id IS NULL
        """)

        orphaned = cursor_current.fetchone()[0]

        if orphaned > 0:
            print(f"  ❌ Found {orphaned} suppliers with invalid province references!")
            return False
        else:
            print(f"  ✅ All foreign key relationships are valid")

        cursor_legacy.close()
        cursor_current.close()

        return True

    def generate_report(self):
        """Generate migration report"""
        print("\n" + "="*80)
        print("DATA MIGRATION REPORT")
        print("="*80)

        print("\n📊 Migration Statistics:")
        print(f"  • Provinces migrated:  {self.stats['provinces_migrated']}")
        print(f"  • Provinces skipped:   {self.stats['provinces_skipped']}")
        print(f"  • Suppliers migrated:  {self.stats['suppliers_migrated']}")
        print(f"  • Suppliers skipped:   {self.stats['suppliers_skipped']}")
        print(f"  • Total errors:        {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\n❌ Errors encountered:")
            for error in self.stats['errors']:
                print(f"  • {error}")

        total_migrated = self.stats['provinces_migrated'] + self.stats['suppliers_migrated']
        total_items = total_migrated + self.stats['provinces_skipped'] + self.stats['suppliers_skipped']
        success_rate = (total_migrated / total_items * 100) if total_items > 0 else 0

        print(f"\n{'='*80}")
        print(f"SUCCESS RATE: {success_rate:.1f}% ({total_migrated}/{total_items} items migrated)")
        print(f"{'='*80}\n")

        if success_rate == 100 and len(self.stats['errors']) == 0:
            print("🎉 Migration completed successfully!")
        elif success_rate >= 80:
            print("⚠️  Migration completed with some items skipped")
        else:
            print("❌ Migration completed with errors")


def main():
    """Main migration function"""
    print("="*80)
    print("DATA MIGRATION: Provinces/Territories & Provincial Suppliers")
    print("="*80)
    print("Source: Legacy Database (port 5433)")
    print("Target: Current Database (port 5434)")
    print("="*80)

    migrator = DataMigrator()

    try:
        # Connect to databases
        if not migrator.connect():
            print("❌ Failed to connect to databases")
            return 1

        # Fetch data from legacy database
        provinces = migrator.fetch_provinces_territories()
        suppliers = migrator.fetch_provincial_suppliers()

        if not provinces and not suppliers:
            print("⚠️  No data to migrate")
            return 0

        # Migrate provinces first (they're referenced by suppliers)
        if provinces:
            if not migrator.migrate_provinces_territories(provinces):
                print("❌ Province migration failed")
                return 1

        # Migrate suppliers
        if suppliers:
            if not migrator.migrate_provincial_suppliers(suppliers):
                print("❌ Supplier migration failed")
                return 1

        # Verify migration
        if not migrator.verify_migration():
            print("⚠️  Migration verification found issues")

        # Generate report
        migrator.generate_report()

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        migrator.close()


if __name__ == '__main__':
    sys.exit(main())
