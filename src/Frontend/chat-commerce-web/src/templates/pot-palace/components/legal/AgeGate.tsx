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
    <div className="fixed inset-0 z-[9999] bg-black/95 backdrop-blur-xl flex items-center justify-center p-4">
      {/* Animated background with cannabis leaves */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-10 -left-10 w-40 h-40 bg-gradient-to-br from-purple-600/30 to-pink-600/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/3 -right-10 w-60 h-60 bg-gradient-to-br from-yellow-400/20 to-green-400/20 rounded-full blur-3xl animate-pulse delay-700" />
        <div className="absolute bottom-10 left-1/4 w-52 h-52 bg-gradient-to-br from-green-500/25 to-purple-500/25 rounded-full blur-3xl animate-pulse delay-1000" />
        
        {/* Floating cannabis leaves */}
        <div className="absolute top-20 left-10 text-6xl opacity-20 animate-float">🌿</div>
        <div className="absolute top-40 right-20 text-5xl opacity-15 animate-float-delayed">🍃</div>
        <div className="absolute bottom-20 left-1/3 text-7xl opacity-10 animate-float-slow">🌿</div>
        <div className="absolute bottom-40 right-1/4 text-4xl opacity-20 animate-float">🍃</div>
      </div>

      {/* Main content */}
      <div className="relative max-w-lg w-full">
        <div className="bg-gradient-to-br from-purple-900/90 via-purple-800/90 to-pink-900/90 rounded-3xl p-8 shadow-2xl border border-purple-400/30">
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-400/20 to-pink-400/20 blur-xl -z-10" />
          
          {/* Logo/Icon */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-yellow-400 to-green-400 shadow-lg mb-4">
              <span className="text-5xl">🌿</span>
            </div>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-pink-400 to-purple-400 mb-2">
              Age Verification Required
            </h1>
            <p className="text-purple-200 text-lg">
              You must be 19 or older to enter this site
            </p>
          </div>

          {/* Legal disclaimer */}
          <div className="bg-black/30 rounded-xl p-4 mb-6 border border-purple-400/20">
            <p className="text-purple-100 text-sm leading-relaxed">
              <span className="font-semibold text-yellow-400">⚠️ WARNING:</span> This website contains information about cannabis products. 
              Cannabis is legal for adults 19+ in certain jurisdictions. By entering this site, you confirm that you are of legal age 
              in your jurisdiction and agree to our Terms of Service and Privacy Policy.
            </p>
          </div>

          {!showDatePicker ? (
            <div className="space-y-4">
              {/* Quick verification buttons */}
              <button
                onClick={handleQuickVerify}
                className="w-full py-4 px-6 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold rounded-xl shadow-lg transform transition-all duration-200 hover:scale-105 hover:shadow-xl"
              >
                <span className="text-lg">Yes, I am 19 or older</span>
              </button>
              
              <button
                onClick={() => setShowDatePicker(true)}
                className="w-full py-3 px-6 bg-purple-700/50 hover:bg-purple-700/70 text-purple-100 font-semibold rounded-xl border border-purple-400/30 transition-all duration-200"
              >
                Enter my date of birth
              </button>
              
              <button
                onClick={denyAge}
                className="w-full py-3 px-6 bg-red-900/50 hover:bg-red-900/70 text-red-200 font-semibold rounded-xl border border-red-400/30 transition-all duration-200"
              >
                No, I am under 19
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">
                  Enter your date of birth:
                </label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => {
                    setSelectedDate(e.target.value);
                    setError('');
                  }}
                  max={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-3 bg-purple-900/50 border border-purple-400/30 rounded-xl text-purple-100 focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-400/20"
                />
                {error && (
                  <p className="text-red-400 text-sm mt-2">{error}</p>
                )}
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleDateVerify}
                  className="flex-1 py-3 px-6 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold rounded-xl shadow-lg transform transition-all duration-200 hover:scale-105"
                >
                  Verify Age
                </button>
                
                <button
                  onClick={() => {
                    setShowDatePicker(false);
                    setSelectedDate('');
                    setError('');
                  }}
                  className="flex-1 py-3 px-6 bg-purple-700/50 hover:bg-purple-700/70 text-purple-100 font-semibold rounded-xl border border-purple-400/30 transition-all duration-200"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {/* Footer text */}
          <div className="mt-6 pt-6 border-t border-purple-400/20">
            <p className="text-purple-300 text-xs text-center">
              By entering this site, you agree to our use of cookies and tracking technologies. 
              For more information, see our Privacy Policy and Cookie Policy.
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(10deg); }
        }
        
        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-25px) rotate(-10deg); }
        }
        
        @keyframes float-slow {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-15px) rotate(5deg); }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        
        .animate-float-delayed {
          animation: float-delayed 8s ease-in-out infinite;
          animation-delay: 1s;
        }
        
        .animate-float-slow {
          animation: float-slow 10s ease-in-out infinite;
          animation-delay: 2s;
        }
      `}</style>
    </div>
  );
};

export default AgeGate;