import React from 'react';
import type { ChatButtonProps } from '../../../../core/contracts/template.contracts';

const ChatButton: React.FC<ChatButtonProps> = ({
  onClick,
  disabled = false,
  isSending = false
}) => {
  return (
    <button
      id="send-button"
      onClick={onClick}
      disabled={disabled || isSending}
      className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-black font-mono font-bold rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] disabled:from-gray-700 disabled:to-gray-600 disabled:text-gray-400 disabled:cursor-not-allowed disabled:shadow-none flex items-center gap-2 uppercase tracking-wider"
    >
      {isSending ? (
        <>
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Processing...</span>
        </>
      ) : (
        <>
          <span className="text-lg">▶</span>
          <span>Execute</span>
        </>
      )}
    </button>
  );
};

export default ChatButton;