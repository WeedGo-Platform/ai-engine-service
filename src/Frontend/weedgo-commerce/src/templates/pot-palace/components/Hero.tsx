import React from 'react';
import { IHeroProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceHero: React.FC<IHeroProps> = ({
  title = 'Premium Cannabis, Delivered',
  subtitle = 'Experience quality and convenience with our curated selection',
  backgroundImage,
  primaryButton,
  secondaryButton,
  className
}) => {
  return (
    <div className={clsx(
      'relative min-h-[600px] flex items-center justify-center',
      'bg-gradient-to-br from-[#2D5F3F] via-[#3B7A55] to-[#2D5F3F]',
      'overflow-hidden',
      className
    )}>
      {/* Subtle organic pattern overlay */}
      <div className="absolute inset-0 opacity-5">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="leaf-pattern" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M50 10 Q40 30 50 50 Q60 30 50 10" fill="white" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#leaf-pattern)" />
        </svg>
      </div>

      {backgroundImage && (
        <img
          src={backgroundImage}
          alt=""
          className="absolute inset-0 w-full h-full object-cover opacity-15 mix-blend-overlay"
        />
      )}

      {/* Subtle accent shapes */}
      <div className="absolute top-20 right-20 w-64 h-64 bg-[#C9A86A] rounded-full opacity-10 blur-3xl" />
      <div className="absolute bottom-20 left-20 w-80 h-80 bg-[#7A9E88] rounded-full opacity-10 blur-3xl" />

      <div className="relative z-10 text-center px-4 max-w-4xl mx-auto py-20">
        {/* Clean, modern title */}
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-display font-bold text-white mb-6 leading-tight tracking-tight">
          {title}
        </h1>

        {subtitle && (
          <p className="text-lg md:text-xl text-white/90 mb-12 max-w-2xl mx-auto font-light leading-relaxed">
            {subtitle}
          </p>
        )}

        {/* Clean call-to-action buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          {primaryButton && (
            <a
              href={primaryButton.href}
              onClick={primaryButton.onClick}
              className="group inline-flex items-center px-8 py-4 bg-white text-[#2D5F3F] font-semibold text-base rounded-lg hover:bg-[#C9A86A] hover:text-white transition-all duration-300 shadow-lg hover:shadow-xl transform hover:translate-y-[-2px]"
            >
              <span>{primaryButton.text}</span>
              <svg className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
          )}

          {secondaryButton && (
            <a
              href={secondaryButton.href}
              onClick={secondaryButton.onClick}
              className="inline-flex items-center px-8 py-4 bg-transparent border-2 border-white text-white font-semibold text-base rounded-lg hover:bg-white hover:text-[#2D5F3F] transition-all duration-300"
            >
              <span>{secondaryButton.text}</span>
            </a>
          )}
        </div>

        {/* Trust indicators */}
        <div className="mt-16 flex flex-wrap justify-center gap-8 text-white/80 text-sm">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Licensed & Legal</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
              <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z" />
            </svg>
            <span>Same-Day Delivery</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Premium Quality</span>
          </div>
        </div>
      </div>

      {/* Smooth bottom transition */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#FAFAF8] to-transparent" />
    </div>
  );
};
