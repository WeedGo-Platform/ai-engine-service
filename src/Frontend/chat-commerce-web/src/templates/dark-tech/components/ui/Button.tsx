import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  loading = false,
  className = '', 
  ...props 
}) => {
  const baseClasses = 'tech-button font-mono transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#00FF88]';
  
  const sizeClasses = {
    sm: 'px-4 py-1 text-xs',
    md: 'px-6 py-2 text-sm',
    lg: 'px-8 py-3 text-base'
  };
  
  const variantClasses = {
    primary: 'bg-[#00FF88] text-[#0A0E1A] hover:bg-[#00CC6A]',
    secondary: 'bg-[#00D4FF] text-[#0A0E1A] hover:bg-[#00B8E6]',
    outline: 'border border-[#00FF88] text-[#00FF88] hover:bg-[#00FF88] hover:text-[#0A0E1A]',
    danger: 'bg-[#FF0066] text-white hover:bg-[#E6005C]'
  };

  return (
    <button
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      disabled={loading}
      {...props}
    >
      {loading ? (
        <div className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{'> '}LOADING...</span>
        </div>
      ) : (
        <>{'> '}{children}</>
      )}
    </button>
  );
};

export default Button;