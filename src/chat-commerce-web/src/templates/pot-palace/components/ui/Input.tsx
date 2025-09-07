import React from 'react';
import { InputProps } from '../../../../core/contracts/template.contracts';

const Input: React.FC<InputProps> = ({
  type = 'text',
  value,
  placeholder,
  label,
  error,
  disabled = false,
  required = false,
  onChange,
  className = '',
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(e.target.value);
  };

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-semibold text-purple-800 mb-2 flex items-center gap-1">
          {label}
          {required && <span className="text-pink-600">*</span>}
          <span className="text-green-600 text-xs">🌿</span>
        </label>
      )}
      <div className="relative">
        <input
          type={type}
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          onChange={handleChange}
          className={`
            w-full px-4 py-3 rounded-xl border-2 font-medium transition-all
            bg-gradient-to-r from-purple-50 to-pink-50
            border-purple-300 focus:border-purple-600 focus:ring-4 focus:ring-purple-200
            placeholder-purple-400 text-purple-800
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''}
            hover:shadow-md focus:shadow-lg
            backdrop-blur-sm
          `}
        />
        {error && (
          <div className="absolute -bottom-6 left-0 text-red-500 text-sm flex items-center gap-1">
            <span>⚠️</span>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Input;