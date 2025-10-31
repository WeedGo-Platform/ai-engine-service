#!/usr/bin/env python3
"""
Script to fix hardcoded localhost URLs in frontend files
Replaces inline environment checks with centralized getApiEndpoint() helper
"""

import re
import sys
from pathlib import Path

def fix_file(file_path):
    """Fix hardcoded URLs in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Pattern 1: `${import.meta.env.VITE_API_URL || 'http://localhost:5024'}/api/...`
        # Replace with getApiEndpoint('/...')
        pattern1 = r'`\$\{import\.meta\.env\.VITE_API_URL \|\| [\'"]http://localhost:[0-9]+[\'"]\}/api(/[^`]*)`'
        replacement1 = r"getApiEndpoint('\1')"
        new_content, count1 = re.subn(pattern1, replacement1, content)
        if count1 > 0:
            changes_made.append(f"Replaced {count1} inline URL(s) with getApiEndpoint()")
            content = new_content

        # Pattern 2: import.meta.env.VITE_API_URL || 'http://localhost:5024'
        # (not in template literal, used in variable assignment or similar)
        pattern2 = r"import\.meta\.env\.VITE_API_URL \|\| ['\"]http://localhost:[0-9]+['\"]"
        replacement2 = "appConfig.api.baseUrl"
        new_content, count2 = re.subn(pattern2, replacement2, content)
        if count2 > 0:
            changes_made.append(f"Replaced {count2} API_BASE_URL declaration(s) with appConfig.api.baseUrl")
            content = new_content

        # Pattern 3: State initialization with hardcoded URL
        # useState('http://localhost:5024')
        pattern3 = r"useState\(['\"]http://localhost:5024['\"]\)"
        replacement3 = "useState(appConfig.api.baseUrl)"
        new_content, count3 = re.subn(pattern3, replacement3, content)
        if count3 > 0:
            changes_made.append(f"Replaced {count3} useState with hardcoded URL")
            content = new_content

        # Pattern 4: Placeholder in input
        # placeholder="http://localhost:5024"
        pattern4 = r'placeholder=["\']http://localhost:[0-9]+["\']'
        replacement4 = 'placeholder="API URL from environment"'
        new_content, count4 = re.subn(pattern4, replacement4, content)
        if count4 > 0:
            changes_made.append(f"Updated {count4} placeholder(s)")
            content = new_content

        if content != original_content:
            # Check if imports are needed
            needs_get_api_endpoint = 'getApiEndpoint' in content and "from '../config/app.config'" not in content and 'from "@/config/app.config"' not in content
            needs_app_config = 'appConfig' in content and "from '../config/app.config'" not in content and 'from "@/config/app.config"' not in content

            if needs_get_api_endpoint or needs_app_config:
                # Find the last import statement
                import_pattern = r"(import .*?;\n)"
                imports = list(re.finditer(import_pattern, content))
                if imports:
                    last_import = imports[-1]
                    insert_pos = last_import.end()

                    if needs_get_api_endpoint and needs_app_config:
                        new_import = "import { getApiEndpoint, appConfig } from '../config/app.config';\n"
                    elif needs_get_api_endpoint:
                        new_import = "import { getApiEndpoint } from '../config/app.config';\n"
                    else:
                        new_import = "import { appConfig } from '../config/app.config';\n"

                    content = content[:insert_pos] + new_import + content[insert_pos:]
                    changes_made.append("Added app.config import")

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✓ Fixed {file_path.name}:")
            for change in changes_made:
                print(f"  - {change}")
            return True
        else:
            print(f"  {file_path.name}: No changes needed")
            return False

    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    """Main function"""
    # Files to fix
    base_path = Path(__file__).parent / "src/Frontend/ai-admin-dashboard/src"

    files_to_fix = [
        # Pages
        base_path / "pages/LogViewer.tsx",
        base_path / "pages/TenantManagement.tsx",
        base_path / "pages/TenantSignup.tsx",
        base_path / "pages/VoiceAPITest.tsx",
        # Components
        base_path / "components/AdminNotifications.tsx",
        base_path / "components/ChatWidget.tsx",
        base_path / "components/OntarioLicenseValidator.tsx",
        base_path / "components/SalesChatWidget.tsx",
        base_path / "components/TenantEditModal.tsx",
        # Hooks
        base_path / "hooks/useBackendTranslation.ts",
        # Config
        base_path / "config/auth.config.ts",
    ]

    print("🔧 Fixing hardcoded localhost URLs...\n")

    fixed_count = 0
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    print(f"\n✅ Fixed {fixed_count} file(s)")

if __name__ == "__main__":
    main()
