import React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  variant?: 'default' | 'filled' | 'ghost';
}

/**
 * Reusable Input component with consistent styling and validation support
 */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      variant = 'default',
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const variantClasses = {
      default: 'border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
      filled: 'border-0 bg-gray-100 dark:bg-gray-700',
      ghost: 'border-0 bg-transparent hover:bg-gray-50 dark:hover:bg-gray-800'
    };

    const inputClasses = clsx(
      'rounded-lg transition-all duration-200 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400',
      variantClasses[variant],
      'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
      error && 'border-red-500 focus:ring-red-500',
      disabled && 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-900',
      leftIcon && 'pl-10',
      rightIcon && 'pr-10',
      !leftIcon && !rightIcon && 'px-4',
      'py-2.5',
      fullWidth && 'w-full',
      className
    );

    return (
      <div className={clsx('relative', fullWidth && 'w-full')}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            className={inputClasses}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? 'error-message' : helperText ? 'helper-text' : undefined}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}
        </div>

        {error && (
          <p id="error-message" className="mt-1 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p id="helper-text" className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';