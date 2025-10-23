import React, { useEffect } from 'react';
import { IModalProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceModal: React.FC<IModalProps> = ({
  isOpen,
  onClose,
  children,
  title,
  size = 'md',
  closeOnOverlayClick = true,
  className
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

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={closeOnOverlayClick ? onClose : undefined}
      />
      <div className={clsx(
        'relative bg-white rounded-3xl shadow-2xl',
        'transform transition-all duration-500',
        'animate-bounce-in',
        'border-4 border-green-300',
        sizes[size],
        'max-h-[90vh] overflow-hidden flex flex-col',
        className
      )}>
        {title && (
          <div className="flex items-center justify-between p-6 border-b-3 border-green-200 bg-gradient-to-r from-green-50 to-yellow-50">
            {title && (
              <h2 className="text-2xl font-bold text-gray-800 font-display">
                {title}
              </h2>
            )}
            <button
              onClick={onClose}
              className="ml-auto text-3xl hover:scale-110 transition-transform text-green-600 hover:text-green-800"
            >
              ✕
            </button>
          </div>
        )}
        <div className="p-6 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  );
};
