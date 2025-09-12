import React from 'react';
import type { ILayout, LayoutProps } from '../../../core/contracts/template.contracts';

export const Layout: ILayout = ({ children, theme }) => {
  return (
    <div className="min-h-screen bg-white">
      {children}
    </div>
  );
};