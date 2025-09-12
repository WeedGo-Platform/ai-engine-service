import React, { useState } from 'react';

interface SpeakerButtonProps {
  isPlaying?: boolean;
  isMuted?: boolean;
  volume?: number;
  onTogglePlay?: () => void;
  onToggleMute?: () => void;
  onVolumeChange?: (volume: number) => void;
}

const SpeakerButton: React.FC<SpeakerButtonProps> = ({
  isPlaying = false,
  isMuted = false,
  volume = 0.7,
  onTogglePlay,
  onToggleMute,
  onVolumeChange,
}) => {
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);

  const getVolumeIcon = () => {
    if (isMuted || volume === 0) {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
        </svg>
      );
    } else if (volume < 0.5) {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M7 9v6h4l5 5V4l-5 5H7z"/>
        </svg>
      );
    } else {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
      );
    }
  };

  return (
    <div className="relative">
      {/* Main Button */}
      <button
        onClick={onTogglePlay}
        onMouseEnter={() => setShowVolumeSlider(true)}
        onMouseLeave={() => setTimeout(() => setShowVolumeSlider(false), 300)}
        className="p-3 rounded-xl transition-all hover:scale-110 relative overflow-hidden"
        style={{
          background: isPlaying 
            ? 'linear-gradient(135deg, rgba(252, 211, 77, 0.3) 0%, rgba(252, 211, 77, 0.1) 100%)'
            : 'rgba(26, 26, 26, 0.6)',
          border: `2px solid ${isPlaying ? 'rgba(252, 211, 77, 0.5)' : 'rgba(252, 211, 77, 0.2)'}`,
          color: isPlaying ? '#FCD34D' : '#F3E7C3',
          boxShadow: isPlaying ? '0 0 30px rgba(252, 211, 77, 0.3)' : 'none',
        }}
        aria-label={isPlaying ? "Pause audio" : "Play audio"}
      >
        {/* Sound Waves Animation */}
        {isPlaying && !isMuted && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div 
              className="absolute w-full h-full rounded-xl"
              style={{
                background: 'radial-gradient(circle, rgba(252, 211, 77, 0.2) 0%, transparent 70%)',
                animation: 'dub-echo 2s ease-out infinite',
              }}
            />
          </div>
        )}

        {/* Icon */}
        <div className="relative z-10">
          {getVolumeIcon()}
        </div>

        {/* Playing Indicator */}
        {isPlaying && !isMuted && (
          <div className="absolute bottom-1 right-1 flex space-x-0.5">
            <div 
              className="w-1 h-1 rounded-full"
              style={{ 
                background: '#DC2626',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0s',
              }}
            />
            <div 
              className="w-1 h-1 rounded-full"
              style={{ 
                background: '#FCD34D',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0.2s',
              }}
            />
            <div 
              className="w-1 h-1 rounded-full"
              style={{ 
                background: '#16A34A',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                animationDelay: '0.4s',
              }}
            />
          </div>
        )}
      </button>

      {/* Volume Slider */}
      {showVolumeSlider && (
        <div 
          className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 smooth-fade-in"
          onMouseEnter={() => setShowVolumeSlider(true)}
          onMouseLeave={() => setShowVolumeSlider(false)}
        >
          <div 
            className="px-3 py-2 rounded-lg"
            style={{
              background: 'rgba(26, 26, 26, 0.95)',
              border: '1px solid rgba(252, 211, 77, 0.3)',
              backdropFilter: 'blur(10px)',
            }}
          >
            {/* Volume Controls */}
            <div className="flex flex-col items-center space-y-2">
              {/* Volume Slider */}
              <div className="h-24 flex items-center">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume * 100}
                  onChange={(e) => onVolumeChange?.(Number(e.target.value) / 100)}
                  className="h-24"
                  style={{
                    writingMode: 'vertical-lr' as any,
                    WebkitAppearance: 'slider-vertical',
                    width: '4px',
                    background: 'linear-gradient(to top, #16A34A, #FCD34D, #DC2626)',
                    outline: 'none',
                  }}
                />
              </div>

              {/* Volume Percentage */}
              <span 
                className="text-xs font-semibold"
                style={{ color: '#FCD34D' }}
              >
                {Math.round(volume * 100)}%
              </span>

              {/* Mute Button */}
              <button
                onClick={onToggleMute}
                className="p-1.5 rounded-lg transition-all hover:scale-110"
                style={{
                  background: isMuted ? 'rgba(220, 38, 38, 0.2)' : 'transparent',
                  border: `1px solid ${isMuted ? 'rgba(220, 38, 38, 0.5)' : 'rgba(252, 211, 77, 0.3)'}`,
                  color: isMuted ? '#DC2626' : '#FCD34D',
                }}
                aria-label={isMuted ? "Unmute" : "Mute"}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  {isMuted ? (
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                  ) : (
                    <path d="M3 9v6h4l5 5V4L7 9H3z"/>
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* Arrow Pointer */}
          <div 
            className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1"
            style={{
              width: 0,
              height: 0,
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '6px solid rgba(252, 211, 77, 0.3)',
            }}
          />
        </div>
      )}

      {/* Decorative Music Note */}
      {isPlaying && !isMuted && (
        <div 
          className="absolute -top-2 -right-2 text-sm opacity-60 float-notes"
          style={{ color: '#FCD34D' }}
        >
          ♫
        </div>
      )}
    </div>
  );
};

export default SpeakerButton;