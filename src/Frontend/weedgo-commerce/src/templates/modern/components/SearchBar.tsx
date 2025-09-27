import React, { useState } from 'react';
import { ISearchBarProps } from '../../types';
import { clsx } from 'clsx';

export const ModernSearchBar: React.FC<ISearchBarProps> = ({
  placeholder = 'Search for products, strains, brands...',
  onSearch,
  value: controlledValue,
  onChange,
  className,
  variant = 'default',
  showButton = true
}) => {
  const [localValue, setLocalValue] = useState('');
  const value = controlledValue ?? localValue;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (onChange) {
      onChange(newValue);
    } else {
      setLocalValue(newValue);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(value);
  };

  const variants = {
    default: 'bg-white border-[#D2D2D7]',
    dark: 'bg-[#2C2C2E] border-[#3A3A3C] text-white',
    minimal: 'bg-[#F5F5F7] border-transparent'
  };

  return (
    <form onSubmit={handleSubmit} className={clsx('w-full', className)}>
      <div className="relative flex items-center">
        <div className="relative flex-1">
          {/* Search Icon */}
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#86868B]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Input Field */}
          <input
            type="text"
            value={value}
            onChange={handleChange}
            placeholder={placeholder}
            className={clsx(
              'w-full pl-12 pr-4 py-3',
              'rounded-lg border',
              'text-base font-normal',
              'placeholder-[#86868B]',
              'transition-all duration-200',
              'focus:outline-none focus:border-[#0A84FF] focus:ring-2 focus:ring-[#0A84FF]/20',
              variants[variant as keyof typeof variants]
            )}
          />
        </div>

        {/* Search Button */}
        {showButton && (
          <button
            type="submit"
            className={clsx(
              'ml-3 px-6 py-3',
              'bg-[#0A84FF] hover:bg-[#0073E6]',
              'text-white font-medium',
              'rounded-lg',
              'transition-all duration-200',
              'shadow-sm hover:shadow-md',
              'focus:outline-none focus:ring-2 focus:ring-[#0A84FF]/50'
            )}
          >
            Search
          </button>
        )}
      </div>
    </form>
  );
};
