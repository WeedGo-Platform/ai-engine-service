#!/usr/bin/env python3

import os
import re
import sys

# Pages to update
pages = [
    "src/pages/Products.tsx",
    "src/pages/Inventory.tsx",
    "src/pages/Accessories.tsx",
    "src/pages/Orders.tsx",
    "src/pages/Customers.tsx",
    "src/pages/Communications.tsx",
    "src/pages/DeliveryManagement.tsx"
]

def add_store_selection_imports(content):
    """Add necessary imports if they don't exist"""
    imports_to_add = []

    # Check and add StoreSelectionModal import
    if "import StoreSelectionModal" not in content:
        imports_to_add.append("import StoreSelectionModal from '../components/StoreSelectionModal';")

    # Check and add useStoreContext import
    if "useStoreContext" not in content:
        imports_to_add.append("import { useStoreContext } from '../contexts/StoreContext';")

    # Check and add useAuth import
    if "useAuth" not in content:
        imports_to_add.append("import { useAuth } from '../contexts/AuthContext';")

    # Check and add useNavigate import
    if "useNavigate" not in content and "from 'react-router-dom'" not in content:
        imports_to_add.append("import { useNavigate } from 'react-router-dom';")

    # Check and add useEffect, useState if needed
    if "useState" not in content or "useEffect" not in content:
        # Update React import
        content = re.sub(
            r"import React.*? from 'react';",
            "import React, { useState, useEffect } from 'react';",
            content
        )

    # Add imports after the last import statement
    if imports_to_add:
        last_import_match = None
        for match in re.finditer(r"^import.*?;$", content, re.MULTILINE):
            last_import_match = match

        if last_import_match:
            insert_position = last_import_match.end()
            imports_str = "\n" + "\n".join(imports_to_add)
            content = content[:insert_position] + imports_str + content[insert_position:]

    return content

def add_store_selection_hooks(content, component_name):
    """Add hooks and state for store selection"""

    # Find the component function start
    component_pattern = rf"const {component_name}.*?=.*?\(.*?\).*?=>\s*{{"
    match = re.search(component_pattern, content, re.DOTALL)

    if not match:
        print(f"  ✗ Could not find component definition for {component_name}")
        return content

    # Find where to insert hooks (after the opening brace)
    insert_pos = match.end()

    # Check if hooks already exist
    if "showStoreSelectionModal" in content:
        print(f"  ✓ Store selection hooks already exist")
        return content

    hooks_code = """
  const navigate = useNavigate();
  const { currentStore, selectStore, stores } = useStoreContext();
  const { user, isSuperAdmin, isTenantAdminOnly, isStoreManager } = useAuth();
  const [showStoreSelectionModal, setShowStoreSelectionModal] = useState(false);
  const [selectedStoreForPage, setSelectedStoreForPage] = useState<{id: string, name: string} | null>(null);

  // Determine if we need to show store selection modal
  useEffect(() => {
    if (isSuperAdmin() || isTenantAdminOnly()) {
      // For admins, check if we have a current store selected
      if (currentStore) {
        setSelectedStoreForPage({ id: currentStore.id, name: currentStore.name });
      } else if (!selectedStoreForPage) {
        // Only show modal if no store is selected
        setShowStoreSelectionModal(true);
      }
    } else if (isStoreManager()) {
      // For store managers, use the current store from context (which should be auto-selected)
      if (currentStore) {
        setSelectedStoreForPage({ id: currentStore.id, name: currentStore.name });
      } else if (user?.stores && user.stores.length > 0) {
        // Fallback to user's first store if context hasn't loaded yet
        const userStore = user.stores[0];
        setSelectedStoreForPage({ id: userStore.id, name: userStore.name });
      }
    }
  }, [currentStore, user, isSuperAdmin, isTenantAdminOnly, isStoreManager]);

  const handleStoreSelect = async (tenantId: string, storeId: string, storeName: string, tenantName?: string) => {
    try {
      await selectStore(storeId, storeName);
      setSelectedStoreForPage({ id: storeId, name: storeName });
      setShowStoreSelectionModal(false);
    } catch (error) {
      console.error('Failed to select store:', error);
      // Still set the local state even if context update fails
      setSelectedStoreForPage({ id: storeId, name: storeName });
      setShowStoreSelectionModal(false);
    }
  };
"""

    # Insert hooks
    content = content[:insert_pos] + hooks_code + content[insert_pos:]

    return content

def add_loading_state(content, component_name):
    """Add loading state while store is being determined"""

    # Find the return statement of the component
    return_pattern = rf"return\s*\("
    match = re.search(return_pattern, content)

    if not match:
        print(f"  ✗ Could not find return statement")
        return content

    # Check if loading state already exists
    if "!selectedStoreForPage && !showStoreSelectionModal" in content:
        print(f"  ✓ Loading state already exists")
        return content

    loading_code = """
  // Show loading state while determining store
  if (!selectedStoreForPage && !showStoreSelectionModal) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  """

    # Insert loading state before the main return
    insert_pos = match.start()
    content = content[:insert_pos] + loading_code + content[insert_pos:]

    return content

def add_modal_component(content):
    """Add StoreSelectionModal component to the JSX"""

    # Find the last closing tag in the component (usually </div>)
    # Look for the pattern of the main return statement's closing

    # Check if modal already exists
    if "<StoreSelectionModal" in content:
        print(f"  ✓ StoreSelectionModal component already exists")
        return content

    # Find the last closing tag before the component's closing brace
    # This is a bit tricky, so we'll look for the pattern of the return statement
    # and then find its corresponding closing tag

    # Find the main return statement
    return_match = re.search(r"return\s*\([^{]*?<div", content, re.DOTALL)
    if not return_match:
        print(f"  ✗ Could not find main return div")
        return content

    # Count opening and closing div tags to find the right place
    # Simple approach: add before the last closing tag in the file
    last_close_tag = content.rfind("</div>")
    second_last_close = content.rfind("</div>", 0, last_close_tag)

    if second_last_close == -1:
        insert_pos = last_close_tag
    else:
        # Try to find a good spot - usually after the last major component
        insert_pos = last_close_tag

    modal_code = """

      <StoreSelectionModal
        isOpen={showStoreSelectionModal}
        onSelect={handleStoreSelect}
        onClose={() => {
          // Close modal and navigate to dashboard
          setShowStoreSelectionModal(false);
          navigate('/dashboard');
        }}
      />"""

    content = content[:insert_pos] + modal_code + content[insert_pos:]

    return content

def extract_component_name(filepath):
    """Extract component name from file path"""
    filename = os.path.basename(filepath)
    return filename.replace('.tsx', '')

def process_file(filepath):
    """Process a single file to add store selection modal"""

    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False

    component_name = extract_component_name(filepath)
    print(f"\nProcessing {component_name}...")

    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already has store selection
    if "showStoreSelectionModal" in content and "StoreSelectionModal" in content:
        print(f"  ✓ Already has store selection modal")
        return True

    # Process the file
    original_content = content

    # Step 1: Add imports
    content = add_store_selection_imports(content)

    # Step 2: Add hooks and state
    content = add_store_selection_hooks(content, component_name)

    # Step 3: Add loading state
    content = add_loading_state(content, component_name)

    # Step 4: Add modal component
    content = add_modal_component(content)

    # Write back only if changed
    if content != original_content:
        # Create backup
        backup_path = filepath + '.bak'
        with open(backup_path, 'w') as f:
            f.write(original_content)

        # Write updated content
        with open(filepath, 'w') as f:
            f.write(content)

        print(f"  ✓ Updated successfully (backup saved as {backup_path})")
        return True
    else:
        print(f"  ℹ No changes needed")
        return True

def main():
    print("=" * 60)
    print("Adding Store Selection Modal to Required Pages")
    print("=" * 60)

    success_count = 0
    for page_path in pages:
        if process_file(page_path):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"Completed: {success_count}/{len(pages)} pages updated")
    print("=" * 60)

    if success_count < len(pages):
        print("\n⚠ Some pages could not be updated. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✓ All pages updated successfully!")
        print("\nNote: Please review the changes and test the functionality.")
        print("You may need to adjust the store selection logic based on your specific requirements.")

if __name__ == "__main__":
    main()