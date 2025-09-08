import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Product, productSearchService } from '../../services/productSearch';
import { useCart } from '../../contexts/CartContext';

interface ProductSearchDropdownProps {
  onProductSelect?: (product: Product) => void;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  dropdownClassName?: string;
  resultItemClassName?: string;
  showPrice?: boolean;
  showImage?: boolean;
  showDetails?: boolean;
  maxResults?: number;
  autoFocus?: boolean;
  onClose?: () => void;
}

const ProductSearchDropdown: React.FC<ProductSearchDropdownProps> = ({
  onProductSelect,
  placeholder = "Search products...",
  className = "",
  inputClassName = "",
  dropdownClassName = "",
  resultItemClassName = "",
  showPrice = true,
  showImage = true,
  showDetails = true,
  maxResults = 10,
  autoFocus = false,
  onClose
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [products, setProducts] = useState<Product[]>([]);
  const [quantities, setQuantities] = useState<{ [key: string]: number }>({});
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const [portalRoot, setPortalRoot] = useState<HTMLElement | null>(null);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Get cart context
  const { addToCart: addItemToCart } = useCart();

  // Create portal root on mount
  useEffect(() => {
    const root = document.getElementById('search-dropdown-portal');
    if (!root) {
      const newRoot = document.createElement('div');
      newRoot.id = 'search-dropdown-portal';
      newRoot.style.position = 'fixed';
      newRoot.style.top = '0';
      newRoot.style.left = '0';
      newRoot.style.width = '0';
      newRoot.style.height = '0';
      newRoot.style.pointerEvents = 'none';
      newRoot.style.zIndex = '999999'; // Higher than floating chat portal
      document.body.appendChild(newRoot);
      setPortalRoot(newRoot);
    } else {
      setPortalRoot(root);
    }

    return () => {
      const root = document.getElementById('search-dropdown-portal');
      if (root && root.childNodes.length === 0) {
        root.remove();
      }
    };
  }, []);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node) &&
          dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        onClose?.();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Update dropdown position when open or window resizes
  useEffect(() => {
    const updatePosition = () => {
      if (inputRef.current && isOpen) {
        const rect = inputRef.current.getBoundingClientRect();
        setDropdownPosition({
          top: rect.bottom + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    };

    updatePosition();

    if (isOpen) {
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition);
      return () => {
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition);
      };
    }
  }, [isOpen]);

  // Load products on mount
  useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      try {
        const loadedProducts = await productSearchService.loadProducts();
        setProducts(loadedProducts);
        console.log(`Loaded ${loadedProducts.length} products for search`);
      } catch (error) {
        console.error('Error loading products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadProducts();
  }, []);

  // Handle search with debounce
  const handleSearch = useCallback((searchQuery: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!searchQuery.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    searchTimeoutRef.current = setTimeout(() => {
      const searchResults = productSearchService.searchProducts(searchQuery, products);
      setResults(searchResults.slice(0, maxResults));
      setIsOpen(searchResults.length > 0);
      setSelectedIndex(-1);
    }, 300); // 300ms debounce
  }, [products, maxResults]);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    handleSearch(value);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : results.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleProductSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  // Handle product selection
  const handleProductSelect = (product: Product) => {
    onProductSelect?.(product);
    setQuery('');
    setIsOpen(false);
    setResults([]);
    setSelectedIndex(-1);
  };

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
      await addItemToCart(product, quantity);
      // Reset quantity after successful add
      setQuantities(prev => ({ ...prev, [product.id]: 1 }));
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  // Format price
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  // Get product badge color based on type
  const getTypeBadgeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'bg-purple-500';
      case 'sativa': return 'bg-green-500';
      case 'hybrid': return 'bg-blue-500';
      case 'cbd': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.trim() && results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className={`w-full px-4 py-2 pr-10 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 ${inputClassName}`}
        />
        
        {/* Search Icon */}
        <svg
          className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>

        {/* Loading Spinner */}
        {isLoading && (
          <div className="absolute right-10 top-1/2 transform -translate-y-1/2">
            <svg className="animate-spin h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}
      </div>

      {/* Results Dropdown Portal */}
      {isOpen && results.length > 0 && portalRoot && createPortal(
        <div 
          ref={dropdownRef}
          className={`bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto ${dropdownClassName}`}
          style={{
            position: 'fixed',
            top: `${dropdownPosition.top + 8}px`,
            left: `${dropdownPosition.left}px`,
            width: `${dropdownPosition.width}px`,
            zIndex: 999999,
            pointerEvents: 'auto'
          }}
        >
          {results.map((product, index) => (
            <div
              key={product.id}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`
                flex items-center gap-3 p-3 transition-colors
                ${index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'}
                ${index !== results.length - 1 ? 'border-b border-gray-100' : ''}
                ${resultItemClassName}
              `}
            >
              {/* Product Image */}
              {showImage && (
                <div className="flex-shrink-0">
                  {product.thumbnail_url || product.image_url ? (
                    <img
                      src={product.thumbnail_url || product.image_url}
                      alt={product.name}
                      className="w-12 h-12 object-cover rounded"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/placeholder-product.png';
                      }}
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                      <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                </div>
              )}

              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Product Name - Clickable */}
                    <p 
                      className="font-medium text-gray-900 truncate cursor-pointer hover:text-blue-600"
                      onClick={() => handleProductSelect(product)}
                    >
                      {product.name}
                    </p>

                    {/* Product Details */}
                    {showDetails && (
                      <div className="flex items-center gap-2 mt-1">
                        {/* Brand */}
                        {product.brand && (
                          <span className="text-xs text-gray-500">
                            {product.brand}
                          </span>
                        )}

                        {/* Type Badges */}
                        {product.plant_type && (
                          <span className={`text-xs px-2 py-0.5 rounded-full text-white ${getTypeBadgeColor(product.plant_type)}`}>
                            {product.plant_type}
                          </span>
                        )}

                        {/* Category */}
                        {product.sub_category && (
                          <span className="text-xs text-gray-500">
                            {product.sub_category}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Additional Info */}
                    {showDetails && (
                      <div className="flex items-center gap-3 mt-1">
                        {/* THC/CBD Content */}
                        {(product.thc_content || product.cbd_content) && (
                          <div className="flex items-center gap-2 text-xs text-gray-600">
                            {product.thc_content && (
                              <span>THC: {product.thc_content}%</span>
                            )}
                            {product.cbd_content && (
                              <span>CBD: {product.cbd_content}%</span>
                            )}
                          </div>
                        )}

                        {/* Size */}
                        {product.size && (
                          <span className="text-xs text-gray-500">
                            {product.size}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Price and Controls */}
                  <div className="flex flex-col items-end gap-2 ml-3">
                    {/* Price */}
                    {showPrice && (
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          {formatPrice(product.price)}
                        </p>
                        {/* Stock Status */}
                        {product.in_stock !== undefined && (
                          <p className={`text-xs ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                            {product.in_stock ? 'In Stock' : 'Out of Stock'}
                          </p>
                        )}
                      </div>
                    )}
                    
                    {/* Quantity Controls and Cart Button */}
                    <div className="flex items-center gap-2">
                      {/* Quantity Controls */}
                      <div className="flex items-center gap-1 bg-gray-100 rounded-lg">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleQuantityChange(product.id, -1);
                          }}
                          className="p-1 hover:bg-gray-200 rounded-l-lg transition-colors"
                          title="Decrease quantity"
                        >
                          <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                          </svg>
                        </button>
                        
                        <span className="px-2 min-w-[2rem] text-center text-sm font-medium">
                          {quantities[product.id] || 1}
                        </span>
                        
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleQuantityChange(product.id, 1);
                          }}
                          className="p-1 hover:bg-gray-200 rounded-r-lg transition-colors"
                          title="Increase quantity"
                        >
                          <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                        </button>
                      </div>
                      
                      {/* Add to Cart Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToCart(product);
                        }}
                        className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                        title="Add to cart"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>,
        portalRoot
      )}

      {/* No Results Portal */}
      {isOpen && query.trim() && results.length === 0 && !isLoading && portalRoot && createPortal(
        <div
          ref={dropdownRef}
          className={`bg-white border border-gray-200 rounded-lg shadow-lg p-4 ${dropdownClassName}`}
          style={{
            position: 'fixed',
            top: `${dropdownPosition.top + 8}px`,
            left: `${dropdownPosition.left}px`,
            width: `${dropdownPosition.width}px`,
            zIndex: 999999,
            pointerEvents: 'auto'
          }}
        >
          <p className="text-gray-500 text-center">
            No products found for "{query}"
          </p>
        </div>,
        portalRoot
      )}
    </div>
  );
};

export default ProductSearchDropdown;