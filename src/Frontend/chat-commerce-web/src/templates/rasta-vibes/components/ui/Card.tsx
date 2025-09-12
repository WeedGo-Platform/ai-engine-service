import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated' | 'gradient';
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  footer,
  variant = 'default',
  className = '',
  onClick,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'bordered':
        return {
          background: 'rgba(26, 26, 26, 0.9)',
          border: '3px solid transparent',
          backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.9), rgba(26, 26, 26, 0.9)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
          backgroundOrigin: 'border-box',
          backgroundClip: 'padding-box, border-box',
        };
      case 'elevated':
        return {
          background: 'rgba(26, 26, 26, 0.95)',
          border: '2px solid rgba(252, 211, 77, 0.2)',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5), 0 0 60px rgba(252, 211, 77, 0.1)',
        };
      case 'gradient':
        return {
          background: 'linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(252, 211, 77, 0.1) 50%, rgba(22, 163, 74, 0.1) 100%)',
          border: '2px solid rgba(252, 211, 77, 0.3)',
        };
      case 'default':
      default:
        return {
          background: 'rgba(26, 26, 26, 0.8)',
          border: '2px solid rgba(252, 211, 77, 0.2)',
        };
    }
  };

  const variantStyles = getVariantStyles();

  return (
    <div
      className={`
        rounded-xl overflow-hidden transition-all
        ${onClick ? 'cursor-pointer hover:scale-105 rasta-hover' : ''}
        ${className}
      `}
      style={{
        ...variantStyles,
        backdropFilter: 'blur(10px)',
      }}
      onClick={onClick}
    >
      {/* Header */}
      {(title || subtitle) && (
        <div 
          className="px-6 py-4"
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderBottom: '1px solid rgba(252, 211, 77, 0.2)',
          }}
        >
          {title && (
            <h3 
              className="text-xl font-bold"
              style={{
                color: '#FCD34D',
                fontFamily: 'Bebas Neue, sans-serif',
                letterSpacing: '1px',
                textShadow: '0 0 10px rgba(252, 211, 77, 0.3)',
              }}
            >
              {title}
            </h3>
          )}
          {subtitle && (
            <p 
              className="text-sm mt-1"
              style={{
                color: '#F3E7C3',
                fontFamily: 'Ubuntu, sans-serif',
                opacity: 0.8,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div 
          className="px-6 py-4"
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderTop: '1px solid rgba(252, 211, 77, 0.2)',
          }}
        >
          {footer}
        </div>
      )}

      {/* Decorative Corner Elements */}
      {variant === 'bordered' && (
        <>
          <div 
            className="absolute top-2 left-2 text-xs opacity-30"
            style={{ color: '#DC2626' }}
          >
            ☮
          </div>
          <div 
            className="absolute top-2 right-2 text-xs opacity-30"
            style={{ color: '#FCD34D' }}
          >
            ♫
          </div>
          <div 
            className="absolute bottom-2 left-2 text-xs opacity-30"
            style={{ color: '#16A34A' }}
          >
            🌿
          </div>
          <div 
            className="absolute bottom-2 right-2 text-xs opacity-30"
            style={{ color: '#FCD34D' }}
          >
            ♥
          </div>
        </>
      )}
    </div>
  );
};

export default Card;