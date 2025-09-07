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
      className={`p-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
        isRecording 
          ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-lg' 
          : 'bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400'
      }`}
      title={isRecording ? "Stop recording" : "Start voice recording"}
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  );
};

export default MicrophoneButton;