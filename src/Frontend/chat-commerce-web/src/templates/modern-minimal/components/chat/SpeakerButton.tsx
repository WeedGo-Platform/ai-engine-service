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
      className={`p-3.5 rounded-xl transition-all shadow-sm hover:shadow-md ${
        isEnabled 
          ? 'bg-gray-800 text-white' 
          : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
      } ${isSpeaking ? 'animate-pulse' : ''} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      title={isEnabled ? "Disable audio" : "Enable audio"}
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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