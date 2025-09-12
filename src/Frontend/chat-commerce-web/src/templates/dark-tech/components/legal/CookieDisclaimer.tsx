import React, { useState, useEffect } from 'react';
import { useCompliance, CookiePreferences } from '../../../../contexts/ComplianceContext';

const CookieDisclaimer: React.FC = () => {
  const { showCookieDisclaimer, acceptAllCookies, acceptNecessaryCookies, updateCookiePreferences } = useCompliance();
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true,
    analytics: false,
    marketing: false,
    preferences: false
  });
  const [terminalText, setTerminalText] = useState('');

  useEffect(() => {
    if (showCookieDisclaimer) {
      // Typewriter effect
      const text = 'COOKIE_PROTOCOL_INITIATED...';
      let index = 0;
      const interval = setInterval(() => {
        if (index <= text.length) {
          setTerminalText(text.slice(0, index));
          index++;
        } else {
          clearInterval(interval);
        }
      }, 50);
      return () => clearInterval(interval);
    }
  }, [showCookieDisclaimer]);

  if (!showCookieDisclaimer) return null;

  const handleSavePreferences = () => {
    updateCookiePreferences(preferences);
    setShowDetails(false);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[9998] p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-black border border-cyan-400 shadow-lg shadow-cyan-400/20">
          {/* Terminal header */}
          <div className="bg-cyan-400 text-black px-3 py-1 font-mono text-xs flex items-center justify-between">
            <span>[SYSTEM::COOKIES]</span>
            <span>{terminalText}</span>
          </div>

          <div className="p-4 font-mono">
            {!showDetails ? (
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="text-cyan-400 text-xl mt-1">[🍪]</div>
                  <div>
                    <h3 className="text-green-400 text-sm mb-1">
                      &gt; COOKIE_NOTICE: Data collection protocol active
                    </h3>
                    <p className="text-cyan-400/80 text-xs leading-relaxed">
                      This system utilizes cookies for enhanced performance, analytics, and user tracking. 
                      Execute "ACCEPT_ALL" to authorize full data collection or configure manually.
                    </p>
                    <button
                      onClick={() => setShowDetails(true)}
                      className="text-green-400 hover:text-green-300 text-xs mt-2 underline transition-colors"
                    >
                      &gt; MANUAL_CONFIG
                    </button>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-2 w-full lg:w-auto">
                  <button
                    onClick={acceptNecessaryCookies}
                    className="px-4 py-2 bg-black border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all duration-200 text-xs"
                  >
                    [ESSENTIAL_ONLY]
                  </button>
                  <button
                    onClick={acceptAllCookies}
                    className="px-4 py-2 bg-black border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-all duration-200 text-xs font-bold"
                  >
                    [ACCEPT_ALL]
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-3 pb-3 border-b border-cyan-400/30">
                  <h3 className="text-green-400 text-sm">
                    &gt; COOKIE_CONFIGURATION
                  </h3>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-red-500 hover:text-red-400 text-lg leading-none"
                  >
                    [X]
                  </button>
                </div>
                
                <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                  {/* Necessary Cookies */}
                  <div className="bg-black border border-cyan-400/30 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-cyan-400 text-xs mb-1">[NECESSARY::REQUIRED]</h4>
                        <p className="text-cyan-400/60 text-xs">
                          Core system functionality. Cannot be disabled.
                        </p>
                      </div>
                      <div className="ml-3">
                        <div className="w-10 h-5 bg-green-400/30 border border-green-400 relative cursor-not-allowed">
                          <div className="absolute right-0 top-0 bottom-0 w-5 bg-green-400" />
                          <span className="absolute inset-0 flex items-center justify-center text-black text-xs font-bold">ON</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Analytics Cookies */}
                  <div className="bg-black border border-cyan-400/30 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-cyan-400 text-xs mb-1">[ANALYTICS::OPTIONAL]</h4>
                        <p className="text-cyan-400/60 text-xs">
                          System usage monitoring and optimization.
                        </p>
                      </div>
                      <div className="ml-3">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, analytics: !prev.analytics }))}
                          className={`w-10 h-5 border relative transition-all ${
                            preferences.analytics 
                              ? 'bg-green-400/30 border-green-400' 
                              : 'bg-red-500/30 border-red-500'
                          }`}
                        >
                          <div className={`absolute top-0 bottom-0 w-5 transition-all ${
                            preferences.analytics 
                              ? 'right-0 bg-green-400' 
                              : 'left-0 bg-red-500'
                          }`} />
                          <span className="absolute inset-0 flex items-center justify-center text-black text-xs font-bold">
                            {preferences.analytics ? 'ON' : 'OFF'}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Marketing Cookies */}
                  <div className="bg-black border border-cyan-400/30 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-cyan-400 text-xs mb-1">[MARKETING::OPTIONAL]</h4>
                        <p className="text-cyan-400/60 text-xs">
                          Targeted content delivery and campaign tracking.
                        </p>
                      </div>
                      <div className="ml-3">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, marketing: !prev.marketing }))}
                          className={`w-10 h-5 border relative transition-all ${
                            preferences.marketing 
                              ? 'bg-green-400/30 border-green-400' 
                              : 'bg-red-500/30 border-red-500'
                          }`}
                        >
                          <div className={`absolute top-0 bottom-0 w-5 transition-all ${
                            preferences.marketing 
                              ? 'right-0 bg-green-400' 
                              : 'left-0 bg-red-500'
                          }`} />
                          <span className="absolute inset-0 flex items-center justify-center text-black text-xs font-bold">
                            {preferences.marketing ? 'ON' : 'OFF'}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Preference Cookies */}
                  <div className="bg-black border border-cyan-400/30 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-cyan-400 text-xs mb-1">[PREFERENCES::OPTIONAL]</h4>
                        <p className="text-cyan-400/60 text-xs">
                          User settings and customization storage.
                        </p>
                      </div>
                      <div className="ml-3">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, preferences: !prev.preferences }))}
                          className={`w-10 h-5 border relative transition-all ${
                            preferences.preferences 
                              ? 'bg-green-400/30 border-green-400' 
                              : 'bg-red-500/30 border-red-500'
                          }`}
                        >
                          <div className={`absolute top-0 bottom-0 w-5 transition-all ${
                            preferences.preferences 
                              ? 'right-0 bg-green-400' 
                              : 'left-0 bg-red-500'
                          }`} />
                          <span className="absolute inset-0 flex items-center justify-center text-black text-xs font-bold">
                            {preferences.preferences ? 'ON' : 'OFF'}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-2 pt-3 border-t border-cyan-400/30">
                  <button
                    onClick={() => {
                      setPreferences({
                        necessary: true,
                        analytics: true,
                        marketing: true,
                        preferences: true
                      });
                    }}
                    className="px-3 py-2 bg-black border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all text-xs"
                  >
                    [ENABLE_ALL]
                  </button>
                  <button
                    onClick={() => {
                      setPreferences({
                        necessary: true,
                        analytics: false,
                        marketing: false,
                        preferences: false
                      });
                    }}
                    className="px-3 py-2 bg-black border border-red-500 text-red-500 hover:bg-red-500 hover:text-black transition-all text-xs"
                  >
                    [DISABLE_OPTIONAL]
                  </button>
                  <button
                    onClick={handleSavePreferences}
                    className="px-3 py-2 bg-black border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-all text-xs font-bold"
                  >
                    [SAVE_CONFIG]
                  </button>
                </div>
                
                <div className="pt-3 border-t border-cyan-400/30">
                  <p className="text-cyan-400/60 text-xs">
                    &gt; READ: <span className="text-cyan-400 underline cursor-pointer">PRIVACY.TXT</span> | <span className="text-cyan-400 underline cursor-pointer">COOKIES.TXT</span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 255, 255, 0.1);
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 255, 255, 0.5);
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 255, 255, 0.7);
        }
      `}</style>
    </div>
  );
};

export default CookieDisclaimer;