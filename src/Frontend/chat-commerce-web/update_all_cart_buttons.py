#!/usr/bin/env python3
import os
import re

templates = [
    "pot-palace",
    "dark-tech", 
    "rasta-vibes",
    "weedgo",
    "metal",
    "dirty",
    "vintage"
]

base_path = "src/templates"

for template in templates:
    file_path = f"{base_path}/{template}/components/layout/TopMenuBar.tsx"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        continue
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if CartButton is already imported
    if "import CartButton" not in content:
        # Find the last import line
        import_pattern = r'(import.*from.*\n)+'
        match = re.search(import_pattern, content)
        if match:
            last_import_end = match.end()
            # Add CartButton import after the last import
            new_import = "import CartButton from '../../../../components/common/CartButton';\n"
            content = content[:last_import_end] + new_import + content[last_import_end:]
    
    # Replace cart button implementations with CartButton component
    # Pattern to match various cart button implementations
    patterns = [
        # Pattern 1: Button with svg and possible badge
        r'{/\*.*?Cart.*?\*/}\s*<button[^>]*>.*?<svg.*?</svg>.*?</button>',
        # Pattern 2: Button with cart icon path
        r'<button[^>]*title="Cart"[^>]*>.*?d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z".*?</button>',
        # Pattern 3: Generic cart button with nested elements
        r'<button[^>]*(?:title="Cart"|className="[^"]*cart[^"]*")[^>]*>(?:(?!</button>).)*</button>',
    ]
    
    replaced = False
    for pattern in patterns:
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, '<CartButton />', content, flags=re.DOTALL)
            replaced = True
            break
    
    # If no pattern matched but we find "Cart" in a button, try a simpler replacement
    if not replaced and '<button' in content and 'Cart' in content:
        # Find cart buttons by looking for buttons with cart-related content
        lines = content.split('\n')
        new_lines = []
        in_cart_button = False
        cart_button_depth = 0
        
        for i, line in enumerate(lines):
            if 'Cart' in line and '<button' in line:
                in_cart_button = True
                cart_button_depth = 1
                # Check if it's a self-closing button
                if '/>' in line:
                    new_lines.append(line.split('<button')[0] + '<CartButton />')
                    in_cart_button = False
                else:
                    new_lines.append(line.split('<button')[0] + '<CartButton />')
            elif in_cart_button:
                if '<button' in line:
                    cart_button_depth += 1
                if '</button>' in line:
                    cart_button_depth -= 1
                    if cart_button_depth == 0:
                        in_cart_button = False
                        continue  # Skip this line
                if in_cart_button:
                    continue  # Skip lines inside cart button
            else:
                new_lines.append(line)
        
        if len(new_lines) != len(lines):
            content = '\n'.join(new_lines)
            replaced = True
    
    # Write the updated content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    if replaced:
        print(f"✅ Updated {template} TopMenuBar")
    else:
        print(f"⚠️  No cart button found to update in {template}")

print("\n✨ Cart button update complete!")