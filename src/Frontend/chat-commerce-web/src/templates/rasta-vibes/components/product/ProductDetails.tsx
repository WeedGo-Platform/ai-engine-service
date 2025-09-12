import React, { useState } from 'react';
import { Product } from '../../../../services/productSearch';
import { useCart } from '../../../../contexts/CartContext';
import QuantitySelector from './QuantitySelector';
import ProductRecommendations from './ProductRecommendations';

interface ProductDetailsProps {
  product: Product;
}

const ProductDetails: React.FC<ProductDetailsProps> = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const [imageError, setImageError] = useState(false);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const { addToCart } = useCart();

  const handleAddToCart = async () => {
    setIsAddingToCart(true);
    try {
      await addToCart(product, quantity);
      // Reset quantity after successful add
      setQuantity(1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setIsAddingToCart(false);
    }
  };

  const getStrainBadgeStyle = (strain?: string) => {
    switch (strain?.toLowerCase()) {
      case 'indica':
        return 'bg-gradient-to-r from-red-600 to-red-500 text-white shadow-lg';
      case 'sativa':
        return 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg';
      case 'hybrid':
        return 'bg-gradient-to-r from-yellow-500 to-yellow-400 text-black shadow-lg';
      default:
        return 'bg-gradient-to-r from-gray-600 to-gray-500 text-white shadow-lg';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Main Product Card - Rasta Style */}
      <div className="bg-gradient-to-br from-yellow-50 via-green-50 to-red-50 rounded-2xl overflow-hidden shadow-2xl border-4 border-yellow-400">
        {/* Decorative Header with Rasta stripes */}
        <div className="h-3 bg-gradient-to-r from-green-600 via-yellow-400 to-red-600"></div>
        
        <div className="p-6 md:p-8">
          {/* Header with organic typography */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-6">
            <div className="mb-4 md:mb-0">
              <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-yellow-500 mb-2">
                {product.name}
              </h2>
              {product.brand && (
                <p className="text-sm text-gray-700 font-medium">
                  🌿 Cultivated by {product.brand}
                </p>
              )}
            </div>
            
            {/* Price with Rasta colors */}
            <div className="text-right">
              <div className="text-3xl font-bold text-green-700">
                ${product.price.toFixed(2)}
              </div>
              {product.size && (
                <div className="text-sm text-gray-600 mt-1">
                  {product.size}
                </div>
              )}
            </div>
          </div>

          {/* Product Image with organic border */}
          <div className="relative mb-8 group">
            <div className="absolute -inset-2 bg-gradient-to-r from-green-400 via-yellow-400 to-red-400 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity"></div>
            <div className="relative bg-white rounded-xl p-2 shadow-xl">
              {(product.image_url || product.thumbnail_url) && !imageError ? (
                <img
                  src={product.image_url || product.thumbnail_url}
                  alt={product.name}
                  className="w-full h-64 object-contain rounded-lg"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="w-full h-64 flex items-center justify-center bg-gradient-to-br from-yellow-100 to-green-100 rounded-lg">
                  <div className="text-center">
                    <div className="text-6xl mb-2">🌿</div>
                    <p className="text-gray-600 font-medium">Natural Vibes</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Strain and Category Badges */}
          <div className="flex flex-wrap gap-3 mb-6">
            {product.strain_type && (
              <span className={`px-4 py-2 text-sm font-bold rounded-full ${getStrainBadgeStyle(product.strain_type)}`}>
                {product.strain_type} ✨
              </span>
            )}
            {product.category && (
              <span className="px-4 py-2 text-sm font-bold bg-gradient-to-r from-green-500 to-green-400 text-white rounded-full shadow-lg">
                {product.category} 🍃
              </span>
            )}
            {product.plant_type && (
              <span className="px-4 py-2 text-sm font-bold bg-gradient-to-r from-yellow-500 to-yellow-400 text-black rounded-full shadow-lg">
                {product.plant_type} ☀️
              </span>
            )}
          </div>

          {/* THC/CBD Content - Colorful bars */}
          <div className="grid grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl p-4 shadow-lg border-2 border-green-300">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-gray-700">THC Power</span>
                <span className="text-2xl">🔥</span>
              </div>
              <div className="text-3xl font-bold text-green-600 mb-2">
                {product.thc_content || 0}%
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((product.thc_content || 0) * 3, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-4 shadow-lg border-2 border-yellow-300">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-gray-700">CBD Healing</span>
                <span className="text-2xl">💚</span>
              </div>
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {product.cbd_content || 0}%
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((product.cbd_content || 0) * 10, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Description with organic styling */}
          {product.description && (
            <div className="mb-8 bg-white rounded-xl p-6 shadow-lg border-l-4 border-green-500">
              <h3 className="text-lg font-bold text-green-700 mb-3 flex items-center gap-2">
                <span className="text-2xl">📖</span> About This Herb
              </h3>
              <p className="text-gray-700 leading-relaxed">
                {product.description}
              </p>
            </div>
          )}

          {/* Terpenes - Colorful pills */}
          {product.terpenes && product.terpenes.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-bold text-green-700 mb-3 flex items-center gap-2">
                <span className="text-2xl">🌺</span> Terpene Profile
              </h3>
              <div className="flex flex-wrap gap-2">
                {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => {
                  const colors = [
                    'from-red-400 to-red-500',
                    'from-green-400 to-green-500',
                    'from-yellow-400 to-yellow-500',
                    'from-purple-400 to-purple-500',
                    'from-pink-400 to-pink-500',
                  ];
                  const colorClass = colors[index % colors.length];
                  return (
                    <span 
                      key={index}
                      className={`px-3 py-1 text-sm font-medium text-white bg-gradient-to-r ${colorClass} rounded-full shadow-md`}
                    >
                      {terpene}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Add to Cart Section */}
          <div className="bg-gradient-to-r from-green-100 via-yellow-100 to-red-100 rounded-xl p-6 shadow-inner">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <QuantitySelector
                  quantity={quantity}
                  onChange={setQuantity}
                />
                <div className="text-center md:text-left">
                  <div className="text-sm text-gray-600">Total Vibes</div>
                  <div className="text-2xl font-bold text-green-700">
                    ${(product.price * quantity).toFixed(2)}
                  </div>
                </div>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={isAddingToCart}
                className="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 text-white font-bold text-lg rounded-full hover:shadow-2xl transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center gap-2"
              >
                {isAddingToCart ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Adding...
                  </>
                ) : (
                  <>
                    <span>Add to Basket</span>
                    <span className="text-2xl">🛒</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Peace message */}
          <div className="text-center mt-6 text-sm text-gray-600 font-medium">
            One Love • One Heart • Let's Get Together 💛💚❤️
          </div>
        </div>
      </div>

      {/* Product Recommendations */}
      <div className="mt-8">
        <ProductRecommendations currentProduct={product} />
      </div>
    </div>
  );
};

export default ProductDetails;