import React from 'react';
import { Message } from '../../types';

interface ChatMetadataProps {
  message: Message;
  onRetry?: (messageId: string) => void;
}

const ChatMetadata: React.FC<ChatMetadataProps> = ({ message, onRetry }) => {
  return (
    <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
      <div className="flex items-center space-x-3">
        {message.responseTime && (
          <span>Response time: {message.responseTime}ms</span>
        )}
        {message.tokens && (
          <span>Tokens: {message.tokens}</span>
        )}
      </div>
      {onRetry && message.sender === 'assistant' && (
        <button
          onClick={() => onRetry(message.id)}
          className="text-blue-600 hover:text-blue-700 flex items-center space-x-1"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};

export default ChatMetadata;