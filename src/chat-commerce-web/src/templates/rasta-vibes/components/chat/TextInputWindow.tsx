import React, { useState, useRef, useEffect } from 'react';

interface TextInputWindowProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
  autoFocus?: boolean;
}

const TextInputWindow: React.FC<TextInputWindowProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Express yourself...",
  maxLength = 500,
  disabled = false,
  autoFocus = false,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !disabled) {
      onSubmit();
    }
  };

  return (
    <div className="relative">
      {/* Input Container */}
      <div 
        className="relative overflow-hidden rounded-xl transition-all"
        style={{
          background: isFocused 
            ? 'linear-gradient(135deg, rgba(252, 211, 77, 0.15) 0%, rgba(252, 211, 77, 0.05) 100%)'
            : 'rgba(26, 26, 26, 0.6)',
          border: `2px solid ${isFocused ? 'rgba(252, 211, 77, 0.5)' : 'rgba(252, 211, 77, 0.2)'}`,
          boxShadow: isFocused ? '0 0 30px rgba(252, 211, 77, 0.2)' : 'none',
        }}
      >
        {/* Animated Border Gradient */}
        {isFocused && (
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(252, 211, 77, 0.2), transparent)',
              animation: 'jah-shimmer 2s linear infinite',
            }}
          />
        )}

        {/* Decorative Icon */}
        <div 
          className="absolute left-3 top-1/2 transform -translate-y-1/2 text-xl"
          style={{ 
            color: isFocused ? '#FCD34D' : '#F3E7C3',
            opacity: 0.6,
          }}
        >
          ✍️
        </div>

        {/* Input Field */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          maxLength={maxLength}
          disabled={disabled}
          className="w-full px-12 py-3 bg-transparent outline-none"
          style={{
            color: '#FCD34D',
            fontFamily: 'Ubuntu, sans-serif',
          }}
        />

        {/* Character Counter */}
        <div 
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs"
          style={{ 
            color: value.length > maxLength * 0.9 ? '#DC2626' : '#FCD34D',
            opacity: 0.5,
          }}
        >
          {value.length}/{maxLength}
        </div>
      </div>

      {/* Helper Text */}
      {isFocused && (
        <div 
          className="mt-1 text-xs opacity-60 smooth-fade-in"
          style={{ color: '#16A34A' }}
        >
          Press Enter to send your message • Spread love and positivity
        </div>
      )}
    </div>
  );
};

export default TextInputWindow;