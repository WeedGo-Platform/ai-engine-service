import React from 'react';
import { IHeaderProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceLogo } from './Logo';
import { PotPalaceButton } from './Button';

export const PotPalaceHeader: React.FC<IHeaderProps> = ({
  onChatToggle,
  className
}) => {
  return (
    <header className={clsx(
      'sticky top-0 z-40',
      'bg-purple-600',
      'border-b-4 border-lime-500',
      'shadow-2xl',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <PotPalaceLogo size="lg" variant="full" />

          <nav className="hidden md:flex items-center gap-6">
            <a href="/shop" className="text-white font-black hover:text-lime-400 transition-colors uppercase">
              Shop 🛒
            </a>
            <a href="/deals" className="text-white font-black hover:text-orange-400 transition-colors uppercase">
              Deals 🔥
            </a>
            <a href="/learn" className="text-white font-black hover:text-yellow-400 transition-colors uppercase">
              Learn 📚
            </a>
            <a href="/account" className="text-white font-black hover:text-pink-400 transition-colors uppercase">
              Account 👤
            </a>
          </nav>

          <div className="flex items-center gap-4">
            {onChatToggle && (
              <PotPalaceButton
                onClick={onChatToggle}
                variant="secondary"
                size="md"
                rightIcon="💬"
              >
                Chat
              </PotPalaceButton>
            )}
            <PotPalaceButton
              variant="primary"
              size="md"
            >
              Cart (0) 🛒
            </PotPalaceButton>
          </div>
        </div>
      </div>
    </header>
  );
};
