import React from 'react';
import { IAdvancedSearchProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceAdvancedSearch: React.FC<IAdvancedSearchProps> = (props) => {
  // Simplified Pot Palace themed AdvancedSearch
  return (
    <div className={clsx(
      'pot-palace-component',
      'bg-white rounded-2xl border-3 border-green-300 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <span className="text-3xl">🌿</span>
        <p className="mt-2 font-bold">PotPalace AdvancedSearch</p>
        <p className="text-sm">Coming soon!</p>
      </div>
    </div>
  );
};
