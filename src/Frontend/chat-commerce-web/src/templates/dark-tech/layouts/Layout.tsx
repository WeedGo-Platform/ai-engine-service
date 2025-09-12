import React from 'react';
import type { ILayout, LayoutProps } from '../../../core/contracts/template.contracts';

export const Layout: ILayout = ({ children, theme }) => {
  const gridPattern = `data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3Cpattern id='grid' width='60' height='60' patternUnits='userSpaceOnUse'%3E%3Cpath d='M 60 0 L 0 0 0 60' fill='none' stroke='rgba(0,255,136,0.05)' stroke-width='1'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23grid)'/%3E%3C/svg%3E`;
  
  return (
    <div className="min-h-screen bg-[#0A0E1A] text-[#E0E6ED]">
      <div className="fixed inset-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-transparent to-green-500/10" />
        <div 
          className="absolute inset-0"
          style={{ backgroundImage: `url("${gridPattern}")` }}
        />
      </div>
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};