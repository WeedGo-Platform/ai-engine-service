import React, { useState } from 'react';
import { useCompliance, CookiePreferences } from '../../../../contexts/ComplianceContext';
import Button from '../ui/Button';

interface CookieDisclaimerProps {
  onAccept?: () => void;
  onDecline?: () => void;
  position?: 'top' | 'bottom';
}

const CookieDisclaimer: React.FC<CookieDisclaimerProps> = ({
  onAccept,
  onDecline,
  position = 'bottom',
}) => {
  const { showCookieDisclaimer, acceptAllCookies, acceptNecessaryCookies, updateCookiePreferences } = useCompliance();
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true,
    analytics: false,
    marketing: false,
    preferences: false
  });

  const handleAccept = () => {
    acceptAllCookies();
    onAccept?.();
  };

  const handleDecline = () => {
    acceptNecessaryCookies();
    onDecline?.();
  };

  const handleSavePreferences = () => {
    updateCookiePreferences(preferences);
    setShowDetails(false);
  };

  if (!showCookieDisclaimer) return null;

  return (
    <div 
      className={`fixed left-0 right-0 z-40 p-4 ${
        position === 'top' ? 'top-0' : 'bottom-0'
      } smooth-fade-in`}
    >
      <div 
        className="max-w-6xl mx-auto rounded-xl overflow-hidden"
        style={{
          background: 'rgba(26, 26, 26, 0.98)',
          border: '3px solid transparent',
          backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.98), rgba(26, 26, 26, 0.98)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
          backgroundOrigin: 'border-box',
          backgroundClip: 'padding-box, border-box',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5), 0 0 60px rgba(252, 211, 77, 0.2)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Top Bar */}
        <div className="h-1 flex">
          <div className="flex-1" style={{ background: '#16A34A' }} />
          <div className="flex-1" style={{ background: '#FCD34D' }} />
          <div className="flex-1" style={{ background: '#DC2626' }} />
        </div>

        <div className="px-6 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0 md:space-x-6">
            {/* Content */}
            <div className="flex items-start space-x-4 flex-1">
              {/* Cookie Icon */}
              <div className="text-3xl flex-shrink-0 reggae-pulse">
                🍪
              </div>

              {/* Text */}
              <div>
                <h3 
                  className="text-lg font-bold mb-1"
                  style={{
                    color: '#FCD34D',
                    fontFamily: 'Bebas Neue, sans-serif',
                    letterSpacing: '1px',
                  }}
                >
                  Sweet Cookies for Sweet Vibes
                </h3>
                <p 
                  className="text-sm"
                  style={{
                    color: '#F3E7C3',
                    fontFamily: 'Ubuntu, sans-serif',
                    lineHeight: '1.5',
                  }}
                >
                  We use cookies (the digital kind) to enhance your experience and keep the good vibes flowing. 
                  These help us remember your preferences and provide you with the most irie shopping experience. 
                  By continuing, you're spreading the love and accepting our{' '}
                  <span 
                    className="underline cursor-pointer hover:opacity-80"
                    style={{ color: '#16A34A' }}
                  >
                    Cookie Policy
                  </span>
                  .
                </p>

                {/* Decorative Elements */}
                <div className="flex items-center space-x-2 mt-2 text-xs opacity-50">
                  <span style={{ color: '#DC2626' }}>☮</span>
                  <span style={{ color: '#FCD34D' }}>Peace</span>
                  <span style={{ color: '#16A34A' }}>•</span>
                  <span style={{ color: '#FCD34D' }}>Love</span>
                  <span style={{ color: '#DC2626' }}>•</span>
                  <span style={{ color: '#FCD34D' }}>Cookies</span>
                  <span style={{ color: '#16A34A' }}>🌿</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3">
              {onDecline && (
                <Button
                  variant="ghost"
                  size="small"
                  onClick={handleDecline}
                >
                  No Thanks
                </Button>
              )}
              
              <Button
                variant="secondary"
                size="small"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? 'Hide' : 'Preferences'}
              </Button>
              
              <Button
                variant="primary"
                size="small"
                onClick={handleAccept}
                icon={<span>✓</span>}
              >
                Accept All
              </Button>
            </div>
          </div>
        </div>

        {/* Preferences Details */}
        {showDetails && (
          <div 
            className="px-6 py-4"
            style={{
              borderTop: '1px solid rgba(252, 211, 77, 0.2)',
              background: 'rgba(0, 0, 0, 0.3)',
            }}
          >
            <h4 className="text-sm font-bold mb-3" style={{ color: '#FCD34D' }}>
              Cookie Preferences
            </h4>
            <div className="space-y-2">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={preferences.necessary}
                  disabled
                  className="rounded"
                />
                <span className="text-sm" style={{ color: '#F3E7C3' }}>
                  Necessary (Required) - Essential for site functionality
                </span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={preferences.analytics}
                  onChange={(e) => setPreferences({...preferences, analytics: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm" style={{ color: '#F3E7C3' }}>
                  Analytics - Help us understand how you use our site
                </span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={preferences.marketing}
                  onChange={(e) => setPreferences({...preferences, marketing: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm" style={{ color: '#F3E7C3' }}>
                  Marketing - Personalized offers and recommendations
                </span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={preferences.preferences}
                  onChange={(e) => setPreferences({...preferences, preferences: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm" style={{ color: '#F3E7C3' }}>
                  Preferences - Remember your settings and choices
                </span>
              </label>
            </div>
            <div className="mt-4 flex justify-end">
              <Button
                variant="primary"
                size="small"
                onClick={handleSavePreferences}
              >
                Save Preferences
              </Button>
            </div>
          </div>
        )}

        {/* Bottom Decorative Bar */}
        <div 
          className="h-8 flex items-center justify-center space-x-4 text-xs opacity-30"
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderTop: '1px solid rgba(252, 211, 77, 0.2)',
          }}
        >
          <span style={{ color: '#DC2626' }}>♪</span>
          <span style={{ color: '#FCD34D' }}>One Love</span>
          <span style={{ color: '#16A34A' }}>♪</span>
          <span style={{ color: '#FCD34D' }}>One Heart</span>
          <span style={{ color: '#DC2626' }}>♪</span>
        </div>
      </div>
    </div>
  );
};

export default CookieDisclaimer;