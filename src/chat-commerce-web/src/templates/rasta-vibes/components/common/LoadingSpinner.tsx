import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large' | 'xlarge';
  message?: string;
  fullScreen?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  message = 'Loading vibes...',
  fullScreen = false,
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return { width: '30px', height: '30px', borderWidth: '3px' };
      case 'medium':
        return { width: '50px', height: '50px', borderWidth: '4px' };
      case 'large':
        return { width: '70px', height: '70px', borderWidth: '5px' };
      case 'xlarge':
        return { width: '100px', height: '100px', borderWidth: '6px' };
      default:
        return { width: '50px', height: '50px', borderWidth: '4px' };
    }
  };

  const sizeStyles = getSizeStyles();

  const content = (
    <div className="flex flex-col items-center justify-center space-y-4">
      {/* Main Spinner */}
      <div className="relative">
        {/* Outer Ring */}
        <div 
          className="rounded-full irie-spin"
          style={{
            ...sizeStyles,
            borderStyle: 'solid',
            borderColor: '#DC2626 #FCD34D #16A34A transparent',
          }}
        />
        
        {/* Inner Elements */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ 
            fontSize: size === 'small' ? '12px' : 
                     size === 'medium' ? '20px' : 
                     size === 'large' ? '28px' : '40px' 
          }}
        >
          <span className="lion-glow" style={{ color: '#FCD34D' }}>
            🦁
          </span>
        </div>

        {/* Orbiting Elements */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ animation: 'spin 3s linear infinite reverse' }}
        >
          <div 
            className="absolute"
            style={{ 
              top: '-10px',
              fontSize: size === 'small' ? '10px' : '14px',
              color: '#DC2626',
            }}
          >
            ☮
          </div>
          <div 
            className="absolute"
            style={{ 
              right: '-10px',
              fontSize: size === 'small' ? '10px' : '14px',
              color: '#FCD34D',
            }}
          >
            ♫
          </div>
          <div 
            className="absolute"
            style={{ 
              bottom: '-10px',
              fontSize: size === 'small' ? '10px' : '14px',
              color: '#16A34A',
            }}
          >
            🌿
          </div>
          <div 
            className="absolute"
            style={{ 
              left: '-10px',
              fontSize: size === 'small' ? '10px' : '14px',
              color: '#FCD34D',
            }}
          >
            ♥
          </div>
        </div>
      </div>

      {/* Loading Message */}
      {message && (
        <div className="text-center">
          <p 
            className="font-medium"
            style={{ 
              color: '#FCD34D',
              fontFamily: 'Ubuntu, sans-serif',
              fontSize: size === 'small' ? '12px' : '14px',
            }}
          >
            {message}
          </p>
          
          {/* Animated Dots */}
          <div className="flex justify-center space-x-1 mt-2">
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: '#DC2626',
                animationDelay: '0s',
              }}
            />
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: '#FCD34D',
                animationDelay: '0.3s',
              }}
            />
            <div 
              className="w-2 h-2 rounded-full reggae-pulse"
              style={{ 
                background: '#16A34A',
                animationDelay: '0.6s',
              }}
            />
          </div>
        </div>
      )}

      {/* Inspirational Quote */}
      {size !== 'small' && (
        <p 
          className="text-xs text-center opacity-60 max-w-xs"
          style={{ color: '#F3E7C3' }}
        >
          "Don't worry about a thing, 'cause every little thing gonna be alright"
        </p>
      )}

      <style>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );

  if (fullScreen) {
    return (
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Background Pattern */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `
              repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(252, 211, 77, 0.1) 10px,
                rgba(252, 211, 77, 0.1) 20px
              )
            `,
          }}
        />
        
        {/* Floating Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 text-6xl opacity-10 float-notes" style={{ color: '#FCD34D' }}>
            ♪
          </div>
          <div className="absolute bottom-10 right-10 text-5xl opacity-10 float-notes" style={{ color: '#16A34A', animationDelay: '2s' }}>
            ♫
          </div>
          <div className="absolute top-1/2 left-1/4 text-4xl opacity-10 leaf-sway" style={{ color: '#DC2626' }}>
            🌿
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default LoadingSpinner;