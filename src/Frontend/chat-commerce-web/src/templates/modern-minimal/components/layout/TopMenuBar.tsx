import React, { useState } from 'react';
import PageToggle from '../../../../components/common/PageToggle';
import { useAuth } from '../../../../contexts/AuthContext';
import { useCart } from '../../../../contexts/CartContext';
import modernMinimalLogo from '../../assets/modern-minimal-logo.png';
import ProductSearchDropdown from '../../../../components/search/ProductSearchDropdown';
import { Product } from '../../../../services/productSearch';
import SimpleCart from '../../../../components/cart/SimpleCart';
import CartButton from '../../../../components/common/CartButton';

interface TopMenuBarProps {
  onShowLogin: () => void;
  onShowRegister: () => void;
  onViewProductDetails?: (product: Product) => void;
}

const TopMenuBar: React.FC<TopMenuBarProps> = ({
  onShowLogin,
  onShowRegister,
  onViewProductDetails
}) => {
  const { currentUser, logout, isAuthenticated } = useAuth();
  const { itemCount } = useCart();
  const [isCartOpen, setIsCartOpen] = useState(false);
  return (
    <div className="w-full bg-white backdrop-blur-xl px-8 py-3 flex items-center justify-between border-b border-slate-300 relative overflow-hidden z-40 h-[64px] shadow-md">
      {/* Ultra-minimal Apple-inspired design */}
      
      <div className="flex items-center gap-6 relative z-10">
        {/* Logo - Sophisticated monochrome */}
        <div className="flex items-center gap-3">
          <img src={modernMinimalLogo} alt="Pot Palace Cannabis Co." className="h-8 w-auto opacity-90 grayscale contrast-125" />
        </div>
      </div>

      {/* Search Bar - Minimal and refined */}
      <div className="flex-1 max-w-xl mx-12 relative">
        {/* Page Toggle Button */}
        <PageToggle className="flex-shrink-0" />
        <ProductSearchDropdown
          placeholder="Search"
          className="flex-1"
          inputClassName="w-full px-4 py-2 bg-slate-100 backdrop-blur-sm rounded-lg text-slate-900 placeholder-slate-600 pr-10 
                     focus:outline-none focus:bg-white focus:ring-2 focus:ring-slate-400 border border-slate-300
                     transition-all duration-300 text-sm font-medium
                     hover:bg-slate-50"
          dropdownClassName="bg-white border-slate-200 shadow-xl rounded-lg"
          resultItemClassName="hover:bg-slate-50 border-slate-100"
          onProductSelect={(product) => {
            console.log('Product selected:', product);
            if (onViewProductDetails) {
              onViewProductDetails(product);
            }
          }}
        />
      </div>

      {/* Right Actions - Clean geometric design */}
      <div className="relative z-10">
        <div className="flex items-center gap-1">
          {/* Language Button - Subtle hover effect */}
          <button className="p-2.5 rounded-lg hover:bg-slate-100 transition-all duration-200 group" title="Language">
            <svg className="w-4 h-4 text-slate-700 group-hover:text-slate-900 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          </button>
          
          {/* Cart Button - Minimal design */}
          <CartButton />

          {/* Divider */}
          <div className="w-px h-5 bg-slate-300 mx-2"></div>
          
          {/* Login/Logout Button */}
          {isAuthenticated ? (
            <button 
              onClick={logout} 
              className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all duration-200" 
              title="Sign Out"
            >
              Sign Out
            </button>
          ) : (
            <>
              <button 
                onClick={onShowLogin} 
                className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all duration-200" 
                title="Sign In"
              >
                Sign In
              </button>
              
              {/* Sign Up Button - Premium feel */}
              <button 
                onClick={onShowRegister} 
                className="ml-2 px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg" 
                title="Get Started"
              >
                Get Started
              </button>
            </>
          )}
          
          {/* User Profile - Elegant display */}
          {isAuthenticated && currentUser && (
            <div className="flex items-center gap-2 ml-3">
              <div className="w-8 h-8 bg-gradient-to-br from-slate-200 to-slate-300 rounded-full flex items-center justify-center">
                <span className="text-xs font-semibold text-slate-800">
                  {(currentUser.name || currentUser.email || 'U')[0].toUpperCase()}
                </span>
              </div>
              <span className="text-sm font-medium text-slate-800 hidden lg:block">
                {currentUser.name || currentUser.email}
              </span>
            </div>
          )}
        </div>
      </div>
      
      {/* Cart Overlay */}
      {isCartOpen && <SimpleCart isOpen={isCartOpen} onClose={() => setIsCartOpen(false)} />}
    </div>
  );
};

export default TopMenuBar;