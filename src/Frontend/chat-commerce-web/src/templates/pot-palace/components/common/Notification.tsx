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
        return 'from-green-600 via-emerald-500 to-green-400 border-green-400/50 shadow-[0_0_30px_rgba(34,197,94,0.6)]';
      case 'error':
        return 'from-red-600 via-pink-500 to-red-400 border-red-400/50 shadow-[0_0_30px_rgba(239,68,68,0.6)]';
      case 'warning':
        return 'from-yellow-600 via-amber-500 to-orange-400 border-yellow-400/50 shadow-[0_0_30px_rgba(251,191,36,0.6)]';
      case 'info':
      default:
        return 'from-purple-600 via-pink-500 to-purple-400 border-purple-400/50 shadow-[0_0_30px_rgba(168,85,247,0.6)]';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✨🌿';
      case 'error':
        return '💀⚠️';
      case 'warning':
        return '🔥⚡';
      case 'info':
      default:
        return '🌟💫';
    }
  };

  return (
    <div 
      className={`fixed top-24 right-6 z-50 transition-all duration-300 ${
        isLeaving ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'
      }`}
      style={{
        animation: !isLeaving ? 'floatIn 0.5s ease-out, float 3s ease-in-out infinite' : undefined
      }}
    >
      <div className={`bg-gradient-to-r ${getTypeStyles()} text-white px-8 py-4 rounded-2xl shadow-2xl border-2 backdrop-blur-xl flex items-center gap-3 min-w-[300px] relative overflow-hidden`}>
        {/* Animated background effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-shimmer" 
             style={{ animation: 'shimmer 2s infinite' }}></div>
        
        {/* Content */}
        <span className="text-2xl animate-pulse relative z-10">{getIcon()}</span>
        <div className="flex-1 relative z-10">
          <p className="font-bold text-lg text-yellow-100 drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]">
            {message}
          </p>
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
            className="relative z-10 p-1 hover:bg-white/20 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <style>{`
        @keyframes floatIn {
          0% {
            transform: translateX(100%) scale(0.8);
            opacity: 0;
          }
          100% {
            transform: translateX(0) scale(1);
            opacity: 1;
          }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
      `}</style>
    </div>
  );
};

export default Notification;