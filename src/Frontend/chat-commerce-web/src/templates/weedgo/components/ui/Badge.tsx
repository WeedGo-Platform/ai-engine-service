import React from 'react';
import { BadgeProps } from '../../../../core/contracts/template.contracts';

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const baseClasses = 'inline-flex items-center font-mono font-medium rounded-lg';
  
  const variantClasses = {
    primary: 'bg-blue-700 text-white',
    secondary: 'bg-gray-200 text-gray-800',
    success: 'bg-green-600 text-white',
    warning: 'bg-orange-600 text-white',
    danger: 'bg-red-600 text-white',
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