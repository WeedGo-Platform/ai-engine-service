import React, { createContext, useContext, useState } from 'react';

type PageType = 'landing' | 'chat';

interface PageContextType {
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
  togglePage: () => void;
}

const PageContext = createContext<PageContextType | undefined>(undefined);

export const usePageContext = () => {
  const context = useContext(PageContext);
  if (!context) {
    throw new Error('usePageContext must be used within a PageProvider');
  }
  return context;
};

interface PageProviderProps {
  children: React.ReactNode;
}

export const PageProvider: React.FC<PageProviderProps> = ({ children }) => {
  const [currentPage, setCurrentPage] = useState<PageType>('chat');

  const togglePage = () => {
    setCurrentPage(prev => prev === 'chat' ? 'landing' : 'chat');
  };

  return (
    <PageContext.Provider value={{ currentPage, setCurrentPage, togglePage }}>
      {children}
    </PageContext.Provider>
  );
};