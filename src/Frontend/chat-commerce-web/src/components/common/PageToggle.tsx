import React from 'react';
import { usePageContext } from '../../contexts/PageContext';

interface PageToggleProps {
  className?: string;
}

const PageToggle: React.FC<PageToggleProps> = ({ className = '' }) => {
  const { currentPage, togglePage } = usePageContext();
  const isLanding = currentPage === 'landing';
  
  return (
    <button
      onClick={togglePage}
      className={`relative inline-flex items-center h-7 w-14 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
        isLanding ? 'bg-gradient-to-r from-green-500 to-green-600' : 'bg-gradient-to-r from-blue-500 to-blue-600'
      } ${className}`}
      title={isLanding ? 'Slide to Chat View' : 'Slide to Landing Page'}
      aria-label="Toggle between landing and chat page"
    >
      <span className="sr-only">Toggle page view</span>
      
      {/* Slider thumb with icon */}
      <span
        className={`${
          isLanding ? 'translate-x-0.5' : 'translate-x-7'
        } inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white transition-transform duration-300 shadow-lg`}
      >
        {/* Sliding arrows icon */}
        <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isLanding ? (
            // Right arrows for sliding to chat
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          ) : (
            // Left arrows for sliding to landing
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          )}
        </svg>
      </span>
      
      {/* Background indicators */}
      <div className="absolute inset-0 flex items-center justify-between px-1.5 pointer-events-none">
        <div className={`transition-opacity duration-300 ${isLanding ? 'opacity-100' : 'opacity-30'}`}>
          <svg className="w-3 h-3 text-white/80" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.707 2.293a1 1 0 00-1.414 0l-9 9a1 1 0 001.414 1.414L2 12.414V19a1 1 0 001 1h5a1 1 0 001-1v-5h2v5a1 1 0 001 1h5a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-9-9z" />
          </svg>
        </div>
        <div className={`transition-opacity duration-300 ${!isLanding ? 'opacity-100' : 'opacity-30'}`}>
          <svg className="w-3 h-3 text-white/80" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </div>
      </div>
    </button>
  );
};

export default PageToggle;