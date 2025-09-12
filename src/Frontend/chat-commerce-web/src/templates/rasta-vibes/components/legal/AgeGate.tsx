import React, { useState } from 'react';
import Button from '../ui/Button';

interface AgeGateProps {
  onVerified: () => void;
  minAge?: number;
}

const AgeGate: React.FC<AgeGateProps> = ({
  onVerified,
  minAge = 21,
}) => {
  const [birthDate, setBirthDate] = useState('');
  const [error, setError] = useState('');

  const verifyAge = () => {
    if (!birthDate) {
      setError('Please enter your birth date');
      return;
    }

    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }

    if (age >= minAge) {
      onVerified();
    } else {
      setError(`You must be ${minAge} or older to enter this site`);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(135deg, #1A1A1A 0%, #2D1B00 50%, #1A2E05 100%)',
      }}
    >
      {/* Background Pattern */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            repeating-linear-gradient(
              45deg,
              transparent,
              transparent 20px,
              rgba(252, 211, 77, 0.1) 20px,
              rgba(252, 211, 77, 0.1) 40px
            )
          `,
        }}
      />

      {/* Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 text-8xl opacity-10 float-notes" style={{ color: '#FCD34D' }}>
          ♪
        </div>
        <div className="absolute bottom-10 right-10 text-7xl opacity-10 float-notes" style={{ color: '#16A34A', animationDelay: '3s' }}>
          ♫
        </div>
        <div className="absolute top-1/3 right-1/4 text-6xl opacity-10 leaf-sway" style={{ color: '#DC2626' }}>
          🌿
        </div>
      </div>

      {/* Content Card */}
      <div 
        className="relative max-w-md w-full p-8 rounded-2xl text-center"
        style={{
          background: 'rgba(26, 26, 26, 0.98)',
          border: '3px solid transparent',
          backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.98), rgba(26, 26, 26, 0.98)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
          backgroundOrigin: 'border-box',
          backgroundClip: 'padding-box, border-box',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.8), 0 0 100px rgba(252, 211, 77, 0.2)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Top Bar */}
        <div className="absolute top-0 left-0 right-0 h-1 flex rounded-t-xl overflow-hidden">
          <div className="flex-1" style={{ background: '#DC2626' }} />
          <div className="flex-1" style={{ background: '#FCD34D' }} />
          <div className="flex-1" style={{ background: '#16A34A' }} />
        </div>

        {/* Icon */}
        <div className="text-6xl mb-4 lion-glow" style={{ color: '#FCD34D' }}>
          🦁
        </div>

        {/* Title */}
        <h1 
          className="text-3xl font-bold mb-2"
          style={{
            color: '#FCD34D',
            fontFamily: 'Bebas Neue, sans-serif',
            letterSpacing: '2px',
            textShadow: '0 0 30px rgba(252, 211, 77, 0.5)',
          }}
        >
          Age Verification Required
        </h1>

        {/* Subtitle */}
        <p 
          className="mb-6"
          style={{
            color: '#F3E7C3',
            fontFamily: 'Ubuntu, sans-serif',
          }}
        >
          You must be {minAge}+ to enter this sacred space
        </p>

        {/* Decorative Divider */}
        <div className="flex items-center justify-center space-x-3 mb-6">
          <span style={{ color: '#DC2626' }}>☮</span>
          <div className="h-px flex-1" style={{ background: 'rgba(252, 211, 77, 0.3)' }} />
          <span style={{ color: '#FCD34D' }}>🌿</span>
          <div className="h-px flex-1" style={{ background: 'rgba(252, 211, 77, 0.3)' }} />
          <span style={{ color: '#16A34A' }}>♥</span>
        </div>

        {/* Birth Date Input */}
        <div className="mb-6">
          <label 
            htmlFor="birthdate"
            className="block text-sm font-medium mb-2"
            style={{ color: '#FCD34D' }}
          >
            Enter Your Birth Date
          </label>
          <input
            id="birthdate"
            type="date"
            value={birthDate}
            onChange={(e) => {
              setBirthDate(e.target.value);
              setError('');
            }}
            className="w-full px-4 py-3 rounded-lg outline-none"
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              border: `2px solid ${error ? 'rgba(220, 38, 38, 0.5)' : 'rgba(252, 211, 77, 0.3)'}`,
              color: '#F3E7C3',
              fontFamily: 'Ubuntu, sans-serif',
            }}
            max={new Date().toISOString().split('T')[0]}
          />
          
          {error && (
            <p 
              className="mt-2 text-sm"
              style={{ color: '#DC2626' }}
            >
              {error}
            </p>
          )}
        </div>

        {/* Verify Button */}
        <Button
          variant="primary"
          size="large"
          fullWidth
          onClick={verifyAge}
        >
          Verify Age & Enter
        </Button>

        {/* Legal Text */}
        <p 
          className="mt-6 text-xs"
          style={{
            color: '#F3E7C3',
            opacity: 0.6,
          }}
        >
          By entering this site, you agree to our Terms of Service and confirm 
          that you are of legal age in your jurisdiction.
        </p>

        {/* Quote */}
        <div className="mt-6 pt-6" style={{ borderTop: '1px solid rgba(252, 211, 77, 0.2)' }}>
          <p 
            className="text-sm italic"
            style={{ color: '#FCD34D', opacity: 0.8 }}
          >
            "Herb is the healing of the nation"
          </p>
          <p 
            className="text-xs mt-1"
            style={{ color: '#F3E7C3', opacity: 0.6 }}
          >
            - Bob Marley
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgeGate;