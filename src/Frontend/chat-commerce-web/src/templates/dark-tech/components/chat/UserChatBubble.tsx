import React from 'react';
import type { UserChatBubbleProps } from '../../../../core/contracts/template.contracts';

const UserChatBubble: React.FC<UserChatBubbleProps> = ({
  content
}) => {
  return (
    <div className="flex justify-end">
      <div className="max-w-4xl">
        <div className="relative px-5 py-3 rounded-lg bg-gradient-to-r from-purple-900/90 to-pink-900/90 text-pink-300 border border-pink-500/30 shadow-[0_0_20px_rgba(236,72,153,0.2)]">
          <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-pink-500"></div>
          <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-pink-500"></div>
          <div className="text-base font-mono leading-relaxed">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default UserChatBubble;