import React, { useState } from 'react';
import { Header } from '@/components/organisms/Header';
import { Footer } from '@/components/organisms/Footer';
import ChatInterface from '@components/chat/ChatInterface';
import { useDarkMode } from '@/hooks/useDarkMode';

interface MainLayoutRefactoredProps {
  children: React.ReactNode;
}

/**
 * Refactored MainLayout following clean architecture principles
 * Demonstrates separation of concerns and atomic design pattern
 */
export const MainLayoutRefactored: React.FC<MainLayoutRefactoredProps> = ({ children }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { isDarkMode } = useDarkMode();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header Component */}
      <Header onChatToggle={() => setIsChatOpen(!isChatOpen)} />

      {/* Main Content */}
      <main className="flex-grow container-max py-6">
        {children}
      </main>

      {/* Footer Component */}
      <Footer className="mt-auto" />

      {/* Chat Interface */}
      {isChatOpen && (
        <ChatInterface onClose={() => setIsChatOpen(false)} />
      )}
    </div>
  );
};

export default MainLayoutRefactored;