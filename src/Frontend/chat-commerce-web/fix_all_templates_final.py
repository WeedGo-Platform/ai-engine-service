#!/usr/bin/env python3
import os
import glob

# Template for a properly structured TopMenuBar component
template = """import React, {{ useState }} from 'react';
import {{ useAuth }} from '../../../../contexts/AuthContext';
import {{ useCart }} from '../../../../contexts/CartContext';
import potPalaceLogo from '../../../../assets/pot-palace-logo.png';
import ProductSearchDropdown from '../../../../components/search/ProductSearchDropdown';
import {{ Product }} from '../../../../services/productSearch';
import SimpleCart from '../../../../components/cart/SimpleCart';
import CartButton from '../../../../components/common/CartButton';

interface TopMenuBarProps {{
  onShowLogin: () => void;
  onShowRegister: () => void;
  onViewProductDetails?: (product: Product) => void;
}}

const TopMenuBar: React.FC<TopMenuBarProps> = ({{
  onShowLogin,
  onShowRegister,
  onViewProductDetails
}}) => {{
  const {{ currentUser, logout, isAuthenticated }} = useAuth();
  const {{ itemCount }} = useCart();
  const [isCartOpen, setIsCartOpen] = useState(false);

  return (
    <div className="{class_name}">
      {{/* Left section with logo */}}
      <div className="flex items-center gap-4">
        <img src={{potPalaceLogo}} alt="{alt_text}" className="h-6 sm:h-8 w-auto" />
      </div>

      {{/* Center section with search */}}
      <div className="flex-1 max-w-md mx-6">
        <ProductSearchDropdown
          placeholder="{search_placeholder}"
          className="w-full"
          onProductSelect={{(product) => {{
            console.log("Product selected:", product);
            if (onViewProductDetails) {{
              onViewProductDetails(product);
            }}
          }}}}
        />
      </div>

      {{/* Right section with icons */}}
      <div className="flex items-center gap-2">
        {{/* Cart Button */}}
        <CartButton />
        
        {{/* Login/Logout Icon */}}
        {{isAuthenticated ? (
          <button 
            onClick={{logout}} 
            className="{logout_btn_class}" 
            title="Logout"
          >
            <svg className="{icon_class}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </button>
        ) : (
          <button 
            onClick={{onShowLogin}} 
            className="{login_btn_class}" 
            title="Login"
          >
            <svg className="{icon_class}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </button>
        )}}
        
        {{/* Sign Up Icon - Only show when not logged in */}}
        {{!isAuthenticated && (
          <button 
            onClick={{onShowRegister}} 
            className="{register_btn_class}" 
            title="Sign Up"
          >
            <svg className="{register_icon_class}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </button>
        )}}
        
        {{/* User Profile - Show when logged in */}}
        {{isAuthenticated && currentUser && (
          <div className="{user_profile_class}">
            <span className="{user_text_class}">{{currentUser.name || currentUser.email}}</span>
          </div>
        )}}
      </div>
      
      {{/* Cart Overlay */}}
      {{isCartOpen && <SimpleCart isOpen={{isCartOpen}} onClose={{() => setIsCartOpen(false)}} />}}
    </div>
  );
}};

export default TopMenuBar;"""

# Template configurations
templates = {
    'weedgo': {
        'class_name': 'w-full bg-gradient-to-r from-green-900 via-green-800 to-green-900 px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]',
        'alt_text': 'WeedGo',
        'search_placeholder': 'Search cannabis products...',
        'logout_btn_class': 'p-2 sm:p-2.5 rounded-full hover:bg-green-700/50 transition-all group',
        'login_btn_class': 'p-2 sm:p-2.5 rounded-full hover:bg-green-700/50 transition-all group',
        'register_btn_class': 'p-2.5 rounded-full hover:bg-green-700/50 transition-all group',
        'icon_class': 'w-4 sm:w-5 h-4 sm:h-5 text-green-200 group-hover:text-white transition-colors',
        'register_icon_class': 'w-5 h-5 text-green-200 group-hover:text-white transition-colors',
        'user_profile_class': 'flex items-center gap-2 px-3 py-1 bg-green-700/50 rounded-full',
        'user_text_class': 'text-green-200 text-sm font-medium'
    },
    'vintage': {
        'class_name': 'w-full bg-gradient-to-r from-[#8B7355] via-[#A0826D] to-[#B8956A] px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]',
        'alt_text': 'Vintage Cannabis',
        'search_placeholder': 'Search vintage strains...',
        'logout_btn_class': 'p-2 sm:p-2.5 rounded-full hover:bg-[#8B7355]/20 transition-all group',
        'login_btn_class': 'p-2 sm:p-2.5 rounded-full hover:bg-[#8B7355]/20 transition-all group',
        'register_btn_class': 'p-2.5 rounded-full hover:bg-[#8B7355]/20 transition-all group',
        'icon_class': 'w-4 sm:w-5 h-4 sm:h-5 text-[#FFF8DC] group-hover:text-[#FFD700] transition-colors',
        'register_icon_class': 'w-5 h-5 text-[#FFF8DC] group-hover:text-[#FFD700] transition-colors',
        'user_profile_class': 'flex items-center gap-2 px-3 py-1 bg-[#8B7355]/20 rounded-full',
        'user_text_class': 'text-[#FFF8DC] text-sm font-medium'
    },
    'metal': {
        'class_name': 'w-full bg-gradient-to-r from-[#1A1A1A] via-[#2C2C2C] to-[#1A1A1A] px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]',
        'alt_text': 'Metal Cannabis',
        'search_placeholder': 'Search products...',
        'logout_btn_class': 'p-2 sm:p-2.5 rounded-none hover:bg-[#333333]/50 transition-all group',
        'login_btn_class': 'p-2 sm:p-2.5 rounded-none hover:bg-[#333333]/50 transition-all group',
        'register_btn_class': 'p-2.5 rounded-none hover:bg-[#333333]/50 transition-all group',
        'icon_class': 'w-4 sm:w-5 h-4 sm:h-5 text-[#999999] group-hover:text-[#DC143C] transition-colors',
        'register_icon_class': 'w-5 h-5 text-[#999999] group-hover:text-[#DC143C] transition-colors',
        'user_profile_class': 'flex items-center gap-2 px-3 py-1 bg-[#333333]/50 rounded-none',
        'user_text_class': 'text-[#999999] text-sm font-bold uppercase'
    },
    'dirty': {
        'class_name': 'w-full bg-gradient-to-r from-[#3E2723] via-[#5D4037] to-[#4E342E] px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]',
        'alt_text': 'Dirty Cannabis',
        'search_placeholder': 'Search strains...',
        'logout_btn_class': 'p-2 sm:p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group',
        'login_btn_class': 'p-2 sm:p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group',
        'register_btn_class': 'p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group',
        'icon_class': 'w-4 sm:w-5 h-4 sm:h-5 text-[#9E9E9E] group-hover:text-[#FF5722] transition-colors',
        'register_icon_class': 'w-5 h-5 text-[#9E9E9E] group-hover:text-[#FF5722] transition-colors',
        'user_profile_class': 'flex items-center gap-2 px-3 py-1 bg-[#424242]/50 rounded-lg',
        'user_text_class': 'text-[#9E9E9E] text-sm font-medium'
    }
}

# Process each template
for template_name, config in templates.items():
    file_path = f'src/templates/{template_name}/components/layout/TopMenuBar.tsx'
    if os.path.exists(file_path):
        content = template.format(**config)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed {template_name}")

print("All templates fixed!")