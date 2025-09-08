import React from 'react';
import { Message } from '../../types';
import { safeStringify } from '../../../../utils/messageParser';

interface AIChatBubbleProps {
  message: Message;
}

const AIChatBubble: React.FC<AIChatBubbleProps> = ({ message }) => {
  return (
    <div className="max-w-4xl">
      <div className="px-5 py-3 rounded-3xl shadow-2xl transition-all duration-300 hover:scale-105 relative overflow-hidden bg-gradient-to-br from-green-500/90 via-yellow-500/80 to-red-500/70 text-white border-2 border-yellow-400/50">
        {/* Shimmer effect overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-shimmer" style={{ animation: 'shimmer 3s infinite' }}></div>
        
        {/* Lion Avatar */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl flex-shrink-0 bg-gradient-to-br from-yellow-400/30 to-yellow-600/30 border-2 border-yellow-400/50">
            🦁
          </div>
          
          <div className="flex-1">
            <div className="text-base font-medium whitespace-pre-wrap break-words">
              {safeStringify(message.content || message.text, 'No message content')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChatBubble;