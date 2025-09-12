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

  if (isLoading) {
    return (
      <div className="bg-black/90 backdrop-blur-xl rounded-lg border border-green-500/30 p-6">
        <h3 className="text-lg font-mono font-bold text-green-400 mb-4">LOADING_RECOMMENDATIONS...</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-black/50 border border-green-500/20 rounded-lg p-4 animate-pulse">
              <div className="w-full h-32 bg-green-500/10 rounded mb-3"></div>
              <div className="h-4 bg-green-500/10 rounded mb-2"></div>
              <div className="h-3 bg-green-500/10 rounded w-2/3"></div>
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
    <div className="bg-black/90 backdrop-blur-xl rounded-lg border border-green-500/30 shadow-[0_0_30px_rgba(34,197,94,0.2)] overflow-hidden">
      <div className="p-6">
        <h3 className="text-lg font-mono font-bold text-green-400 mb-4 flex items-center gap-2">
          <span className="text-green-500 animate-pulse">▶</span>
          RECOMMENDED_PRODUCTS
          <span className="text-xs text-green-300/50 font-normal">({recommendations.length} ITEMS)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {recommendations.map((product) => (
            <div
              key={product.id}
              className="group bg-black/50 border border-green-500/20 rounded-lg overflow-hidden hover:border-green-400/50 transition-all duration-300 hover:shadow-[0_0_15px_rgba(34,197,94,0.3)]"
            >
              {/* Product Image */}
              <div className="relative h-32 bg-gradient-to-br from-gray-900 to-black overflow-hidden">
                {product.image_url || product.thumbnail_url ? (
                  <img
                    src={product.thumbnail_url || product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <svg className="w-12 h-12 text-green-500/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                
                {/* Overlay with scan line effect */}
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="absolute bottom-0 left-0 right-0 h-px bg-green-400 animate-scan"></div>
                </div>
              </div>

              {/* Product Info */}
              <div className="p-3">
                <h4 className="font-mono text-sm text-green-400 font-semibold mb-1 truncate">
                  {product.name}
                </h4>
                
                {/* Strain Type Badge */}
                {product.strain_type && (
                  <span className="inline-block px-2 py-0.5 text-xs font-mono bg-green-900/30 text-green-300 border border-green-500/30 rounded mb-2">
                    {product.strain_type.toUpperCase()}
                  </span>
                )}

                {/* THC/CBD Info */}
                <div className="flex justify-between items-center text-xs font-mono text-green-300/70 mb-2">
                  <span>THC: {product.thc_content || 0}%</span>
                  <span>CBD: {product.cbd_content || 0}%</span>
                </div>

                {/* Price and Add Button */}
                <div className="flex items-center justify-between">
                  <span className="text-green-400 font-mono font-bold">
                    ${product.price.toFixed(2)}
                  </span>
                  
                  <button
                    onClick={() => handleQuickAdd(product)}
                    disabled={addingToCart === product.id}
                    className="px-3 py-1 text-xs font-mono bg-green-500/20 text-green-400 border border-green-500/50 rounded hover:bg-green-500/30 hover:border-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {addingToCart === product.id ? (
                      <span className="flex items-center gap-1">
                        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                      </span>
                    ) : (
                      'ADD+'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes scan {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        .animate-scan {
          animation: scan 2s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default ProductRecommendations;