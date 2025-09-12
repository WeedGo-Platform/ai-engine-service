import React, { useState, useEffect, useRef } from 'react';
import { Product, productSearchService } from '../../services/productSearch';
import { ProductRecommendationsProps, ProductRecommendation } from '../../types/product.types';
import { useCart } from '../../contexts/CartContext';

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

  // Load recommendations based on current product
  useEffect(() => {
    const loadRecommendations = async () => {
      setIsLoading(true);
      try {
        const allProducts = await productSearchService.loadProducts();
        
        // Filter and score products for recommendations
        const scored = allProducts
          .filter(p => p.id !== currentProduct.id) // Exclude current product
          .map(product => {
            let score = 0;
            let reasons: string[] = [];

            // Same category
            if (product.category === currentProduct.category) {
              score += 3;
              reasons.push('Same category');
            }

            // Same plant type
            if (product.plant_type === currentProduct.plant_type) {
              score += 2;
              reasons.push('Same type');
            }

            // Same strain type
            if (product.strain_type === currentProduct.strain_type) {
              score += 2;
              reasons.push('Same strain');
            }

            // Same brand
            if (product.brand === currentProduct.brand) {
              score += 1;
              reasons.push('Same brand');
            }

            // Similar THC content (within 5%)
            if (product.thc_content && currentProduct.thc_content) {
              const diff = Math.abs(product.thc_content - currentProduct.thc_content);
              if (diff <= 5) {
                score += 1;
                reasons.push('Similar THC');
              }
            }

            // Similar price range (within 20%)
            const priceDiff = Math.abs(product.price - currentProduct.price) / currentProduct.price;
            if (priceDiff <= 0.2) {
              score += 1;
              reasons.push('Similar price');
            }

            // Common terpenes
            if (product.terpenes && currentProduct.terpenes) {
              const commonTerpenes = product.terpenes.filter(t => 
                currentProduct.terpenes?.includes(t)
              );
              if (commonTerpenes.length > 0) {
                score += commonTerpenes.length;
                reasons.push('Similar terpenes');
              }
            }

            return {
              ...product,
              relevanceScore: score,
              reason: reasons[0] || 'You might like'
            } as ProductRecommendation;
          })
          .filter(p => p.relevanceScore > 0) // Only include products with some relevance
          .sort((a, b) => b.relevanceScore - a.relevanceScore)
          .slice(0, maxRecommendations);

        setRecommendations(scored);
      } catch (error) {
        console.error('Error loading recommendations:', error);
        setRecommendations([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecommendations();
  }, [currentProduct, maxRecommendations]);

  // Handle quantity change
  const handleQuantityChange = (productId: string, delta: number) => {
    setQuantities(prev => {
      const currentQty = prev[productId] || 1;
      const newQty = Math.max(1, currentQty + delta);
      return { ...prev, [productId]: newQty };
    });
  };

  // Handle add to cart
  const handleAddToCart = async (product: Product) => {
    const quantity = quantities[product.id] || 1;
    try {
      if (onAddToCart) {
        await onAddToCart(product, quantity);
      } else {
        await addToCart(product, quantity);
      }
      // Reset quantity after successful add
      setQuantities(prev => ({ ...prev, [product.id]: 1 }));
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  // Scroll handlers
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

  // Format price
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  // Get strain type color
  const getStrainTypeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'bg-purple-500';
      case 'sativa': return 'bg-green-500';
      case 'hybrid': return 'bg-blue-500';
      case 'cbd': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">You might also like</h3>
        <div className="flex gap-4 overflow-hidden">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex-shrink-0 w-64 bg-gray-100 rounded-lg animate-pulse">
              <div className="aspect-square bg-gray-200 rounded-t-lg" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
                <div className="h-6 bg-gray-200 rounded w-1/2" />
              </div>
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">You might also like</h3>
        
        {/* Scroll Controls */}
        {recommendations.length > 3 && (
          <div className="flex gap-2">
            <button
              onClick={scrollLeft}
              className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
              aria-label="Scroll left"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={scrollRight}
              className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
              aria-label="Scroll right"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Recommendations Grid */}
      <div 
        ref={scrollContainerRef}
        className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {recommendations.map((product) => (
          <div
            key={product.id}
            className="flex-shrink-0 w-64 bg-white border rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
          >
            {/* Product Image */}
            <div 
              className="aspect-square bg-gray-100 cursor-pointer relative group"
              onClick={() => onProductSelect?.(product)}
            >
              {product.image_url || product.thumbnail_url ? (
                <img
                  src={product.image_url || product.thumbnail_url}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-16 h-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              
              {/* Recommendation Reason Badge */}
              {product.reason && (
                <div className="absolute top-2 left-2 px-2 py-1 bg-white/90 backdrop-blur-sm rounded text-xs font-medium">
                  {product.reason}
                </div>
              )}

              {/* Quick View Overlay */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <span className="text-white font-medium">View Details</span>
              </div>
            </div>

            {/* Product Info */}
            <div className="p-4 space-y-3">
              {/* Name and Brand */}
              <div>
                <h4 
                  className="font-medium text-gray-900 truncate cursor-pointer hover:text-blue-600"
                  onClick={() => onProductSelect?.(product)}
                  title={product.name}
                >
                  {product.name}
                </h4>
                {product.brand && (
                  <p className="text-sm text-gray-600 truncate">{product.brand}</p>
                )}
              </div>

              {/* Badges */}
              <div className="flex gap-1">
                {product.plant_type && (
                  <span className={`px-2 py-0.5 rounded-full text-white text-xs ${getStrainTypeColor(product.plant_type)}`}>
                    {product.plant_type}
                  </span>
                )}
                {(product.thc_content || product.cbd_content) && (
                  <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs">
                    {product.thc_content ? `THC ${product.thc_content}%` : `CBD ${product.cbd_content}%`}
                  </span>
                )}
              </div>

              {/* Price and Stock */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatPrice(product.price)}
                  </p>
                  {product.size && (
                    <p className="text-xs text-gray-500">{product.size}</p>
                  )}
                </div>
                {product.in_stock !== undefined && (
                  <p className={`text-xs ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                    {product.in_stock ? 'In Stock' : 'Out of Stock'}
                  </p>
                )}
              </div>

              {/* Quantity and Add to Cart */}
              <div className="flex items-center gap-2">
                {/* Quantity Controls */}
                <div className="flex items-center border rounded">
                  <button
                    onClick={() => handleQuantityChange(product.id, -1)}
                    className="p-1 hover:bg-gray-100 transition-colors"
                    disabled={!product.in_stock}
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  </button>
                  <span className="px-2 text-sm min-w-[2rem] text-center">
                    {quantities[product.id] || 1}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(product.id, 1)}
                    className="p-1 hover:bg-gray-100 transition-colors"
                    disabled={!product.in_stock}
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>

                {/* Add to Cart Button */}
                <button
                  onClick={() => handleAddToCart(product)}
                  disabled={!product.in_stock}
                  className={`flex-1 py-1.5 px-3 rounded text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                    product.in_stock
                      ? 'bg-blue-500 hover:bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Add
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductRecommendations;