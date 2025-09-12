import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          background: 'linear-gradient(135deg, #DC2626, #FCD34D, #16A34A)',
          backgroundSize: '200% 200%',
          animation: !disabled && !loading ? 'rasta-wave 3s ease infinite' : 'none',
          color: '#000',
          border: '2px solid rgba(0, 0, 0, 0.3)',
        };
      case 'secondary':
        return {
          background: 'rgba(252, 211, 77, 0.2)',
          border: '2px solid rgba(252, 211, 77, 0.5)',
          color: '#FCD34D',
        };
      case 'danger':
        return {
          background: 'rgba(220, 38, 38, 0.2)',
          border: '2px solid rgba(220, 38, 38, 0.5)',
          color: '#DC2626',
        };
      case 'success':
        return {
          background: 'rgba(22, 163, 74, 0.2)',
          border: '2px solid rgba(22, 163, 74, 0.5)',
          color: '#16A34A',
        };
      case 'ghost':
        return {
          background: 'transparent',
          border: '2px solid transparent',
          color: '#FCD34D',
        };
      default:
        return {};
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '0.5rem 1rem',
          fontSize: '0.875rem',
        };
      case 'medium':
        return {
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
        };
      case 'large':
        return {
          padding: '1rem 2rem',
          fontSize: '1.125rem',
        };
      default:
        return {};
    }
  };

  const variantStyles = getVariantStyles();
  const sizeStyles = getSizeStyles();
  const isDisabled = disabled || loading;

  return (
    <button
      className={`
        relative overflow-hidden rounded-lg font-semibold
        transition-all hover:scale-105 active:scale-95
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      style={{
        ...variantStyles,
        ...sizeStyles,
        fontFamily: 'Ubuntu, sans-serif',
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 0.6 : 1,
      }}
      disabled={isDisabled}
      {...props}
    >
      {/* Button Content */}
      <div className="relative z-10 flex items-center justify-center space-x-2">
        {/* Loading Spinner */}
        {loading && (
          <div className="flex space-x-1">
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: variant === 'primary' ? '#000' : variantStyles.color,
                animationDelay: '0s',
              }}
            />
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: variant === 'primary' ? '#000' : variantStyles.color,
                animationDelay: '0.2s',
              }}
            />
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: variant === 'primary' ? '#000' : variantStyles.color,
                animationDelay: '0.4s',
              }}
            />
          </div>
        )}

        {/* Icon */}
        {!loading && icon && <span>{icon}</span>}

        {/* Text */}
        {children && <span>{children}</span>}
      </div>

      {/* Hover Effect Overlay */}
      {!isDisabled && (
        <div 
          className="absolute inset-0 opacity-0 hover:opacity-20 transition-opacity"
          style={{
            background: variant === 'primary' 
              ? 'radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%)'
              : 'radial-gradient(circle, rgba(252, 211, 77, 0.3) 0%, transparent 70%)',
          }}
        />
      )}
    </button>
  );
};

export default Button;