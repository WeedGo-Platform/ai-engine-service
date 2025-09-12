import React, { useState } from 'react';
import { useCompliance } from '../../../../contexts/ComplianceContext';

const AgeGate: React.FC = () => {
  const { showAgeGate, verifyAge, denyAge } = useCompliance();
  const [selectedDate, setSelectedDate] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [error, setError] = useState('');

  if (!showAgeGate) return null;

  const handleQuickVerify = () => {
    // Quick verification - assumes user is 19+
    const verificationDate = new Date();
    verificationDate.setFullYear(verificationDate.getFullYear() - 19);
    verifyAge(verificationDate);
  };

  const handleDateVerify = () => {
    if (!selectedDate) {
      setError('Please select your date of birth');
      return;
    }
    
    const dob = new Date(selectedDate);
    const today = new Date();
    
    if (dob > today) {
      setError('Invalid date of birth');
      return;
    }
    
    verifyAge(dob);
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-blue-700/95 backdrop-blur-sm flex items-center justify-center p-4">
      {/* Subtle geometric pattern background */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.05) 35px, rgba(255,255,255,.05) 70px)`,
        }} />
      </div>

      {/* Main content */}
      <div className="relative max-w-lg w-full">
        <div className="bg-white rounded-lg shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-blue-700 px-8 py-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white mb-4">
                <svg className="w-10 h-10 text-blue-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h1 className="text-3xl font-light text-white mb-2">
                Age Verification Required
              </h1>
              <p className="text-gray-300">
                You must be 19 or older to access this site
              </p>
            </div>
          </div>

          {/* Body */}
          <div className="p-8">
            {/* Legal disclaimer */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
              <p className="text-gray-600 text-sm leading-relaxed">
                <span className="font-semibold text-blue-700">Legal Notice:</span> This website contains information about cannabis products. 
                Cannabis is legal for adults 19+ in certain jurisdictions. By entering, you confirm that you are of legal age 
                and agree to our Terms of Service and Privacy Policy.
              </p>
            </div>

            {!showDatePicker ? (
              <div className="space-y-3">
                {/* Quick verification buttons */}
                <button
                  onClick={handleQuickVerify}
                  className="w-full py-3 px-6 bg-blue-700 hover:bg-blue-600 text-white font-medium rounded-lg  "
                >
                  Yes, I am 19 or older
                </button>
                
                <button
                  onClick={() => setShowDatePicker(true)}
                  className="w-full py-3 px-6 bg-white hover:bg-gray-50 text-blue-700 font-medium rounded-lg border border-gray-300  "
                >
                  Enter my date of birth
                </button>
                
                <button
                  onClick={denyAge}
                  className="w-full py-3 px-6 bg-white hover:bg-red-50 text-red-600 font-medium rounded-lg border border-red-200  "
                >
                  No, I am under 19
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-700 mb-2 font-medium">
                    Date of Birth:
                  </label>
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      setError('');
                    }}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-blue-700 focus:outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200 "
                  />
                  {error && (
                    <p className="text-red-600 text-sm mt-2">{error}</p>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={handleDateVerify}
                    className="flex-1 py-3 px-6 bg-blue-700 hover:bg-blue-600 text-white font-medium rounded-lg  "
                  >
                    Verify Age
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowDatePicker(false);
                      setSelectedDate('');
                      setError('');
                    }}
                    className="flex-1 py-3 px-6 bg-white hover:bg-gray-50 text-blue-700 font-medium rounded-lg border border-gray-300  "
                  >
                    Back
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-8 py-4 bg-gray-50 border-t border-gray-200">
            <p className="text-gray-500 text-xs text-center">
              By entering this site, you agree to our use of cookies and tracking technologies. 
              View our <a href="/privacy" className="text-gray-700 underline">Privacy Policy</a> and{' '}
              <a href="/cookies" className="text-gray-700 underline">Cookie Policy</a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgeGate;