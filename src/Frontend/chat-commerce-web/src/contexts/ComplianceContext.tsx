import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types
interface CookiePreferences {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
  preferences: boolean;
}

interface ComplianceContextType {
  // Age verification
  isAgeVerified: boolean;
  verifyAge: (dateOfBirth: Date) => void;
  denyAge: () => void;
  
  // Cookie consent
  cookieConsent: CookiePreferences | null;
  acceptAllCookies: () => void;
  acceptNecessaryCookies: () => void;
  updateCookiePreferences: (preferences: CookiePreferences) => void;
  
  // Modal visibility
  showAgeGate: boolean;
  showCookieDisclaimer: boolean;
  
  // Utilities
  clearCompliance: () => void;
}

// Constants
const AGE_VERIFICATION_KEY = 'potpalace_age_verified';
const AGE_VERIFICATION_TIMESTAMP_KEY = 'potpalace_age_verified_timestamp';
const COOKIE_CONSENT_KEY = 'potpalace_cookie_consent';
const MINIMUM_AGE = 19; // Cannabis legal age
const VERIFICATION_DURATION = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds

// Create context
const ComplianceContext = createContext<ComplianceContextType | undefined>(undefined);

// Provider component
export const ComplianceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAgeVerified, setIsAgeVerified] = useState(false);
  const [cookieConsent, setCookieConsent] = useState<CookiePreferences | null>(null);
  const [showAgeGate, setShowAgeGate] = useState(false);
  const [showCookieDisclaimer, setShowCookieDisclaimer] = useState(false);

  // Check stored compliance on mount
  useEffect(() => {
    checkStoredCompliance();
  }, []);

  // Check stored age verification and cookie consent
  const checkStoredCompliance = () => {
    // Check age verification
    const storedAgeVerified = localStorage.getItem(AGE_VERIFICATION_KEY);
    const storedTimestamp = localStorage.getItem(AGE_VERIFICATION_TIMESTAMP_KEY);
    
    if (storedAgeVerified === 'true' && storedTimestamp) {
      const timestamp = parseInt(storedTimestamp);
      const now = Date.now();
      
      // Check if verification is still valid (within 30 days)
      if (now - timestamp < VERIFICATION_DURATION) {
        setIsAgeVerified(true);
      } else {
        // Verification expired, clear and show gate
        localStorage.removeItem(AGE_VERIFICATION_KEY);
        localStorage.removeItem(AGE_VERIFICATION_TIMESTAMP_KEY);
        setShowAgeGate(true);
      }
    } else {
      setShowAgeGate(true);
    }
    
    // Check cookie consent
    const storedCookieConsent = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (storedCookieConsent) {
      try {
        const consent = JSON.parse(storedCookieConsent);
        setCookieConsent(consent);
      } catch (error) {
        console.error('Error parsing cookie consent:', error);
        setShowCookieDisclaimer(true);
      }
    } else {
      setShowCookieDisclaimer(true);
    }
  };

  // Verify age
  const verifyAge = (dateOfBirth: Date) => {
    const today = new Date();
    const age = today.getFullYear() - dateOfBirth.getFullYear();
    const monthDiff = today.getMonth() - dateOfBirth.getMonth();
    const dayDiff = today.getDate() - dateOfBirth.getDate();
    
    // Calculate exact age
    const exactAge = monthDiff < 0 || (monthDiff === 0 && dayDiff < 0) ? age - 1 : age;
    
    if (exactAge >= MINIMUM_AGE) {
      setIsAgeVerified(true);
      setShowAgeGate(false);
      localStorage.setItem(AGE_VERIFICATION_KEY, 'true');
      localStorage.setItem(AGE_VERIFICATION_TIMESTAMP_KEY, Date.now().toString());
    } else {
      denyAge();
    }
  };

  // Deny age verification
  const denyAge = () => {
    setIsAgeVerified(false);
    setShowAgeGate(true);
    localStorage.removeItem(AGE_VERIFICATION_KEY);
    localStorage.removeItem(AGE_VERIFICATION_TIMESTAMP_KEY);
    
    // Optionally redirect to an appropriate page
    // window.location.href = 'https://www.responsibility.org/';
  };

  // Accept all cookies
  const acceptAllCookies = () => {
    const preferences: CookiePreferences = {
      necessary: true,
      analytics: true,
      marketing: true,
      preferences: true
    };
    setCookieConsent(preferences);
    setShowCookieDisclaimer(false);
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(preferences));
    
    // Initialize analytics and marketing scripts here
    initializeThirdPartyScripts(preferences);
  };

  // Accept only necessary cookies
  const acceptNecessaryCookies = () => {
    const preferences: CookiePreferences = {
      necessary: true,
      analytics: false,
      marketing: false,
      preferences: false
    };
    setCookieConsent(preferences);
    setShowCookieDisclaimer(false);
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(preferences));
  };

  // Update cookie preferences
  const updateCookiePreferences = (preferences: CookiePreferences) => {
    setCookieConsent(preferences);
    setShowCookieDisclaimer(false);
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(preferences));
    
    // Update third-party scripts based on preferences
    initializeThirdPartyScripts(preferences);
  };

  // Initialize third-party scripts based on consent
  const initializeThirdPartyScripts = (preferences: CookiePreferences) => {
    if (preferences.analytics) {
      // Initialize Google Analytics, Mixpanel, etc.
      console.log('Analytics cookies enabled');
    }
    
    if (preferences.marketing) {
      // Initialize Facebook Pixel, Google Ads, etc.
      console.log('Marketing cookies enabled');
    }
    
    if (preferences.preferences) {
      // Initialize preference-based features
      console.log('Preference cookies enabled');
    }
  };

  // Clear all compliance data
  const clearCompliance = () => {
    setIsAgeVerified(false);
    setCookieConsent(null);
    setShowAgeGate(true);
    setShowCookieDisclaimer(true);
    localStorage.removeItem(AGE_VERIFICATION_KEY);
    localStorage.removeItem(AGE_VERIFICATION_TIMESTAMP_KEY);
    localStorage.removeItem(COOKIE_CONSENT_KEY);
  };

  const value: ComplianceContextType = {
    isAgeVerified,
    verifyAge,
    denyAge,
    cookieConsent,
    acceptAllCookies,
    acceptNecessaryCookies,
    updateCookiePreferences,
    showAgeGate,
    showCookieDisclaimer,
    clearCompliance
  };

  return (
    <ComplianceContext.Provider value={value}>
      {children}
    </ComplianceContext.Provider>
  );
};

// Hook to use compliance context
export const useCompliance = () => {
  const context = useContext(ComplianceContext);
  if (!context) {
    throw new Error('useCompliance must be used within a ComplianceProvider');
  }
  return context;
};

// Export types
export type { CookiePreferences, ComplianceContextType };