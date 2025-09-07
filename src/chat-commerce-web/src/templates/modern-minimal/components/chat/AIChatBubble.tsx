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
        <div className="px-6 py-4 bg-gray-100 rounded-2xl">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-3xl">
        <div className="px-6 py-4 bg-gray-100 text-gray-800 rounded-2xl shadow-sm">
          <div className="text-base leading-relaxed">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default AIChatBubble;