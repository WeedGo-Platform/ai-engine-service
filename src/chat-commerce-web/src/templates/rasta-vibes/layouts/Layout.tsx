import React from 'react';
import type { ILayout } from '../../../core/contracts/template.contracts';

export const Layout: ILayout = ({ children }) => {
  return (
    <div className="rasta-vibes-theme min-h-screen relative overflow-hidden">
      {/* Animated Background Gradient */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          background: 'linear-gradient(135deg, #1A1A1A 0%, #2D1B00 25%, #1A2E05 50%, #2D1B00 75%, #1A1A1A 100%)',
          backgroundSize: '400% 400%',
          animation: 'rasta-wave 20s ease infinite',
        }}
      />
      
      {/* Subtle Pattern Overlay */}
      <div 
        className="fixed inset-0 z-0 opacity-10"
        style={{
          backgroundImage: `
            repeating-linear-gradient(
              45deg,
              transparent,
              transparent 10px,
              rgba(252, 211, 77, 0.1) 10px,
              rgba(252, 211, 77, 0.1) 20px
            ),
            repeating-linear-gradient(
              -45deg,
              transparent,
              transparent 10px,
              rgba(22, 163, 74, 0.1) 10px,
              rgba(22, 163, 74, 0.1) 20px
            )
          `,
        }}
      />

      {/* Floating Elements Container */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        {/* Floating Music Notes */}
        <div className="absolute top-10 left-10 text-6xl opacity-10 float-notes" style={{ color: '#FCD34D', animationDelay: '0s' }}>♪</div>
        <div className="absolute top-40 right-20 text-5xl opacity-10 float-notes" style={{ color: '#16A34A', animationDelay: '5s' }}>♫</div>
        <div className="absolute bottom-20 left-1/3 text-7xl opacity-10 float-notes" style={{ color: '#DC2626', animationDelay: '10s' }}>♪</div>
        <div className="absolute top-1/2 right-1/3 text-6xl opacity-10 float-notes" style={{ color: '#FCD34D', animationDelay: '15s' }}>♫</div>
        
        {/* Cannabis Leaf Decorations */}
        <div className="absolute top-20 right-10 text-4xl opacity-10 leaf-sway" style={{ color: '#16A34A' }}>🌿</div>
        <div className="absolute bottom-40 left-20 text-5xl opacity-10 leaf-sway" style={{ color: '#16A34A', animationDelay: '2s' }}>🌿</div>
        
        {/* Peace Symbols */}
        <div className="absolute top-1/3 left-1/4 text-3xl opacity-10 positive-vibration" style={{ color: '#FCD34D' }}>☮</div>
        <div className="absolute bottom-1/3 right-1/4 text-4xl opacity-10 positive-vibration" style={{ color: '#DC2626', animationDelay: '1.5s' }}>☮</div>
      </div>

      {/* Lion of Judah Watermark */}
      <div className="rasta-lion-watermark" />

      {/* Rasta Border Frame */}
      <div className="fixed inset-4 z-0 pointer-events-none">
        <div 
          className="w-full h-full rounded-2xl"
          style={{
            border: '3px solid transparent',
            backgroundImage: 'linear-gradient(#1A1A1A, #1A1A1A), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
            backgroundOrigin: 'border-box',
            backgroundClip: 'padding-box, border-box',
            opacity: 0.3,
          }}
        />
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {children}
      </div>

      {/* Bottom Decorative Bar */}
      <div 
        className="fixed bottom-0 left-0 right-0 h-1 z-20"
        style={{
          background: 'linear-gradient(90deg, #DC2626 0%, #DC2626 33%, #FCD34D 33%, #FCD34D 66%, #16A34A 66%, #16A34A 100%)',
        }}
      />

      {/* Inspirational Quote */}
      <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-10 pointer-events-none">
        <p className="text-xs opacity-30" style={{ color: '#FCD34D', fontFamily: 'Ubuntu, sans-serif' }}>
          "One Love, One Heart, Let's Get Together and Feel Alright"
        </p>
      </div>
    </div>
  );
};