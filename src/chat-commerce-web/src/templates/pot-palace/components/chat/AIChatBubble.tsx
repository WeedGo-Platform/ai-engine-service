import React from 'react';
import type { AIChatBubbleProps } from '../../../../core/contracts/template.contracts';

const AIChatBubble: React.FC<AIChatBubbleProps> = ({
  content,
  isTyping,
  personality,
  agent
}) => {
  if (isTyping) {
    return (
      <div className="flex justify-start">
        <div className="px-4 py-3 rounded-2xl bg-black/75 border border-purple-700/30 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping"></div>
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-4xl">
        <div className="px-5 py-3 rounded-2xl bg-black/75 text-green-400 border border-green-700/40 backdrop-blur-sm shadow-lg">
          <div className="text-base font-medium">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default AIChatBubble;