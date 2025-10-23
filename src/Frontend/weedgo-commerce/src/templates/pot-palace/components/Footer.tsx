import React from 'react';
import { IFooterProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceLogo } from './Logo';

export const PotPalaceFooter: React.FC<IFooterProps> = ({
  className
}) => {
  return (
    <footer className={clsx(
      'bg-[#1F2937]',
      'text-white mt-20',
      'border-t border-[#374151]',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="mb-4">
              <svg className="h-10 w-10 text-[#7A9E88]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z" />
              </svg>
              <span className="font-display font-bold text-xl text-white mt-2 block">Pot Palace</span>
            </div>
            <p className="mt-4 text-[#9CA3AF] text-sm leading-relaxed">
              Your premium cannabis destination for quality products and exceptional service.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-white mb-4">Shop</h3>
            <ul className="space-y-2.5">
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Flower</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Edibles</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Concentrates</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Accessories</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-white mb-4">Learn</h3>
            <ul className="space-y-2.5">
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Cannabis 101</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Dosing Guide</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Terpenes</a></li>
              <li><a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors text-sm">Blog</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-white mb-4">Connect</h3>
            <div className="flex gap-4">
              <a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
              </a>
              <a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
              </a>
              <a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/></svg>
              </a>
              <a href="#" className="text-[#9CA3AF] hover:text-[#7A9E88] transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37zm1.5-4.87h.01"/></svg>
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-[#374151] text-center text-[#9CA3AF] text-sm">
          <p>© 2024 Pot Palace. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
