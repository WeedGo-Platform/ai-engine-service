import React, { useState, useEffect, useRef } from 'react';
import { Product, productSearchService } from '../../../../services/productSearch';
import { ProductRecommendationsProps, ProductRecommendation } from '../../../../types/product.types';
import { useCart } from '../../../../contexts/CartContext';

const ProductRecommendations: React.FC<ProductRecommendationsProps> = ({
  currentProduct,
  onProductSelect,
  onAddToCart,
  maxRecommendations = 6
}) => {
  const [recommendations, setRecommendations] = useState<ProductRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [quantities, setQuantities] = useState<{ [key: string]: number }>({});
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { addToCart } = useCart();

  useEffect(() => {
    const loadRecommendations = async () => {
      setIsLoading(true);
      try {
        const allProducts = await productSearchService.loadProducts();
        
        const scored = allProducts
          .filter(p => p.id !== currentProduct.id)
          .map(product => {
            let score = 0;
            let reasons: string[] = [];

            if (product.category === currentProduct.category) {
              score += 3;
              reasons.push('Related');
            }
            if (product.plant_type === currentProduct.plant_type) {
              score += 2;
              reasons.push('Similar');
            }
            if (product.brand === currentProduct.brand) {
              score += 1;
              reasons.push('Same brand');
            }

            return {
              ...product,
              relevanceScore: score,
              reason: reasons[0] || ''
            } as ProductRecommendation;
          })
          .filter(p => p.relevanceScore > 0)
          .sort((a, b) => b.relevanceScore - a.relevanceScore)
          .slice(0, maxRecommendations);

        setRecommendations(scored);
      } catch (error) {
        console.error('Error loading recommendations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecommendations();
  }, [currentProduct, maxRecommendations]);

  const handleAddToCart = async (product: Product) => {
    const quantity = quantities[product.id] || 1;
    try {
      if (onAddToCart) {
        await onAddToCart(product, quantity);
      } else {
        await addToCart(product, quantity);
      }
      setQuantities(prev => ({ ...prev, [product.id]: 1 }));
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h3 className="text-sm font-medium text-gray-900 uppercase tracking-wider">Similar Products</h3>
        <div className="flex gap-4 overflow-hidden">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex-shrink-0 w-64">
              <div className="aspect-square bg-gray-100 rounded-sm animate-pulse" />
              <div className="pt-4 space-y-2">
                <div className="h-3 bg-gray-100 rounded animate-pulse" />
                <div className="h-3 bg-gray-100 rounded w-2/3 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 uppercase tracking-wider">Similar Products</h3>
        
        {recommendations.length > 3 && (
          <div className="flex gap-2">
            <button
              onClick={scrollLeft}
              className="p-1.5 border border-gray-300 rounded-sm hover:bg-gray-50 transition-colors"
              aria-label="Previous"
            >
              <svg className="w-3 h-3 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={scrollRight}
              className="p-1.5 border border-gray-300 rounded-sm hover:bg-gray-50 transition-colors"
              aria-label="Next"
            >
              <svg className="w-3 h-3 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <div 
        ref={scrollContainerRef}
        className="flex gap-6 overflow-x-auto pb-2 scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {recommendations.map((product) => (
          <div
            key={product.id}
            className="flex-shrink-0 w-64 group"
          >
            {/* Product Image */}
            <div 
              className="aspect-square bg-gray-50 rounded-sm cursor-pointer relative overflow-hidden"
              onClick={() => onProductSelect?.(product)}
            >
              {product.image_url || product.thumbnail_url ? (
                <img
                  src={product.image_url || product.thumbnail_url}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-12 h-12 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              
              {product.reason && (
                <div className="absolute top-2 left-2 px-2 py-1 bg-white/90 backdrop-blur-sm rounded-sm text-xs">
                  {product.reason}
                </div>
              )}
            </div>

            {/* Product Info */}
            <div className="pt-4 space-y-2">
              <div>
                <h4 
                  className="font-light text-gray-900 truncate cursor-pointer hover:text-gray-600 transition-colors"
                  onClick={() => onProductSelect?.(product)}
                  title={product.name}
                >
                  {product.name}
                </h4>
                {product.brand && (
                  <p className="text-xs text-gray-500 uppercase tracking-wider truncate">{product.brand}</p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <p className="text-lg font-light text-gray-900">
                  {formatPrice(product.price)}
                </p>
                
                <button
                  onClick={() => handleAddToCart(product)}
                  disabled={!product.in_stock}
                  className={`px-4 py-1.5 rounded-sm text-xs font-medium transition-all ${
                    product.in_stock
                      ? 'bg-gray-900 hover:bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {product.in_stock ? 'Add' : 'Out'}
                </button>
              </div>

              {/* Minimal product info */}
              <div className="flex gap-2 text-xs text-gray-500">
                {product.plant_type && (
                  <span>{product.plant_type}</span>
                )}
                {(product.thc_content || product.cbd_content) && (
                  <>
                    {product.plant_type && <span>•</span>}
                    <span>
                      {product.thc_content ? `THC ${product.thc_content}%` : `CBD ${product.cbd_content}%`}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductRecommendations;