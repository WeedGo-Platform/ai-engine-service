import React from 'react';
import { ICategoryCardProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceCategoryCard: React.FC<ICategoryCardProps> = ({
  title,
  description,
  icon,
  image,
  onClick,
  variant = 'default',
  className
}) => {
  const variants = {
    default: 'bg-[#FB923C] border-4 border-[#84CC16] text-white',
    featured: 'bg-[#A855F7] border-4 border-[#84CC16] text-white',
    compact: 'bg-[#84CC16] border-4 border-[#FB923C] text-white'
  };

  return (
    <div
      onClick={onClick}
      className={clsx(
        'rounded-3xl overflow-hidden cursor-pointer p-8',
        'transform transition-all duration-300',
        'hover:scale-110 hover:rotate-2 hover:shadow-2xl',
        'relative',
        variants[variant],
        className
      )}
    >
      {/* Fun background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="w-full h-full"
          style={{
            backgroundImage: `repeating-linear-gradient(-45deg, transparent 0px, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 20px)`
          }}
        />
      </div>

      {/* Icon or Image */}
      {icon && (
        <div className="text-6xl mb-4 animate-bounce">
          {icon}
        </div>
      )}

      {image && !icon && (
        <div className="h-32 w-32 mx-auto mb-4 rounded-full overflow-hidden border-4 border-white">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="relative z-10">
        <h3 className="font-black text-2xl mb-3 uppercase tracking-wider drop-shadow-lg">
          {title}
        </h3>

        {description && (
          <p className="text-lg font-bold opacity-95">
            {description}
          </p>
        )}

        {/* Fun decorative element */}
        <div className="mt-4 flex justify-center gap-2">
          <span className="text-2xl">⭐</span>
          <span className="text-2xl">⭐</span>
          <span className="text-2xl">⭐</span>
        </div>
      </div>

      {/* Floating emoji decorations */}
      <div className="absolute -top-2 -right-2 text-3xl animate-spin" style={{ animationDuration: '3s' }}>
        ✨
      </div>
      <div className="absolute -bottom-2 -left-2 text-3xl animate-pulse">
        🌟
      </div>
    </div>
  );
};
