import React from 'react';
import { ILoadingScreenProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceLoadingScreen: React.FC<ILoadingScreenProps> = ({
  message = 'Loading your experience...',
  variant = 'spinner',
  fullScreen = true,
  className
}) => {
  const variants = {
    spinner: (
      <div className="animate-spin text-6xl">
        🌿
      </div>
    ),
    dots: (
      <div className="flex gap-2">
        <span className="w-4 h-4 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
        <span className="w-4 h-4 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
        <span className="w-4 h-4 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
      </div>
    ),
    bars: (
      <div className="flex gap-1">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="w-2 h-8 bg-gradient-to-t from-green-500 to-yellow-400 animate-pulse"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
    ),
    pulse: (
      <div className="relative">
        <div className="w-20 h-20 bg-green-500 rounded-full animate-ping absolute"></div>
        <div className="w-20 h-20 bg-green-500 rounded-full relative"></div>
      </div>
    )
  };

  return (
    <div className={clsx(
      fullScreen && 'fixed inset-0',
      'flex flex-col items-center justify-center',
      'bg-gradient-to-br from-green-50 to-yellow-50',
      className
    )}>
      {variants[variant]}
      {message && (
        <p className="mt-4 text-lg font-bold text-gray-800 animate-pulse">
          {message}
        </p>
      )}
    </div>
  );
};
