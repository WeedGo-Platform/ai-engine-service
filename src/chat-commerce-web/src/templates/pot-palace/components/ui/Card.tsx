import React from 'react';
import { CardProps } from '../../../../core/contracts/template.contracts';

const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  className = '',
}) => {
  const baseClasses = 'rounded-2xl transition-all duration-300 relative overflow-hidden';
  
  const variantClasses = {
    elevated: `
      bg-gradient-to-br from-white via-purple-50 to-pink-50 
      shadow-lg hover:shadow-xl border border-purple-200
      backdrop-blur-sm
    `,
    outlined: `
      bg-gradient-to-br from-white/80 to-purple-50/80 
      border-2 border-purple-300 hover:border-purple-400
      backdrop-blur-sm
    `,
    filled: `
      bg-gradient-to-br from-purple-100 to-pink-100 
      border border-purple-300
      backdrop-blur-sm
    `,
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className} group`}>
      {/* Content */}
      <div className="relative z-10 p-6">
        {children}
      </div>

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-purple-200/30 to-transparent rounded-bl-full opacity-50 group-hover:opacity-70 transition-opacity"></div>
      <div className="absolute bottom-0 left-0 w-16 h-16 bg-gradient-to-tr from-pink-200/30 to-transparent rounded-tr-full opacity-50 group-hover:opacity-70 transition-opacity"></div>
      
      {/* Cannabis leaf subtle pattern */}
      <div className="absolute top-4 left-4 text-green-200/20 text-sm group-hover:text-green-200/30 transition-colors">
        🌿
      </div>
      <div className="absolute bottom-4 right-4 text-purple-200/20 text-xs group-hover:text-purple-200/30 transition-colors">
        ✨
      </div>
    </div>
  );
};

export default Card;