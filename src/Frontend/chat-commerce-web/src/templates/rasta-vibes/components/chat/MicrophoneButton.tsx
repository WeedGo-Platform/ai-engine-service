import React, { useState, useEffect } from 'react';

interface MicrophoneButtonProps {
  isListening?: boolean;
  isDisabled?: boolean;
  onToggle?: () => void;
  volume?: number; // Current microphone input level (0-1)
}

const MicrophoneButton: React.FC<MicrophoneButtonProps> = ({
  isListening = false,
  isDisabled = false,
  onToggle,
  volume = 0,
}) => {
  const [pulseScale, setPulseScale] = useState(1);

  useEffect(() => {
    if (isListening && volume > 0) {
      setPulseScale(1 + volume * 0.3);
    } else {
      setPulseScale(1);
    }
  }, [isListening, volume]);

  return (
    <div className="relative">
      {/* Pulse Rings */}
      {isListening && (
        <>
          <div 
            className="absolute inset-0 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(220, 38, 38, 0.3) 0%, transparent 70%)',
              animation: 'dub-echo 1.5s ease-out infinite',
              transform: `scale(${pulseScale})`,
            }}
          />
          <div 
            className="absolute inset-0 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(252, 211, 77, 0.3) 0%, transparent 70%)',
              animation: 'dub-echo 1.5s ease-out infinite',
              animationDelay: '0.5s',
              transform: `scale(${pulseScale})`,
            }}
          />
          <div 
            className="absolute inset-0 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(22, 163, 74, 0.3) 0%, transparent 70%)',
              animation: 'dub-echo 1.5s ease-out infinite',
              animationDelay: '1s',
              transform: `scale(${pulseScale})`,
            }}
          />
        </>
      )}

      {/* Main Button */}
      <button
        onClick={onToggle}
        disabled={isDisabled}
        className="relative p-4 rounded-full transition-all hover:scale-110"
        style={{
          background: isListening 
            ? 'linear-gradient(135deg, #DC2626, #FCD34D, #16A34A)'
            : isDisabled
            ? 'rgba(100, 100, 100, 0.3)'
            : 'linear-gradient(135deg, rgba(220, 38, 38, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%)',
          backgroundSize: isListening ? '200% 200%' : '100% 100%',
          animation: isListening ? 'rasta-wave 2s ease infinite' : 'none',
          border: `3px solid ${
            isListening 
              ? 'rgba(252, 211, 77, 0.8)' 
              : isDisabled 
              ? 'rgba(100, 100, 100, 0.3)'
              : 'rgba(220, 38, 38, 0.3)'
          }`,
          boxShadow: isListening 
            ? '0 0 40px rgba(252, 211, 77, 0.5), inset 0 0 20px rgba(0, 0, 0, 0.3)'
            : '0 4px 15px rgba(0, 0, 0, 0.3)',
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          opacity: isDisabled ? 0.5 : 1,
        }}
        aria-label={isListening ? "Stop recording" : "Start recording"}
      >
        {/* Microphone Icon */}
        <svg 
          className="w-6 h-6"
          fill="currentColor" 
          viewBox="0 0 24 24"
          style={{ 
            color: isListening ? '#000' : isDisabled ? '#666' : '#DC2626',
            transform: `scale(${isListening ? pulseScale : 1})`,
            transition: 'transform 0.1s ease',
          }}
        >
          {isListening ? (
            <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
          ) : (
            <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
          )}
        </svg>

        {/* Recording Indicator Dots */}
        {isListening && (
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 flex space-x-1">
            <div 
              className="w-1.5 h-1.5 rounded-full"
              style={{ 
                background: '#DC2626',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0s',
              }}
            />
            <div 
              className="w-1.5 h-1.5 rounded-full"
              style={{ 
                background: '#FCD34D',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0.3s',
              }}
            />
            <div 
              className="w-1.5 h-1.5 rounded-full"
              style={{ 
                background: '#16A34A',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0.6s',
              }}
            />
          </div>
        )}
      </button>

      {/* Status Text */}
      <div 
        className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap"
        style={{ display: isListening || isDisabled ? 'block' : 'none' }}
      >
        <p 
          className="text-xs smooth-fade-in"
          style={{ 
            color: isListening ? '#FCD34D' : '#666',
            fontFamily: 'Ubuntu, sans-serif',
          }}
        >
          {isListening ? 'Listening...' : isDisabled ? 'Mic disabled' : ''}
        </p>
      </div>

      {/* Volume Level Indicator */}
      {isListening && volume > 0 && (
        <div className="absolute -right-8 top-1/2 transform -translate-y-1/2">
          <div className="flex flex-col space-y-1">
            {[0.8, 0.6, 0.4, 0.2].map((threshold, index) => (
              <div
                key={index}
                className="w-1 h-2 rounded-full transition-all"
                style={{
                  background: volume > threshold 
                    ? index === 0 ? '#DC2626' 
                    : index === 1 ? '#FCD34D'
                    : index === 2 ? '#16A34A'
                    : '#16A34A'
                    : 'rgba(100, 100, 100, 0.3)',
                  opacity: volume > threshold ? 1 : 0.3,
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Decorative Elements */}
      {isListening && (
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2">
          <div className="flex space-x-2 text-sm opacity-60">
            <span className="float-notes" style={{ color: '#DC2626', animationDelay: '0s' }}>♪</span>
            <span className="float-notes" style={{ color: '#FCD34D', animationDelay: '0.5s' }}>♫</span>
            <span className="float-notes" style={{ color: '#16A34A', animationDelay: '1s' }}>♪</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MicrophoneButton;