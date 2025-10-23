import React from 'react';
import { ICategoryCardProps, ICategory } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceCategoryCard: React.FC<ICategoryCardProps> = ({
  category,
  title,
  description,
  icon,
  image,
  onClick,
  variant = 'default',
  className
}) => {
  const variants = {
    default: 'bg-white border border-[#E5E7EB] hover:border-[#2D5F3F]',
    featured: 'bg-gradient-to-br from-[#2D5F3F]/5 to-[#7A9E88]/5 border border-[#2D5F3F]',
    compact: 'bg-white border border-[#E5E7EB] hover:border-[#7A9E88]'
  };

  // Use category if provided, otherwise construct from props
  const categoryData: ICategory = category || {
    id: '',
    name: title || '',
    description: description || '',
    image: image || '',
    slug: '',
    productCount: 0
  };

  return (
    <div
      onClick={onClick ? () => onClick(categoryData) : undefined}
      className={clsx(
        'rounded-xl overflow-hidden cursor-pointer p-8',
        'transition-all duration-300',
        'hover:shadow-lg transform hover:translate-y-[-4px]',
        'relative group',
        variants[variant],
        className
      )}
    >
      {/* Subtle accent line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#2D5F3F] to-[#7A9E88] opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Icon or Image */}
      {icon && (
        <div className="text-5xl mb-4 text-[#2D5F3F] flex justify-center">
          {icon}
        </div>
      )}

      {(categoryData.image || image) && !icon && (
        <div className="h-20 w-20 mx-auto mb-4 rounded-lg overflow-hidden bg-[#2D5F3F]/5">
          <img
            src={categoryData.image || image}
            alt={categoryData.name || title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="text-center">
        <h3 className="font-semibold text-xl mb-2 text-[#1F2937] group-hover:text-[#2D5F3F] transition-colors">
          {categoryData.name || title}
        </h3>

        {(categoryData.description || description) && (
          <p className="text-sm text-[#6B7280] leading-relaxed">
            {categoryData.description || description}
          </p>
        )}

        {/* Clean arrow indicator */}
        <div className="mt-4 flex justify-center">
          <svg
            className="w-5 h-5 text-[#2D5F3F] opacity-0 group-hover:opacity-100 transform translate-x-[-4px] group-hover:translate-x-0 transition-all"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>
      </div>
    </div>
  );
};
