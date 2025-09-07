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
        <div className="px-4 py-3 rounded-lg bg-black/90 border border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.8)]"></div>
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.8)]" style={{ animationDelay: '0.3s' }}></div>
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.8)]" style={{ animationDelay: '0.6s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-4xl">
        <div className="relative px-5 py-3 rounded-lg bg-black/90 text-cyan-300 border border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
          <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-cyan-500"></div>
          <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-cyan-500"></div>
          <div className="text-base font-mono leading-relaxed">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default AIChatBubble;