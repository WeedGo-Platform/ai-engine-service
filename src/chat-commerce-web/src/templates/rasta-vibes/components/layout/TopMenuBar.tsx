import React from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import potPalaceLogo from '../../../../assets/pot-palace-logo.png';
import ProductSearchDropdown from '../../../../components/search/ProductSearchDropdown';

interface TopMenuBarProps {
  onShowLogin: () => void;
  onShowRegister: () => void;
}

const TopMenuBar: React.FC<TopMenuBarProps> = ({
  onShowLogin,
  onShowRegister
}) => {
  const { currentUser, logout, isAuthenticated } = useAuth();
  
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
      {/* Top Decorative Bar */}
      <div className="absolute top-0 left-0 right-0 h-1 flex">
        <div className="flex-1" style={{ background: '#16A34A' }} />
        <div className="flex-1" style={{ background: '#FCD34D' }} />
        <div className="flex-1" style={{ background: '#DC2626' }} />
      </div>

      {/* Animated gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-400/10 to-transparent animate-shimmer"></div>
      
      <div className="flex items-center gap-2 sm:gap-4 relative z-10">
        {/* Logo */}
        <div className="flex items-center gap-2 sm:gap-3">
          <img 
            src={potPalaceLogo} 
            alt="Pot Palace" 
            className="h-8 sm:h-10 w-auto"
            style={{ 
              filter: 'drop-shadow(0 0 10px rgba(252, 211, 77, 0.5)) hue-rotate(45deg) saturate(1.5)' 
            }}
          />
        </div>
      </div>

      {/* Search Bar - Hidden on mobile */}
      <div className="hidden md:flex flex-1 max-w-2xl mx-4 lg:mx-8 relative">
        <ProductSearchDropdown
          placeholder="Search for products..."
          className="w-full"
          inputClassName="w-full px-4 sm:px-5 py-2 sm:py-2.5 bg-black/50 backdrop-blur-sm rounded-full text-yellow-300 placeholder-yellow-600/70 pr-10 sm:pr-12 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 shadow-md text-sm sm:text-base border border-yellow-500/30"
          dropdownClassName="bg-gradient-to-b from-black/90 to-black/80 backdrop-blur-md border-yellow-500/30 shadow-2xl rounded-2xl"
          resultItemClassName="hover:bg-gradient-to-r hover:from-red-900/30 hover:via-yellow-900/30 hover:to-green-900/30 border-yellow-500/20 text-yellow-100"
          onProductSelect={(product) => {
            console.log('Product selected:', product);
            // Handle product selection - could navigate to product page or add to cart
          }}
        />
      </div>

      {/* Right Actions - Transparent Cylinder with Icons */}
      <div className="relative z-10">
        <div className="flex items-center gap-1 sm:gap-4 px-2 sm:px-6 py-1 sm:py-1.5 bg-gradient-to-r from-red-900/30 via-yellow-900/30 to-green-900/30 backdrop-blur-md rounded-full border border-yellow-500/30 shadow-lg">
          {/* Search Icon - Mobile only */}
          <button className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group md:hidden" title="Search">
            <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
          
          {/* Language Icon */}
          <button className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group hidden sm:block" title="Language">
            <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          </button>
          
          {/* Cart Icon */}
          <button className="p-2 sm:p-2.5 rounded-full hover:bg-yellow-500/20 transition-all group" title="Cart">
            <svg className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </button>
          
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
    </div>
  );
};

export default TopMenuBar;