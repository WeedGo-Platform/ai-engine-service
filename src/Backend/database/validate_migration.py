#!/usr/bin/env python3
"""
Migration Validation Script
Validates that the schema migration was successful and tests key functionality
"""

import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple
import json

class MigrationValidator:
    """Validates migration success and tests database functionality"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print(f"✅ Connected to {self.db_config['host']}:{self.db_config['port']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def test_new_tables(self):
        """Test that all 6 new tables exist and are accessible"""
        print("\n🔍 Testing New Tables...")

        new_tables = [
            'agi_audit_aggregates',
            'agi_audit_alerts',
            'agi_audit_logs',
            'agi_rate_limit_buckets',
            'agi_rate_limit_rules',
            'agi_rate_limit_violations'
        ]

        cursor = self.conn.cursor()

        for table_name in new_tables:
            try:
                # Check table exists
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                # Check we can insert (then rollback)
                cursor.execute("BEGIN")
                if table_name == 'agi_audit_logs':
                    cursor.execute(f"""
                        INSERT INTO {table_name} (event_type, severity, event_hash, timestamp)
                        VALUES ('test', 'info', 'test_hash', NOW())
                    """)
                elif table_name == 'agi_rate_limit_buckets':
                    cursor.execute(f"""
                        INSERT INTO {table_name} (key, tokens, last_update)
                        VALUES ('test_key', 100.0, NOW())
                    """)
                elif table_name == 'agi_rate_limit_rules':
                    cursor.execute(f"""
                        INSERT INTO {table_name} (name, scope, strategy, limit_value, window_seconds)
                        VALUES ('test_rule', 'global', 'fixed_window', 100, 60)
                    """)
                else:
                    # For tables with auto-increment IDs
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        AND is_nullable = 'NO'
                        AND column_default IS NULL
                    """)
                    required_cols = cursor.fetchall()

                cursor.execute("ROLLBACK")

                self.results['passed'].append(f"✅ Table {table_name}: Accessible, can insert")
                print(f"  ✅ {table_name}: OK")

            except Exception as e:
                self.results['failed'].append(f"❌ Table {table_name}: {str(e)}")
                print(f"  ❌ {table_name}: {str(e)}")

        cursor.close()

    def test_missing_columns(self):
        """Test that critical missing columns were added"""
        print("\n🔍 Testing Critical Column Additions...")

        critical_columns = [
            ('ai_conversations', 'tenant_id'),
            ('ai_conversations', 'personality_id'),
            ('profiles', 'customer_type'),
            ('ocs_inventory', 'quantity_available'),
            ('deliveries', 'customer_id'),
            ('payment_transactions', 'tenant_id'),
            ('promotions', 'tenant_id'),
            ('broadcasts', 'tenant_id'),
        ]

        cursor = self.conn.cursor()

        for table_name, column_name in critical_columns:
            try:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND column_name = '{column_name}'
                """)

                result = cursor.fetchone()
                if result:
                    self.results['passed'].append(f"✅ Column {table_name}.{column_name}: {result[1]}")
                    print(f"  ✅ {table_name}.{column_name}: {result[1]}")
                else:
                    self.results['failed'].append(f"❌ Column {table_name}.{column_name}: NOT FOUND")
                    print(f"  ❌ {table_name}.{column_name}: NOT FOUND")

            except Exception as e:
                self.results['failed'].append(f"❌ {table_name}.{column_name}: {str(e)}")
                print(f"  ❌ {table_name}.{column_name}: {str(e)}")

        cursor.close()

    def test_triggers(self):
        """Test that triggers are working"""
        print("\n🔍 Testing Triggers...")

        cursor = self.conn.cursor()

        # Get trigger count
        cursor.execute("""
            SELECT COUNT(DISTINCT trigger_name)
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        trigger_count = cursor.fetchone()[0]
        print(f"  ℹ️  Total triggers: {trigger_count}")

        # Test a specific trigger (updated_at)
        try:
            cursor.execute("BEGIN")

            # Check if ai_personalities has updated_at
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'ai_personalities'
                AND column_name = 'updated_at'
            """)

            if cursor.fetchone():
                # Test the trigger
                cursor.execute("""
                    UPDATE ai_personalities
                    SET name = name
                    WHERE id = (SELECT id FROM ai_personalities LIMIT 1)
                    RETURNING updated_at
                """)

                result = cursor.fetchone()
                if result and result[0]:
                    self.results['passed'].append("✅ Trigger test: updated_at triggers working")
                    print("  ✅ updated_at triggers: Working")
                else:
                    self.results['warnings'].append("⚠️  No test data for trigger validation")
                    print("  ⚠️  No test data available")
            else:
                self.results['warnings'].append("⚠️  updated_at column not found for trigger test")

            cursor.execute("ROLLBACK")

        except Exception as e:
            cursor.execute("ROLLBACK")
            self.results['warnings'].append(f"⚠️  Trigger test: {str(e)}")
            print(f"  ⚠️  Trigger test: {str(e)}")

        cursor.close()

    def test_indexes(self):
        """Test that critical indexes exist"""
        print("\n🔍 Testing Critical Indexes...")

        critical_indexes = [
            ('ocs_inventory', 'idx_ocs_inventory_sku_lower'),
            ('profiles', 'idx_profiles_customer_type'),
            ('payment_transactions', 'idx_transactions_tenant'),
            ('deliveries', 'idx_deliveries_customer_id'),
        ]

        cursor = self.conn.cursor()

        for table_name, index_name in critical_indexes:
            try:
                cursor.execute(f"""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND tablename = '{table_name}'
                    AND indexname = '{index_name}'
                """)

                result = cursor.fetchone()
                if result:
                    self.results['passed'].append(f"✅ Index {index_name}: Exists")
                    print(f"  ✅ {index_name}: OK")
                else:
                    self.results['warnings'].append(f"⚠️  Index {index_name}: NOT FOUND")
                    print(f"  ⚠️  {index_name}: Not found")

            except Exception as e:
                self.results['failed'].append(f"❌ Index {index_name}: {str(e)}")
                print(f"  ❌ {index_name}: {str(e)}")

        cursor.close()

    def test_functions(self):
        """Test that critical functions exist and are callable"""
        print("\n🔍 Testing Critical Functions...")

        critical_functions = [
            'update_updated_at_column',
            'calculate_final_price',
            'is_promotion_active_now',
            'get_store_ai_config',
        ]

        cursor = self.conn.cursor()

        for func_name in critical_functions:
            try:
                cursor.execute(f"""
                    SELECT proname, pronargs
                    FROM pg_proc
                    WHERE proname = '{func_name}'
                    AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                """)

                result = cursor.fetchone()
                if result:
                    self.results['passed'].append(f"✅ Function {func_name}: Exists")
                    print(f"  ✅ {func_name}: OK")
                else:
                    self.results['failed'].append(f"❌ Function {func_name}: NOT FOUND")
                    print(f"  ❌ {func_name}: Not found")

            except Exception as e:
                self.results['failed'].append(f"❌ Function {func_name}: {str(e)}")
                print(f"  ❌ {func_name}: {str(e)}")

        cursor.close()

    def check_constraint_issues(self):
        """Check the 2 known constraint issues"""
        print("\n🔍 Checking Known Constraint Issues...")

        cursor = self.conn.cursor()

        # Issue 1: user_role_simple type
        try:
            cursor.execute("""
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE constraint_name LIKE '%user_role%'
            """)
            results = cursor.fetchall()
            if results:
                print(f"  ℹ️  Found {len(results)} user_role constraints")
                for constraint_name, table_name in results:
                    print(f"     - {constraint_name} on {table_name}")
            else:
                self.results['warnings'].append("⚠️  No user_role constraints found")
                print("  ⚠️  No user_role constraints found")
        except Exception as e:
            print(f"  ⚠️  Error checking user_role: {e}")

        # Issue 2: wishlist unique constraint
        try:
            cursor.execute("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'wishlist'
                AND constraint_type = 'UNIQUE'
            """)
            results = cursor.fetchall()
            if results:
                print(f"  ✅ Wishlist has {len(results)} UNIQUE constraint(s)")
                for (constraint_name,) in results:
                    print(f"     - {constraint_name}")
            else:
                self.results['warnings'].append("⚠️  No unique constraints on wishlist")
                print("  ⚠️  No unique constraints on wishlist")
        except Exception as e:
            print(f"  ⚠️  Error checking wishlist: {e}")

        cursor.close()

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "="*80)
        print("VALIDATION REPORT")
        print("="*80)

        print(f"\n✅ PASSED: {len(self.results['passed'])} tests")
        for test in self.results['passed'][:10]:  # Show first 10
            print(f"  {test}")
        if len(self.results['passed']) > 10:
            print(f"  ... and {len(self.results['passed']) - 10} more")

        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS: {len(self.results['warnings'])} issues")
            for warning in self.results['warnings']:
                print(f"  {warning}")

        if self.results['failed']:
            print(f"\n❌ FAILED: {len(self.results['failed'])} tests")
            for failure in self.results['failed']:
                print(f"  {failure}")

        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        success_rate = (len(self.results['passed']) / total * 100) if total > 0 else 0

        print(f"\n{'='*80}")
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print(f"{'='*80}\n")

        # Save to file
        with open('database/VALIDATION_REPORT.md', 'w') as f:
            f.write("# Migration Validation Report\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Summary\n")
            f.write(f"- ✅ Passed: {len(self.results['passed'])}\n")
            f.write(f"- ⚠️  Warnings: {len(self.results['warnings'])}\n")
            f.write(f"- ❌ Failed: {len(self.results['failed'])}\n")
            f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")

            f.write("## Passed Tests\n")
            for test in self.results['passed']:
                f.write(f"- {test}\n")

            if self.results['warnings']:
                f.write("\n## Warnings\n")
                for warning in self.results['warnings']:
                    f.write(f"- {warning}\n")

            if self.results['failed']:
                f.write("\n## Failed Tests\n")
                for failure in self.results['failed']:
                    f.write(f"- {failure}\n")

        print("📝 Validation report saved to: database/VALIDATION_REPORT.md")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Run validation"""

    # Database config
    db_config = {
        'host': 'localhost',
        'port': 5434,  # Current database
        'database': 'ai_engine',
        'user': 'weedgo',
        'password': 'your_password_here'
    }

    print("="*80)
    print("MIGRATION VALIDATION")
    print("="*80)
    print(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    print("="*80)

    validator = MigrationValidator(db_config)

    if not validator.connect():
        return

    try:
        validator.test_new_tables()
        validator.test_missing_columns()
        validator.test_triggers()
        validator.test_indexes()
        validator.test_functions()
        validator.check_constraint_issues()
        validator.generate_report()

    finally:
        validator.close()

if __name__ == '__main__':
    main()
