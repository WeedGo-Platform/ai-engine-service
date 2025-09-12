#!/usr/bin/env python3
import os
import shutil

BASE_DIR = "/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates"

# Template configurations
templates = {
    'vintage': {
        'name': 'Vintage',
        'theme': {
            'name': 'Vintage',
            'mode': 'light',
            'colors': {
                'primary': '#8B4513',  # Saddle Brown
                'primaryLight': '#A0522D',
                'primaryDark': '#654321',
                'secondary': '#D2691E',  # Chocolate
                'accent': '#DEB887',  # Burlywood
                'success': '#556B2F',
                'warning': '#DAA520',
                'error': '#CD5C5C',
                'info': '#708090',
                'background': 'linear-gradient(135deg, #F5E6D3 0%, #E6D7C3 100%)',
                'surface': '#FFF8DC',  # Cornsilk
                'text': '#3E2723',
                'textSecondary': '#5D4037',
                'border': '#D2B48C',
                'userMessage': '#F5DEB3',  # Wheat
                'assistantMessage': '#FAEBD7',  # Antique White
                'systemMessage': '#FFE4B5',  # Moccasin
            }
        }
    },
    'dirty': {
        'name': 'Dirty',
        'theme': {
            'name': 'Dirty',
            'mode': 'dark',
            'colors': {
                'primary': '#2C2416',  # Dark grunge brown
                'primaryLight': '#3E342A',
                'primaryDark': '#1A1511',
                'secondary': '#5C4033',  # Dark brown
                'accent': '#8B7355',  # Rust
                'success': '#4A5D23',
                'warning': '#B8860B',
                'error': '#8B0000',
                'info': '#4682B4',
                'background': 'linear-gradient(135deg, #1C1C1C 0%, #2B2B2B 100%)',
                'surface': 'rgba(40, 40, 40, 0.95)',
                'text': '#D3D3D3',
                'textSecondary': '#A9A9A9',
                'border': '#4A4A4A',
                'userMessage': 'rgba(92, 64, 51, 0.3)',
                'assistantMessage': 'rgba(60, 60, 60, 0.95)',
                'systemMessage': 'rgba(139, 115, 85, 0.2)',
            }
        }
    },
    'metal': {
        'name': 'Metal',
        'theme': {
            'name': 'Metal',
            'mode': 'dark',
            'colors': {
                'primary': '#FF0000',  # Blood red
                'primaryLight': '#FF4444',
                'primaryDark': '#CC0000',
                'secondary': '#000000',  # Black
                'accent': '#C0C0C0',  # Silver
                'success': '#00FF00',
                'warning': '#FFA500',
                'error': '#DC143C',
                'info': '#1E90FF',
                'background': 'linear-gradient(135deg, #000000 0%, #1A1A1A 50%, #000000 100%)',
                'surface': 'rgba(30, 30, 30, 0.98)',
                'text': '#FFFFFF',
                'textSecondary': '#C0C0C0',
                'border': '#666666',
                'userMessage': 'rgba(255, 0, 0, 0.1)',
                'assistantMessage': 'rgba(48, 48, 48, 0.95)',
                'systemMessage': 'rgba(192, 192, 192, 0.1)',
            }
        }
    }
}

def create_theme_file(template_name, theme_config):
    """Create theme.ts file for a template"""
    content = f"""import type {{ ITheme }} from '../../core/contracts/template.contracts';

export const {template_name}Theme: ITheme = {{
  name: '{theme_config['name']}',
  mode: '{theme_config['mode']}',
  colors: {{
    primary: '{theme_config['colors']['primary']}',
    primaryLight: '{theme_config['colors']['primaryLight']}',
    primaryDark: '{theme_config['colors']['primaryDark']}',
    secondary: '{theme_config['colors']['secondary']}',
    accent: '{theme_config['colors']['accent']}',
    
    success: '{theme_config['colors']['success']}',
    warning: '{theme_config['colors']['warning']}',
    error: '{theme_config['colors']['error']}',
    info: '{theme_config['colors']['info']}',
    
    background: '{theme_config['colors']['background']}',
    surface: '{theme_config['colors']['surface']}',
    text: '{theme_config['colors']['text']}',
    textSecondary: '{theme_config['colors']['textSecondary']}',
    border: '{theme_config['colors']['border']}',
    
    userMessage: '{theme_config['colors']['userMessage']}',
    assistantMessage: '{theme_config['colors']['assistantMessage']}',
    systemMessage: '{theme_config['colors']['systemMessage']}',
  }},
  typography: {{
    fontFamily: {{
      body: {'"-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif"' if template_name != 'vintage' else '"Georgia, \'Times New Roman\', serif"'},
      heading: {'"-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif"' if template_name != 'vintage' else '"Georgia, \'Times New Roman\', serif"'},
      mono: '"Fira Code", "Courier New", monospace',
    }},
    fontSize: {{
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '2rem',
    }},
    fontWeight: {{
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    }},
  }},
  spacing: {{
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  }},
  borderRadius: {{
    sm: '{('0.125rem' if template_name == 'metal' else '0.375rem' if template_name == 'dirty' else '0.5rem')}',
    md: '{('0.25rem' if template_name == 'metal' else '0.5rem' if template_name == 'dirty' else '0.75rem')}',
    lg: '{('0.375rem' if template_name == 'metal' else '0.75rem' if template_name == 'dirty' else '1rem')}',
    xl: '{('0.5rem' if template_name == 'metal' else '1rem')}',
    full: '9999px',
  }},
  shadows: {{
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  }},
}};"""
    
    theme_path = os.path.join(BASE_DIR, template_name, 'theme.ts')
    with open(theme_path, 'w') as f:
        f.write(content)
    print(f"Created theme.ts for {template_name}")

def update_provider_file(template_name, class_name):
    """Update provider.tsx file for a template"""
    provider_path = os.path.join(BASE_DIR, template_name, 'provider.tsx')
    
    # Read the weedgo provider as template
    weedgo_provider = os.path.join(BASE_DIR, 'weedgo', 'provider.tsx')
    with open(weedgo_provider, 'r') as f:
        content = f.read()
    
    # Replace class name and theme import
    content = content.replace('WeedGoTemplateProvider', f'{class_name}TemplateProvider')
    content = content.replace("super('weedgo')", f"super('{template_name}')")
    content = content.replace('weedgoTheme', f'{template_name}Theme')
    
    with open(provider_path, 'w') as f:
        f.write(content)
    print(f"Updated provider.tsx for {template_name}")

# Clean up existing directories
for template_name in templates.keys():
    template_dir = os.path.join(BASE_DIR, template_name)
    if os.path.exists(template_dir):
        shutil.rmtree(template_dir)

# Copy WeedGo template to each new template
for template_name, config in templates.items():
    src = os.path.join(BASE_DIR, 'weedgo')
    dst = os.path.join(BASE_DIR, template_name)
    
    # Copy all files
    shutil.copytree(src, dst)
    
    # Remove Python scripts if they exist
    for script in ['batch_create.py', 'batch_create2.py', 'batch_create3.py', 'create_components.sh']:
        script_path = os.path.join(dst, script)
        if os.path.exists(script_path):
            os.remove(script_path)
    
    # Create custom theme file
    create_theme_file(template_name, config['theme'])
    
    # Update provider file
    update_provider_file(template_name, config['name'])

print("\nAll templates created successfully!")