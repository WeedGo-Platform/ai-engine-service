import React from 'react';
import { BadgeProps } from '../../../../core/contracts/template.contracts';

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const baseClasses = 'inline-flex items-center font-mono font-medium transition-all duration-200';
  
  const variantClasses = {
    primary: 'bg-black text-white',
    secondary: 'bg-gray-200 text-gray-900',
    success: 'bg-gray-900 text-white',
    warning: 'bg-gray-600 text-white',
    danger: 'bg-gray-800 text-white',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;