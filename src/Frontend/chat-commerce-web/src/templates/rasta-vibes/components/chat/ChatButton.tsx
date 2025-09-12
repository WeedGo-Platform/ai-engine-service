import React, { useState } from 'react';

interface ChatButtonProps {
  onClick?: () => void;
  isOpen?: boolean;
  notificationCount?: number;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}

const ChatButton: React.FC<ChatButtonProps> = ({
  onClick,
  isOpen = false,
  notificationCount = 0,
  position = 'bottom-right',
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const getPositionStyles = () => {
    switch (position) {
      case 'bottom-right':
        return { bottom: '20px', right: '20px' };
      case 'bottom-left':
        return { bottom: '20px', left: '20px' };
      case 'top-right':
        return { top: '20px', right: '20px' };
      case 'top-left':
        return { top: '20px', left: '20px' };
      default:
        return { bottom: '20px', right: '20px' };
    }
  };

  return (
    <div 
      className="fixed z-50"
      style={getPositionStyles()}
    >
      {/* Ripple Effect Background */}
      <div 
        className="absolute inset-0 rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(252, 211, 77, 0.3) 0%, transparent 70%)',
          animation: 'reggae-pulse 2s ease-in-out infinite',
          transform: 'scale(1.5)',
        }}
      />

      {/* Main Button */}
      <button
        onClick={onClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="relative w-16 h-16 rounded-full flex items-center justify-center transition-all hover:scale-110"
        style={{
          background: isOpen 
            ? 'linear-gradient(135deg, #DC2626, #FCD34D, #16A34A)'
            : 'linear-gradient(135deg, #16A34A, #FCD34D, #DC2626)',
          backgroundSize: '200% 200%',
          animation: 'rasta-wave 3s ease infinite',
          boxShadow: `
            0 4px 20px rgba(0, 0, 0, 0.3),
            0 0 40px rgba(252, 211, 77, 0.3),
            inset 0 0 20px rgba(0, 0, 0, 0.2)
          `,
          border: '3px solid rgba(0, 0, 0, 0.5)',
        }}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {/* Icon */}
        <div 
          className="text-2xl transition-transform"
          style={{
            color: '#000',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        >
          {isOpen ? '✖' : '💬'}
        </div>

        {/* Notification Badge */}
        {notificationCount > 0 && !isOpen && (
          <div 
            className="absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
            style={{
              background: '#DC2626',
              color: '#FCD34D',
              border: '2px solid #000',
              animation: 'one-love-beat 1.5s ease-in-out infinite',
            }}
          >
            {notificationCount > 9 ? '9+' : notificationCount}
          </div>
        )}

        {/* Hover Tooltip */}
        {isHovered && !isOpen && (
          <div 
            className="absolute bottom-full mb-2 px-3 py-1 rounded-lg whitespace-nowrap smooth-fade-in"
            style={{
              background: 'rgba(26, 26, 26, 0.95)',
              border: '1px solid rgba(252, 211, 77, 0.3)',
              color: '#FCD34D',
              fontSize: '0.75rem',
            }}
          >
            <div className="flex items-center space-x-2">
              <span>Chat with us</span>
              <span>🦁</span>
            </div>
            <div 
              className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1"
              style={{
                width: 0,
                height: 0,
                borderLeft: '6px solid transparent',
                borderRight: '6px solid transparent',
                borderTop: '6px solid rgba(252, 211, 77, 0.3)',
              }}
            />
          </div>
        )}
      </button>

      {/* Decorative Elements */}
      <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex space-x-1 text-xs opacity-50">
        <span style={{ color: '#DC2626' }}>♪</span>
        <span style={{ color: '#FCD34D' }}>☮</span>
        <span style={{ color: '#16A34A' }}>♥</span>
      </div>
    </div>
  );
};

export default ChatButton;