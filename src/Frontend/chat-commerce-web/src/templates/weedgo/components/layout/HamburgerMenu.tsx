import React from 'react';
import { HamburgerMenuProps } from '../../../../core/contracts/template.contracts';

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="p-2.5 rounded-lg hover:bg-gray-100   group"
      aria-label="Toggle menu"
    >
      <div className="w-5 h-4 flex flex-col justify-between relative">
        <span
          className={`block h-0.5 w-full bg-gray-700 group-hover:bg-blue-700 transform   origin-center ${
            isOpen ? 'rotate-45 translate-y-1.5' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-gray-700 group-hover:bg-blue-700   ${
            isOpen ? 'opacity-0' : ''
          }`}
        />
        <span
          className={`block h-0.5 w-full bg-gray-700 group-hover:bg-blue-700 transform   origin-center ${
            isOpen ? '-rotate-45 -translate-y-1.5' : ''
          }`}
        />
      </div>
    </button>
  );
};

export default HamburgerMenu;