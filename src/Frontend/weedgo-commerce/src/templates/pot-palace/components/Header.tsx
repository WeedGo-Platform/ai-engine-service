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
      'bg-white',
      'border-b border-[#E5E7EB]',
      'shadow-sm',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <PotPalaceLogo size="lg" variant="full" />

          <nav className="hidden md:flex items-center gap-8">
            <a href="/shop" className="text-[#1F2937] font-medium hover:text-[#2D5F3F] transition-colors text-sm">
              Shop
            </a>
            <a href="/deals" className="text-[#1F2937] font-medium hover:text-[#2D5F3F] transition-colors text-sm">
              Deals
            </a>
            <a href="/learn" className="text-[#1F2937] font-medium hover:text-[#2D5F3F] transition-colors text-sm">
              Learn
            </a>
            <a href="/account" className="text-[#1F2937] font-medium hover:text-[#2D5F3F] transition-colors text-sm">
              Account
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {onChatToggle && (
              <PotPalaceButton
                onClick={onChatToggle}
                variant="ghost"
                size="sm"
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                }
              >
                Chat
              </PotPalaceButton>
            )}
            <PotPalaceButton
              variant="primary"
              size="sm"
              leftIcon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              }
            >
              Cart (0)
            </PotPalaceButton>
          </div>
        </div>
      </div>
    </header>
  );
};
