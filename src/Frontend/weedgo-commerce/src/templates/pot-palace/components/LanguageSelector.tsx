import React from 'react';
import { ILanguageSelectorProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceLanguageSelector: React.FC<ILanguageSelectorProps> = (props) => {
  // Simplified Pot Palace themed LanguageSelector
  return (
    <div className={clsx(
      'pot-palace-component',
      'bg-white rounded-2xl border-3 border-green-300 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <span className="text-3xl">🌿</span>
        <p className="mt-2 font-bold">PotPalace LanguageSelector</p>
        <p className="text-sm">Coming soon!</p>
      </div>
    </div>
  );
};
