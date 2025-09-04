import React, { useState } from 'react';
import {
  Plus,
  Minus,
  ShoppingCart,
  Star,
  Info,
  Package,
  AlertCircle,
  TrendingUp,
  Leaf
} from 'lucide-react';

interface Product {
  id: number | string;
  product_name: string;
  brand: string;
  category: string;
  sub_category?: string;
  unit_price: number;
  size?: string;
  thc_max_percent?: number;
  cbd_max_percent?: number;
  thc_range?: string;
  cbd_range?: string;
  short_description?: string;
  long_description?: string;
  inventory_count?: number;
  in_stock?: boolean;
  effects?: string[];
  terpenes?: string[];
  strain_type?: string;
  image_url?: string;
  rating?: number;
  review_count?: number;
}

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product, quantity: number) => void;
  onShowDetails?: (product: Product) => void;
  compact?: boolean;
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onAddToCart,
  onShowDetails,
  compact = false
}) => {
  const [quantity, setQuantity] = useState(1);
  const [isHovered, setIsHovered] = useState(false);
  const [showFullDescription, setShowFullDescription] = useState(false);

  const handleIncrement = () => {
    if (product.inventory_count && quantity < product.inventory_count) {
      setQuantity(quantity + 1);
    } else if (!product.inventory_count) {
      setQuantity(quantity + 1);
    }
  };

  const handleDecrement = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const handleAddToCart = () => {
    if (onAddToCart) {
      onAddToCart(product, quantity);
    }
  };

  const getStrainIcon = (strain?: string) => {
    switch (strain?.toLowerCase()) {
      case 'sativa':
        return '🌞';
      case 'indica':
        return '🌙';
      case 'hybrid':
        return '🌤️';
      default:
        return '🍃';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'flower':
        return '🌺';
      case 'edibles':
        return '🍪';
      case 'vapes':
        return '💨';
      case 'extracts':
        return '💧';
      case 'pre-rolls':
        return '🚬';
      case 'topicals':
        return '🧴';
      default:
        return '📦';
    }
  };

  if (compact) {
    // Compact view for chat interface
    return (
      <div
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-3 hover:shadow-md transition-shadow"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="flex gap-3">
          {/* Product Image */}
          {product.image_url && (
            <div className="flex-shrink-0">
              <img
                src={product.image_url}
                alt={product.product_name}
                className="w-20 h-20 object-cover rounded-md"
              />
            </div>
          )}
          
          {/* Product Info */}
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-semibold text-sm text-gray-900 truncate">
                  {product.product_name}
                </h4>
                <p className="text-xs text-gray-600">{product.brand}</p>
              </div>
              <span className="text-lg font-bold text-green-600">
                ${product.unit_price.toFixed(2)}
              </span>
            </div>
            
            {/* THC/CBD Info */}
            <div className="flex gap-3 mt-1">
              {product.thc_range && (
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                  THC: {product.thc_range}
                </span>
              )}
              {product.cbd_range && product.cbd_max_percent > 0 && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                  CBD: {product.cbd_range}
                </span>
              )}
              {product.strain_type && (
                <span className="text-xs text-gray-600">
                  {getStrainIcon(product.strain_type)} {product.strain_type}
                </span>
              )}
            </div>
            
            {/* Quantity Controls */}
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDecrement}
                  className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center"
                  disabled={quantity <= 1}
                >
                  <Minus className="w-3 h-3" />
                </button>
                <span className="text-sm font-medium w-8 text-center">{quantity}</span>
                <button
                  onClick={handleIncrement}
                  className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center"
                  disabled={product.inventory_count ? quantity >= product.inventory_count : false}
                >
                  <Plus className="w-3 h-3" />
                </button>
              </div>
              
              <button
                onClick={handleAddToCart}
                className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 transition-colors"
                disabled={product.in_stock === false}
              >
                <ShoppingCart className="w-3 h-3" />
                Add
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full card view
  return (
    <div
      className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Product Image */}
      {product.image_url && (
        <div className="relative h-48 bg-gray-100">
          <img
            src={product.image_url}
            alt={product.product_name}
            className="w-full h-full object-cover"
          />
          {/* Category Badge */}
          <div className="absolute top-2 left-2 bg-white/90 px-2 py-1 rounded-full text-xs font-medium">
            {getCategoryIcon(product.category)} {product.category}
          </div>
          {/* Stock Status */}
          {product.in_stock === false && (
            <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs">
              Out of Stock
            </div>
          )}
        </div>
      )}

      <div className="p-4">
        {/* Product Name and Brand */}
        <div className="mb-2">
          <h3 className="font-bold text-lg text-gray-900">{product.product_name}</h3>
          <p className="text-sm text-gray-600">{product.brand}</p>
        </div>

        {/* Rating */}
        {product.rating && (
          <div className="flex items-center gap-1 mb-2">
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={`w-4 h-4 ${
                    i < Math.floor(product.rating || 0)
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-gray-600">
              ({product.review_count || 0} reviews)
            </span>
          </div>
        )}

        {/* Description */}
        {product.short_description && (
          <p className="text-sm text-gray-700 mb-3">
            {showFullDescription ? product.long_description : product.short_description}
            {product.long_description && product.long_description !== product.short_description && (
              <button
                onClick={() => setShowFullDescription(!showFullDescription)}
                className="ml-1 text-blue-600 hover:underline text-xs"
              >
                {showFullDescription ? 'Show less' : 'Show more'}
              </button>
            )}
          </p>
        )}

        {/* THC/CBD Content */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {product.thc_range && (
            <div className="bg-purple-50 rounded-md px-3 py-2">
              <div className="text-xs text-purple-600 font-medium">THC</div>
              <div className="text-sm font-bold text-purple-800">{product.thc_range}</div>
            </div>
          )}
          {product.cbd_range && product.cbd_max_percent > 0 && (
            <div className="bg-blue-50 rounded-md px-3 py-2">
              <div className="text-xs text-blue-600 font-medium">CBD</div>
              <div className="text-sm font-bold text-blue-800">{product.cbd_range}</div>
            </div>
          )}
        </div>

        {/* Effects */}
        {product.effects && product.effects.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-gray-600 mb-1">Effects:</div>
            <div className="flex flex-wrap gap-1">
              {product.effects.slice(0, 3).map((effect, idx) => (
                <span
                  key={idx}
                  className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full"
                >
                  {effect}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Price and Size */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-2xl font-bold text-green-600">
              ${product.unit_price.toFixed(2)}
            </div>
            {product.size && (
              <div className="text-xs text-gray-600">{product.size}</div>
            )}
          </div>
          {product.strain_type && (
            <div className="text-right">
              <div className="text-2xl">{getStrainIcon(product.strain_type)}</div>
              <div className="text-xs text-gray-600">{product.strain_type}</div>
            </div>
          )}
        </div>

        {/* Quantity Selector and Add to Cart */}
        <div className="flex items-center gap-3">
          <div className="flex items-center border border-gray-300 rounded-md">
            <button
              onClick={handleDecrement}
              className="p-2 hover:bg-gray-100 transition-colors"
              disabled={quantity <= 1}
            >
              <Minus className="w-4 h-4" />
            </button>
            <span className="px-4 py-2 font-medium">{quantity}</span>
            <button
              onClick={handleIncrement}
              className="p-2 hover:bg-gray-100 transition-colors"
              disabled={product.inventory_count ? quantity >= product.inventory_count : false}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          <button
            onClick={handleAddToCart}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400"
            disabled={product.in_stock === false}
          >
            <ShoppingCart className="w-5 h-5" />
            Add to Cart
          </button>
        </div>

        {/* Stock Info */}
        {product.inventory_count && product.inventory_count < 10 && (
          <div className="mt-2 flex items-center gap-1 text-xs text-orange-600">
            <AlertCircle className="w-3 h-3" />
            Only {product.inventory_count} left in stock
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductCard;