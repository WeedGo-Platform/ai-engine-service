import React, { useState } from 'react';
import { SelectProps } from '../../../../core/contracts/template.contracts';

const Select: React.FC<SelectProps> = ({
  options,
  value,
  placeholder,
  label,
  disabled = false,
  onChange,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const selectedOption = options.find(opt => opt.value === value);

  const handleSelect = (optionValue: string) => {
    onChange?.(optionValue);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-semibold text-purple-800 mb-2 flex items-center gap-1">
          {label}
          <span className="text-green-600 text-xs">🌿</span>
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={`
            w-full px-4 py-3 rounded-xl border-2 font-medium transition-all text-left flex items-center justify-between
            bg-gradient-to-r from-purple-50 to-pink-50
            border-purple-300 focus:border-purple-600 focus:ring-4 focus:ring-purple-200
            text-purple-800
            disabled:opacity-50 disabled:cursor-not-allowed
            hover:shadow-md focus:shadow-lg
            backdrop-blur-sm
          `}
        >
          <span className={selectedOption ? 'text-purple-800' : 'text-purple-400'}>
            {selectedOption ? selectedOption.label : placeholder || 'Select an option'}
          </span>
          <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''} text-purple-600`}>
            🍃
          </span>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-purple-300 rounded-xl shadow-lg overflow-hidden z-50 backdrop-blur-sm">
            {options.map((option, index) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`
                  w-full px-4 py-3 text-left transition-all font-medium
                  hover:bg-gradient-to-r hover:from-purple-100 hover:to-pink-100
                  focus:bg-gradient-to-r focus:from-purple-100 focus:to-pink-100
                  ${value === option.value ? 'bg-gradient-to-r from-purple-200 to-pink-200 text-purple-800' : 'text-purple-700'}
                  ${index !== options.length - 1 ? 'border-b border-purple-200' : ''}
                  flex items-center justify-between
                `}
              >
                {option.label}
                {value === option.value && <span className="text-green-600">✨</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default Select;