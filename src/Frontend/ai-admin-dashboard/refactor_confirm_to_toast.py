#!/usr/bin/env python3
"""
Replace window.confirm() and confirm() with confirmToastAsync
"""

import re
import os
from pathlib import Path

def ensure_confirm_toast_import(content):
    """Ensure confirmToastAsync is imported in the file"""
    # Check if confirmToastAsync is already imported
    if "confirmToastAsync" in content:
        return content

    # Find the last import statement
    import_pattern = r"^import .+;$"
    import_matches = list(re.finditer(import_pattern, content, re.MULTILINE))

    if import_matches:
        # Insert after the last import
        last_import = import_matches[-1]
        insert_pos = last_import.end()
        confirm_import = "\nimport { confirmToastAsync } from '../components/ConfirmToast';"
        content = content[:insert_pos] + confirm_import + content[insert_pos:]
    else:
        # Add at beginning
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if not line.strip().startswith('//') and not line.strip().startswith('/*') and line.strip():
                insert_idx = i
                break
        lines.insert(insert_idx, "import { confirmToastAsync } from '../components/ConfirmToast';")
        content = '\n'.join(lines)

    return content

def replace_confirm_calls(content):
    """Replace confirm() calls with confirmToastAsync"""

    # Pattern 1: if (confirm('message')) { ... }
    # Replace with: if (await confirmToastAsync('message')) { ... }
    pattern1 = r"if\s*\(\s*(?:window\.)?confirm\((['\"`])(.+?)\1\)\s*\)"

    def replacer1(match):
        quote = match.group(1)
        message = match.group(2)
        return f"if (await confirmToastAsync({quote}{message}{quote}))"

    content = re.sub(pattern1, replacer1, content)

    # Pattern 2: if (!confirm('message')) return;
    pattern2 = r"if\s*\(\s*!(?:window\.)?confirm\((['\"`])(.+?)\1\)\s*\)\s*return"

    def replacer2(match):
        quote = match.group(1)
        message = match.group(2)
        return f"if (!(await confirmToastAsync({quote}{message}{quote}))) return"

    content = re.sub(pattern2, replacer2, content)

    # Pattern 3: const result = confirm('message')
    pattern3 = r"(?:const|let|var)\s+(\w+)\s*=\s*(?:window\.)?confirm\((['\"`])(.+?)\2\)"

    def replacer3(match):
        var_name = match.group(1)
        quote = match.group(2)
        message = match.group(3)
        return f"const {var_name} = await confirmToastAsync({quote}{message}{quote})"

    content = re.sub(pattern3, replacer3, content)

    # Pattern 4: Remove TODO comments we added earlier
    content = re.sub(r"/\*\s*TODO: Replace confirm dialog\s*\*/\s*", "", content)

    return content

def make_function_async(content, function_name):
    """Make a function async if it contains await"""
    # Pattern to find function declaration
    func_pattern = rf"((?:const|let|var|export)\s+)?({function_name})\s*(?::\s*\w+)?\s*=\s*(?:async\s+)?\("

    def make_async(match):
        prefix = match.group(1) or ""
        name = match.group(2)
        return f"{prefix}{name} = async ("

    content = re.sub(func_pattern, make_async, content)

    # Also handle regular function declarations
    func_decl_pattern = rf"(async\s+)?function\s+({function_name})\s*\("

    def make_async_decl(match):
        name = match.group(2)
        return f"async function {name}("

    content = re.sub(func_decl_pattern, make_async_decl, content)

    return content

def find_functions_with_await(content):
    """Find all functions that contain await and need to be made async"""
    # This is a simple heuristic - find function names that contain await confirmToastAsync
    functions_to_make_async = set()

    # Pattern to find await confirmToastAsync calls and their containing function
    lines = content.split('\n')
    current_function = None

    for i, line in enumerate(lines):
        # Try to find function definition
        func_match = re.search(r"(?:const|let|var|export\s+(?:const|let|var)|function)\s+(\w+)\s*(?:=\s*(?:async\s+)?\(|:\s*\w+\s*=\s*(?:async\s+)?\(|\()", line)
        if func_match:
            current_function = func_match.group(1)

        # Check for await confirmToastAsync
        if "await confirmToastAsync" in line and current_function:
            functions_to_make_async.add(current_function)

    return functions_to_make_async

def process_file(file_path):
    """Process a single file to replace confirm with confirmToastAsync"""
    print(f"Processing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Check if file has confirm calls
    if not ('confirm(' in content or 'window.confirm' in content):
        print(f"  ✓ No confirm calls found, skipping")
        return False

    # Replace confirm calls
    content = replace_confirm_calls(content)

    # Find functions that need to be async
    functions_to_async = find_functions_with_await(content)

    # Make those functions async
    for func_name in functions_to_async:
        content = make_function_async(content, func_name)

    # Ensure import is added
    if content != original_content:
        content = ensure_confirm_toast_import(content)

    # Write back
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated successfully ({len(functions_to_async)} functions made async)")
        return True

    return False

def main():
    """Main function to process all TypeScript/TSX files"""
    src_dir = Path("src")

    if not src_dir.exists():
        print("Error: src directory not found. Run this script from the project root.")
        return

    # Find all .ts and .tsx files
    ts_files = list(src_dir.rglob("*.ts")) + list(src_dir.rglob("*.tsx"))

    print(f"Found {len(ts_files)} TypeScript files\n")

    updated_count = 0
    for file_path in ts_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: Updated {updated_count} files")
    print(f"{'='*60}")

    # Create a report
    report_path = "confirm_toast_refactor_report.md"
    with open(report_path, 'w') as f:
        f.write("# Confirm Toast Refactoring Report\n\n")
        f.write(f"- Total files processed: {len(ts_files)}\n")
        f.write(f"- Files updated: {updated_count}\n")
        f.write(f"\n## Changes Made\n\n")
        f.write("1. Replaced `confirm()` and `window.confirm()` with `confirmToastAsync()`\n")
        f.write("2. Added `async` keyword to functions that use `await confirmToastAsync()`\n")
        f.write("3. Added import for `confirmToastAsync` from ConfirmToast component\n\n")
        f.write("## Important Notes\n\n")
        f.write("- Functions containing `await` have been made `async`\n")
        f.write("- You may need to add `async` to parent functions if they call these functions\n")
        f.write("- The confirmToastAsync returns a Promise<boolean>\n")
        f.write("- Toast appears at top-center with custom styling\n\n")
        f.write("## Next Steps\n\n")
        f.write("1. Test all confirmation dialogs\n")
        f.write("2. Verify async/await chain is complete\n")
        f.write("3. Check that parent functions handle the Promise correctly\n")
        f.write("4. Update TypeScript types if needed\n")

    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    main()
