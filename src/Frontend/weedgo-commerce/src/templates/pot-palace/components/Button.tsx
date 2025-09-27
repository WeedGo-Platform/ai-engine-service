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
  const baseStyles = 'inline-flex items-center justify-center font-black uppercase tracking-wider transition-all duration-300 transform active:scale-95 relative overflow-hidden';

  const variants = {
    primary: 'bg-[#84CC16] hover:bg-[#6FA914] text-white shadow-2xl hover:shadow-xl border-4 border-white',
    secondary: 'bg-[#FB923C] hover:bg-[#F97316] text-white shadow-2xl hover:shadow-xl border-4 border-white',
    outline: 'bg-transparent border-4 border-[#A855F7] text-[#A855F7] hover:bg-[#A855F7] hover:text-white',
    ghost: 'bg-transparent text-[#84CC16] hover:bg-[#84CC16]/10 border-2 border-transparent hover:border-[#84CC16]',
    danger: 'bg-[#DC2626] hover:bg-[#B91C1C] text-white shadow-2xl border-4 border-white'
  };

  const sizes = {
    xs: 'px-4 py-2 text-sm rounded-xl',
    sm: 'px-5 py-2.5 text-base rounded-2xl',
    md: 'px-8 py-4 text-lg rounded-3xl',
    lg: 'px-10 py-5 text-xl rounded-full',
    xl: 'px-12 py-6 text-2xl rounded-full'
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
        'hover:rotate-2 hover:-translate-y-1',
        className
      )}
    >
      {loading ? (
        <span className="animate-spin mr-2 text-2xl">🌿</span>
      ) : leftIcon && (
        <span className="mr-2 text-xl">{leftIcon}</span>
      )}
      {children}
      {rightIcon && (
        <span className="ml-2 text-xl">{rightIcon}</span>
      )}
    </button>
  );
};
