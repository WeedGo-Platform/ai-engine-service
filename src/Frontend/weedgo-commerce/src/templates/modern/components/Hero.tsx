import React from 'react';
import { IHeroProps } from '../../types';
import { clsx } from 'clsx';

export const ModernHero: React.FC<IHeroProps> = ({
  title = 'Premium Cannabis Collection',
  subtitle = 'Curated selection of the finest products, delivered with care',
  backgroundImage,
  primaryButton,
  secondaryButton,
  className
}) => {
  return (
    <div className={clsx(
      'relative min-h-[600px] flex items-center justify-center',
      'bg-gradient-to-b from-[#1D1D1F] to-[#2C2C2E]', // Space gray gradient
      'overflow-hidden',
      className
    )}>
      {/* Subtle grid pattern overlay */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(#86868B 1px, transparent 1px), linear-gradient(90deg, #86868B 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {backgroundImage && (
        <img
          src={backgroundImage}
          alt=""
          className="absolute inset-0 w-full h-full object-cover opacity-15"
        />
      )}

      <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
        {/* Clean, minimal title */}
        <h1 className="text-5xl md:text-6xl font-light text-white mb-6 tracking-tight">
          {title}
        </h1>

        {subtitle && (
          <p className="text-xl md:text-2xl text-[#86868B] mb-12 font-light tracking-wide">
            {subtitle}
          </p>
        )}

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          {primaryButton && (
            <a
              href={primaryButton.href}
              onClick={primaryButton.onClick}
              className="inline-flex items-center px-8 py-3 bg-[#0A84FF] hover:bg-[#0073E6] text-white font-medium text-base rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
            >
              {primaryButton.text}
              <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          )}

          {secondaryButton && (
            <a
              href={secondaryButton.href}
              onClick={secondaryButton.onClick}
              className="inline-flex items-center px-8 py-3 bg-white/10 backdrop-blur hover:bg-white/15 text-white font-medium text-base rounded-lg transition-all duration-200 border border-white/20"
            >
              {secondaryButton.text}
            </a>
          )}
        </div>
      </div>

      {/* Subtle decorative elements */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#86868B] to-transparent opacity-30" />
    </div>
  );
};
