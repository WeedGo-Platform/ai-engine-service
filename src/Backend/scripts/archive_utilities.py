#!/usr/bin/env python3
"""
Phase 2: Utility Script Archival
Identifies and archives one-off utility scripts
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def categorize_utility(filename):
    """Categorize utility scripts by their purpose"""

    # Migration scripts
    if 'migration' in filename or filename.startswith('run_'):
        return 'migrations', 'One-time migration scripts (likely obsolete after master migration)'

    # Diagnostic/check scripts
    if filename.startswith('check_') or filename.startswith('show_') or filename.startswith('verify_'):
        return 'diagnostics', 'Database/system diagnostic scripts (one-time use)'

    # Debug scripts
    if filename.startswith('debug_'):
        return 'debug', 'Debug scripts (one-time troubleshooting)'

    # Data manipulation
    if any(filename.startswith(x) for x in ['add_', 'update_', 'populate_', 'clear_']):
        return 'data_manipulation', 'Data modification scripts (one-time use)'

    # Setup/initialization
    if any(filename.startswith(x) for x in ['create_', 'generate_', 'fix_']):
        return 'setup', 'Setup and initialization scripts'

    # Analysis/reporting
    if filename.startswith('analyze_'):
        return 'analysis', 'Analysis and reporting scripts'

    return 'other', 'Miscellaneous utility scripts'

def get_utility_scripts():
    """Find all utility scripts in backend root"""
    backend_root = Path('.')

    utility_patterns = [
        'check_*.py',
        'debug_*.py',
        'fix_*.py',
        'run_*.py',
        'create_*.py',
        'add_*.py',
        'update_*.py',
        'populate_*.py',
        'clear_*.py',
        'generate_*.py',
        'show_*.py',
        'verify_*.py',
        'apply_*.py',
        'analyze_*.py'
    ]

    all_utilities = []
    for pattern in utility_patterns:
        all_utilities.extend(backend_root.glob(pattern))

    return list(set(all_utilities))  # Remove duplicates

def main():
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}Utility Script Archival - Phase 2{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

    utility_scripts = get_utility_scripts()

    if not utility_scripts:
        print(f"{Colors.OKGREEN}No utility scripts found in root directory.{Colors.ENDC}")
        return

    print(f"Found {Colors.BOLD}{len(utility_scripts)}{Colors.ENDC} utility scripts in root directory\n")

    # Categorize
    categorized = defaultdict(list)
    categories_desc = {}

    for script in utility_scripts:
        category, desc = categorize_utility(script.name)
        categorized[category].append(script)
        categories_desc[category] = desc

    # Display categorization
    print(f"{Colors.OKCYAN}Script Categorization:{Colors.ENDC}")
    print("-" * 70)

    for category in sorted(categorized.keys()):
        files = categorized[category]
        print(f"\n{Colors.BOLD}{category.upper()}{Colors.ENDC} ({len(files)} files)")
        print(f"  {Colors.OKBLUE}{categories_desc[category]}{Colors.ENDC}")
        print(f"  → Will move to: scripts/archive/{category}/\n")

        for file in sorted(files)[:5]:  # Show first 5
            print(f"    • {file.name}")

        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")

    print("\n" + "=" * 70)
    print(f"{Colors.WARNING}These scripts will be moved to scripts/archive/{Colors.ENDC}")
    print(f"{Colors.WARNING}You can restore them from archive if needed later.{Colors.ENDC}\n")

    # Get user confirmation
    response = input(f"Proceed with archiving? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print(f"{Colors.FAIL}Cancelled by user{Colors.ENDC}")
        return

    print()

    # Create archive structure
    backend_root = Path('.')
    archive_root = backend_root / 'scripts' / 'archive'
    timestamp = datetime.now().strftime('%Y%m%d')

    moved_count = 0

    for category, files in categorized.items():
        category_dir = archive_root / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Create README
        readme = category_dir / 'README.md'
        if not readme.exists():
            readme.write_text(f"""# {category.replace('_', ' ').title()} Scripts

{categories_desc[category]}

**Archived:** {datetime.now().strftime('%Y-%m-%d')}

## Scripts

These scripts were moved from the Backend root directory during codebase cleanup.
They are preserved here for reference but are likely obsolete.

## Files

""")

        # Move files
        for script in files:
            dest = category_dir / script.name

            if dest.exists():
                # Add timestamp if file already exists
                stem = script.stem
                suffix = script.suffix
                dest = category_dir / f"{stem}_{timestamp}{suffix}"

            shutil.move(str(script), str(dest))
            moved_count += 1
            print(f"{Colors.OKGREEN}Archived:{Colors.ENDC} {script.name} → scripts/archive/{category}/")

            # Update README
            with readme.open('a') as f:
                f.write(f"- `{script.name}`\n")

    print("\n" + "=" * 70)
    print(f"{Colors.OKGREEN}✓ Archival Complete!{Colors.ENDC}")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Scripts archived: {Colors.BOLD}{moved_count}{Colors.ENDC}")
    print(f"  Categories: {Colors.BOLD}{len(categorized)}{Colors.ENDC}")
    print(f"\nArchive location: scripts/archive/")
    for category in sorted(categorized.keys()):
        print(f"  ├── {category}/  ({len(categorized[category])} files)")

    print(f"\n{Colors.OKCYAN}Important Notes:{Colors.ENDC}")
    print("  • Archived scripts are preserved in version control")
    print("  • You can restore any script by copying it back")
    print("  • Review each category's README.md for details")
    print("  • Consider deleting truly obsolete scripts after review")

    print(f"\n{Colors.OKCYAN}Next Steps:{Colors.ENDC}")
    print("  1. Review archived scripts to confirm none are actively used")
    print("  2. Update any documentation that references these scripts")
    print("  3. Commit: git add . && git commit -m 'chore: archive utility scripts'")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}Interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        raise
