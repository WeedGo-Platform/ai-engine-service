import React from 'react';
import { CardProps } from '../../../../core/contracts/template.contracts';

const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  className = '',
}) => {
  const baseClasses = 'relative bg-gray-900 transition-all duration-500 overflow-hidden group';
  
  const variantClasses = {
    elevated: `
      border-2 border-cyan-800 shadow-lg shadow-cyan-400/20
      hover:shadow-xl hover:shadow-cyan-400/30 hover:border-cyan-600
    `,
    outlined: `
      border-4 border-cyan-700 hover:border-cyan-500
      bg-gray-800/50 backdrop-blur-sm
    `,
    filled: `
      bg-gradient-to-br from-gray-800 to-gray-900 
      border-2 border-magenta-800 shadow-inner
    `,
  };

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={{
        backgroundImage: 'linear-gradient(45deg, transparent 49%, rgba(6, 182, 212, 0.03) 50%, transparent 51%)',
        backgroundSize: '20px 20px',
      }}
    >
      {/* Glowing border effect */}
      <div className="absolute inset-0 border-2 border-transparent bg-gradient-to-r from-cyan-400 via-magenta-400 to-lime-400 opacity-0 group-hover:opacity-10 transition-opacity duration-500" 
           style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'subtract' }} />

      {/* Corner brackets */}
      <div className="absolute top-2 left-2 w-4 h-4 border-l-2 border-t-2 border-cyan-400 opacity-40 group-hover:opacity-70 transition-opacity duration-300"></div>
      <div className="absolute top-2 right-2 w-4 h-4 border-r-2 border-t-2 border-cyan-400 opacity-40 group-hover:opacity-70 transition-opacity duration-300"></div>
      <div className="absolute bottom-2 left-2 w-4 h-4 border-l-2 border-b-2 border-cyan-400 opacity-40 group-hover:opacity-70 transition-opacity duration-300"></div>
      <div className="absolute bottom-2 right-2 w-4 h-4 border-r-2 border-b-2 border-cyan-400 opacity-40 group-hover:opacity-70 transition-opacity duration-300"></div>

      {/* Content */}
      <div className="relative z-10 p-6">
        {children}
      </div>

      {/* Scanning line effect */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-0 group-hover:opacity-60 transition-opacity duration-500 group-hover:animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-magenta-400 to-transparent opacity-0 group-hover:opacity-60 transition-opacity duration-500 group-hover:animate-pulse" style={{ animationDelay: '1s' }}></div>
      
      {/* Side lights */}
      <div className="absolute left-0 top-1/4 w-0.5 h-1/2 bg-gradient-to-b from-transparent via-cyan-400/30 to-transparent opacity-0 group-hover:opacity-60 transition-opacity duration-500 group-hover:animate-pulse" style={{ animationDelay: '0.5s' }}></div>
      <div className="absolute right-0 top-1/3 w-0.5 h-1/3 bg-gradient-to-b from-transparent via-lime-400/30 to-transparent opacity-0 group-hover:opacity-60 transition-opacity duration-500 group-hover:animate-pulse" style={{ animationDelay: '1.5s' }}></div>

      {/* Matrix-style decorative elements */}
      <div className="absolute top-4 right-4 text-cyan-400/20 font-mono text-xs group-hover:text-cyan-400/40 transition-colors duration-300">
        {`[${Math.floor(Math.random() * 999).toString().padStart(3, '0')}]`}
      </div>
      <div className="absolute bottom-4 left-4 text-magenta-400/20 font-mono text-xs group-hover:text-magenta-400/40 transition-colors duration-300">
        {'</>'}
      </div>
    </div>
  );
};

export default Card;