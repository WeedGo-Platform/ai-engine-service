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
      className="px-6 py-3 bg-gradient-to-r from-pink-600 to-pink-500 hover:from-pink-500 hover:to-pink-400 text-purple-950 font-bold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-lg disabled:from-purple-700 disabled:to-purple-600 disabled:text-purple-400 disabled:cursor-not-allowed flex items-center gap-2"
    >
      {isSending ? (
        <>
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Chatting...</span>
        </>
      ) : (
        <>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span>Chat</span>
        </>
      )}
    </button>
  );
};

export default ChatButton;