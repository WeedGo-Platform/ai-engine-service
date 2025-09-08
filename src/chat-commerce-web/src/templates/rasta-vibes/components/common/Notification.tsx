import React, { useEffect, useState } from 'react';

interface NotificationProps {
  type?: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration?: number;
  onClose?: () => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

const Notification: React.FC<NotificationProps> = ({
  type = 'info',
  title,
  message,
  duration = 5000,
  onClose,
  position = 'top-right',
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, 300);
  };

  if (!isVisible) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return {
          background: 'linear-gradient(135deg, rgba(22, 163, 74, 0.95) 0%, rgba(22, 163, 74, 0.85) 100%)',
          borderColor: '#16A34A',
          icon: '✅',
          iconColor: '#FCD34D',
        };
      case 'error':
        return {
          background: 'linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(220, 38, 38, 0.85) 100%)',
          borderColor: '#DC2626',
          icon: '❌',
          iconColor: '#FCD34D',
        };
      case 'warning':
        return {
          background: 'linear-gradient(135deg, rgba(252, 211, 77, 0.95) 0%, rgba(252, 211, 77, 0.85) 100%)',
          borderColor: '#FCD34D',
          icon: '⚠️',
          iconColor: '#000',
        };
      case 'info':
      default:
        return {
          background: 'linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(26, 26, 26, 0.85) 100%)',
          borderColor: '#FCD34D',
          icon: 'ℹ️',
          iconColor: '#FCD34D',
        };
    }
  };

  const getPositionStyles = () => {
    const base = 'fixed z-50';
    switch (position) {
      case 'top-right':
        return `${base} top-4 right-4`;
      case 'top-left':
        return `${base} top-4 left-4`;
      case 'bottom-right':
        return `${base} bottom-4 right-4`;
      case 'bottom-left':
        return `${base} bottom-4 left-4`;
      case 'top-center':
        return `${base} top-4 left-1/2 transform -translate-x-1/2`;
      case 'bottom-center':
        return `${base} bottom-4 left-1/2 transform -translate-x-1/2`;
      default:
        return `${base} top-4 right-4`;
    }
  };

  const styles = getTypeStyles();

  return (
    <div 
      className={`${getPositionStyles()} ${isLeaving ? 'babylon-dissolve' : 'smooth-fade-in'}`}
      style={{
        animation: isLeaving ? 'babylon-dissolve 0.3s ease-out' : 'smooth-fade-in 0.3s ease-out',
      }}
    >
      <div 
        className="min-w-[300px] max-w-md rounded-xl overflow-hidden shadow-2xl"
        style={{
          background: styles.background,
          border: `3px solid ${styles.borderColor}`,
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Rasta Border Top */}
        <div className="h-1 flex">
          <div className="flex-1" style={{ background: '#DC2626' }} />
          <div className="flex-1" style={{ background: '#FCD34D' }} />
          <div className="flex-1" style={{ background: '#16A34A' }} />
        </div>

        <div className="p-4">
          <div className="flex items-start space-x-3">
            {/* Icon */}
            <div 
              className="text-2xl flex-shrink-0 reggae-pulse"
              style={{ color: styles.iconColor }}
            >
              {styles.icon}
            </div>

            {/* Content */}
            <div className="flex-1">
              {title && (
                <h3 
                  className="font-bold mb-1"
                  style={{ 
                    color: type === 'warning' ? '#000' : '#FCD34D',
                    fontFamily: 'Bebas Neue, sans-serif',
                    fontSize: '1.125rem',
                    letterSpacing: '1px',
                  }}
                >
                  {title}
                </h3>
              )}
              <p 
                className="text-sm"
                style={{ 
                  color: type === 'warning' ? '#000' : '#F3E7C3',
                  fontFamily: 'Ubuntu, sans-serif',
                  lineHeight: '1.5',
                }}
              >
                {message}
              </p>
            </div>

            {/* Close Button */}
            <button
              onClick={handleClose}
              className="text-xl opacity-70 hover:opacity-100 transition-opacity"
              style={{ color: type === 'warning' ? '#000' : '#FCD34D' }}
              aria-label="Close notification"
            >
              ✖
            </button>
          </div>

          {/* Progress Bar */}
          {duration > 0 && (
            <div 
              className="mt-3 h-1 rounded-full overflow-hidden"
              style={{ background: 'rgba(0, 0, 0, 0.3)' }}
            >
              <div 
                className="h-full rounded-full"
                style={{
                  background: 'linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
                  animation: `shrink-width ${duration}ms linear`,
                  transformOrigin: 'left',
                }}
              />
            </div>
          )}
        </div>

        {/* Decorative Bottom */}
        <div 
          className="px-4 pb-2 flex justify-center space-x-2 text-xs opacity-50"
          style={{ color: type === 'warning' ? '#000' : '#FCD34D' }}
        >
          <span>☮</span>
          <span>•</span>
          <span>♥</span>
          <span>•</span>
          <span>✊</span>
        </div>
      </div>

      <style>{`
        @keyframes shrink-width {
          from {
            transform: scaleX(1);
          }
          to {
            transform: scaleX(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Notification;