import React from 'react';
import { HamburgerMenuProps } from '../../../../core/contracts/template.contracts';

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="p-2 bg-black border border-cyan-400 hover:bg-cyan-400 hover:text-black text-cyan-400 transition-all duration-200 group"
      aria-label="[MENU_TOGGLE]"
    >
      <div className="w-6 h-5 flex flex-col justify-between relative">
        <span
          className={`block h-0.5 w-full bg-current transform transition-all duration-300 ${
            isOpen ? 'rotate-45 translate-y-2' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-current transition-all duration-300 ${
            isOpen ? 'opacity-0' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-current transform transition-all duration-300 ${
            isOpen ? '-rotate-45 -translate-y-2' : ''
          }`}
        />
      </div>
    </button>
  );
};

export default HamburgerMenu;