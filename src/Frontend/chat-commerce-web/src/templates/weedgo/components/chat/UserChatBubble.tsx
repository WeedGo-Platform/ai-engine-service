import React from 'react';
import type { UserChatBubbleProps } from '../../../../core/contracts/template.contracts';

const UserChatBubble: React.FC<UserChatBubbleProps> = ({
  content
}) => {
  return (
    <div className="flex justify-end">
      <div className="max-w-3xl">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-800 to-gray-700 text-white rounded-2xl shadow-md">
          <div className="text-base leading-relaxed">{content}</div>
        </div>
      </div>
    </div>
  );
};

export default UserChatBubble;