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
    <div className="w-full bg-black px-6 py-3 flex items-center justify-between relative overflow-hidden z-40 h-[72px] border-b border-cyan-500/30">
      {/* Left section with logo */}
      <div className="flex items-center gap-4">
        <img src={potPalaceLogo} alt="Dark Tech" className="h-8 w-auto" />
      </div>

      {/* Center section with search */}
      <div className="flex-1 max-w-md mx-6 flex items-center gap-2">
        {/* Page Toggle Button */}
        <PageToggle className="flex-shrink-0" />
        <ProductSearchDropdown
          placeholder="Search matrix..."
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

        {/* Matrix divider */}
        <div className="w-px h-6 bg-gradient-to-b from-transparent via-cyan-500 to-transparent mx-1"></div>
        
        {/* Login/Logout - Terminal style */}
        {isAuthenticated ? (
          <button 
            onClick={logout} 
            className="px-3 py-1.5 bg-red-900/30 border border-red-500/50 rounded-sm text-red-400 font-mono text-xs uppercase tracking-wider
                     hover:bg-red-900/50 hover:border-red-400 hover:text-red-300 hover:shadow-[0_0_15px_rgba(255,0,0,0.4)]
                     transition-all duration-300" 
            title="LOGOUT"
          >
            &lt;LOGOUT/&gt;
          </button>
        ) : (
          <button 
            onClick={onShowLogin} 
            className="px-3 py-1.5 bg-cyan-900/30 border border-cyan-500/50 rounded-sm text-cyan-400 font-mono text-xs uppercase tracking-wider
                     hover:bg-cyan-900/50 hover:border-cyan-400 hover:text-cyan-300 hover:shadow-[0_0_15px_rgba(0,255,255,0.4)]
                     transition-all duration-300 relative overflow-hidden group" 
            title="ACCESS"
          >
            <span className="relative z-10">&lt;ACCESS/&gt;</span>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/20 to-cyan-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
          </button>
        )}
        
        {/* Sign Up - Glowing button */}
        {!isAuthenticated && (
          <button 
            onClick={onShowRegister} 
            className="px-3 py-1.5 bg-gradient-to-r from-purple-900/50 to-pink-900/50 border border-purple-500/50 rounded-sm text-purple-300 font-mono text-xs uppercase tracking-wider
                     hover:from-purple-900/70 hover:to-pink-900/70 hover:border-purple-400 hover:text-purple-200
                     hover:shadow-[0_0_20px_rgba(147,51,234,0.5)]
                     transition-all duration-300 relative overflow-hidden" 
            title="INITIALIZE"
          >
            <span className="relative z-10">&lt;INIT/&gt;</span>
            <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300">
              <div className="h-full w-full bg-gradient-to-r from-transparent via-purple-400/20 to-transparent animate-shimmer"></div>
            </div>
          </button>
        )}
        
        {/* User Profile - Cyberpunk display */}
        {isAuthenticated && currentUser && (
          <div className="flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-cyan-900/30 to-purple-900/30 border border-cyan-500/30 rounded-sm">
            <div className="relative">
              <div className="w-6 h-6 bg-gradient-to-br from-cyan-500 to-purple-500 rounded-sm flex items-center justify-center">
                <span className="text-[10px] font-bold text-black">
                  {(currentUser.name || currentUser.email || 'U')[0].toUpperCase()}
                </span>
              </div>
              <div className="absolute inset-0 bg-cyan-400 rounded-sm animate-ping opacity-20"></div>
            </div>
            <span className="text-cyan-300 text-xs font-mono uppercase tracking-wider">
              USER:{(currentUser.name || currentUser.email || 'ANONYMOUS').substring(0, 8)}
            </span>
          </div>
        )}
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes scan {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(7200%); }
        }
        .animate-shimmer {
          animation: shimmer 3s infinite;
        }
        .animate-scan {
          animation: scan 4s linear infinite;
        }
      `}</style>
      
      {/* Cart Overlay */}
      {isCartOpen && <SimpleCart isOpen={isCartOpen} onClose={() => setIsCartOpen(false)} />}
    </div>
  );
};

export default TopMenuBar;