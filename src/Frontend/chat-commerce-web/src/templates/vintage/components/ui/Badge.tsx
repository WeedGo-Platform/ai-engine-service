import React from 'react';
import { useTemplate } from '../../../../core/providers/template.provider';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  rounded?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  rounded = false,
  className = '',
  style,
}) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: `${theme.colors.secondary}22`,
          color: theme.colors.secondary,
        };
      case 'secondary':
        return {
          backgroundColor: `${theme.colors.primary}22`,
          color: theme.colors.primary,
        };
      case 'success':
        return {
          backgroundColor: `${theme.colors.success}22`,
          color: theme.colors.success,
        };
      case 'warning':
        return {
          backgroundColor: `${theme.colors.warning}22`,
          color: theme.colors.warning,
        };
      case 'danger':
        return {
          backgroundColor: `${theme.colors.error}22`,
          color: theme.colors.error,
        };
      case 'info':
        return {
          backgroundColor: `${theme.colors.info}22`,
          color: theme.colors.info,
        };
      default:
        return {
          backgroundColor: `${theme.colors.textSecondary}22`,
          color: theme.colors.text,
        };
    }
  };
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };
  
  const roundedClass = rounded ? 'rounded-full' : 'rounded-md';
  const variantStyles = getVariantStyles();
  
  return (
    <span
      className={`inline-flex items-center font-medium ${sizes[size]} ${roundedClass} ${className}`}
      style={{
        ...variantStyles,
        ...style,
      }}
    >
      {children}
    </span>
  );
};

export default Badge;