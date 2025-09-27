import React from 'react';
import { IHeaderProps } from '../../types';
import { clsx } from 'clsx';
import { ModernLogo } from './Logo';
import { ModernButton } from './Button';

export const ModernHeader: React.FC<IHeaderProps> = ({
  onChatToggle,
  className
}) => {
  return (
    <header className={clsx(
      'sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-100',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <ModernLogo size="md" variant="full" />

          <nav className="hidden md:flex items-center gap-8">
            <a href="/shop" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Shop
            </a>
            <a href="/deals" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Deals
            </a>
            <a href="/learn" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Learn
            </a>
            <a href="/account" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Account
            </a>
          </nav>

          <div className="flex items-center gap-4">
            {onChatToggle && (
              <ModernButton
                onClick={onChatToggle}
                variant="ghost"
                size="sm"
              >
                Chat
              </ModernButton>
            )}
            <ModernButton
              variant="primary"
              size="sm"
            >
              Cart
            </ModernButton>
          </div>
        </div>
      </div>
    </header>
  );
};
