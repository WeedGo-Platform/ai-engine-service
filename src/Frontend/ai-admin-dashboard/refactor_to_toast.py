#!/usr/bin/env python3
"""
Refactor all blocking alert() and confirm() dialogs to toast notifications.
This script will:
1. Replace alert() with toast.success() or toast.error()
2. Replace confirm() with toast + callback pattern or custom confirm toast
3. Add necessary imports
"""

import re
import os
from pathlib import Path

def ensure_toast_import(content):
    """Ensure react-hot-toast is imported in the file"""
    # Check if toast is already imported
    if "from 'react-hot-toast'" in content or 'from "react-hot-toast"' in content:
        return content

    # Find the last import statement
    import_pattern = r"^import .+;$"
    import_matches = list(re.finditer(import_pattern, content, re.MULTILINE))

    if import_matches:
        # Insert after the last import
        last_import = import_matches[-1]
        insert_pos = last_import.end()
        toast_import = "\nimport toast from 'react-hot-toast';"
        content = content[:insert_pos] + toast_import + content[insert_pos:]
    else:
        # No imports found, add at the beginning after any comments
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if not line.strip().startswith('//') and not line.strip().startswith('/*') and line.strip():
                insert_idx = i
                break
        lines.insert(insert_idx, "import toast from 'react-hot-toast';")
        content = '\n'.join(lines)

    return content

def replace_alert_calls(content):
    """Replace alert() calls with toast notifications"""

    # Pattern to match alert() calls with various quote types and content
    # Handles: alert('message'), alert("message"), alert(`message ${var}`)
    alert_pattern = r"alert\((['\"`])(.+?)\1\)"

    def alert_replacer(match):
        quote = match.group(1)
        message = match.group(2)

        # Determine if it's an error or success message based on keywords
        error_keywords = ['error', 'failed', 'invalid', 'please', 'must', 'cannot', 'unable', 'warning']
        success_keywords = ['success', 'created', 'updated', 'deleted', 'saved', 'completed', 'approved', 'rejected']

        message_lower = message.lower()

        # Check if it's an error message
        is_error = any(keyword in message_lower for keyword in error_keywords)
        is_success = any(keyword in message_lower for keyword in success_keywords)

        if is_error and not is_success:
            return f"toast.error({quote}{message}{quote})"
        elif is_success:
            return f"toast.success({quote}{message}{quote})"
        else:
            # Default to toast (neutral)
            return f"toast({quote}{message}{quote})"

    content = re.sub(alert_pattern, alert_replacer, content)

    # Handle multiline alert calls
    multiline_alert_pattern = r"alert\(\s*(['\"`])((?:.|\n)+?)\1\s*\)"
    content = re.sub(multiline_alert_pattern, alert_replacer, content, flags=re.DOTALL)

    # Handle template literals specifically
    template_alert_pattern = r"alert\(`([^`]+)`\)"

    def template_alert_replacer(match):
        message = match.group(1)
        message_lower = message.lower()

        error_keywords = ['error', 'failed', 'invalid', 'please', 'must', 'cannot', 'unable', 'warning']
        success_keywords = ['success', 'created', 'updated', 'deleted', 'saved', 'completed']

        is_error = any(keyword in message_lower for keyword in error_keywords)
        is_success = any(keyword in message_lower for keyword in success_keywords)

        if is_error and not is_success:
            return f"toast.error(`{message}`)"
        elif is_success:
            return f"toast.success(`{message}`)"
        else:
            return f"toast(`{message}`)"

    content = re.sub(template_alert_pattern, template_alert_replacer, content)

    return content

def replace_confirm_calls(content):
    """Replace confirm() calls with toast-based pattern"""

    # This is more complex as confirm() requires user interaction
    # We'll convert to a pattern using toast with actions

    # Pattern: if (confirm('message')) { action }
    confirm_if_pattern = r"if\s*\(\s*confirm\((['\"`])(.+?)\1\)\s*\)\s*\{([^}]+)\}"

    def confirm_replacer(match):
        quote = match.group(1)
        message = match.group(2)
        action = match.group(3).strip()

        # For now, we'll use toast.error to show we can't directly replace confirm
        # In a real implementation, you'd use a custom confirmation dialog or library
        return f"""// TODO: Replace with custom confirmation dialog
      toast((t) => (
        <div>
          <p>{quote}{message}{quote}</p>
          <div className="flex gap-2 mt-2">
            <button onClick={{() => {{
              toast.dismiss(t.id);
              {action}
            }}}} className="px-3 py-1 bg-blue-500 text-white rounded">
              Confirm
            </button>
            <button onClick={{() => toast.dismiss(t.id)}} className="px-3 py-1 bg-gray-300 rounded">
              Cancel
            </button>
          </div>
        </div>
      ), {{ duration: Infinity }})"""

    # For simple cases, just comment it
    simple_confirm_pattern = r"confirm\((['\"`])(.+?)\1\)"

    def simple_confirm_replacer(match):
        quote = match.group(1)
        message = match.group(2)
        # Replace with a comment noting manual review needed
        return f"/* TODO: Replace confirm dialog */ window.confirm({quote}{message}{quote})"

    content = re.sub(simple_confirm_pattern, simple_confirm_replacer, content)

    return content

def process_file(file_path):
    """Process a single file to replace alert/confirm with toast"""
    print(f"Processing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Check if file has alert or confirm calls
    if 'alert(' not in content and 'confirm(' not in content:
        print(f"  ✓ No alert/confirm calls found, skipping")
        return False

    # Replace alert calls
    if 'alert(' in content:
        content = replace_alert_calls(content)

    # Replace confirm calls (commented approach)
    if 'confirm(' in content:
        content = replace_confirm_calls(content)

    # Ensure toast import is added
    if content != original_content:
        content = ensure_toast_import(content)

    # Write back
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated successfully")
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
    report_path = "toast_refactor_report.md"
    with open(report_path, 'w') as f:
        f.write("# Toast Refactoring Report\n\n")
        f.write(f"- Total files processed: {len(ts_files)}\n")
        f.write(f"- Files updated: {updated_count}\n")
        f.write(f"\n## Changes Made\n\n")
        f.write("1. Replaced `alert()` calls with appropriate toast notifications:\n")
        f.write("   - Error messages → `toast.error()`\n")
        f.write("   - Success messages → `toast.success()`\n")
        f.write("   - Neutral messages → `toast()`\n\n")
        f.write("2. Marked `confirm()` calls for manual review (requires custom implementation)\n\n")
        f.write("3. Added `import toast from 'react-hot-toast'` where needed\n\n")
        f.write("## Next Steps\n\n")
        f.write("1. Search for `TODO: Replace confirm dialog` comments\n")
        f.write("2. Implement custom confirmation dialogs or use a library\n")
        f.write("3. Test all toast notifications\n")
        f.write("4. Verify translations still work for i18n messages\n")

    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    main()
