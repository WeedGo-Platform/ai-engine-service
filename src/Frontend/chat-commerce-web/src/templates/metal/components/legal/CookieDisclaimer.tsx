import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';

interface CookieDisclaimerProps {
  onAccept?: () => void;
  onDecline?: () => void;
}

const CookieDisclaimer: React.FC<CookieDisclaimerProps> = ({ onAccept, onDecline }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const hasAccepted = localStorage.getItem('cookiesAccepted');
    if (!hasAccepted) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookiesAccepted', 'true');
    setIsVisible(false);
    if (onAccept) onAccept();
  };

  const handleDecline = () => {
    localStorage.setItem('cookiesAccepted', 'false');
    setIsVisible(false);
    if (onDecline) onDecline();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            <div className="flex-1">
              <p className="text-sm text-gray-700">
                We use cookies to enhance your experience, analyze site traffic, and for marketing purposes. 
                By continuing to use this site, you consent to our use of cookies.
              </p>
              <a href="#" className="text-sm text-blue-600 hover:text-blue-700 underline">
                Learn more about our Cookie Policy
              </a>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={handleDecline}>
              Decline
            </Button>
            <Button variant="primary" size="sm" onClick={handleAccept}>
              Accept Cookies
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieDisclaimer;