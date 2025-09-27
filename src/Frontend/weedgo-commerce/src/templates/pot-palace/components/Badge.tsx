import React from 'react';
import { IBadgeProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceBadge: React.FC<IBadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className
}) => {
  const variants = {
    primary: 'bg-green-100 text-green-800 border-green-300',
    secondary: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    success: 'bg-green-500 text-white',
    danger: 'bg-red-100 text-red-800 border-red-300',
    warning: 'bg-orange-100 text-orange-800 border-orange-300',
    info: 'bg-blue-100 text-blue-800 border-blue-300'
  };

  const sizes = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-sm',
    md: 'px-3 py-1.5 text-base',
    lg: 'px-4 py-2 text-lg'
  };

  return (
    <span className={clsx(
      'inline-flex items-center font-bold rounded-full border-2',
      variants[variant],
      sizes[size],
      'animate-pulse',
      className
    )}>
      {children}
    </span>
  );
};
