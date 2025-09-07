import React from 'react';
import { HamburgerMenuProps } from '../../../../core/contracts/template.contracts';

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="p-2.5 rounded-lg hover:bg-slate-100 transition-all duration-200 group"
      aria-label="Toggle menu"
    >
      <div className="w-5 h-4 flex flex-col justify-between relative">
        <span
          className={`block h-0.5 w-full bg-slate-700 group-hover:bg-slate-900 transform transition-all duration-300 origin-center ${
            isOpen ? 'rotate-45 translate-y-1.5' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-slate-700 group-hover:bg-slate-900 transition-all duration-300 ${
            isOpen ? 'opacity-0' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-slate-700 group-hover:bg-slate-900 transform transition-all duration-300 origin-center ${
            isOpen ? '-rotate-45 -translate-y-1.5' : ''
          }`}
        />
      </div>
    </button>
  );
};

export default HamburgerMenu;