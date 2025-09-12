import React from 'react';
import { useTemplate } from '../../../../core/providers/template.provider';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  disabled,
  children,
  className = '',
  style,
  ...props
}) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: disabled ? `${theme.colors.secondary}66` : theme.colors.secondary,
          color: '#FFFFFF',
          borderColor: 'transparent',
        };
      case 'secondary':
        return {
          backgroundColor: disabled ? `${theme.colors.primary}66` : theme.colors.primary,
          color: '#FFFFFF',
          borderColor: 'transparent',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: theme.colors.text,
          borderColor: theme.colors.border,
          borderWidth: '2px',
          borderStyle: 'solid',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: disabled ? theme.colors.textSecondary : theme.colors.text,
          borderColor: 'transparent',
        };
      case 'danger':
        return {
          backgroundColor: disabled ? `${theme.colors.error}66` : theme.colors.error,
          color: '#FFFFFF',
          borderColor: 'transparent',
        };
      default:
        return {};
    }
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  const variantStyles = getVariantStyles();
  
  return (
    <button
      className={`${baseStyles} ${sizes[size]} ${widthClass} ${className}`}
      style={{
        ...variantStyles,
        ...style,
      }}
      disabled={disabled || loading}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          const target = e.currentTarget;
          if (variant === 'primary') {
            target.style.backgroundColor = theme.colors.secondary;
            target.style.filter = 'brightness(0.9)';
          } else if (variant === 'secondary') {
            target.style.backgroundColor = theme.colors.primaryDark;
          } else if (variant === 'outline') {
            target.style.backgroundColor = `${theme.colors.surface}`;
          } else if (variant === 'ghost') {
            target.style.backgroundColor = `${theme.colors.surface}`;
          } else if (variant === 'danger') {
            target.style.filter = 'brightness(0.9)';
          }
        }
        props.onMouseEnter?.(e as any);
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          const target = e.currentTarget;
          target.style.backgroundColor = variantStyles.backgroundColor;
          target.style.filter = 'none';
        }
        props.onMouseLeave?.(e as any);
      }}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
};

export default Button;