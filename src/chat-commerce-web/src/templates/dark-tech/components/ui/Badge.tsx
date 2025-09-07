import React from 'react';
import { BadgeProps } from '../../../../core/contracts/template.contracts';

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const baseClasses = 'inline-flex items-center gap-2 font-mono font-bold uppercase tracking-wider transition-all duration-300 relative overflow-hidden';
  
  const variantClasses = {
    primary: 'bg-cyan-900 text-cyan-100 border-2 border-cyan-600 shadow-lg shadow-cyan-400/30',
    secondary: 'bg-magenta-900 text-magenta-100 border-2 border-magenta-600 shadow-lg shadow-magenta-400/30',
    success: 'bg-lime-900 text-lime-100 border-2 border-lime-600 shadow-lg shadow-lime-400/30',
    warning: 'bg-yellow-900 text-yellow-100 border-2 border-yellow-600 shadow-lg shadow-yellow-400/30',
    danger: 'bg-red-900 text-red-100 border-2 border-red-600 shadow-lg shadow-red-400/30',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const getIcon = (variant: string) => {
    switch (variant) {
      case 'primary': return '◉';
      case 'secondary': return '◈';
      case 'success': return '✓';
      case 'warning': return '⚠';
      case 'danger': return '✕';
      default: return '◦';
    }
  };

  const getGlowColor = (variant: string) => {
    switch (variant) {
      case 'primary': return 'cyan';
      case 'secondary': return 'magenta';
      case 'success': return 'lime';
      case 'warning': return 'yellow';
      case 'danger': return 'red';
      default: return 'cyan';
    }
  };

  const glowColor = getGlowColor(variant);

  return (
    <span 
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className} group hover:scale-105 hover:shadow-xl`}
      style={{
        backgroundImage: 'linear-gradient(45deg, transparent 49%, rgba(255, 255, 255, 0.05) 50%, transparent 51%)',
        backgroundSize: '8px 8px',
      }}
    >
      {/* Glowing border effect */}
      <div 
        className={`absolute inset-0 border-2 border-transparent bg-gradient-to-r from-${glowColor}-400 via-${glowColor}-300 to-${glowColor}-400 opacity-0 group-hover:opacity-30 transition-opacity duration-300`}
        style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'subtract' }} 
      />

      {/* Corner brackets */}
      <div className={`absolute top-0 left-0 w-1.5 h-1.5 border-l border-t border-${glowColor}-400 opacity-60`}></div>
      <div className={`absolute top-0 right-0 w-1.5 h-1.5 border-r border-t border-${glowColor}-400 opacity-60`}></div>
      <div className={`absolute bottom-0 left-0 w-1.5 h-1.5 border-l border-b border-${glowColor}-400 opacity-60`}></div>
      <div className={`absolute bottom-0 right-0 w-1.5 h-1.5 border-r border-b border-${glowColor}-400 opacity-60`}></div>

      {/* Icon */}
      <span className="relative z-10 group-hover:animate-pulse">
        {getIcon(variant)}
      </span>
      
      {/* Content */}
      <span className="relative z-10">
        {children}
      </span>

      {/* Scanning line */}
      <div className={`absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-${glowColor}-400 to-transparent opacity-0 group-hover:opacity-70 group-hover:animate-pulse transition-opacity duration-300`}></div>
    </span>
  );
};

export default Badge;