import React from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import potPalaceLogo from '../../../../assets/pot-palace-logo.png';

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
    <div className="w-full bg-black px-6 py-3 flex items-center justify-between relative overflow-hidden z-40 h-[72px] border-b border-cyan-500/30">
      {/* Cyberpunk background effects */}
      <div className="absolute inset-0 bg-gradient-to-r from-purple-900/20 via-cyan-900/20 to-pink-900/20 animate-pulse"></div>
      <div className="absolute inset-0 opacity-5">
        <div className="h-full w-full bg-gradient-to-br from-cyan-500/10 via-transparent to-purple-500/10"></div>
      </div>
      
      {/* Animated neon lines */}
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-shimmer"></div>
      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-pink-500 to-transparent animate-shimmer" style={{animationDelay: '1s'}}></div>
      
      <div className="flex items-center gap-4 relative z-10">
        {/* Logo with glitch effect */}
        <div className="flex items-center gap-3 relative group">
          <div className="absolute inset-0 bg-cyan-500/30 blur-xl group-hover:bg-pink-500/30 transition-all duration-500"></div>
          <img src={potPalaceLogo} alt="Pot Palace" className="h-10 w-auto relative z-10 filter hue-rotate-180 saturate-200 brightness-150" />
          <div className="absolute inset-0 flex items-center">
            <img src={potPalaceLogo} alt="" className="h-10 w-auto opacity-30 filter hue-rotate-90 blur-sm animate-pulse" />
          </div>
        </div>
      </div>

      {/* Search Bar - Terminal style */}
      <div className="flex-1 max-w-2xl mx-8 relative z-10">
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-pink-500 rounded-sm opacity-0 group-hover:opacity-30 blur transition-all duration-300"></div>
          <input
            type="text"
            placeholder="&gt; SEARCH_DATABASE..."
            className="w-full px-4 py-2.5 bg-black/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm text-cyan-400 placeholder-cyan-700 pr-12 
                     focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_20px_rgba(0,255,255,0.3)]
                     font-mono text-sm uppercase tracking-wider transition-all duration-300
                     hover:border-cyan-400/50 hover:shadow-[0_0_10px_rgba(0,255,255,0.2)]"
          />
          <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-cyan-500/10 rounded-sm transition-all group/btn">
            <svg className="w-5 h-5 text-cyan-500 group-hover/btn:text-cyan-300 group-hover/btn:drop-shadow-[0_0_8px_rgba(0,255,255,0.8)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
          {/* Scanline effect */}
          <div className="absolute inset-0 pointer-events-none opacity-20">
            <div className="h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-scan"></div>
          </div>
        </div>
      </div>

      {/* Right Actions - Holographic panel */}
      <div className="relative z-10">
        <div className="relative">
          {/* Holographic background */}
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-pink-500/10 blur-md"></div>
          
          <div className="relative flex items-center gap-2 px-4 py-2 bg-black/50 backdrop-blur-md border border-cyan-500/30 rounded-sm
                        shadow-[0_0_20px_rgba(0,255,255,0.2)]">
            {/* Language Icon - Neon glow */}
            <button className="p-2 rounded-sm hover:bg-cyan-500/10 transition-all group relative" title="LANGUAGE">
              <svg className="w-5 h-5 text-cyan-400 group-hover:text-cyan-300 transition-colors drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">LANG</span>
            </button>
            
            {/* Cart Icon - Pulsing neon */}
            <button className="p-2 rounded-sm hover:bg-pink-500/10 transition-all group relative" title="CART">
              <svg className="w-5 h-5 text-pink-400 group-hover:text-pink-300 transition-colors drop-shadow-[0_0_5px_rgba(255,0,255,0.5)] animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-pink-500 rounded-full animate-ping"></span>
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-pink-400 rounded-full"></span>
              <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-pink-500 opacity-0 group-hover:opacity-100 transition-opacity">CART</span>
            </button>

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
        </div>
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
    </div>
  );
};

export default TopMenuBar;