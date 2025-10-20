import React from 'react';
import { getApiUrl } from '../../config/app.config';
import { Plus, Info, Star, TrendingUp, Award, Clock, Leaf, Sparkles } from 'lucide-react';

interface ProductCardProps {
  product: {
    id: string;
    name: string;
    product_name?: string;
    brand?: string;
    price: number;
    retail_price?: number;
    display_price?: string;
    primary_image?: string;
    image_url?: string;
    thc_content?: number;
    cbd_content?: number;
    thc_badge?: string;
    cbd_badge?: string;
    category: string;
    subcategory?: string;
    plant_type?: string;
    strain_type?: string;
    rating?: number;
    review_count?: number;
    quantity_available: number;
    is_featured?: boolean;
    is_new?: boolean;
    is_sale?: boolean;
    sale_price?: number;
    sales_count?: number;
    size?: string;
  };
  onAddToCart: () => void;
  onClick: () => void;
}

export default function ProductCard({ product, onAddToCart, onClick }: ProductCardProps) {
  // Calculate discount percentage if on sale
  const discountPercentage = product.is_sale && product.sale_price && product.retail_price
    ? Math.round(((product.retail_price - product.sale_price) / product.retail_price) * 100)
    : 0;

  // Determine plant type color
  const getPlantTypeColor = (type: string) => {
    const lowerType = type?.toLowerCase() || '';
    if (lowerType.includes('sativa')) return 'bg-orange-500';
    if (lowerType.includes('indica')) return 'bg-purple-500';
    if (lowerType.includes('hybrid')) return 'bg-green-500';
    if (lowerType.includes('cbd')) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg dark:hover:shadow-2xl transition-all duration-300 cursor-pointer group border border-gray-100 dark:border-gray-700">
      <div onClick={onClick} className="relative">
        {/* Product Image */}
        <div className="relative overflow-hidden rounded-t-lg bg-gray-100 dark:bg-gray-700">
          <img
            src={product.image_url || '/placeholder-product.jpg'}
            alt={product.name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-product.jpg';
            }}
          />

          {/* Top Badges - Featured, New, Sale */}
          <div className="absolute top-2 left-2 flex flex-wrap gap-1 max-w-[60%]">
            {product.is_featured && (
              <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded-full flex items-center gap-1 shadow-sm">
                <Award className="w-3 h-3" />
                Featured
              </span>
            )}
            {product.is_new && (
              <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded-full flex items-center gap-1 shadow-sm">
                <Sparkles className="w-3 h-3" />
                New
              </span>
            )}
            {product.is_sale && discountPercentage > 0 && (
              <span className="px-2 py-1 bg-red-500 text-white text-xs rounded-full flex items-center gap-1 shadow-sm animate-pulse">
                <TrendingUp className="w-3 h-3" />
                {discountPercentage}% OFF
              </span>
            )}
            {product.sales_count && product.sales_count > 50 && (
              <span className="px-2 py-1 bg-pink-500 text-white text-xs rounded-full shadow-sm">
                Hot Item
              </span>
            )}
          </div>

          {/* Stock Status */}
          <div className="absolute top-2 right-2">
            {product.quantity_available === 0 ? (
              <span className="px-2 py-1 bg-red-500 text-white text-xs rounded-full shadow-sm">
                Out of Stock
              </span>
            ) : product.quantity_available < 10 ? (
              <span className="px-2 py-1 bg-orange-500 text-white text-xs rounded-full shadow-sm">
                Only {product.quantity_available} left
              </span>
            ) : product.quantity_available > 100 ? (
              <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full shadow-sm">
                In Stock
              </span>
            ) : null}
          </div>

          {/* Cannabinoid Badges - Bottom of Image */}
          <div className="absolute bottom-2 left-2 right-2 flex justify-between items-end">
            <div className="flex gap-1">
              {(product.thc_content || product.thc_badge) && (
                <span className="px-2 py-1 bg-green-600/90 backdrop-blur-sm text-white text-xs rounded-full font-semibold shadow-sm">
                  THC {product.thc_content ? `${product.thc_content}%` : product.thc_badge}
                </span>
              )}
              {(product.cbd_content || product.cbd_badge) && (
                <span className="px-2 py-1 bg-blue-600/90 backdrop-blur-sm text-white text-xs rounded-full font-semibold shadow-sm">
                  CBD {product.cbd_content ? `${product.cbd_content}%` : product.cbd_badge}
                </span>
              )}
            </div>
            {product.size && (
              <span className="px-2 py-1 bg-gray-800/90 backdrop-blur-sm text-white text-xs rounded-full shadow-sm">
                {product.size}
              </span>
            )}
          </div>
        </div>

        {/* Product Info */}
        <div className="p-4">
          {/* Category and Plant Type */}
          <div className="flex items-center gap-2 mb-2">
            {product.subcategory && (
              <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                {product.subcategory}
              </span>
            )}
            {(product.plant_type || product.strain_type) && (
              <span className={`px-2 py-0.5 text-white text-xs rounded-full ${getPlantTypeColor(product.plant_type || product.strain_type || '')}`}>
                <Leaf className="w-3 h-3 inline mr-1" />
                {product.plant_type || product.strain_type}
              </span>
            )}
          </div>

          {/* Product Name */}
          <h3 className="font-semibold text-gray-800 dark:text-white mb-1 line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
            {product.name || product.product_name}
          </h3>

          {/* Brand */}
          {product.brand && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{product.brand}</p>
          )}

          {/* Rating */}
          {product.rating && (
            <div className="flex items-center gap-1 mb-2">
              <div className="flex">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-4 h-4 ${
                      i < Math.floor(product.rating || 0)
                        ? 'text-yellow-500 fill-current'
                        : 'text-gray-300 dark:text-gray-600'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {product.rating.toFixed(1)}
                {product.review_count && ` (${product.review_count} reviews)`}
              </span>
            </div>
          )}

          {/* Price */}
          <div className="flex items-baseline gap-2">
            {product.is_sale && product.sale_price ? (
              <>
                <span className="text-xl font-bold text-red-600 dark:text-red-400">
                  ${product.sale_price.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400 line-through">
                  ${(product.retail_price || product.price || 0).toFixed(2)}
                </span>
              </>
            ) : (
              <span className="text-xl font-bold text-primary-600 dark:text-primary-400">
                ${(product.retail_price || product.price || 0).toFixed(2)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Add to Cart Button */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAddToCart();
          }}
          disabled={product.quantity_available === 0}
          className="w-full py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
        >
          <Plus className="w-5 h-5" />
          {product.quantity_available === 0 ? 'Out of Stock' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
}