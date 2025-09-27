import React from 'react';
import { IInputProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceInput: React.FC<IInputProps> = ({
  value,
  onChange,
  placeholder,
  type = 'text',
  error,
  label,
  required,
  disabled,
  className,
  icon
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-bold text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-600">
            {icon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={clsx(
            'w-full px-4 py-3 rounded-xl border-3',
            'bg-white text-gray-800',
            'placeholder-gray-400',
            'transition-all duration-300',
            'focus:outline-none focus:ring-4',
            icon && 'pl-10',
            error
              ? 'border-red-500 focus:ring-red-200'
              : 'border-green-300 focus:border-green-500 focus:ring-green-200',
            disabled && 'bg-gray-100 cursor-not-allowed',
            className
          )}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-500 font-semibold">{error}</p>
      )}
    </div>
  );
};
