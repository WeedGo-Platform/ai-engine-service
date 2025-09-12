import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'premium';
  size?: 'small' | 'medium' | 'large';
  icon?: React.ReactNode;
  animated?: boolean;
  onClick?: () => void;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'medium',
  icon,
  animated = false,
  onClick,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return {
          background: 'rgba(22, 163, 74, 0.2)',
          border: '1px solid rgba(22, 163, 74, 0.5)',
          color: '#16A34A',
        };
      case 'warning':
        return {
          background: 'rgba(252, 211, 77, 0.2)',
          border: '1px solid rgba(252, 211, 77, 0.5)',
          color: '#FCD34D',
        };
      case 'danger':
        return {
          background: 'rgba(220, 38, 38, 0.2)',
          border: '1px solid rgba(220, 38, 38, 0.5)',
          color: '#DC2626',
        };
      case 'info':
        return {
          background: 'rgba(59, 130, 246, 0.2)',
          border: '1px solid rgba(59, 130, 246, 0.5)',
          color: '#3B82F6',
        };
      case 'premium':
        return {
          background: 'linear-gradient(135deg, rgba(220, 38, 38, 0.2), rgba(252, 211, 77, 0.2), rgba(22, 163, 74, 0.2))',
          border: '1px solid transparent',
          borderImage: 'linear-gradient(135deg, #DC2626, #FCD34D, #16A34A) 1',
          color: '#FCD34D',
        };
      case 'default':
      default:
        return {
          background: 'rgba(100, 100, 100, 0.2)',
          border: '1px solid rgba(100, 100, 100, 0.5)',
          color: '#F3E7C3',
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '0.125rem 0.5rem',
          fontSize: '0.75rem',
        };
      case 'medium':
        return {
          padding: '0.25rem 0.75rem',
          fontSize: '0.875rem',
        };
      case 'large':
        return {
          padding: '0.375rem 1rem',
          fontSize: '1rem',
        };
      default:
        return {};
    }
  };

  const variantStyles = getVariantStyles();
  const sizeStyles = getSizeStyles();

  return (
    <span
      className={`
        inline-flex items-center space-x-1 rounded-full font-medium transition-all
        ${onClick ? 'cursor-pointer hover:scale-105' : ''}
        ${animated ? (variant === 'premium' ? 'rasta-wave' : 'reggae-pulse') : ''}
      `}
      style={{
        ...variantStyles,
        ...sizeStyles,
        fontFamily: 'Ubuntu, sans-serif',
        boxShadow: animated ? '0 0 20px rgba(252, 211, 77, 0.3)' : 'none',
      }}
      onClick={onClick}
    >
      {/* Icon */}
      {icon && <span className="flex-shrink-0">{icon}</span>}
      
      {/* Content */}
      <span>{children}</span>

      {/* Premium Badge Animation */}
      {variant === 'premium' && animated && (
        <span className="absolute inset-0 rounded-full opacity-30">
          <span 
            className="absolute inset-0 rounded-full"
            style={{
              background: 'linear-gradient(135deg, #DC2626, #FCD34D, #16A34A)',
              animation: 'rasta-wave 3s ease infinite',
            }}
          />
        </span>
      )}
    </span>
  );
};

export default Badge;