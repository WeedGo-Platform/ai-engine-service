import React from 'react';
import type { MicrophoneButtonProps } from '../../../../core/contracts/template.contracts';

const MicrophoneButton: React.FC<MicrophoneButtonProps> = ({
  isRecording,
  onClick,
  disabled = false
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`p-3 rounded-lg transition-all border disabled:opacity-50 disabled:cursor-not-allowed ${
        isRecording 
          ? 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.5)]' 
          : 'bg-black/50 border-gray-700/50 text-gray-500 hover:border-gray-600'
      }`}
      title={isRecording ? "Recording::ACTIVE" : "Voice::READY"}
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  );
};

export default MicrophoneButton;