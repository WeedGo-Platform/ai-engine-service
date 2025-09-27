#!/bin/bash

BASE_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/weedgo-commerce/src/templates/pot-palace/components"

# Modal Component
cat > "$BASE_DIR/Modal.tsx" << 'EOF'
import React, { useEffect } from 'react';
import { IModalProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceModal: React.FC<IModalProps> = ({
  isOpen,
  onClose,
  children,
  title,
  size = 'md',
  closeOnOverlayClick = true,
  className
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={closeOnOverlayClick ? onClose : undefined}
      />
      <div className={clsx(
        'relative bg-white rounded-3xl shadow-2xl',
        'transform transition-all duration-500',
        'animate-bounce-in',
        'border-4 border-green-300',
        sizes[size],
        'max-h-[90vh] overflow-hidden flex flex-col',
        className
      )}>
        {(title || onClose) && (
          <div className="flex items-center justify-between p-6 border-b-3 border-green-200 bg-gradient-to-r from-green-50 to-yellow-50">
            {title && (
              <h2 className="text-2xl font-bold text-gray-800 font-display">
                {title}
              </h2>
            )}
            <button
              onClick={onClose}
              className="ml-auto text-3xl hover:scale-110 transition-transform text-green-600 hover:text-green-800"
            >
              ✕
            </button>
          </div>
        )}
        <div className="p-6 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  );
};
EOF

# Header Component
cat > "$BASE_DIR/Header.tsx" << 'EOF'
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
      'bg-gradient-to-r from-green-600 via-green-500 to-yellow-400',
      'border-b-4 border-green-800',
      'shadow-xl',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <PotPalaceLogo size="lg" variant="full" />

          <nav className="hidden md:flex items-center gap-6">
            <a href="/shop" className="text-white font-bold hover:text-yellow-200 transition-colors">
              Shop 🛒
            </a>
            <a href="/deals" className="text-white font-bold hover:text-yellow-200 transition-colors">
              Deals 🔥
            </a>
            <a href="/learn" className="text-white font-bold hover:text-yellow-200 transition-colors">
              Learn 📚
            </a>
            <a href="/account" className="text-white font-bold hover:text-yellow-200 transition-colors">
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
              className="bg-white text-green-600 hover:bg-yellow-100"
            >
              Cart (0)
            </PotPalaceButton>
          </div>
        </div>
      </div>
    </header>
  );
};
EOF

# Footer Component
cat > "$BASE_DIR/Footer.tsx" << 'EOF'
import React from 'react';
import { IFooterProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceLogo } from './Logo';

export const PotPalaceFooter: React.FC<IFooterProps> = ({
  className
}) => {
  return (
    <footer className={clsx(
      'bg-gradient-to-b from-green-800 to-green-900',
      'text-white mt-20',
      'border-t-4 border-yellow-500',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <PotPalaceLogo size="md" variant="full" />
            <p className="mt-4 text-green-200">
              Your premium cannabis destination 🌿
            </p>
          </div>

          <div>
            <h3 className="font-bold text-yellow-400 mb-4">Shop</h3>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-yellow-300">Flower</a></li>
              <li><a href="#" className="hover:text-yellow-300">Edibles</a></li>
              <li><a href="#" className="hover:text-yellow-300">Concentrates</a></li>
              <li><a href="#" className="hover:text-yellow-300">Accessories</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-yellow-400 mb-4">Learn</h3>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-yellow-300">Cannabis 101</a></li>
              <li><a href="#" className="hover:text-yellow-300">Dosing Guide</a></li>
              <li><a href="#" className="hover:text-yellow-300">Terpenes</a></li>
              <li><a href="#" className="hover:text-yellow-300">Blog</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-yellow-400 mb-4">Connect</h3>
            <div className="flex gap-4 text-2xl">
              <span className="cursor-pointer hover:scale-110 transition-transform">📧</span>
              <span className="cursor-pointer hover:scale-110 transition-transform">📱</span>
              <span className="cursor-pointer hover:scale-110 transition-transform">🐦</span>
              <span className="cursor-pointer hover:scale-110 transition-transform">📷</span>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-green-700 text-center text-green-300">
          <p>© 2024 Pot Palace. All rights reserved. Stay lifted! 🚀</p>
        </div>
      </div>
    </footer>
  );
};
EOF

# SearchBar Component
cat > "$BASE_DIR/SearchBar.tsx" << 'EOF'
import React, { useState } from 'react';
import { ISearchBarProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceSearchBar: React.FC<ISearchBarProps> = ({
  value: controlledValue,
  onChange,
  onSearch,
  placeholder = 'Search for your favorite strains...',
  variant = 'default',
  className,
  showSuggestions = false
}) => {
  const [localValue, setLocalValue] = useState('');
  const value = controlledValue ?? localValue;

  const handleChange = (newValue: string) => {
    setLocalValue(newValue);
    onChange?.(newValue);
  };

  const handleSearch = () => {
    onSearch?.(value);
  };

  const variants = {
    default: 'border-3 border-green-400 focus-within:border-green-600',
    compact: 'border-2 border-green-300 focus-within:border-green-500',
    minimal: 'border-b-2 border-green-300 rounded-none focus-within:border-green-500'
  };

  return (
    <div className={clsx('relative w-full', className)}>
      <div className={clsx(
        'flex items-center bg-white rounded-2xl overflow-hidden',
        'transition-all duration-300 shadow-lg hover:shadow-xl',
        variants[variant]
      )}>
        <span className="pl-4 text-2xl">🔍</span>
        <input
          type="text"
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder={placeholder}
          className="flex-1 px-4 py-3 outline-none bg-transparent text-gray-800 placeholder-gray-400"
        />
        <button
          onClick={handleSearch}
          className="px-6 py-3 bg-green-600 text-white font-bold hover:bg-green-700 transition-colors"
        >
          Search 🌿
        </button>
      </div>

      {showSuggestions && value.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border-2 border-green-200 p-4 z-10">
          <p className="text-gray-600">Popular searches:</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              Blue Dream
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              OG Kush
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              Sour Diesel
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
EOF

# Hero Component
cat > "$BASE_DIR/Hero.tsx" << 'EOF'
import React from 'react';
import { IHeroProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceButton } from './Button';

export const PotPalaceHero: React.FC<IHeroProps> = ({
  title = 'Welcome to Pot Palace',
  subtitle = 'Your Premium Cannabis Destination',
  backgroundImage,
  cta,
  className
}) => {
  return (
    <div className={clsx(
      'relative min-h-[500px] flex items-center justify-center',
      'bg-gradient-to-br from-green-600 via-green-500 to-yellow-400',
      'overflow-hidden',
      className
    )}>
      {backgroundImage && (
        <img
          src={backgroundImage}
          alt=""
          className="absolute inset-0 w-full h-full object-cover opacity-30"
        />
      )}

      <div className="relative z-10 text-center px-4">
        <h1 className="text-5xl md:text-7xl font-display font-bold text-white mb-4 animate-bounce-in">
          {title} 🌿
        </h1>
        <p className="text-xl md:text-2xl text-yellow-100 mb-8">
          {subtitle}
        </p>

        {cta && (
          <PotPalaceButton
            onClick={cta.action}
            variant="secondary"
            size="xl"
            rightIcon="→"
            className="animate-pulse"
          >
            {cta.text}
          </PotPalaceButton>
        )}
      </div>

      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" className="w-full">
          <path
            fill="white"
            d="M0,64L80,69.3C160,75,320,85,480,80C640,75,800,53,960,48C1120,43,1280,53,1360,58.7L1440,64L1440,120L1360,120C1280,120,1120,120,960,120C800,120,640,120,480,120C320,120,160,120,80,120L0,120Z"
          />
        </svg>
      </div>
    </div>
  );
};
EOF

echo "✅ Critical components implemented!"