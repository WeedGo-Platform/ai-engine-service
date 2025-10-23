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
    primary: 'bg-[#2D5F3F]/10 text-[#2D5F3F] border-[#2D5F3F]/20',
    secondary: 'bg-[#7A9E88]/10 text-[#7A9E88] border-[#7A9E88]/20',
    success: 'bg-[#059669]/10 text-[#059669] border-[#059669]/20',
    danger: 'bg-[#DC2626]/10 text-[#DC2626] border-[#DC2626]/20',
    warning: 'bg-[#D97706]/10 text-[#D97706] border-[#D97706]/20',
    info: 'bg-[#0891B2]/10 text-[#0891B2] border-[#0891B2]/20'
  };

  const sizes = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-sm',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  };

  return (
    <span className={clsx(
      'inline-flex items-center font-medium rounded-md border',
      variants[variant],
      sizes[size],
      className
    )}>
      {children}
    </span>
  );
};
