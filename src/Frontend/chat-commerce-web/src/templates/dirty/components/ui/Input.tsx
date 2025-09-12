import React from 'react';
import { useTemplate } from '../../../../core/providers/template.provider';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className = '',
  style,
  ...props
}) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium mb-1" style={{ color: theme.colors.text }}>
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: theme.colors.textSecondary }}>
            {leftIcon}
          </div>
        )}
        <input
          className={`
            w-full px-4 py-2 border rounded-lg
            focus:ring-2 focus:border-transparent
            transition-all duration-200
            ${leftIcon ? 'pl-10' : ''}
            ${rightIcon ? 'pr-10' : ''}
            ${props.disabled ? 'cursor-not-allowed' : ''}
            ${className}
          `}
          style={{
            backgroundColor: props.disabled ? `${theme.colors.surface}99` : theme.colors.surface,
            borderColor: error ? theme.colors.error : theme.colors.border,
            color: theme.colors.text,
            outlineColor: theme.colors.secondary,
            ...style,
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = theme.colors.secondary;
            e.currentTarget.style.boxShadow = `0 0 0 3px ${theme.colors.secondary}33`;
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = error ? theme.colors.error : theme.colors.border;
            e.currentTarget.style.boxShadow = 'none';
            props.onBlur?.(e);
          }}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: theme.colors.textSecondary }}>
            {rightIcon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm" style={{ color: theme.colors.error }}>{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm" style={{ color: theme.colors.textSecondary }}>{helperText}</p>
      )}
    </div>
  );
};

export default Input;