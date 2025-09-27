import React from 'react';
import { ISkeletonProps } from '../../types';
import { clsx } from 'clsx';

export const ModernSkeleton: React.FC<ISkeletonProps> = (props) => {
  // Modern premium themed Skeleton
  return (
    <div className={clsx(
      'modern-component',
      'bg-white rounded-lg shadow-sm border border-gray-100 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <p className="font-semibold">Modern Skeleton</p>
        <p className="text-sm text-gray-500 mt-1">Premium implementation coming soon</p>
      </div>
    </div>
  );
};
