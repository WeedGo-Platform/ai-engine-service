import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      return (
        <div 
          className="min-h-screen flex items-center justify-center p-4"
          style={{
            background: 'linear-gradient(135deg, #1A1A1A 0%, #2D1B00 50%, #1A2E05 100%)',
          }}
        >
          <div 
            className="max-w-lg w-full p-8 rounded-2xl text-center"
            style={{
              background: 'rgba(26, 26, 26, 0.95)',
              border: '3px solid transparent',
              backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.95), rgba(26, 26, 26, 0.95)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
              backgroundOrigin: 'border-box',
              backgroundClip: 'padding-box, border-box',
              backdropFilter: 'blur(10px)',
            }}
          >
            {/* Icon */}
            <div className="text-6xl mb-4 roots-shake" style={{ color: '#DC2626' }}>
              ⚠️
            </div>

            {/* Title */}
            <h1 
              className="text-3xl font-bold mb-4"
              style={{
                color: '#FCD34D',
                fontFamily: 'Bebas Neue, sans-serif',
                letterSpacing: '2px',
                textShadow: '0 0 20px rgba(252, 211, 77, 0.3)',
              }}
            >
              Babylon System Error
            </h1>

            {/* Message */}
            <p 
              className="mb-6"
              style={{
                color: '#F3E7C3',
                fontFamily: 'Ubuntu, sans-serif',
                lineHeight: '1.6',
              }}
            >
              Something went wrong in the matrix, but don't worry!
              Every little thing gonna be alright.
            </p>

            {/* Error Details */}
            {this.state.error && (
              <div 
                className="mb-6 p-4 rounded-lg text-left"
                style={{
                  background: 'rgba(220, 38, 38, 0.1)',
                  border: '1px solid rgba(220, 38, 38, 0.3)',
                }}
              >
                <p className="text-sm font-mono" style={{ color: '#FCA5A5' }}>
                  {this.state.error.toString()}
                </p>
                {import.meta.env.DEV && this.state.errorInfo && (
                  <details className="mt-2">
                    <summary 
                      className="cursor-pointer text-xs"
                      style={{ color: '#FCD34D' }}
                    >
                      Stack Trace
                    </summary>
                    <pre 
                      className="mt-2 text-xs overflow-auto max-h-40"
                      style={{ color: '#F3E7C3' }}
                    >
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-6 py-3 rounded-lg font-semibold transition-all hover:scale-105"
                style={{
                  background: 'linear-gradient(135deg, #16A34A, #FCD34D, #DC2626)',
                  backgroundSize: '200% 200%',
                  animation: 'rasta-wave 3s ease infinite',
                  color: '#000',
                  border: '2px solid rgba(0, 0, 0, 0.3)',
                  fontFamily: 'Bebas Neue, sans-serif',
                  letterSpacing: '1px',
                }}
              >
                Try Again
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 rounded-lg font-semibold transition-all hover:scale-105"
                style={{
                  background: 'rgba(252, 211, 77, 0.2)',
                  border: '2px solid rgba(252, 211, 77, 0.5)',
                  color: '#FCD34D',
                  fontFamily: 'Bebas Neue, sans-serif',
                  letterSpacing: '1px',
                }}
              >
                Go Home
              </button>
            </div>

            {/* Decorative Elements */}
            <div className="mt-8 flex justify-center space-x-3 text-2xl opacity-50">
              <span className="positive-vibration" style={{ color: '#DC2626' }}>☮</span>
              <span className="leaf-sway" style={{ color: '#FCD34D' }}>🌿</span>
              <span className="one-love-beat" style={{ color: '#16A34A' }}>♥</span>
            </div>

            {/* Quote */}
            <p 
              className="mt-4 text-xs opacity-60"
              style={{ color: '#F3E7C3' }}
            >
              "In this bright future, you can't forget your past" - Bob Marley
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;