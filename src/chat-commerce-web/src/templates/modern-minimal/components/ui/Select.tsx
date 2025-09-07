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
        <label className="block text-sm font-semibold text-slate-900">
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
            bg-white border-2 border-slate-400 rounded-lg
            focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-600
            transition-colors duration-200
            disabled:bg-slate-100 disabled:text-slate-600 disabled:cursor-not-allowed
            flex items-center justify-between
          `}
        >
          <span className={selectedOption ? 'text-slate-900 font-medium' : 'text-slate-600'}>
            {selectedOption ? selectedOption.label : placeholder || 'Select option'}
          </span>
          <span className={`transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''} text-slate-700`}>
            ▼
          </span>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-slate-400 rounded-lg shadow-xl z-50">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`
                  w-full px-4 py-3 text-left font-medium text-sm
                  transition-colors duration-200
                  hover:bg-slate-100 focus:bg-slate-100 focus:outline-none
                  ${value === option.value ? 'bg-slate-800 text-white' : 'text-slate-900'}
                  border-b border-slate-200 last:border-b-0
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