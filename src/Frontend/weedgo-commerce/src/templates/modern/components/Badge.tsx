import React from 'react';
import { IBadgeProps } from '../../types';
import { clsx } from 'clsx';

export const ModernBadge: React.FC<IBadgeProps> = (props) => {
  // Modern premium themed Badge
  return (
    <div className={clsx(
      'modern-component',
      'bg-white rounded-lg shadow-sm border border-gray-100 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <p className="font-semibold">Modern Badge</p>
        <p className="text-sm text-gray-500 mt-1">Premium implementation coming soon</p>
      </div>
    </div>
  );
};
