import React from 'react';
import { IWishlistButtonProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceWishlistButton: React.FC<IWishlistButtonProps> = (props) => {
  // Simplified Pot Palace themed WishlistButton
  return (
    <div className={clsx(
      'pot-palace-component',
      'bg-white rounded-2xl border-3 border-green-300 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <span className="text-3xl">🌿</span>
        <p className="mt-2 font-bold">PotPalace WishlistButton</p>
        <p className="text-sm">Coming soon!</p>
      </div>
    </div>
  );
};
