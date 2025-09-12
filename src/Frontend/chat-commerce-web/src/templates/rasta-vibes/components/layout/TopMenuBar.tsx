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
    <div 
      className="w-full px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[60px] sm:h-[72px]"
      style={{
        background: 'linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(45, 27, 0, 0.9) 50%, rgba(26, 46, 5, 0.9) 100%)',
        borderBottom: '3px solid transparent',
        borderImage: 'linear-gradient(90deg, #DC2626, #FCD34D, #16A34A) 1',
        backdropFilter: 'blur(10px)',
      }}
    >
      {/* Left section with logo */}
      <div className="flex items-center gap-4">
        <img src={potPalaceLogo} alt="Rasta Vibes" className="h-6 sm:h-8 w-auto" />
      </div>

      {/* Center section with search */}
      <div className="flex-1 max-w-md mx-6 flex items-center gap-2">
        {/* Page Toggle Button */}
        <PageToggle className="flex-shrink-0" />
        <ProductSearchDropdown
          placeholder="Search products..."
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
              className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group" 
              title="Logout"
            >
              <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-red-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </button>
          ) : (
            <button 
              onClick={onShowLogin} 
              className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group" 
              title="Login"
            >
              <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </button>
          )}
          
          {/* Sign Up Icon - Only show when not logged in */}
          {!isAuthenticated && (
            <button 
              onClick={onShowRegister} 
              className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group" 
              title="Sign Up"
            >
              <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </button>
          )}
          
          {/* User Profile - Show when logged in */}
        {isAuthenticated && currentUser && (
          <div className="flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-red-900/20 to-green-900/20 rounded-full border border-yellow-500/30">
            <span className="text-yellow-400 text-sm font-medium">{currentUser.name || currentUser.email}</span>
          </div>
        )}
      </div>

      {/* Bottom Decorative Elements */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-center space-x-4 text-xs opacity-30">
        <span style={{ color: '#DC2626' }}>♪</span>
        <span style={{ color: '#FCD34D' }}>•</span>
        <span style={{ color: '#16A34A' }}>♪</span>
        <span style={{ color: '#FCD34D' }}>•</span>
        <span style={{ color: '#DC2626' }}>♪</span>
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 3s infinite;
        }
        .lion-glow {
          animation: lionPulse 2s ease-in-out infinite;
        }
        @keyframes lionPulse {
          0%, 100% { filter: drop-shadow(0 0 10px rgba(252, 211, 77, 0.5)); }
          50% { filter: drop-shadow(0 0 20px rgba(252, 211, 77, 0.8)); }
        }
      `}</style>

      {/* Cart Overlay */}
      {isCartOpen && <SimpleCart isOpen={isCartOpen} onClose={() => setIsCartOpen(false)} />}
    </div>
  );
};

export default TopMenuBar;