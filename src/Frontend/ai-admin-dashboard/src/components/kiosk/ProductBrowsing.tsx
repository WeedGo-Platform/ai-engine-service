import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import {
  Search, Filter, ShoppingCart, Info, Plus, Minus,
  ChevronLeft, ChevronRight, MessageCircle, Star,
  TrendingUp, Clock, Award, Leaf, Cigarette, Cookie,
  Sparkles, Wind, Droplet, Wrench
} from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import { useKioskSession } from '../../hooks/useKioskSession';
import ProductCard from './ProductCard';
import CategoryFilter from './CategoryFilter';
import AIAssistant from './AIAssistant';
import ProductDetailsModal from './ProductDetailsModal';

interface ProductBrowsingProps {
  onCartClick: () => void;
  currentStore: any;
}

interface Product {
  id: string;
  name: string;
  product_name?: string;
  brand: string;
  category: string;
  subcategory: string;
  sub_category?: string; // Alias for subcategory
  price: number;
  retail_price?: number;
  display_price?: string;
  images?: string[];
  primary_image?: string;
  image_url?: string;
  thc_content?: number;
  cbd_content?: number;
  thc_badge?: string;
  cbd_badge?: string;
  description?: string;
  effects?: string[];
  terpenes?: string[];
  quantity_available: number;
  rating?: number;
  review_count?: number;
  plant_type?: string; // For strain type
  strain_type?: string; // Alias for plant_type
  size?: string; // Product size
}

export default function ProductBrowsing({ onCartClick, currentStore }: ProductBrowsingProps) {
  const {
    cart,
    addToCart,
    cartItemCount,
    language,
    recommendations,
    setRecommendations,
    showChat,
    setShowChat
  } = useKiosk();
  const { session, updateActivity } = useKioskSession();

  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubcategory, setSelectedSubcategory] = useState<string | null>(null);
  const [selectedStrainType, setSelectedStrainType] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [selectedQuickFilter, setSelectedQuickFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('name');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Dynamic filter options based on inventory
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [availableSubcategories, setAvailableSubcategories] = useState<string[]>([]);
  const [availableStrainTypes, setAvailableStrainTypes] = useState<string[]>([]);
  const [availableSizes, setAvailableSizes] = useState<string[]>([]);

  // Use dynamic filter values from available inventory
  const subcategories = availableSubcategories;
  const strainTypes = availableStrainTypes;
  const sizes = availableSizes;

  const quickFilters = [
    { id: 'trending', name: 'Trending Now', icon: TrendingUp, color: 'green' },
    { id: 'new', name: 'New Arrivals', icon: Clock, color: 'blue' },
    { id: 'staff-picks', name: 'Staff Picks', icon: Award, color: 'purple' },
  ];

  // Fetch all products initially to get available filters
  useEffect(() => {
    if (currentStore?.id) {
      fetchAllProductsForFilters();
    }
  }, [currentStore]);

  // Fetch products
  useEffect(() => {
    fetchProducts();
  }, [selectedSubcategory, selectedStrainType, selectedSize, selectedQuickFilter, sortBy, page, currentStore]);

  // Fetch recommendations
  useEffect(() => {
    if (session?.session_id) {
      fetchRecommendations();
    }
  }, [session, cart]);

  // Fetch all products to extract available filter values
  const fetchAllProductsForFilters = async () => {
    console.log('fetchAllProductsForFilters called with store:', currentStore?.id);
    try {
      const params = new URLSearchParams({
        store_id: currentStore?.id || '',
        page: '1',
        limit: '1000', // Get all products to extract filter values
        sort_by: 'name',
      });

      const response = await fetch(getApiUrl(`/api/kiosk/products/browse?${params}`));
      const data = await response.json();
      console.log('Fetched products for filters:', data);

      if (data.products && Array.isArray(data.products)) {
        const allProds = data.products;
        console.log('Sample product structure:', allProds[0]);
        setAllProducts(allProds);

        // Extract unique subcategories
        const subcats = [...new Set(allProds
          .map((p: Product) => p.subcategory || p.sub_category)
          .filter(Boolean)
        )].sort();
        console.log('Available subcategories:', subcats);
        setAvailableSubcategories(subcats);

        // Extract unique plant types/strain types
        const strains = [...new Set(allProds
          .map((p: Product) => p.plant_type || p.strain_type)
          .filter(Boolean)
        )].sort();
        console.log('Available strain types:', strains);
        setAvailableStrainTypes(strains);

        // Extract unique sizes
        const productSizes = [...new Set(allProds
          .map((p: Product) => p.size)
          .filter(Boolean)
        )].sort((a, b) => {
          // Sort sizes numerically
          const getNumericValue = (size: string) => {
            const match = size.match(/(\d+\.?\d*)/);
            return match ? parseFloat(match[1]) : 0;
          };
          return getNumericValue(a) - getNumericValue(b);
        });
        console.log('Available sizes:', productSizes);
        setAvailableSizes(productSizes);
      } else {
        console.log('No products returned or invalid format:', data);
      }
    } catch (error) {
      console.error('Error fetching products for filters:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        store_id: currentStore?.id || '',
        page: page.toString(),
        limit: '12',
        sort_by: sortBy,
      });

      if (selectedSubcategory) params.append('subcategory', selectedSubcategory);
      if (selectedStrainType) params.append('strain_type', selectedStrainType);
      if (selectedSize) params.append('size', selectedSize);
      if (selectedQuickFilter) params.append('filter', selectedQuickFilter);
      if (searchTerm) params.append('search', searchTerm);
      if (session?.session_id) params.append('session_id', session.session_id);

      console.log('Fetching with params:', params.toString()); // Debug what filters are being sent
      const response = await fetch(`${getApiUrl('/api/kiosk/products/browse')}?${params}`);

      if (response.ok) {
        const data = await response.json();
        console.log('Kiosk API Response:', data); // Debug log
        console.log('Products array:', data.products); // Debug log
        console.log('Current filters - Subcategory:', selectedSubcategory, 'Strain:', selectedStrainType, 'Size:', selectedSize);
        setProducts(data.products || []);
        setFilteredProducts(data.products || []);
        setTotalPages(data.total_pages || Math.ceil(data.total / 12));
      } else {
        console.error('Failed to fetch products:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await fetch(getApiUrl('/api/kiosk/products/recommendations'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session?.session_id,
          store_id: currentStore.id,
          cart_items: cart.map(item => ({
            product_id: item.productId,
            category: item.category
          }))
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    updateActivity();

    if (term.trim() === '') {
      setFilteredProducts(products);
    } else {
      const filtered = products.filter(product =>
        product.name.toLowerCase().includes(term.toLowerCase()) ||
        product.brand?.toLowerCase().includes(term.toLowerCase()) ||
        product.description?.toLowerCase().includes(term.toLowerCase())
      );
      setFilteredProducts(filtered);
    }
  };

  const handleFilterChange = (filterType: string, value: string | null) => {
    switch(filterType) {
      case 'subcategory':
        // Toggle off if clicking the same subcategory, otherwise select the new one
        setSelectedSubcategory(selectedSubcategory === value ? null : value);
        break;
      case 'strain':
        // Toggle off if clicking the same strain, otherwise select the new one
        setSelectedStrainType(selectedStrainType === value ? null : value);
        break;
      case 'size':
        // Toggle off if clicking the same size, otherwise select the new one
        setSelectedSize(selectedSize === value ? null : value);
        break;
      case 'quick':
        // Toggle off if clicking the same quick filter, otherwise select the new one
        setSelectedQuickFilter(selectedQuickFilter === value ? null : value);
        break;
    }
    setPage(1);
    updateActivity();
  };

  const handleAddToCart = (product: Product) => {
    addToCart({
      id: `${product.id}-${Date.now()}`,
      productId: product.id,
      name: product.name,
      price: product.retail_price,
      quantity: 1,
      image: product.image_url,
      thc: product.thc_content,
      cbd: product.cbd_content,
      category: product.category,
      subcategory: product.subcategory
    });
    updateActivity();
  };

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product);
    updateActivity();
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-800">Browse Products</h1>
            <span className="text-sm text-gray-500">{currentStore?.name || 'Select Store'}</span>
          </div>

          {/* Cart Button */}
          <button
            onClick={onCartClick}
            className="relative p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <ShoppingCart className="w-6 h-6" />
            {cartItemCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
                {cartItemCount}
              </span>
            )}
          </button>
        </div>

        {/* Search Bar */}
        <div className="mt-4 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search products..."
            className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:border-primary-500 text-lg"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Filters */}
        <div className="w-72 bg-white border-r overflow-y-auto">
          <div className="p-4 space-y-6">
            {/* Subcategories */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <Filter className="w-4 h-4 mr-2" />
                Subcategories ({subcategories.length})
              </h3>
              <div className="space-y-1">
                {subcategories.length === 0 ? (
                  <p className="text-sm text-gray-500">Loading filters...</p>
                ) : subcategories.map(subcat => (
                  <button
                    key={subcat}
                    onClick={() => handleFilterChange('subcategory', subcat)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedSubcategory === subcat
                        ? 'bg-primary-100 text-primary-700 font-medium'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {subcat}
                  </button>
                ))}
              </div>
            </div>

            {/* Plant Type (Strain Type) */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <Leaf className="w-4 h-4 mr-2" />
                Plant Type ({strainTypes.length})
              </h3>
              <div className="space-y-1">
                {strainTypes.length === 0 ? (
                  <p className="text-sm text-gray-500">Loading filters...</p>
                ) : strainTypes.map(strain => (
                  <button
                    key={strain}
                    onClick={() => handleFilterChange('strain', strain)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedStrainType === strain
                        ? 'bg-green-100 text-green-700 font-medium'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {strain}
                  </button>
                ))}
              </div>
            </div>

            {/* Sizes */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <Sparkles className="w-4 h-4 mr-2" />
                Sizes ({sizes.length})
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {sizes.length === 0 ? (
                  <p className="text-sm text-gray-500 col-span-3">Loading filters...</p>
                ) : sizes.map(size => (
                  <button
                    key={size}
                    onClick={() => handleFilterChange('size', size)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedSize === size
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Filters */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3">Quick Filters</h3>
              <div className="space-y-2">
                {quickFilters.map(filter => {
                  const Icon = filter.icon;
                  const isActive = selectedQuickFilter === filter.id;
                  const bgColor = isActive
                    ? `bg-${filter.color}-100`
                    : `bg-${filter.color}-50 hover:bg-${filter.color}-100`;
                  const textColor = `text-${filter.color}-700`;

                  return (
                    <button
                      key={filter.id}
                      onClick={() => handleFilterChange('quick', filter.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center ${
                        isActive
                          ? `${bgColor} ${textColor} font-medium`
                          : `${bgColor} ${textColor}`
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {filter.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Sort Options */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3">Sort By</h3>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary-500 bg-white"
              >
                <option value="name">Name (A-Z)</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="thc_high">THC: High to Low</option>
                <option value="cbd_high">CBD: High to Low</option>
                <option value="size_large">Size: Large to Small</option>
                <option value="popular">Most Popular</option>
              </select>
            </div>

            {/* Active Filters Summary */}
            {(selectedSubcategory || selectedStrainType || selectedSize || selectedQuickFilter) && (
              <div className="pt-4 border-t">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-700">Active Filters</h4>
                  <button
                    onClick={() => {
                      setSelectedSubcategory(null);
                      setSelectedStrainType(null);
                      setSelectedSize(null);
                      setSelectedQuickFilter(null);
                    }}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    Clear All
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedSubcategory && (
                    <span className="inline-flex items-center px-2 py-1 bg-primary-50 text-primary-700 rounded-full text-xs">
                      {selectedSubcategory}
                      <button
                        onClick={() => setSelectedSubcategory(null)}
                        className="ml-1 hover:text-primary-900"
                      >
                        ×
                      </button>
                    </span>
                  )}
                  {selectedStrainType && (
                    <span className="inline-flex items-center px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs">
                      {selectedStrainType}
                      <button
                        onClick={() => setSelectedStrainType(null)}
                        className="ml-1 hover:text-green-900"
                      >
                        ×
                      </button>
                    </span>
                  )}
                  {selectedSize && (
                    <span className="inline-flex items-center px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                      {selectedSize}
                      <button
                        onClick={() => setSelectedSize(null)}
                        className="ml-1 hover:text-blue-900"
                      >
                        ×
                      </button>
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Products Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="grid grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                  <div className="h-48 bg-gray-200 rounded-lg mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ) : (
            <>
              {/* Recommendations Section */}
              {recommendations.length > 0 && (
                <div className="mb-6">
                  <h2 className="text-xl font-semibold mb-4 text-gray-700">
                    Recommended for You
                  </h2>
                  <div className="grid grid-cols-3 gap-4">
                    {recommendations.slice(0, 3).map(product => (
                      <ProductCard
                        key={product.id}
                        product={product}
                        onAddToCart={() => handleAddToCart(product)}
                        onClick={() => handleProductClick(product)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Products Grid */}
              {filteredProducts.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">No products found. Try adjusting your filters.</p>
                </div>
              ) : (
              <div className="grid grid-cols-3 gap-6">
                {filteredProducts.map(product => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onAddToCart={() => handleAddToCart(product)}
                    onClick={() => handleProductClick(product)}
                  />
                ))}
              </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex justify-center items-center space-x-4">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg bg-white border hover:bg-gray-50 disabled:opacity-50"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-gray-600">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg bg-white border hover:bg-gray-50 disabled:opacity-50"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* AI Assistant Button */}
      <button
        onClick={() => setShowChat(!showChat)}
        className="fixed bottom-6 right-6 p-4 bg-primary-600 text-white rounded-full shadow-lg hover:bg-primary-700 transition-all transform hover:scale-110"
      >
        <MessageCircle className="w-6 h-6" />
      </button>

      {/* AI Assistant Modal */}
      {showChat && (
        <AIAssistant
          isOpen={showChat}
          onClose={() => setShowChat(false)}
          currentStore={currentStore}
        />
      )}

      {/* Product Detail Modal */}
      {selectedProduct && (
        <ProductDetailsModal
          product={selectedProduct}
          isOpen={!!selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onAddToCart={(quantity: number) => {
            for (let i = 0; i < quantity; i++) {
              handleAddToCart(selectedProduct);
            }
            setSelectedProduct(null);
          }}
        />
      )}
    </div>
  );
}