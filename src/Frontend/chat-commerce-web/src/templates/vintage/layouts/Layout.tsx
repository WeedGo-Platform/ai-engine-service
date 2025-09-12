import React from 'react';
import { ILayout } from '../../../core/contracts/template.contracts';
import CookieDisclaimer from '../components/legal/CookieDisclaimer';
import ErrorBoundary from '../components/common/ErrorBoundary';

export const Layout: ILayout = ({ children }) => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen vintage-layout">
        <main className="flex-1">
          {children}
        </main>
        
        <CookieDisclaimer />
      </div>
    </ErrorBoundary>
  );
};