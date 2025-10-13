#!/usr/bin/env python3
"""
Comprehensive Schema Comparison Tool
Compares legacy and current databases and generates migration scripts
"""

import psycopg2
import json
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from datetime import datetime


class SchemaComparator:
    """Compares two PostgreSQL database schemas"""

    def __init__(self, legacy_config: Dict, current_config: Dict):
        self.legacy_config = legacy_config
        self.current_config = current_config
        self.legacy_conn = None
        self.current_conn = None
        self.differences = defaultdict(list)

    def connect(self):
        """Connect to both databases"""
        print("🔌 Connecting to databases...")
        try:
            self.legacy_conn = psycopg2.connect(**self.legacy_config)
            print(f"  ✅ Legacy DB: {self.legacy_config['host']}:{self.legacy_config['port']}")
        except Exception as e:
            print(f"  ❌ Failed to connect to legacy DB: {e}")
            raise

        try:
            self.current_conn = psycopg2.connect(**self.current_config)
            print(f"  ✅ Current DB: {self.current_config['host']}:{self.current_config['port']}")
        except Exception as e:
            print(f"  ❌ Failed to connect to current DB: {e}")
            raise

    def close(self):
        """Close database connections"""
        if self.legacy_conn:
            self.legacy_conn.close()
        if self.current_conn:
            self.current_conn.close()

    def get_tables(self, conn) -> Dict[str, List[Dict]]:
        """Extract all tables and their columns"""
        cursor = conn.cursor()

        # Get tables
        cursor.execute("""
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.is_nullable,
                c.column_default,
                c.ordinal_position
            FROM information_schema.columns c
            JOIN information_schema.tables t
                ON c.table_name = t.table_name
                AND c.table_schema = t.table_schema
            WHERE c.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            ORDER BY c.table_name, c.ordinal_position
        """)

        tables = defaultdict(list)
        for row in cursor.fetchall():
            table_name = row[0]
            column_info = {
                'column_name': row[1],
                'data_type': row[2],
                'character_maximum_length': row[3],
                'numeric_precision': row[4],
                'numeric_scale': row[5],
                'is_nullable': row[6],
                'column_default': row[7],
                'ordinal_position': row[8]
            }
            tables[table_name].append(column_info)

        cursor.close()
        return tables

    def get_views(self, conn) -> Dict[str, str]:
        """Extract all views and their definitions"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                table_name,
                view_definition
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        views = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        return views

    def get_triggers(self, conn) -> Dict[str, List[Dict]]:
        """Extract all triggers"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.trigger_name,
                t.event_manipulation,
                t.event_object_table,
                t.action_statement,
                t.action_timing,
                t.action_orientation
            FROM information_schema.triggers t
            WHERE t.trigger_schema = 'public'
            ORDER BY t.event_object_table, t.trigger_name
        """)

        triggers = defaultdict(list)
        for row in cursor.fetchall():
            table_name = row[2]
            trigger_info = {
                'trigger_name': row[0],
                'event': row[1],
                'timing': row[4],
                'orientation': row[5],
                'statement': row[3]
            }
            triggers[table_name].append(trigger_info)

        cursor.close()
        return triggers

    def get_functions(self, conn) -> Dict[str, Dict]:
        """Extract all functions/stored procedures"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.proname as function_name,
                pg_get_functiondef(p.oid) as function_definition,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as return_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public'
            AND p.prokind IN ('f', 'p')  -- functions and procedures
            ORDER BY p.proname
        """)

        functions = {}
        for row in cursor.fetchall():
            func_name = row[0]
            functions[func_name] = {
                'definition': row[1],
                'arguments': row[2],
                'return_type': row[3]
            }

        cursor.close()
        return functions

    def get_indexes(self, conn) -> Dict[str, List[Dict]]:
        """Extract all indexes"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname NOT LIKE '%_pkey'  -- Exclude primary keys
            ORDER BY tablename, indexname
        """)

        indexes = defaultdict(list)
        for row in cursor.fetchall():
            table_name = row[0]
            index_info = {
                'index_name': row[1],
                'definition': row[2]
            }
            indexes[table_name].append(index_info)

        cursor.close()
        return indexes

    def get_constraints(self, conn) -> Dict[str, List[Dict]]:
        """Extract all constraints (FK, unique, check)"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                pg_get_constraintdef(pgc.oid) as constraint_definition
            FROM information_schema.table_constraints tc
            JOIN pg_constraint pgc ON tc.constraint_name = pgc.conname
            WHERE tc.table_schema = 'public'
            AND tc.constraint_type IN ('FOREIGN KEY', 'UNIQUE', 'CHECK')
            ORDER BY tc.table_name, tc.constraint_name
        """)

        constraints = defaultdict(list)
        for row in cursor.fetchall():
            table_name = row[0]
            constraint_info = {
                'constraint_name': row[1],
                'constraint_type': row[2],
                'definition': row[3]
            }
            constraints[table_name].append(constraint_info)

        cursor.close()
        return constraints

    def compare_tables(self, legacy_tables: Dict, current_tables: Dict):
        """Compare table structures"""
        print("\n📊 Comparing Tables...")

        legacy_table_names = set(legacy_tables.keys())
        current_table_names = set(current_tables.keys())

        # Missing tables
        missing_tables = legacy_table_names - current_table_names
        if missing_tables:
            print(f"  ⚠️  Missing {len(missing_tables)} tables in current DB")
            for table in sorted(missing_tables):
                self.differences['missing_tables'].append({
                    'table_name': table,
                    'columns': legacy_tables[table]
                })

        # Extra tables (in current but not in legacy)
        extra_tables = current_table_names - legacy_table_names
        if extra_tables:
            print(f"  ℹ️  {len(extra_tables)} extra tables in current DB (will keep)")

        # Compare columns in common tables
        common_tables = legacy_table_names & current_table_names
        tables_with_missing_cols = 0

        for table_name in sorted(common_tables):
            legacy_cols = {col['column_name']: col for col in legacy_tables[table_name]}
            current_cols = {col['column_name']: col for col in current_tables[table_name]}

            missing_columns = set(legacy_cols.keys()) - set(current_cols.keys())

            if missing_columns:
                tables_with_missing_cols += 1
                self.differences['missing_columns'].append({
                    'table_name': table_name,
                    'columns': [legacy_cols[col] for col in missing_columns]
                })

        if tables_with_missing_cols:
            print(f"  ⚠️  {tables_with_missing_cols} tables have missing columns")

        print(f"  ✅ Compared {len(common_tables)} common tables")

    def compare_views(self, legacy_views: Dict, current_views: Dict):
        """Compare views"""
        print("\n👁️  Comparing Views...")

        legacy_view_names = set(legacy_views.keys())
        current_view_names = set(current_views.keys())

        missing_views = legacy_view_names - current_view_names
        if missing_views:
            print(f"  ⚠️  Missing {len(missing_views)} views in current DB")
            for view_name in sorted(missing_views):
                self.differences['missing_views'].append({
                    'view_name': view_name,
                    'definition': legacy_views[view_name]
                })
        else:
            print(f"  ✅ All {len(legacy_view_names)} views present")

    def compare_triggers(self, legacy_triggers: Dict, current_triggers: Dict):
        """Compare triggers"""
        print("\n⚡ Comparing Triggers...")

        # Flatten trigger names for comparison
        legacy_trigger_names = set()
        for table_triggers in legacy_triggers.values():
            for trigger in table_triggers:
                legacy_trigger_names.add(trigger['trigger_name'])

        current_trigger_names = set()
        for table_triggers in current_triggers.values():
            for trigger in table_triggers:
                current_trigger_names.add(trigger['trigger_name'])

        missing_triggers = legacy_trigger_names - current_trigger_names
        if missing_triggers:
            print(f"  ⚠️  Missing {len(missing_triggers)} triggers in current DB")
            for table_name, triggers in legacy_triggers.items():
                for trigger in triggers:
                    if trigger['trigger_name'] in missing_triggers:
                        self.differences['missing_triggers'].append({
                            'table_name': table_name,
                            'trigger': trigger
                        })
        else:
            print(f"  ✅ All {len(legacy_trigger_names)} triggers present")

    def compare_functions(self, legacy_functions: Dict, current_functions: Dict):
        """Compare functions"""
        print("\n🔧 Comparing Functions...")

        legacy_func_names = set(legacy_functions.keys())
        current_func_names = set(current_functions.keys())

        missing_functions = legacy_func_names - current_func_names
        if missing_functions:
            print(f"  ⚠️  Missing {len(missing_functions)} functions in current DB")
            for func_name in sorted(missing_functions):
                self.differences['missing_functions'].append({
                    'function_name': func_name,
                    'function': legacy_functions[func_name]
                })
        else:
            print(f"  ✅ All {len(legacy_func_names)} functions present")

    def compare_indexes(self, legacy_indexes: Dict, current_indexes: Dict):
        """Compare indexes"""
        print("\n🔍 Comparing Indexes...")

        # Flatten index names
        legacy_index_names = set()
        for table_indexes in legacy_indexes.values():
            for idx in table_indexes:
                legacy_index_names.add(idx['index_name'])

        current_index_names = set()
        for table_indexes in current_indexes.values():
            for idx in table_indexes:
                current_index_names.add(idx['index_name'])

        missing_indexes = legacy_index_names - current_index_names
        if missing_indexes:
            print(f"  ⚠️  Missing {len(missing_indexes)} indexes in current DB")
            for table_name, indexes in legacy_indexes.items():
                for idx in indexes:
                    if idx['index_name'] in missing_indexes:
                        self.differences['missing_indexes'].append({
                            'table_name': table_name,
                            'index': idx
                        })
        else:
            print(f"  ✅ All {len(legacy_index_names)} indexes present")

    def compare_constraints(self, legacy_constraints: Dict, current_constraints: Dict):
        """Compare constraints"""
        print("\n🔒 Comparing Constraints...")

        # Flatten constraint names
        legacy_constraint_names = set()
        for table_constraints in legacy_constraints.values():
            for constraint in table_constraints:
                legacy_constraint_names.add(constraint['constraint_name'])

        current_constraint_names = set()
        for table_constraints in current_constraints.values():
            for constraint in table_constraints:
                current_constraint_names.add(constraint['constraint_name'])

        missing_constraints = legacy_constraint_names - current_constraint_names
        if missing_constraints:
            print(f"  ⚠️  Missing {len(missing_constraints)} constraints in current DB")
            for table_name, constraints in legacy_constraints.items():
                for constraint in constraints:
                    if constraint['constraint_name'] in missing_constraints:
                        self.differences['missing_constraints'].append({
                            'table_name': table_name,
                            'constraint': constraint
                        })
        else:
            print(f"  ✅ All {len(legacy_constraint_names)} constraints present")

    def clean_data_type(self, data_type: str, char_len, num_precision, num_scale) -> str:
        """Clean and format PostgreSQL data types properly for DDL"""
        # Remove precision from types that don't support it
        base_type = data_type.lower()

        # Types that should never have precision
        no_precision_types = {
            'integer', 'bigint', 'smallint', 'serial', 'bigserial',
            'boolean', 'text', 'date', 'uuid', 'jsonb', 'json',
            'double precision', 'real', 'bytea', 'inet', 'cidr',
            'macaddr', 'tsquery', 'tsvector'
        }

        # Handle array types
        if data_type == 'ARRAY':
            return 'text[]'  # Default to text array, will need manual review

        # If it's a simple type without precision
        if base_type in no_precision_types:
            return data_type

        # Character types need length
        if base_type in ('character varying', 'varchar', 'character', 'char') and char_len:
            return f"{data_type}({char_len})"

        # Numeric types need precision
        if base_type in ('numeric', 'decimal') and num_precision:
            if num_scale:
                return f"{data_type}({num_precision},{num_scale})"
            return f"{data_type}({num_precision})"

        # Timestamp types
        if 'timestamp' in base_type or 'time' in base_type:
            return data_type

        # Return as-is for everything else
        return data_type

    def generate_migration_sql(self) -> str:
        """Generate SQL migration script from differences"""
        sql_lines = []
        sql_lines.append("-- ============================================================================")
        sql_lines.append("-- Schema Migration: Legacy → Current Database")
        sql_lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_lines.append("-- Description: Copy all missing schema objects from legacy to current")
        sql_lines.append("-- ============================================================================")
        sql_lines.append("")
        sql_lines.append("BEGIN TRANSACTION;")
        sql_lines.append("")

        # 1. Create missing tables
        if self.differences['missing_tables']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 1: Create {len(self.differences['missing_tables'])} Missing Tables")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for table_info in self.differences['missing_tables']:
                table_name = table_info['table_name']
                columns = table_info['columns']

                sql_lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")

                col_defs = []
                for col in columns:
                    # Clean the data type
                    clean_type = self.clean_data_type(
                        col['data_type'],
                        col['character_maximum_length'],
                        col['numeric_precision'],
                        col['numeric_scale']
                    )

                    col_def = f"    {col['column_name']} {clean_type}"

                    # Add NOT NULL
                    if col['is_nullable'] == 'NO':
                        col_def += " NOT NULL"

                    # Add DEFAULT
                    if col['column_default']:
                        col_def += f" DEFAULT {col['column_default']}"

                    col_defs.append(col_def)

                sql_lines.append(",\n".join(col_defs))
                sql_lines.append(");")
                sql_lines.append("")

        # 2. Add missing columns
        if self.differences['missing_columns']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 2: Add Missing Columns to Existing Tables")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for table_info in self.differences['missing_columns']:
                table_name = table_info['table_name']
                columns = table_info['columns']

                sql_lines.append(f"-- Table: {table_name}")
                sql_lines.append(f"ALTER TABLE {table_name}")

                col_adds = []
                for col in columns:
                    # Clean the data type
                    clean_type = self.clean_data_type(
                        col['data_type'],
                        col['character_maximum_length'],
                        col['numeric_precision'],
                        col['numeric_scale']
                    )

                    col_add = f"ADD COLUMN IF NOT EXISTS {col['column_name']} {clean_type}"

                    if col['column_default']:
                        col_add += f" DEFAULT {col['column_default']}"

                    if col['is_nullable'] == 'NO':
                        col_add += " NOT NULL"

                    col_adds.append(col_add)

                sql_lines.append(",\n".join(col_adds))
                sql_lines.append(";")
                sql_lines.append("")

        # 3. Create missing views
        if self.differences['missing_views']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 3: Create {len(self.differences['missing_views'])} Missing Views")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for view_info in self.differences['missing_views']:
                sql_lines.append(f"CREATE OR REPLACE VIEW {view_info['view_name']} AS")
                sql_lines.append(view_info['definition'])
                sql_lines.append(";")
                sql_lines.append("")

        # 4. Create missing functions
        if self.differences['missing_functions']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 4: Create {len(self.differences['missing_functions'])} Missing Functions")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for func_info in self.differences['missing_functions']:
                sql_lines.append(func_info['function']['definition'])
                sql_lines.append(";")
                sql_lines.append("")

        # 5. Create missing indexes
        if self.differences['missing_indexes']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 5: Create {len(self.differences['missing_indexes'])} Missing Indexes")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for idx_info in self.differences['missing_indexes']:
                sql_lines.append(idx_info['index']['definition'])
                sql_lines.append(";")
                sql_lines.append("")

        # 6. Create missing constraints
        if self.differences['missing_constraints']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 6: Create {len(self.differences['missing_constraints'])} Missing Constraints")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for constraint_info in self.differences['missing_constraints']:
                table_name = constraint_info['table_name']
                constraint = constraint_info['constraint']
                sql_lines.append(f"ALTER TABLE {table_name}")
                sql_lines.append(f"ADD CONSTRAINT {constraint['constraint_name']}")
                sql_lines.append(f"{constraint['definition']};")
                sql_lines.append("")

        # 7. Create missing triggers
        if self.differences['missing_triggers']:
            sql_lines.append("-- ============================================================================")
            sql_lines.append(f"-- STEP 7: Create {len(self.differences['missing_triggers'])} Missing Triggers")
            sql_lines.append("-- ============================================================================")
            sql_lines.append("")

            for trigger_info in self.differences['missing_triggers']:
                trigger = trigger_info['trigger']
                table_name = trigger_info['table_name']
                trigger_name = trigger['trigger_name']
                timing = trigger['timing']  # BEFORE or AFTER
                event = trigger['event']  # INSERT, UPDATE, DELETE
                orientation = trigger['orientation']  # ROW or STATEMENT
                statement = trigger['statement']  # EXECUTE FUNCTION ...

                sql_lines.append(f"-- Trigger: {trigger_name} on {table_name}")
                sql_lines.append(f"CREATE OR REPLACE TRIGGER {trigger_name}")
                sql_lines.append(f"{timing} {event} ON {table_name}")
                sql_lines.append(f"FOR EACH {orientation}")
                sql_lines.append(statement)
                sql_lines.append(";")
                sql_lines.append("")

        sql_lines.append("COMMIT;")
        sql_lines.append("")
        sql_lines.append("-- Migration complete!")

        return "\n".join(sql_lines)

    def generate_report(self) -> str:
        """Generate detailed comparison report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DATABASE SCHEMA COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Legacy DB: {self.legacy_config['host']}:{self.legacy_config['port']}")
        lines.append(f"Current DB: {self.current_config['host']}:{self.current_config['port']}")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY:")
        lines.append(f"  Missing Tables:      {len(self.differences['missing_tables'])}")
        lines.append(f"  Tables w/ Missing Columns: {len(self.differences['missing_columns'])}")
        lines.append(f"  Missing Views:       {len(self.differences['missing_views'])}")
        lines.append(f"  Missing Triggers:    {len(self.differences['missing_triggers'])}")
        lines.append(f"  Missing Functions:   {len(self.differences['missing_functions'])}")
        lines.append(f"  Missing Indexes:     {len(self.differences['missing_indexes'])}")
        lines.append(f"  Missing Constraints: {len(self.differences['missing_constraints'])}")
        lines.append("")

        # Details for missing tables
        if self.differences['missing_tables']:
            lines.append("MISSING TABLES:")
            for table_info in self.differences['missing_tables']:
                lines.append(f"  • {table_info['table_name']} ({len(table_info['columns'])} columns)")

        # Details for missing columns
        if self.differences['missing_columns']:
            lines.append("")
            lines.append("TABLES WITH MISSING COLUMNS:")
            for table_info in self.differences['missing_columns']:
                table_name = table_info['table_name']
                columns = [col['column_name'] for col in table_info['columns']]
                lines.append(f"  • {table_name}: {', '.join(columns)}")

        # Details for views
        if self.differences['missing_views']:
            lines.append("")
            lines.append("MISSING VIEWS:")
            for view_info in self.differences['missing_views']:
                lines.append(f"  • {view_info['view_name']}")

        # Details for triggers
        if self.differences['missing_triggers']:
            lines.append("")
            lines.append("MISSING TRIGGERS:")
            for trigger_info in self.differences['missing_triggers']:
                lines.append(f"  • {trigger_info['trigger']['trigger_name']} on {trigger_info['table_name']}")

        # Details for functions
        if self.differences['missing_functions']:
            lines.append("")
            lines.append("MISSING FUNCTIONS:")
            for func_info in self.differences['missing_functions']:
                lines.append(f"  • {func_info['function_name']}")

        # Details for indexes
        if self.differences['missing_indexes']:
            lines.append("")
            lines.append("MISSING INDEXES:")
            for idx_info in self.differences['missing_indexes']:
                lines.append(f"  • {idx_info['index']['index_name']} on {idx_info['table_name']}")

        # Details for constraints
        if self.differences['missing_constraints']:
            lines.append("")
            lines.append("MISSING CONSTRAINTS:")
            for constraint_info in self.differences['missing_constraints']:
                lines.append(f"  • {constraint_info['constraint']['constraint_name']} on {constraint_info['table_name']}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def run_comparison(self):
        """Run full schema comparison"""
        print("\n" + "=" * 80)
        print("DATABASE SCHEMA COMPARISON")
        print("=" * 80)

        # Connect
        self.connect()

        try:
            # Extract schemas
            print("\n📥 Extracting Legacy Schema...")
            legacy_tables = self.get_tables(self.legacy_conn)
            legacy_views = self.get_views(self.legacy_conn)
            legacy_triggers = self.get_triggers(self.legacy_conn)
            legacy_functions = self.get_functions(self.legacy_conn)
            legacy_indexes = self.get_indexes(self.legacy_conn)
            legacy_constraints = self.get_constraints(self.legacy_conn)
            print(f"  ✅ Extracted: {len(legacy_tables)} tables, {len(legacy_views)} views, "
                  f"{len(legacy_functions)} functions")

            print("\n📥 Extracting Current Schema...")
            current_tables = self.get_tables(self.current_conn)
            current_views = self.get_views(self.current_conn)
            current_triggers = self.get_triggers(self.current_conn)
            current_functions = self.get_functions(self.current_conn)
            current_indexes = self.get_indexes(self.current_conn)
            current_constraints = self.get_constraints(self.current_conn)
            print(f"  ✅ Extracted: {len(current_tables)} tables, {len(current_views)} views, "
                  f"{len(current_functions)} functions")

            # Compare
            self.compare_tables(legacy_tables, current_tables)
            self.compare_views(legacy_views, current_views)
            self.compare_triggers(legacy_triggers, current_triggers)
            self.compare_functions(legacy_functions, current_functions)
            self.compare_indexes(legacy_indexes, current_indexes)
            self.compare_constraints(legacy_constraints, current_constraints)

            print("\n" + "=" * 80)
            print("✅ Comparison Complete!")
            print("=" * 80)

        finally:
            self.close()


def main():
    """Main execution"""
    # Database configurations
    legacy_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'ai_engine',
        'user': 'weedgo',
        'password': 'weedgo123'
    }

    current_config = {
        'host': 'localhost',
        'port': 5434,
        'database': 'ai_engine',
        'user': 'weedgo',
        'password': 'weedgo123'
    }

    # Run comparison
    comparator = SchemaComparator(legacy_config, current_config)
    comparator.run_comparison()

    # Generate outputs
    print("\n📝 Generating Reports...")

    # Save comparison report
    report = comparator.generate_report()
    report_file = 'database/schema_comparison_report.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"  ✅ Report saved: {report_file}")

    # Save migration SQL
    migration_sql = comparator.generate_migration_sql()
    sql_file = 'database/schema_migration.sql'
    with open(sql_file, 'w') as f:
        f.write(migration_sql)
    print(f"  ✅ Migration SQL saved: {sql_file}")

    # Save differences as JSON for programmatic access
    json_file = 'database/schema_differences.json'
    with open(json_file, 'w') as f:
        json.dump(dict(comparator.differences), f, indent=2, default=str)
    print(f"  ✅ JSON differences saved: {json_file}")

    print("\n✨ All done! Review the files before applying migration.")


if __name__ == '__main__':
    main()
