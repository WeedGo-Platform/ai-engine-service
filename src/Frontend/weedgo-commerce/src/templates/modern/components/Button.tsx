import React from 'react';
import { IButtonProps } from '../../types';
import { clsx } from 'clsx';

export const ModernButton: React.FC<IButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className,
  type = 'button'
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 backdrop-blur-sm';

  const variants = {
    primary: 'bg-[#0A84FF] text-white hover:bg-[#0073E6] focus:ring-[#0A84FF] shadow-sm',
    secondary: 'bg-[#1D1D1F] text-white hover:bg-[#2C2C2E] focus:ring-[#86868B] shadow-sm',
    outline: 'bg-white/80 backdrop-blur border border-[#D2D2D7] text-[#1D1D1F] hover:bg-[#F5F5F7] focus:ring-[#0A84FF]',
    ghost: 'bg-transparent text-[#86868B] hover:bg-[#F5F5F7]/50 focus:ring-[#86868B]',
    danger: 'bg-[#FF3B30] text-white hover:bg-[#D70015] focus:ring-[#FF3B30] shadow-sm'
  };

  const sizes = {
    xs: 'px-3 py-1.5 text-xs rounded-md',
    sm: 'px-4 py-2 text-sm rounded-lg',
    md: 'px-5 py-2.5 text-sm rounded-lg',
    lg: 'px-6 py-3 text-base rounded-lg',
    xl: 'px-8 py-3.5 text-base rounded-xl'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={clsx(
        baseStyles,
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {loading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : leftIcon && (
        <span className="mr-2">{leftIcon}</span>
      )}
      {children}
      {rightIcon && (
        <span className="ml-2">{rightIcon}</span>
      )}
    </button>
  );
};
