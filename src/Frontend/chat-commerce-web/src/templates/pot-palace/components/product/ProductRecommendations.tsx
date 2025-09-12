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

  // Load recommendations
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
              reasons.push('Same category');
            }
            if (product.plant_type === currentProduct.plant_type) {
              score += 2;
              reasons.push('Same type');
            }
            if (product.strain_type === currentProduct.strain_type) {
              score += 2;
              reasons.push('Same strain');
            }
            if (product.brand === currentProduct.brand) {
              score += 1;
              reasons.push('Same brand');
            }

            return {
              ...product,
              relevanceScore: score,
              reason: reasons[0] || 'You might like'
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

  const handleQuantityChange = (productId: string, delta: number) => {
    setQuantities(prev => {
      const currentQty = prev[productId] || 1;
      const newQty = Math.max(1, currentQty + delta);
      return { ...prev, [productId]: newQty };
    });
  };

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
      currency: 'USD'
    }).format(price);
  };

  const getStrainTypeStyle = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'bg-gradient-to-r from-purple-500 to-purple-600 text-white';
      case 'sativa': return 'bg-gradient-to-r from-green-500 to-green-600 text-white';
      case 'hybrid': return 'bg-gradient-to-r from-purple-500 to-green-500 text-white';
      case 'cbd': return 'bg-gradient-to-r from-orange-500 to-orange-600 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-purple-800 flex items-center gap-2">
          <svg className="w-6 h-6 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
          </svg>
          You Might Also Like
        </h3>
        <div className="flex gap-4 overflow-hidden">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex-shrink-0 w-64 bg-purple-50 rounded-xl animate-pulse">
              <div className="aspect-square bg-purple-100 rounded-t-xl" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-purple-100 rounded" />
                <div className="h-4 bg-purple-100 rounded w-2/3" />
                <div className="h-6 bg-purple-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-purple-800 flex items-center gap-2">
          <svg className="w-6 h-6 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
          </svg>
          You Might Also Like
        </h3>
        
        {recommendations.length > 3 && (
          <div className="flex gap-2">
            <button
              onClick={scrollLeft}
              className="p-2 rounded-full bg-purple-100 hover:bg-purple-200 transition-colors text-purple-600"
              aria-label="Scroll left"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={scrollRight}
              className="p-2 rounded-full bg-purple-100 hover:bg-purple-200 transition-colors text-purple-600"
              aria-label="Scroll right"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <div 
        ref={scrollContainerRef}
        className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {recommendations.map((product) => (
          <div
            key={product.id}
            className="flex-shrink-0 w-64 bg-gradient-to-br from-purple-50 to-white border-2 border-purple-200 rounded-xl overflow-hidden hover:shadow-xl transition-all hover:scale-105 hover:border-purple-400"
          >
            {/* Product Image */}
            <div 
              className="aspect-square bg-gradient-to-br from-purple-100 to-purple-50 cursor-pointer relative group overflow-hidden"
              onClick={() => onProductSelect?.(product)}
            >
              {product.image_url || product.thumbnail_url ? (
                <img
                  src={product.image_url || product.thumbnail_url}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-16 h-16 text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              
              {/* Recommendation Reason Badge */}
              {product.reason && (
                <div className="absolute top-2 left-2 px-3 py-1 bg-purple-600/90 backdrop-blur-sm rounded-lg text-xs font-medium text-white shadow-lg">
                  ✨ {product.reason}
                </div>
              )}

              {/* Cannabis leaf decoration */}
              <div className="absolute bottom-2 right-2 opacity-20">
                <svg className="w-12 h-12 text-purple-700" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
                </svg>
              </div>

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-purple-900/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-4">
                <span className="text-white font-bold">View Details</span>
              </div>
            </div>

            {/* Product Info */}
            <div className="p-4 space-y-3">
              {/* Name and Brand */}
              <div>
                <h4 
                  className="font-bold text-purple-900 truncate cursor-pointer hover:text-purple-600 transition-colors"
                  onClick={() => onProductSelect?.(product)}
                  title={product.name}
                >
                  {product.name}
                </h4>
                {product.brand && (
                  <p className="text-sm text-purple-600 truncate">{product.brand}</p>
                )}
              </div>

              {/* Badges */}
              <div className="flex gap-1">
                {product.plant_type && (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStrainTypeStyle(product.plant_type)}`}>
                    {product.plant_type}
                  </span>
                )}
                {(product.thc_content || product.cbd_content) && (
                  <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-medium">
                    {product.thc_content ? `THC ${product.thc_content}%` : `CBD ${product.cbd_content}%`}
                  </span>
                )}
              </div>

              {/* Price and Stock */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-bold text-purple-800">
                    {formatPrice(product.price)}
                  </p>
                  {product.size && (
                    <p className="text-xs text-purple-600">{product.size}</p>
                  )}
                </div>
                {product.in_stock !== undefined && (
                  <p className={`text-xs font-medium ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                    {product.in_stock ? '✓ Stock' : '✗ Out'}
                  </p>
                )}
              </div>

              {/* Quantity and Add to Cart */}
              <div className="flex items-center gap-2">
                {/* Quantity Controls */}
                <div className="flex items-center border-2 border-purple-200 rounded-lg overflow-hidden bg-white">
                  <button
                    onClick={() => handleQuantityChange(product.id, -1)}
                    className="p-1 hover:bg-purple-100 transition-colors text-purple-600"
                    disabled={!product.in_stock}
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  </button>
                  <span className="px-2 text-sm min-w-[2rem] text-center font-medium text-purple-800">
                    {quantities[product.id] || 1}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(product.id, 1)}
                    className="p-1 hover:bg-purple-100 transition-colors text-purple-600"
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
                  className={`flex-1 py-1.5 px-3 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-1 ${
                    product.in_stock
                      ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
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