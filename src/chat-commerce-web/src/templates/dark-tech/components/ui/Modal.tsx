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
      {/* Backdrop with matrix effect */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-500"
        onClick={onClose}
        style={{
          backgroundImage: `
            radial-gradient(circle at 20% 30%, rgba(6, 182, 212, 0.1) 0%, transparent 70%),
            radial-gradient(circle at 80% 70%, rgba(236, 72, 153, 0.1) 0%, transparent 70%),
            radial-gradient(circle at 50% 50%, rgba(163, 230, 53, 0.05) 0%, transparent 70%)
          `,
        }}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-gray-900 border-2 border-cyan-800 shadow-2xl shadow-cyan-400/20
          w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden
          transform transition-all duration-500
          animate-pulse-glow
        `}
        style={{
          backgroundImage: 'linear-gradient(45deg, transparent 49%, rgba(6, 182, 212, 0.05) 50%, transparent 51%)',
          backgroundSize: '30px 30px',
          animation: 'modalSlideIn 0.5s ease-out',
        }}
      >
        {/* Glowing border */}
        <div className="absolute inset-0 border-2 border-transparent bg-gradient-to-r from-cyan-400 via-magenta-400 to-lime-400 opacity-20 animate-pulse" 
             style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'subtract' }} />

        {/* Corner brackets */}
        <div className="absolute top-0 left-0 w-6 h-6 border-l-4 border-t-4 border-cyan-400"></div>
        <div className="absolute top-0 right-0 w-6 h-6 border-r-4 border-t-4 border-cyan-400"></div>
        <div className="absolute bottom-0 left-0 w-6 h-6 border-l-4 border-b-4 border-cyan-400"></div>
        <div className="absolute bottom-0 right-0 w-6 h-6 border-r-4 border-b-4 border-cyan-400"></div>

        {/* Header */}
        {title && (
          <div className="relative px-6 py-4 border-b-2 border-cyan-800/50 bg-gradient-to-r from-gray-900 to-gray-800">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-cyan-400 font-mono uppercase tracking-wide flex items-center gap-3">
                <span className="text-lime-400 animate-pulse">◉</span>
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-2 text-cyan-400 hover:text-red-400 transition-all duration-300 font-mono text-xl hover:bg-red-900/20 rounded border border-cyan-800 hover:border-red-400"
              >
                ✕
              </button>
            </div>
            {/* Header scanning line */}
            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse"></div>
          </div>
        )}

        {/* Content */}
        <div className="relative px-6 py-6 overflow-y-auto max-h-[calc(90vh-8rem)] scrollbar-thin scrollbar-track-gray-800 scrollbar-thumb-cyan-600">
          {children}
          
          {/* Content scanning lines */}
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-magenta-400/30 to-transparent animate-pulse" style={{ animationDelay: '2s' }}></div>
        </div>

        {/* Close button if no title */}
        {!title && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-3 text-cyan-400 hover:text-red-400 transition-all duration-300 font-mono text-xl hover:bg-red-900/20 rounded border border-cyan-800 hover:border-red-400 bg-gray-900/80 backdrop-blur-sm"
          >
            ✕
          </button>
        )}

        {/* Side scanning lights */}
        <div className="absolute left-0 top-1/4 w-1 h-1/2 bg-gradient-to-b from-transparent via-cyan-400 to-transparent opacity-30 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
        <div className="absolute right-0 top-1/3 w-1 h-1/3 bg-gradient-to-b from-transparent via-magenta-400 to-transparent opacity-30 animate-pulse" style={{ animationDelay: '1.5s' }}></div>
      </div>

      <style>{`
        @keyframes modalSlideIn {
          from {
            opacity: 0;
            transform: translateY(-50px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
          }
          50% {
            box-shadow: 0 0 30px rgba(6, 182, 212, 0.5), 0 0 40px rgba(236, 72, 153, 0.2);
          }
        }
        
        .animate-pulse-glow {
          animation: pulse-glow 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default Modal;