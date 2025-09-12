import React, { useState, useEffect } from 'react';
import { Product, productSearchService } from '../../../../services/productSearch';
import { useCart } from '../../../../contexts/CartContext';

interface ProductRecommendationsProps {
  currentProduct: Product;
  maxRecommendations?: number;
}

const ProductRecommendations: React.FC<ProductRecommendationsProps> = ({
  currentProduct,
  maxRecommendations = 4
}) => {
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { addToCart } = useCart();
  const [addingToCart, setAddingToCart] = useState<string | null>(null);

  useEffect(() => {
    loadRecommendations();
  }, [currentProduct]);

  const loadRecommendations = async () => {
    setIsLoading(true);
    try {
      const products = await productSearchService.loadProducts();
      
      // Filter and score products
      const scoredProducts = products
        .filter(p => p.id !== currentProduct.id)
        .map(product => {
          let score = 0;
          
          // Category matching
          if (product.category === currentProduct.category) score += 5;
          if (product.sub_category === currentProduct.sub_category) score += 3;
          
          // Strain type matching
          if (product.strain_type === currentProduct.strain_type) score += 4;
          
          // Brand matching
          if (product.brand === currentProduct.brand) score += 2;
          
          // Similar THC content
          if (product.thc_content && currentProduct.thc_content) {
            const diff = Math.abs(product.thc_content - currentProduct.thc_content);
            if (diff < 5) score += 3;
            else if (diff < 10) score += 1;
          }
          
          // Price similarity
          const priceDiff = Math.abs(product.price - currentProduct.price);
          if (priceDiff < 10) score += 2;
          else if (priceDiff < 20) score += 1;
          
          return { ...product, relevanceScore: score };
        })
        .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0))
        .slice(0, maxRecommendations);
      
      setRecommendations(scoredProducts);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAdd = async (product: Product) => {
    setAddingToCart(product.id);
    try {
      await addToCart(product, 1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setAddingToCart(null);
    }
  };

  const getStrainEmoji = (strain?: string) => {
    switch (strain?.toLowerCase()) {
      case 'indica': return '😴';
      case 'sativa': return '⚡';
      case 'hybrid': return '☯️';
      default: return '🌿';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-yellow-50 via-green-50 to-red-50 rounded-2xl p-6 shadow-xl border-4 border-yellow-400">
        <h3 className="text-xl font-bold text-green-700 mb-6 flex items-center gap-2">
          <span className="text-2xl animate-spin">🌟</span>
          Loading More Good Vibes...
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white/70 rounded-xl p-4 animate-pulse">
              <div className="w-full h-32 bg-gradient-to-br from-green-200 to-yellow-200 rounded-lg mb-3"></div>
              <div className="h-4 bg-gradient-to-r from-green-200 to-yellow-200 rounded mb-2"></div>
              <div className="h-3 bg-gradient-to-r from-yellow-200 to-red-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-yellow-50 via-green-50 to-red-50 rounded-2xl overflow-hidden shadow-2xl border-4 border-yellow-400">
      {/* Decorative Header */}
      <div className="h-2 bg-gradient-to-r from-green-600 via-yellow-400 to-red-600"></div>
      
      <div className="p-6">
        <h3 className="text-xl font-bold text-green-700 mb-6 flex items-center gap-2">
          <span className="text-2xl">🌈</span>
          More Blessed Herbs
          <span className="text-sm text-gray-600 font-normal">({recommendations.length} selections)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {recommendations.map((product, index) => {
            const colors = [
              'border-green-400',
              'border-yellow-400',
              'border-red-400',
              'border-orange-400',
            ];
            const borderColor = colors[index % colors.length];
            
            return (
              <div
                key={product.id}
                className={`group bg-white rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 border-2 ${borderColor}`}
              >
                {/* Product Image */}
                <div className="relative h-32 bg-gradient-to-br from-yellow-100 to-green-100 overflow-hidden">
                  {product.image_url || product.thumbnail_url ? (
                    <img
                      src={product.thumbnail_url || product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-5xl">🌿</span>
                    </div>
                  )}
                  
                  {/* Hover overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-2 left-2 right-2">
                      <p className="text-white text-xs font-medium truncate">
                        {product.brand || 'Natural Selection'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Product Info */}
                <div className="p-3">
                  <h4 className="font-bold text-sm text-gray-800 mb-1 truncate">
                    {product.name}
                  </h4>
                  
                  {/* Strain Type with emoji */}
                  {product.strain_type && (
                    <div className="flex items-center gap-1 mb-2">
                      <span className="text-lg">{getStrainEmoji(product.strain_type)}</span>
                      <span className="text-xs font-medium text-gray-600">
                        {product.strain_type}
                      </span>
                    </div>
                  )}

                  {/* THC/CBD Info */}
                  <div className="flex justify-between items-center text-xs text-gray-600 mb-3">
                    <span className="flex items-center gap-1">
                      <span className="text-green-600">🔥</span>
                      THC: {product.thc_content || 0}%
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="text-yellow-600">💚</span>
                      CBD: {product.cbd_content || 0}%
                    </span>
                  </div>

                  {/* Price and Add Button */}
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-green-700">
                      ${product.price.toFixed(2)}
                    </span>
                    
                    <button
                      onClick={() => handleQuickAdd(product)}
                      disabled={addingToCart === product.id}
                      className="px-3 py-1.5 text-xs font-bold bg-gradient-to-r from-green-500 to-yellow-500 text-white rounded-full hover:shadow-lg transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                      {addingToCart === product.id ? (
                        <span className="flex items-center gap-1">
                          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        </span>
                      ) : (
                        'Add +'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Peace message */}
        <div className="text-center mt-6 text-sm text-gray-600 font-medium">
          Spread Love & Positive Vibrations 🌍💛💚❤️
        </div>
      </div>
    </div>
  );
};

export default ProductRecommendations;