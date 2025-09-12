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
    <div className="fixed bottom-0 left-0 right-0 z-[9998] p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl border border-gray-200">
          <div className="p-6">
            {!showDetails ? (
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="text-2xl">🍪</div>
                  <div>
                    <h3 className="text-lg font-semibold text-blue-700 mb-1">
                      Cookie Notice
                    </h3>
                    <p className="text-gray-600 text-sm">
                      We use cookies to improve your experience, analyze site traffic, and serve personalized content. 
                      By clicking "Accept All", you consent to our use of cookies.
                    </p>
                    <button
                      onClick={() => setShowDetails(true)}
                      className="text-blue-700 hover:text-gray-700 text-sm font-medium mt-2 underline "
                    >
                      Manage Preferences
                    </button>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
                  <button
                    onClick={acceptNecessaryCookies}
                    className="px-6 py-2.5 bg-white hover:bg-gray-50 text-blue-700 font-medium rounded-lg border border-gray-300  "
                  >
                    Necessary Only
                  </button>
                  <button
                    onClick={acceptAllCookies}
                    className="px-6 py-2.5 bg-blue-700 hover:bg-blue-600 text-white font-medium rounded-lg  "
                  >
                    Accept All
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
                  <h3 className="text-xl font-semibold text-blue-700">
                    Cookie Preferences
                  </h3>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                  >
                    ×
                  </button>
                </div>
                
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {/* Necessary Cookies */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-blue-700 font-medium mb-1">Necessary Cookies</h4>
                        <p className="text-gray-600 text-sm">
                          Essential for website functionality. Always enabled.
                        </p>
                      </div>
                      <div className="ml-4">
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={true}
                            disabled
                            className="sr-only"
                          />
                          <div className="w-11 h-6 bg-gray-300 rounded-full cursor-not-allowed">
                            <div className="absolute right-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Analytics Cookies */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-blue-700 font-medium mb-1">Analytics Cookies</h4>
                        <p className="text-gray-600 text-sm">
                          Help us understand site usage and improve our services.
                        </p>
                      </div>
                      <div className="ml-4">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, analytics: !prev.analytics }))}
                          className="relative"
                        >
                          <div className={`w-11 h-6 rounded-full  ${
                            preferences.analytics ? 'bg-blue-700' : 'bg-gray-300'
                          }`}>
                            <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow  ${
                              preferences.analytics ? 'translate-x-5' : 'translate-x-0.5'
                            }`} />
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Marketing Cookies */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-blue-700 font-medium mb-1">Marketing Cookies</h4>
                        <p className="text-gray-600 text-sm">
                          Used for targeted advertising and campaign measurement.
                        </p>
                      </div>
                      <div className="ml-4">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, marketing: !prev.marketing }))}
                          className="relative"
                        >
                          <div className={`w-11 h-6 rounded-full  ${
                            preferences.marketing ? 'bg-blue-700' : 'bg-gray-300'
                          }`}>
                            <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow  ${
                              preferences.marketing ? 'translate-x-5' : 'translate-x-0.5'
                            }`} />
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Preference Cookies */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-blue-700 font-medium mb-1">Preference Cookies</h4>
                        <p className="text-gray-600 text-sm">
                          Remember your settings for a personalized experience.
                        </p>
                      </div>
                      <div className="ml-4">
                        <button
                          onClick={() => setPreferences(prev => ({ ...prev, preferences: !prev.preferences }))}
                          className="relative"
                        >
                          <div className={`w-11 h-6 rounded-full  ${
                            preferences.preferences ? 'bg-blue-700' : 'bg-gray-300'
                          }`}>
                            <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow  ${
                              preferences.preferences ? 'translate-x-5' : 'translate-x-0.5'
                            }`} />
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => {
                      setPreferences({
                        necessary: true,
                        analytics: true,
                        marketing: true,
                        preferences: true
                      });
                    }}
                    className="px-6 py-2.5 bg-white hover:bg-gray-50 text-blue-700 font-medium rounded-lg border border-gray-300 "
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
                    className="px-6 py-2.5 bg-white hover:bg-gray-50 text-blue-700 font-medium rounded-lg border border-gray-300 "
                  >
                    Reject Optional
                  </button>
                  <button
                    onClick={handleSavePreferences}
                    className="px-6 py-2.5 bg-blue-700 hover:bg-blue-600 text-white font-medium rounded-lg "
                  >
                    Save Preferences
                  </button>
                </div>
                
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-gray-500 text-xs">
                    Learn more about our use of cookies in our{' '}
                    <a href="/privacy" className="text-gray-700 hover:text-blue-700 underline">
                      Privacy Policy
                    </a>{' '}
                    and{' '}
                    <a href="/cookies" className="text-gray-700 hover:text-blue-700 underline">
                      Cookie Policy
                    </a>.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieDisclaimer;