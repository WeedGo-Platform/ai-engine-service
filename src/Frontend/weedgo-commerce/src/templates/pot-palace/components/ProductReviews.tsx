import React from 'react';
import { IProductReviewsProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceProductReviews: React.FC<IProductReviewsProps> = (props) => {
  // Simplified Pot Palace themed ProductReviews
  return (
    <div className={clsx(
      'pot-palace-component',
      'bg-white rounded-2xl border-3 border-green-300 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <span className="text-3xl">🌿</span>
        <p className="mt-2 font-bold">PotPalace ProductReviews</p>
        <p className="text-sm">Coming soon!</p>
      </div>
    </div>
  );
};
