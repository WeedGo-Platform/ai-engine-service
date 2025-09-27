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
          <span className="bg-blue-500 text-white px-2 py-1 rounded text-xs font-semibold">
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
