import React from 'react';
import { IHeroProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceHero: React.FC<IHeroProps> = ({
  title = 'Welcome to Pot Palace',
  subtitle = 'Your Premium Cannabis Destination 🔥',
  backgroundImage,
  primaryButton,
  secondaryButton,
  className
}) => {
  return (
    <div className={clsx(
      'relative min-h-[700px] flex items-center justify-center',
      'bg-[#84CC16]', // Solid lime green background
      'overflow-hidden',
      className
    )}>
      {/* Fun pattern overlay */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0"
          style={{
            backgroundImage: `repeating-linear-gradient(45deg, #FB923C 0px, #FB923C 20px, transparent 20px, transparent 40px)`,
          }}
        />
      </div>

      {backgroundImage && (
        <img
          src={backgroundImage}
          alt=""
          className="absolute inset-0 w-full h-full object-cover opacity-20"
        />
      )}

      <div className="relative z-10 text-center px-4 max-w-5xl mx-auto">
        {/* Big, bold title with emojis */}
        <h1 className="text-6xl md:text-8xl font-black text-white mb-6 uppercase tracking-wider drop-shadow-2xl transform hover:scale-105 transition-transform">
          <span className="inline-block animate-bounce">🌿</span>
          <span className="inline-block mx-4">{title}</span>
          <span className="inline-block animate-bounce" style={{ animationDelay: '0.5s' }}>🌿</span>
        </h1>

        {subtitle && (
          <div className="mb-12">
            <p className="text-2xl md:text-3xl text-white font-bold bg-[#FB923C] inline-block px-6 py-3 rounded-full transform rotate-1 shadow-2xl">
              {subtitle}
            </p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
          {primaryButton && (
            <a
              href={primaryButton.href}
              onClick={primaryButton.onClick}
              className="group relative inline-flex items-center px-12 py-6 bg-[#FB923C] hover:bg-[#F97316] text-white font-black text-xl uppercase rounded-full transform hover:scale-110 hover:rotate-2 transition-all duration-300 shadow-2xl border-4 border-white"
            >
              <span className="mr-2 text-2xl">🚀</span>
              <span>{primaryButton.text}</span>
              <span className="ml-2 text-2xl">🔥</span>
              {/* Pulse effect */}
              <div className="absolute inset-0 rounded-full bg-[#FB923C] opacity-50 animate-ping" />
            </a>
          )}

          {secondaryButton && (
            <a
              href={secondaryButton.href}
              onClick={secondaryButton.onClick}
              className="inline-flex items-center px-10 py-5 bg-white text-[#84CC16] font-black text-xl uppercase rounded-full transform hover:scale-110 hover:-rotate-2 transition-all duration-300 border-4 border-[#A855F7] shadow-2xl hover:bg-[#FFFBEB]"
            >
              <span className="mr-2">✨</span>
              <span>{secondaryButton.text}</span>
              <span className="ml-2">✨</span>
            </a>
          )}
        </div>
      </div>

      {/* Floating decorative emojis */}
      <div className="absolute top-10 left-10 text-7xl animate-spin" style={{ animationDuration: '10s' }}>🍃</div>
      <div className="absolute bottom-10 right-10 text-7xl animate-spin" style={{ animationDuration: '8s', animationDirection: 'reverse' }}>💚</div>
      <div className="absolute top-1/4 right-1/4 text-6xl animate-pulse">⭐</div>
      <div className="absolute bottom-1/4 left-1/4 text-6xl animate-bounce">🌟</div>
      <div className="absolute top-20 right-20 text-5xl animate-pulse" style={{ animationDelay: '1s' }}>💫</div>
      <div className="absolute bottom-20 left-20 text-5xl animate-bounce" style={{ animationDelay: '0.5s' }}>🌈</div>

      {/* Fun wavy bottom border */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" className="w-full">
          <path
            fill="#FFFBEB"
            d="M0,64L80,69.3C160,75,320,85,480,80C640,75,800,53,960,48C1120,43,1280,53,1360,58.7L1440,64L1440,120L1360,120C1280,120,1120,120,960,120C800,120,640,120,480,120C320,120,160,120,80,120L0,120Z"
          />
        </svg>
      </div>
    </div>
  );
};
