import React, { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>((
  {
    label,
    error,
    icon,
    fullWidth = false,
    className = '',
    ...props
  },
  ref
) => {
  return (
    <div className={`${fullWidth ? 'w-full' : ''}`}>
      {/* Label */}
      {label && (
        <label 
          className="block text-sm font-medium mb-2"
          style={{ color: '#FCD34D', fontFamily: 'Ubuntu, sans-serif' }}
        >
          {label}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        {/* Icon */}
        {icon && (
          <div 
            className="absolute left-3 top-1/2 transform -translate-y-1/2"
            style={{ color: '#FCD34D' }}
          >
            {icon}
          </div>
        )}

        {/* Input Field */}
        <input
          ref={ref}
          className={`
            w-full px-4 py-3 rounded-lg outline-none transition-all
            ${icon ? 'pl-10' : ''}
            ${error ? 'pr-10' : ''}
            ${className}
          `}
          style={{
            background: 'rgba(0, 0, 0, 0.5)',
            border: `2px solid ${error ? 'rgba(220, 38, 38, 0.5)' : 'rgba(252, 211, 77, 0.3)'}`,
            color: '#F3E7C3',
            fontFamily: 'Ubuntu, sans-serif',
          }}
          onFocus={(e) => {
            if (!error) {
              e.currentTarget.style.borderColor = 'rgba(252, 211, 77, 0.6)';
              e.currentTarget.style.boxShadow = '0 0 20px rgba(252, 211, 77, 0.2)';
            }
          }}
          onBlur={(e) => {
            if (!error) {
              e.currentTarget.style.borderColor = 'rgba(252, 211, 77, 0.3)';
              e.currentTarget.style.boxShadow = 'none';
            }
          }}
          {...props}
        />

        {/* Error Icon */}
        {error && (
          <div 
            className="absolute right-3 top-1/2 transform -translate-y-1/2"
            style={{ color: '#DC2626' }}
          >
            ⚠️
          </div>
        )}
      </div>

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
});

Input.displayName = 'Input';

export default Input;