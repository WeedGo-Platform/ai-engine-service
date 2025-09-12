#!/usr/bin/env python3
import os
import re

def fix_product_selection(filepath):
    """Ensure ProductSearchDropdown has proper onProductSelect implementation with console logging"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Check if it has ProductSearchDropdown
        if 'ProductSearchDropdown' not in content:
            return False, "No ProductSearchDropdown found"
            
        # Pattern to find ProductSearchDropdown component usage
        dropdown_pattern = r'<ProductSearchDropdown\s*([^/>]*?)(?:/?>|>[\s\S]*?</ProductSearchDropdown>)'
        
        def replace_dropdown(match):
            attrs = match.group(1)
            closing = match.group(0)[-2:]  # Get '/>' or '>'
            
            # Check if onProductSelect already exists
            if 'onProductSelect' in attrs:
                # Check if it has proper implementation with console log
                if 'console.log' not in attrs:
                    # Replace the existing onProductSelect
                    attrs = re.sub(
                        r'onProductSelect=\{[^}]*\}',
                        '''onProductSelect={(product) => {
            console.log('Product selected:', product);
            if (onViewProductDetails) {
              onViewProductDetails(product);
            }
          }}''',
                        attrs
                    )
                return f'<ProductSearchDropdown\n          {attrs.strip()}\n        {closing}'
            else:
                # Add onProductSelect attribute
                new_attrs = attrs.rstrip() + '''
          onProductSelect={(product) => {
            console.log('Product selected:', product);
            if (onViewProductDetails) {
              onViewProductDetails(product);
            }
          }}'''
                return f'<ProductSearchDropdown{new_attrs}\n        {closing}'
        
        # Replace all ProductSearchDropdown instances
        content = re.sub(dropdown_pattern, replace_dropdown, content)
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            return True, "Fixed onProductSelect with console logging"
        
        # Check if console.log is already there
        if 'console.log' in content and 'onProductSelect' in content:
            return False, "Already has console logging"
        
        return False, "No changes needed"
        
    except Exception as e:
        return False, str(e)

# Process all template TopMenuBar files
templates = ['weedgo', 'vintage', 'rasta-vibes', 'pot-palace', 'modern-minimal', 'dark-tech', 'dirty', 'metal']
base_path = '/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates'

for template in templates:
    topbar_path = os.path.join(base_path, template, 'components/layout/TopMenuBar.tsx')
    if os.path.exists(topbar_path):
        success, message = fix_product_selection(topbar_path)
        print(f"{template}: {'✓' if success else '✗'} - {message}")
    else:
        print(f"{template}: File not found")