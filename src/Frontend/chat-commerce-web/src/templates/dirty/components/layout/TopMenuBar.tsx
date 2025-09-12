import React, { useState } from 'react';
import PageToggle from '../../../../components/common/PageToggle';
import { useAuth } from '../../../../contexts/AuthContext';
import { useCart } from '../../../../contexts/CartContext';
import potPalaceLogo from '../../../../assets/pot-palace-logo.png';
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
    <div className="w-full bg-gradient-to-r from-[#3E2723] via-[#5D4037] to-[#4E342E] px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]">
      {/* Left section with logo */}
      <div className="flex items-center gap-4">
        <img src={potPalaceLogo} alt="Dirty Cannabis" className="h-6 sm:h-8 w-auto" />
      </div>

      {/* Center section with search */}
      <div className="flex-1 max-w-md mx-6 flex items-center gap-2">
        {/* Page Toggle Button */}
        <PageToggle className="flex-shrink-0" />
        <ProductSearchDropdown
          placeholder="Search strains..."
          className="flex-1"
          onProductSelect={(product) => {
            console.log("Product selected:", product);
            if (onViewProductDetails) {
              onViewProductDetails(product);
            }
          }}
        />
      </div>

      {/* Right section with icons */}
      <div className="flex items-center gap-2">
        {/* Cart Button */}
        <CartButton />
        
        {/* Login/Logout Icon */}
        {isAuthenticated ? (
          <button 
            onClick={logout} 
            className="p-2 sm:p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group" 
            title="Logout"
          >
            <svg className="w-4 sm:w-5 h-4 sm:h-5 text-[#9E9E9E] group-hover:text-[#FF5722] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </button>
        ) : (
          <button 
            onClick={onShowLogin} 
            className="p-2 sm:p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group" 
            title="Login"
          >
            <svg className="w-4 sm:w-5 h-4 sm:h-5 text-[#9E9E9E] group-hover:text-[#FF5722] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </button>
        )}
        
        {/* Sign Up Icon - Only show when not logged in */}
        {!isAuthenticated && (
          <button 
            onClick={onShowRegister} 
            className="p-2.5 rounded-lg hover:bg-[#424242]/50 transition-all group" 
            title="Sign Up"
          >
            <svg className="w-5 h-5 text-[#9E9E9E] group-hover:text-[#FF5722] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </button>
        )}
        
        {/* User Profile - Show when logged in */}
        {isAuthenticated && currentUser && (
          <div className="flex items-center gap-2 px-3 py-1 bg-[#424242]/50 rounded-lg">
            <span className="text-[#9E9E9E] text-sm font-medium">{currentUser.name || currentUser.email}</span>
          </div>
        )}
      </div>
      
      {/* Cart Overlay */}
      {isCartOpen && <SimpleCart isOpen={isCartOpen} onClose={() => setIsCartOpen(false)} />}
    </div>
  );
};

export default TopMenuBar;