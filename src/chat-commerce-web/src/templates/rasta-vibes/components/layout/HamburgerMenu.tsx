import React from 'react';
import { HamburgerMenuProps } from '../../../../core/contracts/template.contracts';

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="p-3 rounded-xl transition-all duration-300 transform hover:scale-105"
      style={{
        background: isOpen 
          ? 'linear-gradient(135deg, #DC2626 0%, #FCD34D 50%, #16A34A 100%)'
          : 'linear-gradient(135deg, rgba(220, 38, 38, 0.2) 0%, rgba(252, 211, 77, 0.2) 50%, rgba(22, 163, 74, 0.2) 100%)',
        border: '2px solid transparent',
        borderImage: 'linear-gradient(45deg, #DC2626, #FCD34D, #16A34A) 1',
        boxShadow: isOpen 
          ? '0 8px 32px rgba(252, 211, 77, 0.3), 0 0 60px rgba(252, 211, 77, 0.1)'
          : '0 4px 16px rgba(0, 0, 0, 0.2)',
      }}
      aria-label="Toggle menu"
    >
      <div className="w-6 h-5 flex flex-col justify-between relative">
        {/* Top bar */}
        <span
          className={`block h-0.5 w-full transform transition-all duration-300 ${
            isOpen ? 'rotate-45 translate-y-2' : ''
          }`}
          style={{
            background: isOpen ? '#000' : '#FCD34D',
            boxShadow: isOpen ? 'none' : '0 0 4px rgba(252, 211, 77, 0.5)',
          }}
        />
        {/* Middle bar */}
        <span
          className={`block h-0.5 w-full transition-all duration-300 ${
            isOpen ? 'opacity-0 scale-0' : 'opacity-100 scale-100'
          }`}
          style={{
            background: '#FCD34D',
            boxShadow: '0 0 4px rgba(252, 211, 77, 0.5)',
          }}
        />
        {/* Bottom bar */}
        <span
          className={`block h-0.5 w-full transform transition-all duration-300 ${
            isOpen ? '-rotate-45 -translate-y-2' : ''
          }`}
          style={{
            background: isOpen ? '#000' : '#FCD34D',
            boxShadow: isOpen ? 'none' : '0 0 4px rgba(252, 211, 77, 0.5)',
          }}
        />
      </div>
      
      {/* Decorative element */}
      {!isOpen && (
        <div 
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse"
          style={{
            background: 'radial-gradient(circle, #DC2626 0%, transparent 70%)',
            boxShadow: '0 0 8px rgba(220, 38, 38, 0.6)',
          }}
        />
      )}
    </button>
  );
};

export default HamburgerMenu;