import React, { useState } from 'react';
import { IProductCardProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceProductCard: React.FC<IProductCardProps> = ({
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
        'bg-yellow-50 rounded-3xl shadow-lg hover:shadow-2xl',
        'transform transition-all duration-500 hover:scale-105 hover:rotate-1',
        'border-4 border-purple-400 overflow-hidden relative group cursor-pointer',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onQuickView?.(product)}
    >
      {/* Fun Badges */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-2">
        {isOnSale && (
          <span className="bg-red-500 text-white px-4 py-2 rounded-full text-sm font-black animate-pulse shadow-lg transform rotate-[-5deg]">
            🔥 {discountPercentage}% OFF!
          </span>
        )}
        {product.thc_content > 20 && (
          <span className="bg-purple-600 text-white px-4 py-2 rounded-full text-sm font-black shadow-lg transform rotate-[3deg]">
            💪 POTENT AF
          </span>
        )}
        {product.quantity_available < 10 && product.quantity_available > 0 && (
          <span className="bg-orange-500 text-white px-4 py-2 rounded-full text-sm font-black animate-bounce shadow-lg">
            🏃 ALMOST GONE!
          </span>
        )}
      </div>

      {/* Wishlist Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
        }}
        className="absolute top-3 right-3 z-10 bg-white/90 backdrop-blur p-3 rounded-full shadow-lg hover:scale-125 transition-transform border-3 border-lime-400"
      >
        <span className="text-3xl">{isHovered ? '💚' : '🤍'}</span>
      </button>

      {/* Product Image */}
      <div className="relative h-56 overflow-hidden bg-lime-100">
        {!imageError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className={clsx(
              'w-full h-full object-cover transition-transform duration-700',
              isHovered && 'scale-125 rotate-3'
            )}
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-8xl animate-pulse">
            🌿
          </div>
        )}

        {/* Quick Actions Overlay */}
        <div className={clsx(
          'absolute inset-0 bg-purple-900/80 flex items-end justify-center gap-3 p-5 transition-all duration-300',
          isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-full'
        )}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart(product);
            }}
            className="bg-lime-500 hover:bg-lime-400 text-purple-900 px-6 py-3 rounded-full font-black transform hover:scale-110 transition-all shadow-lg border-3 border-lime-600 uppercase"
          >
            Add to Cart 🛒
          </button>
        </div>
      </div>

      {/* Product Info */}
      <div className="p-5 bg-white">
        {/* Category & Brand */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs bg-purple-100 text-purple-800 px-3 py-1 rounded-full font-black uppercase">
            {product.category}
          </span>
          <span className="text-xs text-orange-600 font-bold">
            by {product.brand}
          </span>
        </div>

        {/* Product Name */}
        <h3 className="font-black text-xl text-purple-900 mb-2 line-clamp-2 uppercase">
          {product.name}
        </h3>

        {/* THC/CBD Content */}
        <div className="flex items-center gap-4 mb-3">
          <span className="flex items-center gap-1">
            <span className="font-black text-lime-600">THC:</span>
            <span className="font-black text-purple-900 text-lg">{product.thc_content}%</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="font-black text-blue-600">CBD:</span>
            <span className="font-black text-purple-900 text-lg">{product.cbd_content}%</span>
          </span>
        </div>

        {/* Effects */}
        {product.effects && product.effects.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {product.effects.slice(0, 3).map((effect, idx) => (
              <span key={idx} className="text-xs bg-orange-100 text-orange-800 px-3 py-1 rounded-lg font-bold">
                ✨ {effect}
              </span>
            ))}
          </div>
        )}

        {/* Rating */}
        {product.rating && (
          <div className="flex items-center gap-1 mb-3">
            <div className="flex text-2xl">
              {[...Array(5)].map((_, i) => (
                <span key={i}>
                  {i < Math.floor(product.rating!) ? '⭐' : '☆'}
                </span>
              ))}
            </div>
            <span className="text-sm text-purple-600 font-bold">
              ({product.reviews_count})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-end justify-between mt-4 pt-4 border-t-3 border-purple-200">
          <div>
            {isOnSale ? (
              <>
                <span className="text-gray-500 line-through text-sm font-bold">
                  ${product.price.toFixed(2)}
                </span>
                <span className="text-3xl font-black text-red-500 ml-2">
                  ${product.sale_price!.toFixed(2)}
                </span>
              </>
            ) : (
              <span className="text-3xl font-black text-lime-600">
                ${product.price.toFixed(2)}
              </span>
            )}
            {product.unit_weight && (
              <span className="text-xs text-purple-600 ml-1 font-bold">
                /{product.unit_weight}
              </span>
            )}
          </div>

          {/* Stock Status */}
          <div className="text-sm font-black">
            {product.in_stock ? (
              <span className="text-lime-600">
                ✅ IN STOCK
              </span>
            ) : (
              <span className="text-red-500">
                ❌ SOLD OUT
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
