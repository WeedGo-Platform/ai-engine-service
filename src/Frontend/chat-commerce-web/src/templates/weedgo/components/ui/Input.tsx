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
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-semibold text-gray-800">
          {label}
          {required && <span className="text-gray-600 ml-1">*</span>}
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
            w-full px-4 py-3 text-gray-800 placeholder-gray-500
            bg-white border-2 border-gray-300 rounded-lg
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-600
            disabled:bg-gray-100 disabled:text-gray-600 disabled:cursor-not-allowed
            ${error ? 'border-red-500 focus:border-red-500' : ''}
            font-normal text-sm
          `}
        />
        {error && (
          <p className="mt-1 text-sm text-red-600 font-mono">
            {error}
          </p>
        )}
      </div>
    </div>
  );
};

export default Input;