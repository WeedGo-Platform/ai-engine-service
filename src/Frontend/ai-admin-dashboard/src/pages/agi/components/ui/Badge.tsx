/**
 * Badge and Status Components
 */

import React from 'react';

interface IBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Badge: React.FC<IBadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}) => {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800'
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base'
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {children}
    </span>
  );
};

interface IStatusDotProps {
  status: 'online' | 'offline' | 'busy' | 'away';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusDot: React.FC<IStatusDotProps> = ({
  status,
  label,
  size = 'md'
}) => {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-400',
    busy: 'bg-red-500',
    away: 'bg-yellow-500'
  };

  const sizeClasses = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4'
  };

  return (
    <div className="flex items-center space-x-2">
      <span className="relative flex">
        <span
          className={`${statusColors[status]} ${sizeClasses[size]} rounded-full`}
        />
        {status === 'online' && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${statusColors[status]} opacity-75`}
          />
        )}
      </span>
      {label && <span className="text-sm text-gray-600">{label}</span>}
    </div>
  );
};