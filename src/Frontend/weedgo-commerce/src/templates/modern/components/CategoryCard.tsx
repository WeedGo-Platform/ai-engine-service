import React from 'react';
import { ICategoryCardProps } from '../../types';
import { clsx } from 'clsx';

export const ModernCategoryCard: React.FC<ICategoryCardProps> = ({
  title,
  description,
  icon,
  image,
  onClick,
  variant = 'default',
  className
}) => {
  const variants = {
    default: 'bg-white border-[#D2D2D7]',
    featured: 'bg-[#F5F5F7] border-[#D2D2D7]',
    compact: 'bg-white border-[#E8E8ED]'
  };

  return (
    <div
      onClick={onClick}
      className={clsx(
        'rounded-2xl overflow-hidden cursor-pointer p-6',
        'transition-all duration-200',
        'hover:shadow-lg hover:scale-[1.02]',
        'border',
        'relative',
        variants[variant],
        className
      )}
    >
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent to-black/5 pointer-events-none rounded-2xl" />

      {/* Icon or Image */}
      {icon && (
        <div className="text-4xl mb-4 text-[#1D1D1F]">
          {icon}
        </div>
      )}

      {image && !icon && (
        <div className="h-24 w-24 mb-4 rounded-xl overflow-hidden bg-[#F5F5F7]">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="relative z-10">
        <h3 className="font-semibold text-lg mb-2 text-[#1D1D1F]">
          {title}
        </h3>

        {description && (
          <p className="text-sm text-[#86868B] leading-relaxed">
            {description}
          </p>
        )}

        {/* Subtle arrow indicator */}
        <div className="mt-4 flex items-center text-[#0A84FF]">
          <span className="text-sm font-medium">Learn more</span>
          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  );
};
