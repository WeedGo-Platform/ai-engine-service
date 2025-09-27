import React from 'react';
import { IChatBubbleProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceChatBubble: React.FC<IChatBubbleProps> = ({
  message,
  isUser,
  showAvatar = true,
  className
}) => {
  return (
    <div className={clsx(
      'flex items-start gap-3',
      isUser && 'flex-row-reverse',
      className
    )}>
      {showAvatar && (
        <div className={clsx(
          'w-10 h-10 rounded-full flex items-center justify-center text-xl',
          isUser ? 'bg-green-500' : 'bg-yellow-400'
        )}>
          {isUser ? '👤' : '🌿'}
        </div>
      )}

      <div className={clsx(
        'max-w-[70%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-green-500 text-white rounded-br-none'
          : 'bg-gray-100 text-gray-800 rounded-bl-none'
      )}>
        <p>{message.text}</p>
        {message.products && message.products.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.products.map(product => (
              <div key={product.id} className="bg-white/20 rounded-lg p-2">
                <p className="font-bold">{product.name}</p>
                <p className="text-sm">${product.price}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
