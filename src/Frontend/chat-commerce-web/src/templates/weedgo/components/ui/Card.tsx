import React from 'react';
import { CardProps } from '../../../../core/contracts/template.contracts';

const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  className = '',
}) => {
  const baseClasses = 'bg-white rounded-lg';
  
  const variantClasses = {
    elevated: 'border border-gray-200 shadow-sm hover:shadow-md',
    outlined: 'border-2 border-gray-300 hover:border-gray-400',
    filled: 'bg-gray-50 border border-gray-200',
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <div className="p-6 space-y-4">
        {children}
      </div>
    </div>
  );
};

export default Card;