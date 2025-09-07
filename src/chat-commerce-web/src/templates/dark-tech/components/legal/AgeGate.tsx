import React, { useState, useEffect } from 'react';
import { useCompliance } from '../../../../contexts/ComplianceContext';

const AgeGate: React.FC = () => {
  const { showAgeGate, verifyAge, denyAge } = useCompliance();
  const [selectedDate, setSelectedDate] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [error, setError] = useState('');
  const [glitchText, setGlitchText] = useState('AGE_VERIFICATION');

  useEffect(() => {
    // Glitch effect for text
    const interval = setInterval(() => {
      const glitchChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      const originalText = 'AGE_VERIFICATION';
      let glitched = '';
      
      for (let i = 0; i < originalText.length; i++) {
        if (Math.random() > 0.9) {
          glitched += glitchChars[Math.floor(Math.random() * glitchChars.length)];
        } else {
          glitched += originalText[i];
        }
      }
      
      setGlitchText(glitched);
      setTimeout(() => setGlitchText(originalText), 100);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (!showAgeGate) return null;

  const handleQuickVerify = () => {
    const verificationDate = new Date();
    verificationDate.setFullYear(verificationDate.getFullYear() - 19);
    verifyAge(verificationDate);
  };

  const handleDateVerify = () => {
    if (!selectedDate) {
      setError('[ERROR] Date input required');
      return;
    }
    
    const dob = new Date(selectedDate);
    const today = new Date();
    
    if (dob > today) {
      setError('[ERROR] Invalid timestamp');
      return;
    }
    
    verifyAge(dob);
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-black flex items-center justify-center p-4">
      {/* Matrix rain effect background */}
      <div className="absolute inset-0 overflow-hidden opacity-20">
        <div className="matrix-rain" />
      </div>

      {/* Scanlines effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="scanlines" />
      </div>

      {/* Main content */}
      <div className="relative max-w-lg w-full">
        <div className="bg-black border-2 border-cyan-400 rounded-none shadow-2xl shadow-cyan-400/50">
          {/* Terminal header */}
          <div className="bg-cyan-400 text-black px-4 py-2 font-mono text-sm flex items-center justify-between">
            <span>[SYSTEM::AGE_GATE]</span>
            <span className="text-xs">{new Date().toISOString()}</span>
          </div>

          {/* Terminal body */}
          <div className="p-6 font-mono">
            {/* ASCII art logo */}
            <div className="text-cyan-400 text-xs mb-4 text-center whitespace-pre">
{`    ___   _____ _____ 
   / _ \\ / ____|  ___|
  / /_\\ \\ |  __| |__ 
 / ___ | | |_| |  __|
/_/   \\_\\_____|_____| 
                      
[${glitchText}]`}
            </div>

            {/* System message */}
            <div className="mb-6">
              <p className="text-green-400 mb-2">
                &gt; SYSTEM: Authentication required
              </p>
              <p className="text-green-400 mb-2">
                &gt; MINIMUM_AGE: 19
              </p>
              <p className="text-green-400">
                &gt; STATUS: Awaiting verification...
              </p>
            </div>

            {/* Warning message */}
            <div className="bg-red-900/20 border border-red-500 p-3 mb-6">
              <p className="text-red-400 text-xs leading-relaxed">
                <span className="text-red-500">[WARNING]</span> This system contains restricted content related to cannabis products. 
                Access is limited to authorized users aged 19+. Unauthorized access attempts will be logged. 
                By proceeding, you acknowledge compliance with local regulations.
              </p>
            </div>

            {!showDatePicker ? (
              <div className="space-y-3">
                <button
                  onClick={handleQuickVerify}
                  className="w-full py-3 px-4 bg-black border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-all duration-200 font-mono group"
                >
                  <span className="group-hover:hidden">&gt; CONFIRM: AGE &gt;= 19</span>
                  <span className="hidden group-hover:inline">[EXECUTE]</span>
                </button>
                
                <button
                  onClick={() => setShowDatePicker(true)}
                  className="w-full py-3 px-4 bg-black border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all duration-200 font-mono group"
                >
                  <span className="group-hover:hidden">&gt; INPUT: DATE_OF_BIRTH</span>
                  <span className="hidden group-hover:inline">[MANUAL_ENTRY]</span>
                </button>
                
                <button
                  onClick={denyAge}
                  className="w-full py-3 px-4 bg-black border border-red-500 text-red-500 hover:bg-red-500 hover:text-black transition-all duration-200 font-mono group"
                >
                  <span className="group-hover:hidden">&gt; DENY: AGE &lt; 19</span>
                  <span className="hidden group-hover:inline">[ABORT]</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-cyan-400 mb-2 text-sm">
                    &gt; ENTER_DATE [YYYY-MM-DD]:
                  </label>
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      setError('');
                    }}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 bg-black border border-cyan-400 text-cyan-400 focus:outline-none focus:border-green-400 focus:shadow-lg focus:shadow-green-400/20 font-mono"
                    style={{ colorScheme: 'dark' }}
                  />
                  {error && (
                    <p className="text-red-500 text-xs mt-2 font-mono">{error}</p>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={handleDateVerify}
                    className="flex-1 py-3 px-4 bg-black border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-all duration-200 font-mono"
                  >
                    [VERIFY]
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowDatePicker(false);
                      setSelectedDate('');
                      setError('');
                    }}
                    className="flex-1 py-3 px-4 bg-black border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all duration-200 font-mono"
                  >
                    [CANCEL]
                  </button>
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-cyan-400/30">
              <p className="text-cyan-400/60 text-xs text-center font-mono">
                SYSTEM::COOKIES [ENABLED] | TRACKING::ACTIVE
              </p>
              <p className="text-cyan-400/60 text-xs text-center font-mono mt-1">
                VIEW: <span className="text-cyan-400 underline cursor-pointer">PRIVACY.TXT</span> | <span className="text-cyan-400 underline cursor-pointer">COOKIES.TXT</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes matrix-fall {
          0% {
            transform: translateY(-100%);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh);
            opacity: 0;
          }
        }
        
        .matrix-rain::before {
          content: '10101010101010101010101010101010101010101010101010';
          position: absolute;
          font-family: monospace;
          font-size: 10px;
          color: #00ff00;
          animation: matrix-fall 5s linear infinite;
          white-space: pre;
          left: 10%;
        }
        
        .matrix-rain::after {
          content: '01010101010101010101010101010101010101010101010101';
          position: absolute;
          font-family: monospace;
          font-size: 10px;
          color: #00ff00;
          animation: matrix-fall 7s linear infinite;
          animation-delay: 2s;
          white-space: pre;
          left: 60%;
        }
        
        .scanlines::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            transparent 50%,
            rgba(0, 255, 255, 0.03) 50%
          );
          background-size: 100% 4px;
          pointer-events: none;
          animation: scanlines 8s linear infinite;
        }
        
        @keyframes scanlines {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(10px);
          }
        }
      `}</style>
    </div>
  );
};

export default AgeGate;