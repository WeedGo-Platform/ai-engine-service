import React, { useState } from 'react';
import Button from '../ui/Button';
import Modal from '../ui/Modal';

interface AgeGateProps {
  onVerified: () => void;
  minAge?: number;
}

const AgeGate: React.FC<AgeGateProps> = ({ onVerified, minAge = 21 }) => {
  const [birthDate, setBirthDate] = useState('');
  const [error, setError] = useState('');

  const verifyAge = () => {
    if (!birthDate) {
      setError('Please enter your date of birth');
      return;
    }

    const today = new Date();
    const birth = new Date(birthDate);
    const age = Math.floor((today.getTime() - birth.getTime()) / (365.25 * 24 * 60 * 60 * 1000));

    if (age >= minAge) {
      onVerified();
    } else {
      setError(`You must be at least ${minAge} years old to access this site`);
    }
  };

  return (
    <Modal isOpen={true} onClose={() => {}} closeOnOverlayClick={false} showCloseButton={false}>
      <div className="p-8 text-center">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Age Verification Required</h2>
        <p className="text-gray-600 mb-6">
          You must be {minAge} years or older to access this site.
          Please enter your date of birth to continue.
        </p>

        <div className="max-w-xs mx-auto">
          <input
            type="date"
            value={birthDate}
            onChange={(e) => {
              setBirthDate(e.target.value);
              setError('');
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            max={new Date().toISOString().split('T')[0]}
          />
          
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}

          <Button
            onClick={verifyAge}
            variant="primary"
            fullWidth
            size="lg"
            className="mt-4"
          >
            Verify Age
          </Button>
        </div>

        <p className="mt-6 text-xs text-gray-500">
          By entering this site, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </Modal>
  );
};

export default AgeGate;