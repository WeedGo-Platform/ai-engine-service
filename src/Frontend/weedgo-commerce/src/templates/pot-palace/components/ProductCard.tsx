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
        'bg-white rounded-xl shadow-md hover:shadow-lg',
        'transform transition-all duration-300 hover:translate-y-[-4px]',
        'border border-[#E5E7EB] overflow-hidden relative group cursor-pointer',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onQuickView?.(product)}
    >
      {/* Clean Badges */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-2">
        {isOnSale && (
          <span className="bg-[#DC2626] text-white px-3 py-1 rounded-md text-xs font-semibold shadow-sm">
            {discountPercentage}% OFF
          </span>
        )}
        {product.thc_content > 20 && (
          <span className="bg-[#2D5F3F] text-white px-3 py-1 rounded-md text-xs font-semibold shadow-sm">
            HIGH POTENCY
          </span>
        )}
        {product.quantity_available < 10 && product.quantity_available > 0 && (
          <span className="bg-[#D97706] text-white px-3 py-1 rounded-md text-xs font-semibold shadow-sm">
            LOW STOCK
          </span>
        )}
      </div>

      {/* Wishlist Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
        }}
        className="absolute top-3 right-3 z-10 bg-white/90 backdrop-blur p-2 rounded-full shadow-sm hover:shadow-md transition-all border border-[#E5E7EB]"
      >
        <svg className={clsx("w-5 h-5 transition-colors", isHovered ? "fill-[#DC2626] stroke-[#DC2626]" : "fill-none stroke-[#6B7280]")} viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </button>

      {/* Product Image */}
      <div className="relative h-56 overflow-hidden bg-[#F9FAFB]">
        {!imageError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className={clsx(
              'w-full h-full object-cover transition-transform duration-300',
              isHovered && 'scale-105'
            )}
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-20 h-20 text-[#D1D5DB]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}

        {/* Quick Actions Overlay */}
        <div className={clsx(
          'absolute inset-0 bg-[#2D5F3F]/90 flex items-end justify-center gap-3 p-4 transition-all duration-300',
          isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-full'
        )}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart(product);
            }}
            className="bg-white hover:bg-[#C9A86A] text-[#2D5F3F] hover:text-white px-6 py-2.5 rounded-lg font-semibold transform hover:translate-y-[-2px] transition-all shadow-md text-sm"
          >
            Add to Cart
          </button>
        </div>
      </div>

      {/* Product Info */}
      <div className="p-5 bg-white">
        {/* Category & Brand */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs bg-[#2D5F3F]/10 text-[#2D5F3F] px-2.5 py-1 rounded-md font-medium">
            {product.category}
          </span>
          <span className="text-xs text-[#6B7280]">
            by {product.brand}
          </span>
        </div>

        {/* Product Name */}
        <h3 className="font-semibold text-lg text-[#1F2937] mb-2 line-clamp-2">
          {product.name}
        </h3>

        {/* THC/CBD Content */}
        <div className="flex items-center gap-4 mb-3">
          <span className="flex items-center gap-1">
            <span className="font-medium text-[#6B7280] text-xs">THC:</span>
            <span className="font-semibold text-[#2D5F3F] text-sm">{product.thc_content}%</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="font-medium text-[#6B7280] text-xs">CBD:</span>
            <span className="font-semibold text-[#2D5F3F] text-sm">{product.cbd_content}%</span>
          </span>
        </div>

        {/* Effects */}
        {product.effects && product.effects.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {product.effects.slice(0, 3).map((effect, idx) => (
              <span key={idx} className="text-xs bg-[#C9A86A]/10 text-[#C9A86A] px-2 py-0.5 rounded-md font-medium">
                {effect}
              </span>
            ))}
          </div>
        )}

        {/* Rating */}
        {product.rating && (
          <div className="flex items-center gap-1 mb-3">
            <div className="flex text-[#C9A86A]">
              {[...Array(5)].map((_, i) => (
                <svg key={i} className="w-4 h-4" fill={i < Math.floor(product.rating!) ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              ))}
            </div>
            <span className="text-xs text-[#6B7280]">
              ({product.reviews_count})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-end justify-between mt-4 pt-4 border-t border-[#E5E7EB]">
          <div>
            {isOnSale ? (
              <>
                <span className="text-[#6B7280] line-through text-sm font-medium">
                  ${product.price.toFixed(2)}
                </span>
                <span className="text-2xl font-bold text-[#DC2626] ml-2">
                  ${product.sale_price!.toFixed(2)}
                </span>
              </>
            ) : (
              <span className="text-2xl font-bold text-[#2D5F3F]">
                ${product.price.toFixed(2)}
              </span>
            )}
            {product.unit_weight && (
              <span className="text-xs text-[#6B7280] ml-1">
                /{product.unit_weight}
              </span>
            )}
          </div>

          {/* Stock Status */}
          <div className="text-xs font-medium">
            {product.in_stock ? (
              <span className="text-[#059669]">
                In Stock
              </span>
            ) : (
              <span className="text-[#DC2626]">
                Sold Out
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
