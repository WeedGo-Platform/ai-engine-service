import React, { useState } from 'react';
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

  if (!showCookieDisclaimer) return null;

  const handleSavePreferences = () => {
    updateCookiePreferences(preferences);
    setShowDetails(false);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[9998] p-4 animate-slide-up">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-purple-900/95 via-purple-800/95 to-pink-900/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-purple-400/30 overflow-hidden">
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-400/10 to-pink-400/10 blur-xl -z-10" />
          
          <div className="p-6">
            {!showDetails ? (
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="text-3xl mt-1">🍪</div>
                  <div>
                    <h3 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-purple-400 mb-2">
                      We Value Your Privacy
                    </h3>
                    <p className="text-purple-200 text-sm">
                      We use cookies to enhance your browsing experience, serve personalized content, and analyze our traffic. 
                      By clicking "Accept All", you consent to our use of cookies.
                    </p>
                    <button
                      onClick={() => setShowDetails(true)}
                      className="text-yellow-400 hover:text-yellow-300 text-sm font-semibold mt-2 underline transition-colors"
                    >
                      Manage Preferences
                    </button>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
                  <button
                    onClick={acceptNecessaryCookies}
                    className="px-6 py-3 bg-purple-700/50 hover:bg-purple-700/70 text-purple-100 font-semibold rounded-xl border border-purple-400/30 transition-all duration-200 hover:shadow-lg"
                  >
                    Necessary Only
                  </button>
                  <button
                    onClick={acceptAllCookies}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold rounded-xl shadow-lg transform transition-all duration-200 hover:scale-105 hover:shadow-xl"
                  >
                    Accept All
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-purple-400">
                    Cookie Preferences
                  </h3>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-purple-300 hover:text-purple-100 text-2xl leading-none"
                  >
                    ×
                  </button>
                </div>
                
                <div className="space-y-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                  {/* Necessary Cookies */}
                  <div className="bg-black/20 rounded-xl p-4 border border-purple-400/20">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="text-purple-100 font-semibold">Necessary Cookies</h4>
                        <p className="text-purple-300 text-sm">
                          Essential for the website to function properly. Cannot be disabled.
                        </p>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={true}
                          disabled
                          className="sr-only"
                        />
                        <div className="w-12 h-6 bg-green-500/50 rounded-full cursor-not-allowed">
                          <div className="absolute right-0 top-0 w-6 h-6 bg-green-500 rounded-full shadow-lg" />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Analytics Cookies */}
                  <div className="bg-black/20 rounded-xl p-4 border border-purple-400/20">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="text-purple-100 font-semibold">Analytics Cookies</h4>
                        <p className="text-purple-300 text-sm">
                          Help us understand how visitors interact with our website.
                        </p>
                      </div>
                      <button
                        onClick={() => setPreferences(prev => ({ ...prev, analytics: !prev.analytics }))}
                        className="relative"
                      >
                        <div className={`w-12 h-6 rounded-full transition-colors ${
                          preferences.analytics ? 'bg-green-500/50' : 'bg-purple-700/50'
                        }`}>
                          <div className={`absolute top-0 w-6 h-6 bg-white rounded-full shadow-lg transition-transform ${
                            preferences.analytics ? 'translate-x-6' : 'translate-x-0'
                          }`} />
                        </div>
                      </button>
                    </div>
                  </div>
                  
                  {/* Marketing Cookies */}
                  <div className="bg-black/20 rounded-xl p-4 border border-purple-400/20">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="text-purple-100 font-semibold">Marketing Cookies</h4>
                        <p className="text-purple-300 text-sm">
                          Used to deliver personalized advertisements and track campaigns.
                        </p>
                      </div>
                      <button
                        onClick={() => setPreferences(prev => ({ ...prev, marketing: !prev.marketing }))}
                        className="relative"
                      >
                        <div className={`w-12 h-6 rounded-full transition-colors ${
                          preferences.marketing ? 'bg-green-500/50' : 'bg-purple-700/50'
                        }`}>
                          <div className={`absolute top-0 w-6 h-6 bg-white rounded-full shadow-lg transition-transform ${
                            preferences.marketing ? 'translate-x-6' : 'translate-x-0'
                          }`} />
                        </div>
                      </button>
                    </div>
                  </div>
                  
                  {/* Preference Cookies */}
                  <div className="bg-black/20 rounded-xl p-4 border border-purple-400/20">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="text-purple-100 font-semibold">Preference Cookies</h4>
                        <p className="text-purple-300 text-sm">
                          Remember your settings and preferences for a better experience.
                        </p>
                      </div>
                      <button
                        onClick={() => setPreferences(prev => ({ ...prev, preferences: !prev.preferences }))}
                        className="relative"
                      >
                        <div className={`w-12 h-6 rounded-full transition-colors ${
                          preferences.preferences ? 'bg-green-500/50' : 'bg-purple-700/50'
                        }`}>
                          <div className={`absolute top-0 w-6 h-6 bg-white rounded-full shadow-lg transition-transform ${
                            preferences.preferences ? 'translate-x-6' : 'translate-x-0'
                          }`} />
                        </div>
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-purple-400/20">
                  <button
                    onClick={() => {
                      setPreferences({
                        necessary: true,
                        analytics: true,
                        marketing: true,
                        preferences: true
                      });
                    }}
                    className="px-6 py-3 bg-purple-700/50 hover:bg-purple-700/70 text-purple-100 font-semibold rounded-xl border border-purple-400/30 transition-all duration-200"
                  >
                    Accept All
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
                    className="px-6 py-3 bg-purple-700/50 hover:bg-purple-700/70 text-purple-100 font-semibold rounded-xl border border-purple-400/30 transition-all duration-200"
                  >
                    Reject All
                  </button>
                  <button
                    onClick={handleSavePreferences}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold rounded-xl shadow-lg transform transition-all duration-200 hover:scale-105"
                  >
                    Save Preferences
                  </button>
                </div>
                
                <div className="pt-4 border-t border-purple-400/20">
                  <p className="text-purple-300 text-xs">
                    For more information about how we use cookies, please read our{' '}
                    <a href="/privacy" className="text-yellow-400 hover:text-yellow-300 underline">
                      Privacy Policy
                    </a>{' '}
                    and{' '}
                    <a href="/cookies" className="text-yellow-400 hover:text-yellow-300 underline">
                      Cookie Policy
                    </a>.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        
        .animate-slide-up {
          animation: slide-up 0.5s ease-out;
        }
        
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(139, 92, 246, 0.1);
          border-radius: 10px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(139, 92, 246, 0.5);
          border-radius: 10px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(139, 92, 246, 0.7);
        }
      `}</style>
    </div>
  );
};

export default CookieDisclaimer;