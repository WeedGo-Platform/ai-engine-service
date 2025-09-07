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
        <label className="block text-sm font-semibold text-cyan-400 font-mono uppercase tracking-wide">
          {label}
        </label>
      )}
      <div className="relative group">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={`
            w-full px-4 py-3 text-left font-mono
            bg-gray-900 border-2 border-cyan-800 
            focus:outline-none focus:border-cyan-400 focus:shadow-lg focus:shadow-cyan-400/20
            transition-all duration-300
            disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
            hover:border-cyan-600 hover:shadow-md hover:shadow-cyan-400/10
            flex items-center justify-between
            group-hover:bg-gray-800/80
            relative z-10
          `}
          style={{
            backgroundImage: 'linear-gradient(45deg, transparent 49%, rgba(6, 182, 212, 0.1) 50%, transparent 51%)',
            backgroundSize: '20px 20px',
          }}
        >
          <span className={selectedOption ? 'text-cyan-100' : 'text-cyan-600'}>
            {selectedOption ? selectedOption.label : placeholder || 'SELECT OPTION'}
          </span>
          <span className={`transform transition-all duration-300 ${isOpen ? 'rotate-180 text-magenta-400' : 'text-cyan-400'} font-bold`}>
            ▼
          </span>
        </button>

        {/* Glowing border effect */}
        <div className="absolute inset-0 border-2 border-transparent bg-gradient-to-r from-cyan-400 via-magenta-400 to-lime-400 opacity-0 group-focus-within:opacity-20 transition-opacity duration-300 pointer-events-none" 
             style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'subtract' }} />

        {/* Corner brackets */}
        <div className="absolute top-0 left-0 w-3 h-3 border-l-2 border-t-2 border-cyan-400 opacity-60"></div>
        <div className="absolute top-0 right-0 w-3 h-3 border-r-2 border-t-2 border-cyan-400 opacity-60"></div>
        <div className="absolute bottom-0 left-0 w-3 h-3 border-l-2 border-b-2 border-cyan-400 opacity-60"></div>
        <div className="absolute bottom-0 right-0 w-3 h-3 border-r-2 border-b-2 border-cyan-400 opacity-60"></div>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border-2 border-cyan-800 shadow-2xl shadow-cyan-400/20 z-50 overflow-hidden">
            {options.map((option, index) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`
                  w-full px-4 py-3 text-left font-mono
                  transition-all duration-200
                  hover:bg-cyan-900/50 focus:bg-cyan-900/50 focus:outline-none
                  ${value === option.value ? 'bg-gradient-to-r from-cyan-800 to-magenta-800 text-cyan-100 shadow-inner' : 'text-cyan-300'}
                  ${index !== options.length - 1 ? 'border-b border-cyan-800/50' : ''}
                  relative
                  hover:shadow-md hover:shadow-cyan-400/10
                  focus:shadow-md focus:shadow-cyan-400/10
                `}
                style={{
                  backgroundImage: value === option.value 
                    ? 'linear-gradient(90deg, transparent 49%, rgba(6, 182, 212, 0.2) 50%, transparent 51%)'
                    : undefined,
                  backgroundSize: '10px 10px',
                }}
              >
                <span className="flex items-center justify-between">
                  {option.label}
                  {value === option.value && <span className="text-lime-400 animate-pulse">◉</span>}
                </span>
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