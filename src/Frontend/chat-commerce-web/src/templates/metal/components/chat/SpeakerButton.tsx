import React, { useState } from 'react';

interface SpeakerButtonProps {
  text: string;
  disabled?: boolean;
}

const SpeakerButton: React.FC<SpeakerButtonProps> = ({ text, disabled = false }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
    // TTS logic would go here
    if (!isPlaying) {
      setTimeout(() => setIsPlaying(false), 3000);
    }
  };

  return (
    <button
      onClick={togglePlayback}
      disabled={disabled || !text}
      className={`
        p-2 rounded-lg transition-all duration-200
        ${isPlaying 
          ? 'bg-blue-500 text-white' 
          : 'text-gray-500 hover:bg-gray-100'
        }
        ${disabled || !text ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      aria-label={isPlaying ? 'Stop playback' : 'Play message'}
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        {isPlaying ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        )}
      </svg>
    </button>
  );
};

export default SpeakerButton;