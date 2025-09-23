import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { validateAge } from '@utils/security';

interface AgeVerificationContextType {
  isVerified: boolean;
  isVerifying: boolean;
  verifyAge: (dateOfBirth: Date) => Promise<boolean>;
  clearVerification: () => void;
  requireVerification: () => void;
}

const AgeVerificationContext = createContext<AgeVerificationContextType | undefined>(undefined);

const AGE_VERIFICATION_KEY = 'age_verified';
const VERIFICATION_EXPIRY_KEY = 'age_verification_expiry';
const VERIFICATION_DURATION = 24 * 60 * 60 * 1000; // 24 hours

export const AgeVerificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isVerified, setIsVerified] = useState<boolean>(false);
  const [isVerifying, setIsVerifying] = useState<boolean>(true);
  const [showVerificationModal, setShowVerificationModal] = useState<boolean>(false);

  useEffect(() => {
    checkVerificationStatus();
  }, []);

  const checkVerificationStatus = () => {
    const verified = localStorage.getItem(AGE_VERIFICATION_KEY);
    const expiry = localStorage.getItem(VERIFICATION_EXPIRY_KEY);

    if (verified === 'true' && expiry) {
      const expiryTime = parseInt(expiry, 10);
      if (Date.now() < expiryTime) {
        setIsVerified(true);
      } else {
        // Verification expired
        clearVerification();
      }
    }
    setIsVerifying(false);
  };

  const verifyAge = async (dateOfBirth: Date): Promise<boolean> => {
    setIsVerifying(true);

    try {
      const isValid = validateAge(dateOfBirth);

      if (isValid) {
        // Set verification in localStorage with expiry
        const expiryTime = Date.now() + VERIFICATION_DURATION;
        localStorage.setItem(AGE_VERIFICATION_KEY, 'true');
        localStorage.setItem(VERIFICATION_EXPIRY_KEY, expiryTime.toString());
        setIsVerified(true);
        setShowVerificationModal(false);

        // Optional: Send verification to backend
        try {
          await fetch('/api/auth/verify-age', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dateOfBirth: dateOfBirth.toISOString() })
          });
        } catch (error) {
          // Continue even if backend call fails
        }

        return true;
      } else {
        setIsVerified(false);
        return false;
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const clearVerification = () => {
    localStorage.removeItem(AGE_VERIFICATION_KEY);
    localStorage.removeItem(VERIFICATION_EXPIRY_KEY);
    setIsVerified(false);
  };

  const requireVerification = () => {
    if (!isVerified && !isVerifying) {
      setShowVerificationModal(true);
    }
  };

  return (
    <AgeVerificationContext.Provider
      value={{
        isVerified,
        isVerifying,
        verifyAge,
        clearVerification,
        requireVerification
      }}
    >
      {children}
      {showVerificationModal && !isVerified && (
        <AgeVerificationModal
          onVerify={verifyAge}
          onClose={() => setShowVerificationModal(false)}
        />
      )}
    </AgeVerificationContext.Provider>
  );
};

export const useAgeVerification = () => {
  const context = useContext(AgeVerificationContext);
  if (context === undefined) {
    throw new Error('useAgeVerification must be used within an AgeVerificationProvider');
  }
  return context;
};

// Age Verification Modal Component
interface AgeVerificationModalProps {
  onVerify: (dateOfBirth: Date) => Promise<boolean>;
  onClose: () => void;
}

const AgeVerificationModal: React.FC<AgeVerificationModalProps> = ({ onVerify, onClose }) => {
  const [dateOfBirth, setDateOfBirth] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const dob = new Date(dateOfBirth);
      if (isNaN(dob.getTime())) {
        setError('Please enter a valid date');
        return;
      }

      const isValid = await onVerify(dob);
      if (!isValid) {
        setError('You must be 19 or older to access this site');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExit = () => {
    window.location.href = 'https://www.google.com';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="text-center mb-6">
          <svg
            className="mx-auto h-12 w-12 text-green-600 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Age Verification Required
          </h2>
          <p className="text-gray-600">
            You must be 19 years or older to enter this website.
            Cannabis products are for adult use only.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="dob" className="block text-sm font-medium text-gray-700 mb-1">
              Date of Birth
            </label>
            <input
              id="dob"
              type="date"
              value={dateOfBirth}
              onChange={(e) => setDateOfBirth(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              aria-label="Enter your date of birth"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isSubmitting || !dateOfBirth}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              aria-label="Verify age"
            >
              {isSubmitting ? 'Verifying...' : 'Enter Site'}
            </button>
            <button
              type="button"
              onClick={handleExit}
              className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
              aria-label="Exit site"
            >
              Exit
            </button>
          </div>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            By entering this site, you agree to our Terms of Service and Privacy Policy.
            This website contains information about cannabis products intended for adults only.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgeVerificationModal;