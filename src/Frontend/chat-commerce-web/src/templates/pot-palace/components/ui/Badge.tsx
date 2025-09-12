import React from 'react';
import { BadgeProps } from '../../../../core/contracts/template.contracts';

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const baseClasses = 'inline-flex items-center gap-1 font-semibold rounded-full transition-all duration-300 shadow-sm';
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-purple-300',
    secondary: 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-green-300',
    success: 'bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-emerald-300',
    warning: 'bg-gradient-to-r from-amber-600 to-amber-500 text-white shadow-amber-300',
    danger: 'bg-gradient-to-r from-red-600 to-red-500 text-white shadow-red-300',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const getIcon = (variant: string) => {
    switch (variant) {
      case 'primary': return '💜';
      case 'secondary': return '🌿';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'danger': return '❌';
      default: return '✨';
    }
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className} group`}>
      <span className="group-hover:scale-110 transition-transform">
        {getIcon(variant)}
      </span>
      {children}
    </span>
  );
};

export default Badge;