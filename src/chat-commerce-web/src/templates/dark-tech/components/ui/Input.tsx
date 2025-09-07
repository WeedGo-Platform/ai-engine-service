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
        <label className="block text-sm font-semibold text-cyan-400 font-mono uppercase tracking-wide">
          {label}
          {required && <span className="text-magenta-400 ml-1 animate-pulse">*</span>}
        </label>
      )}
      <div className="relative group">
        <input
          type={type}
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          onChange={handleChange}
          className={`
            w-full px-4 py-3 text-cyan-100 placeholder-cyan-600
            bg-gray-900 border-2 border-cyan-800 
            focus:outline-none focus:border-cyan-400 focus:shadow-lg focus:shadow-cyan-400/20
            transition-all duration-300 font-mono
            disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
            ${error ? 'border-red-500 focus:border-red-400 focus:shadow-red-400/20' : ''}
            hover:border-cyan-600 hover:shadow-md hover:shadow-cyan-400/10
            group-hover:bg-gray-800/80
            relative z-10
          `}
          style={{
            backgroundImage: 'linear-gradient(45deg, transparent 49%, rgba(6, 182, 212, 0.1) 50%, transparent 51%)',
            backgroundSize: '20px 20px',
            animation: error ? 'glitch 0.3s ease-in-out' : undefined,
          }}
        />
        
        {/* Glowing border effect */}
        <div className="absolute inset-0 border-2 border-transparent bg-gradient-to-r from-cyan-400 via-magenta-400 to-lime-400 opacity-0 group-focus-within:opacity-20 transition-opacity duration-300 pointer-events-none" 
             style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'subtract' }} />
        
        {error && (
          <p className="mt-2 text-sm text-red-400 font-mono flex items-center gap-2">
            <span className="animate-pulse">⚠</span>
            {error}
          </p>
        )}

        {/* Corner brackets */}
        <div className="absolute top-0 left-0 w-3 h-3 border-l-2 border-t-2 border-cyan-400 opacity-60"></div>
        <div className="absolute top-0 right-0 w-3 h-3 border-r-2 border-t-2 border-cyan-400 opacity-60"></div>
        <div className="absolute bottom-0 left-0 w-3 h-3 border-l-2 border-b-2 border-cyan-400 opacity-60"></div>
        <div className="absolute bottom-0 right-0 w-3 h-3 border-r-2 border-b-2 border-cyan-400 opacity-60"></div>
      </div>
    </div>
  );
};

export default Input;