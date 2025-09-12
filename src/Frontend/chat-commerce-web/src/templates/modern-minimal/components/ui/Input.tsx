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
        <label className="block text-sm font-semibold text-slate-900">
          {label}
          {required && <span className="text-slate-600 ml-1">*</span>}
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
            w-full px-4 py-3 text-slate-900 placeholder-slate-500
            bg-white border-2 border-slate-400 rounded-lg
            focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-600
            transition-colors duration-200
            disabled:bg-slate-100 disabled:text-slate-600 disabled:cursor-not-allowed
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