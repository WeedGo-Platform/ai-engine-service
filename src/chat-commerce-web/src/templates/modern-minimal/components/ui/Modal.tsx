import React, { useEffect } from 'react';
import { ModalProps } from '../../../../core/contracts/template.contracts';

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  children,
  title,
  size = 'md',
}) => {
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

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-8">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-white border border-gray-300 shadow-2xl 
          w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden
          transform transition-all duration-300
        `}
      >
        {/* Header */}
        {title && (
          <div className="px-8 py-6 border-b border-gray-300">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-light text-gray-900">
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200 font-mono text-lg"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="px-8 py-8 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {children}
        </div>

        {/* Close button if no title */}
        {!title && (
          <button
            onClick={onClose}
            className="absolute top-6 right-6 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200 font-mono text-xl"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default Modal;