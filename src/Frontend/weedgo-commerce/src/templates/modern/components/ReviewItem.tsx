import React from 'react';
import { IReviewItemProps } from '../../types';
import { clsx } from 'clsx';

export const ModernReviewItem: React.FC<IReviewItemProps> = (props) => {
  // Modern premium themed ReviewItem
  return (
    <div className={clsx(
      'modern-component',
      'bg-white rounded-lg shadow-sm border border-gray-100 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <p className="font-semibold">Modern ReviewItem</p>
        <p className="text-sm text-gray-500 mt-1">Premium implementation coming soon</p>
      </div>
    </div>
  );
};
