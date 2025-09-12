import React, { useEffect } from 'react';
import { FiX, FiShoppingCart } from 'react-icons/fi';

interface CartModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

const CartModal: React.FC<CartModalProps> = ({ isOpen, onClose, children }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[99998] animate-fadeIn"
        onClick={onClose}
      />
      
      {/* Slide-out Panel */}
      <div 
        className="fixed right-0 top-0 h-full w-full sm:w-96 bg-gray-50 shadow-2xl z-[99999] flex flex-col animate-slideInRight"
      >
        {children}
      </div>
    </>
  );
};

export default CartModal;