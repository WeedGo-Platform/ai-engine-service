import React, { useEffect, useState } from 'react';

interface NotificationProps {
  show: boolean;
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
  onClose?: () => void;
}

const Notification: React.FC<NotificationProps> = ({ 
  show, 
  message, 
  type = 'success',
  duration = 3000,
  onClose 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      setIsLeaving(false);
      
      const timer = setTimeout(() => {
        setIsLeaving(true);
        setTimeout(() => {
          setIsVisible(false);
          onClose?.();
        }, 300);
      }, duration);
      
      return () => clearTimeout(timer);
    } else {
      setIsLeaving(true);
      setTimeout(() => setIsVisible(false), 300);
    }
  }, [show, duration, onClose]);

  if (!isVisible) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return 'from-green-900/90 to-green-800/80 border-green-500/50 shadow-[0_0_40px_rgba(34,197,94,0.6)]';
      case 'error':
        return 'from-red-900/90 to-red-800/80 border-red-500/50 shadow-[0_0_40px_rgba(239,68,68,0.6)]';
      case 'warning':
        return 'from-amber-900/90 to-orange-800/80 border-amber-500/50 shadow-[0_0_40px_rgba(251,191,36,0.6)]';
      case 'info':
      default:
        return 'from-cyan-900/90 to-blue-800/80 border-cyan-500/50 shadow-[0_0_40px_rgba(6,182,212,0.6)]';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '[✓]';
      case 'error':
        return '[✗]';
      case 'warning':
        return '[!]';
      case 'info':
      default:
        return '[i]';
    }
  };

  const getTypeText = () => {
    switch (type) {
      case 'success':
        return 'SUCCESS';
      case 'error':
        return 'ERROR';
      case 'warning':
        return 'WARNING';
      case 'info':
      default:
        return 'INFO';
    }
  };

  const getTextColor = () => {
    switch (type) {
      case 'success':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-amber-400';
      case 'info':
      default:
        return 'text-cyan-400';
    }
  };

  return (
    <div 
      className={`fixed top-24 right-6 z-50 transition-all duration-300 ${
        isLeaving ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'
      }`}
      style={{
        animation: !isLeaving ? 'glitchIn 0.3s ease-out' : undefined
      }}
    >
      <div className={`bg-gradient-to-r ${getTypeStyles()} backdrop-blur-xl border-2 rounded-lg relative overflow-hidden min-w-[350px]`}>
        {/* Scanline effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/5 to-transparent animate-scan"></div>
        
        {/* Content */}
        <div className="relative z-10 px-6 py-4">
          {/* Header */}
          <div className={`flex items-center gap-2 mb-2 ${getTextColor()} font-mono text-xs font-bold uppercase tracking-widest`}>
            <span className="animate-pulse">{getIcon()}</span>
            <span style={{ textShadow: '0 0 10px currentColor' }}>
              [SYSTEM_{getTypeText()}]
            </span>
          </div>
          
          {/* Message */}
          <div className="text-gray-100 font-mono text-sm leading-relaxed">
            {'> '}{message}
            <span className="animate-pulse ml-1">_</span>
          </div>
          
          {/* Timestamp */}
          <div className="mt-2 text-xs text-gray-500 font-mono">
            [{new Date().toLocaleTimeString()}]
          </div>
        </div>
        
        {/* Close button */}
        {onClose && (
          <button
            onClick={() => {
              setIsLeaving(true);
              setTimeout(() => {
                setIsVisible(false);
                onClose();
              }, 300);
            }}
            className="absolute top-2 right-2 p-1 hover:bg-white/10 rounded transition-colors text-gray-400 hover:text-cyan-400"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <style>{`
        @keyframes glitchIn {
          0% {
            transform: translateX(100%) skewX(-10deg);
            opacity: 0;
            filter: blur(10px);
          }
          50% {
            transform: translateX(0) skewX(5deg);
            opacity: 0.5;
            filter: blur(5px);
          }
          100% {
            transform: translateX(0) skewX(0);
            opacity: 1;
            filter: blur(0);
          }
        }
        
        @keyframes scan {
          0% {
            transform: translateY(-100%);
          }
          100% {
            transform: translateY(100%);
          }
        }
        
        .animate-scan {
          animation: scan 3s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default Notification;