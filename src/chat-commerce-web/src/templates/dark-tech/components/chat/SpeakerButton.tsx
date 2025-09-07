import React from 'react';
import type { SpeakerButtonProps } from '../../../../core/contracts/template.contracts';

const SpeakerButton: React.FC<SpeakerButtonProps> = ({
  isEnabled,
  isSpeaking = false,
  onClick,
  disabled = false
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`p-3 rounded-lg transition-all border ${
        isEnabled 
          ? 'bg-green-500/20 border-green-500/50 text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.4)]' 
          : 'bg-black/50 border-gray-700/50 text-gray-500 hover:border-gray-600'
      } ${isSpeaking ? 'animate-pulse' : ''} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      title={isEnabled ? "Audio::ON" : "Audio::OFF"}
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {isEnabled ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        )}
      </svg>
    </button>
  );
};

export default SpeakerButton;