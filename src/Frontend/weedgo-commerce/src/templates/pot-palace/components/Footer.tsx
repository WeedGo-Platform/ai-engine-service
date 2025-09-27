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
