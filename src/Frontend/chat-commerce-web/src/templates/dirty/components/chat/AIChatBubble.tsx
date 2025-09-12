import React from 'react';
import { Message } from '../../types';
import ChatMetadata from './ChatMetadata';
import { useTemplate } from '../../../../core/providers/template.provider';

interface AIChatBubbleProps {
  message: Message;
  onRetry?: (messageId: string) => void;
}

const AIChatBubble: React.FC<AIChatBubbleProps> = ({ message, onRetry }) => {
  const template = useTemplate();
  const theme = template.getTheme();
  return (
    <div className="flex items-start space-x-3">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ 
          backgroundColor: theme.colors.accent 
        }}>
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ 
            color: theme.colors.text 
          }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      </div>
      <div className="flex-1 max-w-2xl">
        <div className="rounded-lg shadow-sm p-4 border" style={{ 
          backgroundColor: theme.colors.assistantMessage || theme.colors.surface,
          borderColor: theme.colors.border 
        }}>
          <div className="prose prose-sm max-w-none" style={{ 
            color: theme.colors.text 
          }}>
            {message.content || message.text}
          </div>
          <ChatMetadata message={message} onRetry={onRetry} />
        </div>
      </div>
    </div>
  );
};

export default AIChatBubble;