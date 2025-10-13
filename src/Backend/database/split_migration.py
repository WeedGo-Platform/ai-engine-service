#!/usr/bin/env python3
"""
Split Migration Script
Splits the large migration SQL into separate stage files
"""

import re
from pathlib import Path

def split_migration():
    """Split migration SQL into stages"""

    # Read the main migration file
    with open('database/schema_migration.sql', 'r') as f:
        content = f.read()

    # Split by step comments
    steps = re.split(r'-- =+\n-- STEP \d+:', content)

    # Extract stages
    stages = {
        'sequences': [],
        'tables': [],
        'columns': [],
        'views': [],
        'functions': [],
        'indexes': [],
        'constraints': [],
        'triggers': []
    }

    for step in steps[1:]:  # Skip header
        if 'Missing Tables' in step:
            # Extract table creation SQL
            tables_section = step.split('-- =====')[0]
            stages['tables'].append(tables_section)
        elif 'Missing Columns' in step:
            columns_section = step.split('-- =====')[0]
            stages['columns'].append(columns_section)
        elif 'Missing Views' in step:
            views_section = step.split('-- =====')[0]
            stages['views'].append(views_section)
        elif 'Missing Functions' in step:
            functions_section = step.split('-- =====')[0]
            stages['functions'].append(functions_section)
        elif 'Missing Indexes' in step:
            indexes_section = step.split('-- =====')[0]
            stages['indexes'].append(indexes_section)
        elif 'Missing Constraints' in step:
            constraints_section = step.split('-- =====')[0]
            stages['constraints'].append(constraints_section)
        elif 'Missing Triggers' in step:
            triggers_section = step.split('-- =====')[0]
            stages['triggers'].append(triggers_section)

    # Create migrations directory
    migrations_dir = Path('database/migrations')
    migrations_dir.mkdir(exist_ok=True)

    # Write stage 2: Tables (sequences already written)
    if stages['tables']:
        with open(migrations_dir / 'stage2_tables.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 2: Create Missing Tables\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['tables']))
            f.write("\nSELECT 'Stage 2: Tables created successfully' AS status;\n")
        print("✅ Created stage2_tables.sql")

    # Write stage 3: Columns
    if stages['columns']:
        with open(migrations_dir / 'stage3_columns.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 3: Add Missing Columns\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['columns']))
            f.write("\nSELECT 'Stage 3: Columns added successfully' AS status;\n")
        print("✅ Created stage3_columns.sql")

    # Write stage 4: Views
    if stages['views']:
        with open(migrations_dir / 'stage4_views.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 4: Create Missing Views\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['views']))
            f.write("\nSELECT 'Stage 4: Views created successfully' AS status;\n")
        print("✅ Created stage4_views.sql")

    # Write stage 5: Functions
    if stages['functions']:
        with open(migrations_dir / 'stage5_functions.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 5: Create Missing Functions\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['functions']))
            f.write("\nSELECT 'Stage 5: Functions created successfully' AS status;\n")
        print("✅ Created stage5_functions.sql")

    # Write stage 6: Triggers
    if stages['triggers']:
        with open(migrations_dir / 'stage6_triggers.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 6: Create Missing Triggers\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['triggers']))
            f.write("\nSELECT 'Stage 6: Triggers created successfully' AS status;\n")
        print("✅ Created stage6_triggers.sql")

    # Write stage 7: Indexes
    if stages['indexes']:
        with open(migrations_dir / 'stage7_indexes.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 7: Create Missing Indexes\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['indexes']))
            f.write("\nSELECT 'Stage 7: Indexes created successfully' AS status;\n")
        print("✅ Created stage7_indexes.sql")

    # Write stage 8: Constraints
    if stages['constraints']:
        with open(migrations_dir / 'stage8_constraints.sql', 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- Stage 8: Add Missing Constraints\n")
            f.write("-- ============================================================================\n\n")
            f.write(''.join(stages['constraints']))
            f.write("\nSELECT 'Stage 8: Constraints added successfully' AS status;\n")
        print("✅ Created stage8_constraints.sql")

    print("\n✨ All stage files created in database/migrations/")

if __name__ == '__main__':
    split_migration()
