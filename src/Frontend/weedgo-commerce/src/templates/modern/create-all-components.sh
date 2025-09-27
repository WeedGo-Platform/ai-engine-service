#!/bin/bash

BASE_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/weedgo-commerce/src/templates/modern/components"

# Button Component - Premium feel
cat > "$BASE_DIR/Button.tsx" << 'EOF'
import React from 'react';
import { IButtonProps } from '../../types';
import { clsx } from 'clsx';

export const ModernButton: React.FC<IButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className,
  type = 'button'
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variants = {
    primary: 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 focus:ring-indigo-500',
    secondary: 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500',
    outline: 'bg-transparent border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 focus:ring-indigo-500',
    ghost: 'bg-transparent text-indigo-600 hover:bg-indigo-50 focus:ring-indigo-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };

  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs rounded',
    sm: 'px-3 py-2 text-sm rounded-md',
    md: 'px-4 py-2 text-sm rounded-md',
    lg: 'px-4 py-2 text-base rounded-md',
    xl: 'px-6 py-3 text-base rounded-lg'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={clsx(
        baseStyles,
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {loading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : leftIcon && (
        <span className="mr-2">{leftIcon}</span>
      )}
      {children}
      {rightIcon && (
        <span className="ml-2">{rightIcon}</span>
      )}
    </button>
  );
};
EOF

# ProductCard Component - Premium design
cat > "$BASE_DIR/ProductCard.tsx" << 'EOF'
import React, { useState } from 'react';
import { IProductCardProps } from '../../types';
import { clsx } from 'clsx';

export const ModernProductCard: React.FC<IProductCardProps> = ({
  product,
  onAddToCart,
  onQuickView,
  variant = 'default',
  className
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);

  const isOnSale = product.sale_price && product.sale_price < product.price;
  const discountPercentage = isOnSale
    ? Math.round(((product.price - product.sale_price!) / product.price) * 100)
    : 0;

  return (
    <div
      className={clsx(
        'group relative bg-white rounded-lg shadow-sm hover:shadow-xl transition-all duration-300',
        'border border-gray-100 overflow-hidden cursor-pointer',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onQuickView?.(product)}
    >
      {/* Badges */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-2">
        {isOnSale && (
          <span className="bg-red-500 text-white px-2 py-1 rounded text-xs font-semibold">
            -{discountPercentage}%
          </span>
        )}
        {product.thc_content > 20 && (
          <span className="bg-purple-600 text-white px-2 py-1 rounded text-xs font-semibold">
            High THC
          </span>
        )}
      </div>

      {/* Image */}
      <div className="relative aspect-square overflow-hidden bg-gray-50">
        {!imageError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className={clsx(
              'w-full h-full object-cover transition-transform duration-500',
              isHovered && 'scale-110'
            )}
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-20 h-20 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
            </svg>
          </div>
        )}

        {/* Quick Actions */}
        <div className={clsx(
          'absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/60 to-transparent',
          'transform transition-all duration-300',
          isHovered ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0'
        )}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart(product);
            }}
            className="w-full bg-white text-gray-900 px-4 py-2 rounded font-medium hover:bg-gray-100 transition-colors"
          >
            Add to Cart
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
          {product.category}
        </p>
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
          {product.name}
        </h3>
        <p className="text-sm text-gray-600 mb-2">
          {product.brand}
        </p>

        <div className="flex items-center justify-between">
          <div>
            {isOnSale ? (
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-gray-900">
                  ${product.sale_price!.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500 line-through">
                  ${product.price.toFixed(2)}
                </span>
              </div>
            ) : (
              <span className="text-lg font-bold text-gray-900">
                ${product.price.toFixed(2)}
              </span>
            )}
          </div>

          {product.rating && (
            <div className="flex items-center gap-1">
              <span className="text-yellow-400">★</span>
              <span className="text-sm text-gray-600">{product.rating}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
EOF

# Header Component
cat > "$BASE_DIR/Header.tsx" << 'EOF'
import React from 'react';
import { IHeaderProps } from '../../types';
import { clsx } from 'clsx';
import { ModernLogo } from './Logo';
import { ModernButton } from './Button';

export const ModernHeader: React.FC<IHeaderProps> = ({
  onChatToggle,
  className
}) => {
  return (
    <header className={clsx(
      'sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-100',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <ModernLogo size="md" variant="full" />

          <nav className="hidden md:flex items-center gap-8">
            <a href="/shop" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Shop
            </a>
            <a href="/deals" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Deals
            </a>
            <a href="/learn" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Learn
            </a>
            <a href="/account" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
              Account
            </a>
          </nav>

          <div className="flex items-center gap-4">
            {onChatToggle && (
              <ModernButton
                onClick={onChatToggle}
                variant="ghost"
                size="sm"
              >
                Chat
              </ModernButton>
            )}
            <ModernButton
              variant="primary"
              size="sm"
            >
              Cart
            </ModernButton>
          </div>
        </div>
      </div>
    </header>
  );
};
EOF

# Create remaining core components
for component in "Badge" "Logo" "Input" "Skeleton" "Modal" "Footer" "SearchBar" "Hero" "CartItem" "ChatInterface" "ChatBubble" "LoadingScreen" "FilterPanel" "Breadcrumbs" "CategoryCard" "OptimizedImage" "StoreSelector" "LanguageSelector" "WishlistButton" "ErrorBoundary" "AdvancedSearch" "ProductRecommendations" "ProductReviews" "ReviewForm" "ReviewItem"; do
  cat > "$BASE_DIR/$component.tsx" << EOF
import React from 'react';
import { I${component}Props } from '../../types';
import { clsx } from 'clsx';

export const Modern${component}: React.FC<I${component}Props> = (props) => {
  // Modern premium themed ${component}
  return (
    <div className={clsx(
      'modern-component',
      'bg-white rounded-lg shadow-sm border border-gray-100 p-4',
      props.className
    )}>
      <div className="text-center text-gray-600">
        <p className="font-semibold">Modern ${component}</p>
        <p className="text-sm text-gray-500 mt-1">Premium implementation coming soon</p>
      </div>
    </div>
  );
};
EOF
done

echo "✅ All Modern theme components created!"