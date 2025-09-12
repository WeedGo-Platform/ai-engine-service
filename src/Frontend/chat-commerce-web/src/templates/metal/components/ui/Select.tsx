import React from 'react';
import { useTemplate } from '../../../../core/providers/template.provider';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'children' | 'style'> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  style?: React.CSSProperties;
}

const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  options,
  placeholder = 'Select an option',
  className = '',
  style,
  ...props
}) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium mb-1" style={{ color: theme.colors.text }}>
          {label}
        </label>
      )}
      <div className="relative">
        <select
          className={`
            w-full px-4 py-2 pr-10 border rounded-lg
            focus:ring-2 focus:border-transparent
            transition-all duration-200 appearance-none
            ${props.disabled ? 'cursor-not-allowed' : ''}
            ${className}
          `}
          style={{
            backgroundColor: props.disabled ? `${theme.colors.surface}99` : theme.colors.surface,
            borderColor: error ? theme.colors.error : theme.colors.border,
            color: theme.colors.text,
            outlineColor: theme.colors.secondary,
            ...style,
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = theme.colors.secondary;
            e.currentTarget.style.boxShadow = `0 0 0 3px ${theme.colors.secondary}33`;
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = error ? theme.colors.error : theme.colors.border;
            e.currentTarget.style.boxShadow = 'none';
            props.onBlur?.(e);
          }}
          {...props}
        >
          <option value="" disabled>
            {placeholder}
          </option>
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: theme.colors.textSecondary }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {error && (
        <p className="mt-1 text-sm" style={{ color: theme.colors.error }}>{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm" style={{ color: theme.colors.textSecondary }}>{helperText}</p>
      )}
    </div>
  );
};

export default Select;