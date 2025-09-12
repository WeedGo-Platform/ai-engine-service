import React from 'react';
import type { UserChatBubbleProps } from '../../../../core/contracts/template.contracts';

const UserChatBubble: React.FC<UserChatBubbleProps> = ({
  content
}) => {
  return (
    <div className="flex justify-end">
      <div className="max-w-4xl">
        <div className="px-5 py-3 rounded-2xl bg-black/75 border border-yellow-600/40 text-yellow-400 shadow-lg backdrop-blur-sm">
          <div className="text-base font-medium">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default UserChatBubble;