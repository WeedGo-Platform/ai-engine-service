import React, { useState, useRef, useEffect } from 'react';

interface SelectOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  fullWidth?: boolean;
  disabled?: boolean;
}

const Select: React.FC<SelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  label,
  error,
  fullWidth = false,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<SelectOption | null>(
    options.find(opt => opt.value === value) || null
  );
  const selectRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: SelectOption) => {
    setSelectedOption(option);
    onChange?.(option.value);
    setIsOpen(false);
  };

  return (
    <div ref={selectRef} className={`relative ${fullWidth ? 'w-full' : ''}`}>
      {/* Label */}
      {label && (
        <label 
          className="block text-sm font-medium mb-2"
          style={{ color: '#FCD34D', fontFamily: 'Ubuntu, sans-serif' }}
        >
          {label}
        </label>
      )}

      {/* Select Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className="w-full px-4 py-3 rounded-lg text-left flex items-center justify-between transition-all"
        style={{
          background: 'rgba(0, 0, 0, 0.5)',
          border: `2px solid ${error ? 'rgba(220, 38, 38, 0.5)' : isOpen ? 'rgba(252, 211, 77, 0.6)' : 'rgba(252, 211, 77, 0.3)'}`,
          color: selectedOption ? '#F3E7C3' : '#F3E7C3AA',
          fontFamily: 'Ubuntu, sans-serif',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.5 : 1,
          boxShadow: isOpen ? '0 0 20px rgba(252, 211, 77, 0.2)' : 'none',
        }}
        disabled={disabled}
      >
        <span className="flex items-center space-x-2">
          {selectedOption?.icon && <span>{selectedOption.icon}</span>}
          <span>{selectedOption ? selectedOption.label : placeholder}</span>
        </span>
        
        <svg 
          className="w-5 h-5 transition-transform"
          fill="currentColor" 
          viewBox="0 0 24 24"
          style={{
            color: '#FCD34D',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        >
          <path d="M7 10l5 5 5-5z" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          className="absolute z-50 w-full mt-2 rounded-lg overflow-hidden smooth-fade-in"
          style={{
            background: 'rgba(26, 26, 26, 0.98)',
            border: '2px solid rgba(252, 211, 77, 0.5)',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5), 0 0 40px rgba(252, 211, 77, 0.2)',
            maxHeight: '300px',
            overflowY: 'auto',
          }}
        >
          {/* Decorative Top Bar */}
          <div className="h-1 flex">
            <div className="flex-1" style={{ background: '#DC2626' }} />
            <div className="flex-1" style={{ background: '#FCD34D' }} />
            <div className="flex-1" style={{ background: '#16A34A' }} />
          </div>

          {/* Options */}
          {options.map((option, index) => (
            <button
              key={option.value}
              onClick={() => handleSelect(option)}
              className="w-full px-4 py-3 text-left flex items-center space-x-2 transition-all hover:bg-opacity-20"
              style={{
                background: selectedOption?.value === option.value 
                  ? 'rgba(252, 211, 77, 0.2)' 
                  : 'transparent',
                borderBottom: index < options.length - 1 ? '1px solid rgba(252, 211, 77, 0.1)' : 'none',
                color: '#F3E7C3',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(252, 211, 77, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = selectedOption?.value === option.value 
                  ? 'rgba(252, 211, 77, 0.2)' 
                  : 'transparent';
              }}
            >
              {option.icon && <span>{option.icon}</span>}
              <span>{option.label}</span>
              
              {selectedOption?.value === option.value && (
                <span className="ml-auto" style={{ color: '#16A34A' }}>
                  ✓
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <p 
          className="mt-1 text-sm"
          style={{ color: '#DC2626' }}
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default Select;