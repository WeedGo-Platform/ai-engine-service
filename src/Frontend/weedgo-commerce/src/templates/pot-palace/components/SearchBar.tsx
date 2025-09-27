import React, { useState } from 'react';
import { ISearchBarProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceSearchBar: React.FC<ISearchBarProps> = ({
  value: controlledValue,
  onChange,
  onSearch,
  placeholder = 'Search for your favorite strains...',
  variant = 'default',
  className,
  showSuggestions = false
}) => {
  const [localValue, setLocalValue] = useState('');
  const value = controlledValue ?? localValue;

  const handleChange = (newValue: string) => {
    setLocalValue(newValue);
    onChange?.(newValue);
  };

  const handleSearch = () => {
    onSearch?.(value);
  };

  const variants = {
    default: 'border-3 border-green-400 focus-within:border-green-600',
    compact: 'border-2 border-green-300 focus-within:border-green-500',
    minimal: 'border-b-2 border-green-300 rounded-none focus-within:border-green-500'
  };

  return (
    <div className={clsx('relative w-full', className)}>
      <div className={clsx(
        'flex items-center bg-white rounded-2xl overflow-hidden',
        'transition-all duration-300 shadow-lg hover:shadow-xl',
        variants[variant]
      )}>
        <span className="pl-4 text-2xl">🔍</span>
        <input
          type="text"
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder={placeholder}
          className="flex-1 px-4 py-3 outline-none bg-transparent text-gray-800 placeholder-gray-400"
        />
        <button
          onClick={handleSearch}
          className="px-6 py-3 bg-green-600 text-white font-bold hover:bg-green-700 transition-colors"
        >
          Search 🌿
        </button>
      </div>

      {showSuggestions && value.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border-2 border-green-200 p-4 z-10">
          <p className="text-gray-600">Popular searches:</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              Blue Dream
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              OG Kush
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm cursor-pointer hover:bg-green-200">
              Sour Diesel
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
