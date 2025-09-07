import React from 'react';
import type { ILayout, LayoutProps } from '../../../core/contracts/template.contracts';

export const Layout: ILayout = ({ children, theme }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-500 via-pink-500 to-purple-700">
      {children}
    </div>
  );
};