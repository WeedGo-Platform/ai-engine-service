#!/bin/bash

# Create remaining Pot Palace components
BASE_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/weedgo-commerce/src/templates/pot-palace/components"

# Badge Component
cat > "$BASE_DIR/Badge.tsx" << 'EOF'
import React from 'react';
import { IBadgeProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceBadge: React.FC<IBadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className
}) => {
  const variants = {
    primary: 'bg-green-100 text-green-800 border-green-300',
    secondary: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    success: 'bg-green-500 text-white',
    danger: 'bg-red-100 text-red-800 border-red-300',
    warning: 'bg-orange-100 text-orange-800 border-orange-300',
    info: 'bg-blue-100 text-blue-800 border-blue-300'
  };

  const sizes = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-sm',
    md: 'px-3 py-1.5 text-base',
    lg: 'px-4 py-2 text-lg'
  };

  return (
    <span className={clsx(
      'inline-flex items-center font-bold rounded-full border-2',
      variants[variant],
      sizes[size],
      'animate-pulse',
      className
    )}>
      {children}
    </span>
  );
};
EOF

# Logo Component
cat > "$BASE_DIR/Logo.tsx" << 'EOF'
import React from 'react';
import { ILogoProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceLogo: React.FC<ILogoProps> = ({
  size = 'md',
  variant = 'full',
  className
}) => {
  const sizes = {
    xs: 'h-6',
    sm: 'h-8',
    md: 'h-12',
    lg: 'h-16',
    xl: 'h-20'
  };

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <span className={clsx('text-green-600', sizes[size])} style={{ fontSize: 'inherit' }}>
        🌿
      </span>
      {variant === 'full' && (
        <span className={clsx(
          'font-display font-bold bg-gradient-to-r from-green-600 to-yellow-500 bg-clip-text text-transparent',
          sizes[size]
        )}>
          Pot Palace
        </span>
      )}
    </div>
  );
};
EOF

# Input Component
cat > "$BASE_DIR/Input.tsx" << 'EOF'
import React from 'react';
import { IInputProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceInput: React.FC<IInputProps> = ({
  value,
  onChange,
  placeholder,
  type = 'text',
  error,
  label,
  required,
  disabled,
  className,
  icon
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-bold text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-600">
            {icon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={clsx(
            'w-full px-4 py-3 rounded-xl border-3',
            'bg-white text-gray-800',
            'placeholder-gray-400',
            'transition-all duration-300',
            'focus:outline-none focus:ring-4',
            icon && 'pl-10',
            error
              ? 'border-red-500 focus:ring-red-200'
              : 'border-green-300 focus:border-green-500 focus:ring-green-200',
            disabled && 'bg-gray-100 cursor-not-allowed',
            className
          )}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-500 font-semibold">{error}</p>
      )}
    </div>
  );
};
EOF

# Create stub files for remaining components
components=(
  "Skeleton"
  "Modal"
  "Header"
  "Footer"
  "Breadcrumbs"
  "SearchBar"
  "FilterPanel"
  "AdvancedSearch"
  "ProductRecommendations"
  "CartItem"
  "ChatInterface"
  "ChatBubble"
  "ProductReviews"
  "ReviewForm"
  "ReviewItem"
  "LoadingScreen"
  "OptimizedImage"
  "StoreSelector"
  "LanguageSelector"
  "WishlistButton"
  "ErrorBoundary"
  "Hero"
  "CategoryCard"
)

for component in "${components[@]}"; do
  if [ ! -f "$BASE_DIR/$component.tsx" ]; then
    cat > "$BASE_DIR/$component.tsx" << EOF
import React from 'react';
import { I${component}Props } from '../../types';

export const PotPalace${component}: React.FC<I${component}Props> = (props) => {
  // TODO: Implement Pot Palace themed ${component}
  // This is a placeholder implementation
  return (
    <div className="pot-palace-${component,,}">
      {/* Implement ${component} with Pot Palace styling */}
      <div>PotPalace ${component}</div>
    </div>
  );
};
EOF
  fi
done

echo "✅ All Pot Palace components created!"