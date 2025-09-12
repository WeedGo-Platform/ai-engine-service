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
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-semibold text-gray-800">
          {label}
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={`
            w-full px-4 py-3 text-left font-normal text-sm
            bg-white border-2 border-gray-300 rounded-lg
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-600
            disabled:bg-gray-100 disabled:text-gray-600 disabled:cursor-not-allowed
            flex items-center justify-between
          `}
        >
          <span className={selectedOption ? 'text-gray-800 font-medium' : 'text-gray-600'}>
            {selectedOption ? selectedOption.label : placeholder || 'Select option'}
          </span>
          <span className={`transform ${isOpen ? 'rotate-180' : ''} text-gray-700`}>
            ▼
          </span>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-gray-300 rounded-lg shadow-xl z-50">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`
                  w-full px-4 py-3 text-left font-medium text-sm
                  hover:bg-gray-100 focus:bg-gray-100 focus:outline-none
                  ${value === option.value ? 'bg-blue-700 text-white' : 'text-gray-800'}
                  border-b border-gray-200 last:border-b-0
                `}
              >
                {option.label}
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