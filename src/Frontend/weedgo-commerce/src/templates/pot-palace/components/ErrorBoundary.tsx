import React from 'react';
import { IErrorBoundaryProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceErrorBoundary: React.FC<IErrorBoundaryProps> = (props) => {
  // Simplified Pot Palace themed ErrorBoundary
  return (
    <div className={clsx(
      'pot-palace-component',
      'bg-white rounded-2xl border-3 border-green-300 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <span className="text-3xl">🌿</span>
        <p className="mt-2 font-bold">PotPalace ErrorBoundary</p>
        <p className="text-sm">Coming soon!</p>
      </div>
    </div>
  );
};
