import React from 'react';
import potPalaceLogo from '../../assets/pot-palace-logo.png';
import { User } from '../../types';
import PageToggle from '../common/PageToggle';

interface TopMenuBarProps {
  currentUser: User | null;
  onLogout: () => void;
  onShowLogin: () => void;
  onShowRegister: () => void;
}

const TopMenuBar: React.FC<TopMenuBarProps> = ({
  currentUser,
  onLogout,
  onShowLogin,
  onShowRegister
}) => {
  return (
    <div className="w-full bg-gradient-to-r from-[#E91ED4] via-[#FF006E] via-[#FF6B35] to-[#FFA500] px-6 py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[72px]">
      {/* Animated gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
      
      <div className="flex items-center gap-4 relative z-10">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <img src={potPalaceLogo} alt="Pot Palace" className="h-10 w-auto" />
        </div>
      </div>

      {/* Search Bar with Page Toggle */}
      <div className="flex-1 max-w-2xl mx-8 relative z-10 flex items-center gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search for products..."
            className="w-full px-5 py-2.5 bg-white/95 backdrop-blur-sm rounded-full text-gray-800 placeholder-gray-500 pr-12 focus:outline-none focus:ring-2 focus:ring-white/50 shadow-md"
          />
          <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-full transition-colors">
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
        
        {/* Page Toggle Button */}
        <PageToggle />
      </div>

      {/* Right Actions - Transparent Cylinder with Icons */}
      <div className="relative z-10">
        <div className="flex items-center gap-4 px-6 py-1.5 bg-white/30 backdrop-blur-md rounded-full border border-white/30 shadow-lg">
          {/* Language Icon */}
          <button className="p-2.5 rounded-full hover:bg-white/20 transition-all group" title="Language">
            <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          </button>
          
          {/* Cart Icon */}
          <button className="p-2.5 rounded-full hover:bg-white/20 transition-all group" title="Cart">
            <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </button>
          
          {/* Login/Logout Icon */}
          {currentUser ? (
            <button 
              onClick={onLogout} 
              className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
              title="Logout"
            >
              <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </button>
          ) : (
            <button 
              onClick={onShowLogin} 
              className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
              title="Login"
            >
              <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </button>
          )}
          
          {/* Sign Up Icon - Only show when not logged in */}
          {!currentUser && (
            <button 
              onClick={onShowRegister} 
              className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
              title="Sign Up"
            >
              <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </button>
          )}
          
          {/* User Profile - Show when logged in */}
          {currentUser && (
            <div className="flex items-center gap-2 px-3 py-1 bg-white/20 rounded-full">
              <span className="text-white text-sm font-medium">{currentUser.name || currentUser.email}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopMenuBar;