#!/usr/bin/env python3
import os
import re

def fix_topbar_file(filepath):
    """Fix a single TopMenuBar file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if already has CartButton import
        if 'CartButton' not in content:
            return False, "No CartButton found"
            
        # Check for common JSX structure issues
        original_content = content
        
        # Fix extra closing divs at the end
        content = re.sub(r'(\s+</div>\s+</div>\s+)$', '', content)
        
        # Ensure proper return statement structure for Fragment usage
        if '<SimpleCart' in content:
            # Check if it's using Fragment (<>) but incorrectly
            if 'return (<>' in content:
                # Already using Fragment, just ensure proper closing
                if not content.strip().endswith('</>);'):
                    content = re.sub(r'\s*\)\s*;\s*}\s*export', '</>);\n};\n\nexport', content)
            elif 'return (' in content:
                # Check if cart overlay is outside main div
                cart_match = re.search(r'(\{isCartOpen && <SimpleCart[^}]+\})', content)
                if cart_match:
                    cart_code = cart_match.group(1)
                    # Check if it's at the wrong level
                    if re.search(r'</div>\s*\n\s*' + re.escape(cart_code), content):
                        # Move cart overlay inside the main div
                        content = re.sub(r'(</div>)\s*\n\s*(\{isCartOpen && <SimpleCart[^}]+\})\s*</div>', 
                                        r'\n      \2\n    \1', content)
        
        # Fix any double closing div issues
        content = re.sub(r'</div>\s*</div>\s*</div>\s*\);', '</div>\n  );', content)
        
        # Fix Fragment return if needed
        if 'return (<>' in content and not re.search(r'</>\\s*\);?\\s*}', content):
            content = re.sub(r'\s*\);\s*}\s*$', '\n  </>);\n};\n', content)
            
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            return True, "Fixed JSX structure"
        
        return False, "No changes needed"
        
    except Exception as e:
        return False, str(e)

# Fix the problematic templates
templates_to_fix = ['dark-tech', 'dirty', 'metal', 'vintage', 'rasta-vibes']
base_path = '/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates'

for template in templates_to_fix:
    topbar_path = os.path.join(base_path, template, 'components/layout/TopMenuBar.tsx')
    if os.path.exists(topbar_path):
        success, message = fix_topbar_file(topbar_path)
        print(f"{template}: {'✓' if success else '✗'} - {message}")
    else:
        print(f"{template}: File not found")