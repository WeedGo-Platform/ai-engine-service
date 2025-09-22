#!/usr/bin/env python3
"""
Fix TypeScript errors in the codebase
"""
import os
import re

def fix_unused_imports():
    """Remove unused imports from files"""
    files_to_fix = {
        'src/App.tsx': [
            ('TrendingUp', 'ChevronLeft'),
        ],
        'src/components/pos/PaymentModal.tsx': [
            ('React',),
        ],
        'src/components/ChatWidget.tsx': [
            ('Send', 'Zap', 'Hash'),
        ],
        'src/components/accessories/BarcodeIntakeModal.tsx': [
            ('Camera', 'Hash', 'Image'),
        ],
        'src/components/accessories/QuickIntakeModal.tsx': [
            ('Tag', 'Camera'),
        ],
        'src/components/accessories/InventoryAdjustModal.tsx': [
            ('TrendingUp',),
        ],
        'src/components/PaymentProviderSettings.tsx': [
            ('useEffect', 'Settings', 'X'),
        ],
        'src/components/POSTerminalSettings.tsx': [
            ('Settings', 'CreditCard', 'DollarSign'),
        ],
        'src/components/pos/TransactionHistory.tsx': [
            ('MoreVertical', 'Mail', 'Download', 'ChevronDown', 'User', 'Clock'),
        ],
        'src/components/storeSettings/AllSettingsTabbed.tsx': [
            ('useEffect',),
        ],
        'src/components/storeSettings/OnlinePaymentSettings.tsx': [
            ('useEffect', 'CreditCard'),
        ],
        'src/components/TenantEditModal.tsx': [
            ('AlertCircle', 'Shield', 'Zap'),
        ],
        'src/components/ProductDetailsModal.tsx': [
            ('Calendar',),
        ],
        'src/components/CreatePurchaseOrderModal.tsx': [
            ('products',),
        ],
        'src/components/ASNImportModal.tsx': [
            ('Package',),
        ]
    }

    for filepath, unused_imports_list in files_to_fix.items():
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        for unused_imports in unused_imports_list:
            for unused_import in unused_imports:
                # Remove from import statements
                # Pattern 1: Remove from middle or end of import list
                pattern1 = rf',\s*{re.escape(unused_import)}(?=\s*[,}}])'
                content = re.sub(pattern1, '', content)

                # Pattern 2: Remove from beginning of import list
                pattern2 = rf'{re.escape(unused_import)}\s*,\s*'
                content = re.sub(pattern2, '', content)

                # Pattern 3: Remove if it's the only import
                pattern3 = rf'import\s+{{\s*{re.escape(unused_import)}\s*}}\s+from\s+[\'"][^\'"]+[\'"];?\n'
                content = re.sub(pattern3, '', content)

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed unused imports in: {filepath}")

def fix_type_errors():
    """Fix various type errors"""
    fixes = []

    # Fix ASNImportModal null type issue
    fixes.append({
        'file': 'src/components/ASNImportModal.tsx',
        'old': 'supplier_name: selectedProduct?.supplier_name || null',
        'new': 'supplier_name: selectedProduct?.supplier_name || undefined'
    })

    # Fix PaymentProviderSettings type issues
    fixes.append({
        'file': 'src/components/PaymentProviderSettings.tsx',
        'old': '...provider,',
        'new': '...(provider as PaymentProvider),'
    })

    # Fix transaction history status type
    fixes.append({
        'file': 'src/components/pos/TransactionHistory.tsx',
        'old': 'statusColors[transaction.status]',
        'new': 'statusColors[transaction.status as keyof typeof statusColors]'
    })

    # Fix refunded_amount checks
    fixes.append({
        'file': 'src/components/pos/TransactionHistory.tsx',
        'old': 'transaction.refunded_amount',
        'new': '(transaction.refunded_amount ?? 0)'
    })

    # Fix StoreSelectionModal types
    fixes.append({
        'file': 'src/components/StoreSelectionModal.tsx',
        'old': 'const response = await fetch',
        'new': 'const response: any = await fetch'
    })

    # Fix AllSettingsTabbed parameter types
    fixes.append({
        'file': 'src/components/storeSettings/AllSettingsTabbed.tsx',
        'old': '.filter(t =>',
        'new': '.filter((t: any) =>'
    })

    fixes.append({
        'file': 'src/components/storeSettings/AllSettingsTabbed.tsx',
        'old': '.map((terminal, index)',
        'new': '.map((terminal: any, index)'
    })

    fixes.append({
        'file': 'src/components/storeSettings/AllSettingsTabbed.tsx',
        'old': '.map((tip, index)',
        'new': '.map((tip: any, index: number)'
    })

    # Fix TenantEditModal subscription tier indexing
    fixes.append({
        'file': 'src/components/TenantEditModal.tsx',
        'old': 'subscriptionPlans[editedTenant?.subscription_tier',
        'new': 'subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans)'
    })

    # Apply fixes
    for fix in fixes:
        filepath = fix['file']
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        content = content.replace(fix['old'], fix['new'])

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed type error in: {filepath}")

def remove_api_import():
    """Remove unused api import from ASNImportModal"""
    filepath = 'src/components/ASNImportModal.tsx'
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()

        # Remove the api import line
        lines = [line for line in lines if not (line.strip().startswith('import api') or line.strip().startswith('import { api'))]

        with open(filepath, 'w') as f:
            f.writelines(lines)
        print(f"Removed api import from: {filepath}")

def fix_router_config():
    """Fix React Router v7 config"""
    filepath = 'src/App.tsx'
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        # Remove v7_startTransition from future config
        content = re.sub(r',?\s*v7_startTransition:\s*true,?', '', content)

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed router config in: {filepath}")

if __name__ == '__main__':
    print("Fixing TypeScript errors...")
    fix_unused_imports()
    fix_type_errors()
    remove_api_import()
    fix_router_config()
    print("\nDone! Run 'npx tsc --noEmit' to check remaining errors.")