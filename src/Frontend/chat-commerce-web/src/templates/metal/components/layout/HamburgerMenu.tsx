import React from 'react';

interface HamburgerMenuProps {
  isOpen: boolean;
  onToggle: () => void;
}

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onToggle }) => {
  return (
    <>
      <button
        onClick={onToggle}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors md:hidden"
        aria-label="Toggle menu"
      >
        <div className="w-6 h-5 relative flex flex-col justify-between">
          <span className={`block h-0.5 w-full bg-gray-700 transition-all duration-300 ${isOpen ? 'rotate-45 translate-y-2' : ''}`} />
          <span className={`block h-0.5 w-full bg-gray-700 transition-all duration-300 ${isOpen ? 'opacity-0' : ''}`} />
          <span className={`block h-0.5 w-full bg-gray-700 transition-all duration-300 ${isOpen ? '-rotate-45 -translate-y-2' : ''}`} />
        </div>
      </button>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white shadow-lg border-b border-gray-200 md:hidden">
          <nav className="flex flex-col p-4 space-y-2">
            <a href="#" className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">Products</a>
            <a href="#" className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">Deals</a>
            <a href="#" className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">About</a>
            <a href="#" className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">Contact</a>
          </nav>
        </div>
      )}
    </>
  );
};

export default HamburgerMenu;