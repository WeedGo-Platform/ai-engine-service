import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  closeOnBackdrop?: boolean;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'medium',
  closeOnBackdrop = true,
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

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return 'max-w-sm';
      case 'medium':
        return 'max-w-lg';
      case 'large':
        return 'max-w-2xl';
      case 'fullscreen':
        return 'max-w-full h-full';
      default:
        return 'max-w-lg';
    }
  };

  return ReactDOM.createPortal(
    <div 
      className="fixed inset-0 flex items-center justify-center p-4"
      style={{ zIndex: 9999 }}
      onClick={closeOnBackdrop ? onClose : undefined}
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(10px)',
        }}
      />

      {/* Modal Content */}
      <div 
        className={`relative w-full ${getSizeStyles()} ${size === 'fullscreen' ? '' : 'rounded-2xl overflow-hidden'} smooth-fade-in`}
        style={{
          background: 'rgba(26, 26, 26, 0.98)',
          border: '3px solid transparent',
          backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.98), rgba(26, 26, 26, 0.98)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
          backgroundOrigin: 'border-box',
          backgroundClip: 'padding-box, border-box',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.8), 0 0 100px rgba(252, 211, 77, 0.2)',
          animation: 'smooth-fade-in 0.3s ease-out, reggae-pulse 4s ease-in-out infinite',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative Top Bar */}
        <div className="absolute top-0 left-0 right-0 h-1 flex">
          <div className="flex-1" style={{ background: '#DC2626' }} />
          <div className="flex-1" style={{ background: '#FCD34D' }} />
          <div className="flex-1" style={{ background: '#16A34A' }} />
        </div>

        {/* Header */}
        {title && (
          <div 
            className="px-6 py-4 flex items-center justify-between"
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              borderBottom: '2px solid rgba(252, 211, 77, 0.2)',
            }}
          >
            <h2 
              className="text-2xl font-bold"
              style={{
                color: '#FCD34D',
                fontFamily: 'Bebas Neue, sans-serif',
                letterSpacing: '2px',
                textShadow: '0 0 20px rgba(252, 211, 77, 0.5)',
              }}
            >
              {title}
            </h2>
            
            <button
              onClick={onClose}
              className="p-2 rounded-lg transition-all hover:scale-110"
              style={{
                background: 'rgba(220, 38, 38, 0.2)',
                border: '1px solid rgba(220, 38, 38, 0.5)',
                color: '#DC2626',
              }}
              aria-label="Close modal"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Body */}
        <div 
          className="p-6 overflow-y-auto rasta-vibes-scrollbar"
          style={{
            maxHeight: size === 'fullscreen' ? 'calc(100vh - 200px)' : '60vh',
          }}
        >
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div 
            className="px-6 py-4"
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              borderTop: '2px solid rgba(252, 211, 77, 0.2)',
            }}
          >
            {footer}
          </div>
        )}

        {/* Decorative Elements */}
        <div className="absolute top-4 left-4 text-xs opacity-30" style={{ color: '#DC2626' }}>
          ☮
        </div>
        <div className="absolute top-4 right-4 text-xs opacity-30" style={{ color: '#FCD34D' }}>
          ♫
        </div>
        <div className="absolute bottom-4 left-4 text-xs opacity-30" style={{ color: '#16A34A' }}>
          🌿
        </div>
        <div className="absolute bottom-4 right-4 text-xs opacity-30" style={{ color: '#FCD34D' }}>
          ♥
        </div>
      </div>
    </div>,
    document.body
  );
};

export default Modal;