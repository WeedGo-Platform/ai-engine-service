import React from 'react';
import { ILogoProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceLogo: React.FC<ILogoProps> = ({
  size = 'md',
  variant = 'full',
  className
}) => {
  const sizes = {
    xs: 'text-xl',
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl',
    xl: 'text-5xl'
  };

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      <span className={clsx('animate-bounce', sizes[size])}>
        🌿
      </span>
      {variant === 'full' && (
        <span className={clsx(
          'font-black uppercase',
          'text-white',
          sizes[size]
        )}>
          <span className="text-lime-400">POT</span>
          <span className="text-orange-400">PALACE</span>
        </span>
      )}
    </div>
  );
};
