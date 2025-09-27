import React, { useState } from 'react';
import { IChatInterfaceProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceChatBubble } from './ChatBubble';
import { PotPalaceInput } from './Input';
import { PotPalaceButton } from './Button';

export const PotPalaceChatInterface: React.FC<IChatInterfaceProps> = ({
  isOpen = false,
  onClose,
  position = 'bottom-right',
  className
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([
    { id: '1', text: 'Hey there! Welcome to Pot Palace! 🌿', timestamp: new Date(), isUser: false }
  ]);

  if (!isOpen) return null;

  const positions = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'center': 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'
  };

  return (
    <div className={clsx(
      'fixed z-50',
      positions[position],
      'w-96 h-[600px] bg-white rounded-3xl shadow-2xl',
      'border-4 border-green-400 overflow-hidden flex flex-col',
      className
    )}>
      <div className="bg-gradient-to-r from-green-600 to-yellow-500 p-4 flex items-center justify-between">
        <h3 className="text-white font-bold text-lg">Budtender Chat 💬</h3>
        <button
          onClick={onClose}
          className="text-white text-2xl hover:scale-110 transition-transform"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <PotPalaceChatBubble
            key={msg.id}
            message={msg}
            isUser={msg.isUser}
            showAvatar
          />
        ))}
      </div>

      <div className="p-4 border-t-3 border-green-200">
        <div className="flex gap-2">
          <PotPalaceInput
            value={message}
            onChange={setMessage}
            placeholder="Ask about strains..."
            className="flex-1"
          />
          <PotPalaceButton
            onClick={() => {
              if (message.trim()) {
                setMessages([...messages, {
                  id: Date.now().toString(),
                  text: message,
                  timestamp: new Date(),
                  isUser: true
                }]);
                setMessage('');
              }
            }}
            variant="primary"
          >
            Send
          </PotPalaceButton>
        </div>
      </div>
    </div>
  );
};
