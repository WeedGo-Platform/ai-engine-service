import React from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';

export interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  linkToHome?: boolean;
  className?: string;
}

/**
 * Logo component for WeedGo brand identity
 * Responsive and theme-aware
 */
export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showText = true,
  linkToHome = true,
  className
}) => {
  const sizeClasses = {
    sm: {
      icon: 'h-8 w-8',
      text: 'text-xl'
    },
    md: {
      icon: 'h-10 w-10',
      text: 'text-2xl'
    },
    lg: {
      icon: 'h-12 w-12',
      text: 'text-3xl'
    },
    xl: {
      icon: 'h-16 w-16',
      text: 'text-4xl'
    }
  };

  const logoContent = (
    <div className={clsx('flex items-center space-x-2', className)}>
      <div
        className={clsx(
          sizeClasses[size].icon,
          'bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center shadow-lg transform transition-transform hover:scale-105'
        )}
      >
        <span className="text-white font-bold text-xl">W</span>
      </div>
      {showText && (
        <span
          className={clsx(
            sizeClasses[size].text,
            'font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent dark:from-primary-400 dark:to-primary-600'
          )}
        >
          WeedGo
        </span>
      )}
    </div>
  );

  if (linkToHome) {
    return (
      <Link to="/" className="inline-block" aria-label="WeedGo Home">
        {logoContent}
      </Link>
    );
  }

  return logoContent;
};

export default Logo;