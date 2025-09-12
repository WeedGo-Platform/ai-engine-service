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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-gradient-to-br from-purple-50 via-white to-pink-50 
          border-2 border-purple-300 rounded-2xl shadow-2xl 
          w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden
          animate-in zoom-in-95 duration-200
          backdrop-blur-md
        `}
      >
        {/* Header */}
        {title && (
          <div className="px-6 py-4 border-b border-purple-200 bg-gradient-to-r from-purple-100 to-pink-100">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-purple-800 flex items-center gap-2">
                <span className="text-green-600">🌿</span>
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-purple-200 transition-colors text-purple-600 hover:text-purple-800"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="px-6 py-6 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {children}
        </div>

        {/* Close button if no title */}
        {!title && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/80 hover:bg-purple-100 transition-colors text-purple-600 hover:text-purple-800 shadow-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-purple-200 to-transparent rounded-br-full opacity-30"></div>
        <div className="absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-tl from-pink-200 to-transparent rounded-tl-full opacity-30"></div>
      </div>
    </div>
  );
};

export default Modal;