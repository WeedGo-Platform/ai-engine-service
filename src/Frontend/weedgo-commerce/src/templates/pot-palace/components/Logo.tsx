import React from 'react';
import { ILogoProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceLogo: React.FC<ILogoProps> = ({
  size = 'md',
  variant = 'full',
  className
}) => {
  const sizes = {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const textSizes = {
    xs: 'text-sm',
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl'
  };

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      {/* Elegant leaf icon */}
      <svg className={clsx(sizes[size], 'text-[#2D5F3F]')} viewBox="0 0 24 24" fill="currentColor">
        <path d="M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z" />
      </svg>
      {variant === 'full' && (
        <span className={clsx(
          'font-display font-bold',
          'text-[#1F2937]',
          textSizes[size]
        )}>
          Pot Palace
        </span>
      )}
    </div>
  );
};
