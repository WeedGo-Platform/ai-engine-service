import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import AIChatBubble from './AIChatBubble';
import UserChatBubble from './UserChatBubble';
import Scrollbar from '../ui/Scrollbar';
import { useTemplate } from '../../../../core/providers/template.provider';

interface ChatMessagesProps {
  messages: Message[];
  isLoading?: boolean;
  onRetry?: (messageId: string) => void;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isLoading = false,
  onRetry,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const template = useTemplate();
  const theme = template.getTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Scrollbar className="flex-1 p-4 space-y-4" style={{ 
      background: theme.colors.background 
    }} maxHeight="100%">
      {messages.length === 0 && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full shadow-sm mb-4" style={{ 
            backgroundColor: theme.colors.surface 
          }}>
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ 
              color: theme.colors.primary 
            }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-1" style={{ color: theme.colors.text }}>Welcome to Dirty Shop</h3>
          <p style={{ color: theme.colors.textSecondary }}>How can I help you today?</p>
        </div>
      )}
      
      {messages.map((message) => (
        <div key={message.id}>
          {message.sender === 'user' ? (
            <UserChatBubble message={message} />
          ) : (
            <AIChatBubble message={message} onRetry={onRetry} />
          )}
        </div>
      ))}
      
      {isLoading && (
        <div className="flex items-center space-x-2" style={{ color: theme.colors.textSecondary }}>
          <div className="flex space-x-1">
            <div className="w-2 h-2 rounded-full animate-bounce" style={{ 
              backgroundColor: theme.colors.accent, 
              animationDelay: '0ms' 
            }}></div>
            <div className="w-2 h-2 rounded-full animate-bounce" style={{ 
              backgroundColor: theme.colors.accent, 
              animationDelay: '150ms' 
            }}></div>
            <div className="w-2 h-2 rounded-full animate-bounce" style={{ 
              backgroundColor: theme.colors.accent, 
              animationDelay: '300ms' 
            }}></div>
          </div>
          <span className="text-sm">Dirty Shop is typing...</span>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </Scrollbar>
  );
};

export default ChatMessages;