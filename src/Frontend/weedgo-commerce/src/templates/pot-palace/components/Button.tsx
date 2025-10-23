import React from 'react';
import { IButtonProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceButton: React.FC<IButtonProps> = ({
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
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-300 transform active:scale-98 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2D5F3F]';

  const variants = {
    primary: 'bg-[#2D5F3F] hover:bg-[#234B32] text-white shadow-md hover:shadow-lg',
    secondary: 'bg-[#7A9E88] hover:bg-[#658574] text-white shadow-md hover:shadow-lg',
    outline: 'bg-transparent border-2 border-[#2D5F3F] text-[#2D5F3F] hover:bg-[#2D5F3F] hover:text-white',
    ghost: 'bg-transparent text-[#2D5F3F] hover:bg-[#7A9E88]/10',
    danger: 'bg-[#DC2626] hover:bg-[#B91C1C] text-white shadow-md hover:shadow-lg'
  };

  const sizes = {
    xs: 'px-3 py-1.5 text-sm rounded-md',
    sm: 'px-4 py-2 text-sm rounded-lg',
    md: 'px-6 py-3 text-base rounded-lg',
    lg: 'px-8 py-4 text-base rounded-lg',
    xl: 'px-10 py-5 text-lg rounded-lg'
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
        'hover:translate-y-[-2px]',
        className
      )}
    >
      {loading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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
