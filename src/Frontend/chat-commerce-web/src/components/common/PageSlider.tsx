import React, { useEffect, useState } from 'react';
import { usePageContext } from '../../contexts/PageContext';

interface PageSliderProps {
  children: [React.ReactNode, React.ReactNode]; // [landing, chat]
}

const PageSlider: React.FC<PageSliderProps> = ({ children }) => {
  const { currentPage } = usePageContext();
  const [isAnimating, setIsAnimating] = useState(false);
  const [prevPage, setPrevPage] = useState(currentPage);
  
  useEffect(() => {
    if (currentPage !== prevPage) {
      setIsAnimating(true);
      const timer = setTimeout(() => {
        setIsAnimating(false);
        setPrevPage(currentPage);
      }, 500); // Match transition duration
      return () => clearTimeout(timer);
    }
  }, [currentPage, prevPage]);

  const isLanding = currentPage === 'landing';
  
  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Container for both pages */}
      <div 
        className={`
          absolute inset-0 flex transition-transform duration-500 ease-in-out
          ${isLanding ? 'translate-x-0' : '-translate-x-1/2'}
        `}
        style={{ width: '200%' }}
      >
        {/* Landing Page */}
        <div className="w-1/2 h-full flex-shrink-0 overflow-y-auto">
          {children[0]}
        </div>
        
        {/* Chat Page */}
        <div className="w-1/2 h-full flex-shrink-0">
          {children[1]}
        </div>
      </div>
      
      {/* Optional edge shadow for depth effect during transition */}
      {isAnimating && (
        <div 
          className={`
            absolute top-0 bottom-0 w-20 pointer-events-none z-50
            bg-gradient-to-r from-black/20 to-transparent
            transition-opacity duration-500
            ${isLanding ? 'right-0 opacity-0' : 'left-0 opacity-100'}
          `}
        />
      )}
    </div>
  );
};

export default PageSlider;