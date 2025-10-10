#!/usr/bin/env python3
"""
Phase 2: Test Organization Script
Moves misplaced test files to proper test/ directory structure
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def categorize_test_file(filename):
    """Determine which test subdirectory a test file belongs to"""

    # API tests
    if any(x in filename for x in ['api_', 'endpoint_', 'auth_', 'registration_']):
        return 'api'

    # Service tests
    if any(x in filename for x in ['service_', 'barcode_', 'scraper_', 'tool', 'chat_system']):
        return 'services'

    # Voice/Audio tests
    if any(x in filename for x in ['voice_', 'audio_', 'streaming_', 'vad_', 'silero', 'speech']):
        return 'voice'

    # Integration tests (complete system/workflow tests)
    if any(x in filename for x in ['complete_', 'integration_', 'workflow_', 'system_']):
        return 'integration'

    # Database tests
    if any(x in filename for x in ['database_', 'inventory_', 'translation_']):
        return 'database'

    # Email/Communication tests
    if any(x in filename for x in ['email_', 'otp_']):
        return 'communication'

    # Upload/Media tests
    if any(x in filename for x in ['upload_', 'image_']):
        return 'media'

    # Default to unit tests
    return 'unit'

def main():
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}Test File Organization - Phase 2{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    # Get all test files in root directory
    backend_root = Path('.')
    test_files = list(backend_root.glob('test_*.py'))

    if not test_files:
        print(f"{Colors.OKGREEN}No test files found in root directory. Already organized!{Colors.ENDC}")
        return

    print(f"Found {Colors.BOLD}{len(test_files)}{Colors.ENDC} test files in root directory\n")

    # Categorize files
    categorized = defaultdict(list)
    for test_file in test_files:
        category = categorize_test_file(test_file.name)
        categorized[category].append(test_file)

    # Show categorization
    print(f"{Colors.OKCYAN}File Categorization:{Colors.ENDC}")
    print("-" * 60)
    for category, files in sorted(categorized.items()):
        print(f"\n{Colors.BOLD}tests/{category}/{Colors.ENDC} ({len(files)} files)")
        for file in sorted(files):
            print(f"  • {file.name}")

    print("\n" + "=" * 60)
    response = input(f"\n{Colors.WARNING}Proceed with moving files? (yes/no): {Colors.ENDC}").strip().lower()

    if response not in ['yes', 'y']:
        print(f"{Colors.FAIL}Cancelled by user{Colors.ENDC}")
        return

    print()

    # Create test directory structure
    tests_dir = backend_root / 'tests'
    moved_count = 0

    for category, files in categorized.items():
        category_dir = tests_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py if it doesn't exist
        init_file = category_dir / '__init__.py'
        if not init_file.exists():
            init_file.write_text('"""Test module for {}"""\n'.format(category))
            print(f"{Colors.OKGREEN}Created:{Colors.ENDC} {init_file.relative_to(backend_root)}")

        # Move files
        for test_file in files:
            dest = category_dir / test_file.name

            if dest.exists():
                print(f"{Colors.WARNING}Warning:{Colors.ENDC} {dest.name} already exists, skipping")
                continue

            shutil.move(str(test_file), str(dest))
            moved_count += 1
            print(f"{Colors.OKGREEN}Moved:{Colors.ENDC} {test_file.name} → tests/{category}/")

    print("\n" + "=" * 60)
    print(f"{Colors.OKGREEN}✓ Test Organization Complete!{Colors.ENDC}")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Files moved: {Colors.BOLD}{moved_count}{Colors.ENDC}")
    print(f"  Test categories created: {Colors.BOLD}{len(categorized)}{Colors.ENDC}")
    print(f"\nTest directory structure:")
    print(f"  tests/")
    for category in sorted(categorized.keys()):
        print(f"    ├── {category}/  ({len(categorized[category])} files)")

    print(f"\n{Colors.OKCYAN}Next Steps:{Colors.ENDC}")
    print("  1. Update pytest configuration if needed")
    print("  2. Run tests to ensure they still work: pytest tests/")
    print("  3. Update any documentation referencing old test locations")
    print("  4. Commit: git add . && git commit -m 'chore: organize test files into proper structure'")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}Interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        raise
