import React from 'react';
import { useTemplate } from '../../../../core/providers/template.provider';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  border?: boolean;
  hoverable?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  shadow = 'md',
  border = false,
  hoverable = false,
  onClick,
  style,
}) => {
  const template = useTemplate();
  const theme = template.getTheme();
  
  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };
  
  const shadows = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  };
  
  const baseStyles = 'rounded-xl overflow-hidden transition-all duration-300';
  const clickable = onClick ? 'cursor-pointer' : '';
  
  return (
    <div
      className={`${baseStyles} ${paddings[padding]} ${shadows[shadow]} ${clickable} ${className}`}
      style={{
        backgroundColor: theme.colors.surface,
        borderColor: border ? theme.colors.border : 'transparent',
        borderWidth: border ? '1px' : '0',
        borderStyle: 'solid',
        ...style,
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = theme.shadows.xl;
        }
      }}
      onMouseLeave={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = theme.shadows[shadow];
        }
      }}
    >
      {children}
    </div>
  );
};

export default Card;