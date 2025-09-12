import React, { useState } from 'react';

interface MicrophoneButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

const MicrophoneButton: React.FC<MicrophoneButtonProps> = ({ onTranscript, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false);

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // Voice recording logic would go here
    if (isRecording) {
      // Stop recording and process
      setTimeout(() => {
        onTranscript('Sample voice transcript');
      }, 1000);
    }
  };

  return (
    <button
      onClick={toggleRecording}
      disabled={disabled}
      className={`
        p-2 rounded-lg transition-all duration-200
        ${isRecording 
          ? 'bg-red-500 text-white animate-pulse' 
          : 'text-gray-500 hover:bg-gray-100'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  );
};

export default MicrophoneButton;