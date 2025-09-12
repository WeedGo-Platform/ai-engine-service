import React from 'react';
import { Message } from '../../types';
import { useTemplate } from '../../../../core/providers/template.provider';

interface UserChatBubbleProps {
  message: Message;
}

const UserChatBubble: React.FC<UserChatBubbleProps> = ({ message }) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  return (
    <div className="flex items-start justify-end space-x-3">
      <div className="flex-1 max-w-2xl">
        <div className="rounded-lg shadow-sm p-4 ml-auto" style={{ 
          backgroundColor: theme.colors.secondary,
          color: theme.colors.text
        }}>
          <div className="text-sm">
            {message.content || message.text}
          </div>
        </div>
      </div>
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ 
          backgroundColor: theme.colors.userMessage || theme.colors.surface 
        }}>
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ 
            color: theme.colors.textSecondary 
          }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default UserChatBubble;