import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { AppDispatch, RootState } from '@store';
import {
  fetchProducts,
  fetchCategories,
  fetchBrands,
  setFilters,
  clearFilters,
  setPage,
} from '@features/products/productsSlice';
import { addItem } from '@features/cart/cartSlice';
import { IProduct } from '@templates/types';
import toast from 'react-hot-toast';

const ProductsPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const {
    products,
    categories,
    brands,
    filters,
    total,
    page,
    limit,
    hasMore,
    isLoading,
    error,
  } = useSelector((state: RootState) => state.products);

  const storeId = localStorage.getItem('store_id') || 'store_001';

  // Local state for UI controls
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });
  const [sortBy, setSortBy] = useState<string>('name_asc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Load initial data
  useEffect(() => {
    dispatch(fetchCategories());
    dispatch(fetchBrands());
    dispatch(fetchProducts({ storeId, filters, page, limit }));
  }, [dispatch, storeId]);

  // Handle filter changes
  const handleFilterChange = () => {
    const newFilters: any = {};

    if (selectedCategory) newFilters.category = selectedCategory;
    if (selectedBrand) newFilters.brand = selectedBrand;
    if (priceRange.min > 0) newFilters.min_price = priceRange.min;
    if (priceRange.max < 1000) newFilters.max_price = priceRange.max;
    if (sortBy) newFilters.sort_by = sortBy;

    dispatch(setFilters(newFilters));
    dispatch(fetchProducts({ storeId, filters: newFilters, page: 0, limit }));
  };

  // Handle pagination
  const handleLoadMore = () => {
    if (hasMore && !isLoading) {
      const nextPage = page + 1;
      dispatch(setPage(nextPage));
      dispatch(fetchProducts({ storeId, filters, page: nextPage, limit }));
    }
  };

  // Add to cart
  const handleAddToCart = (product: IProduct) => {
    dispatch(addItem({
      id: product.id,
      sku: product.sku,
      name: product.name,
      price: product.sale_price || product.price,
      quantity: 1,
      image: product.image_url,
      max_quantity: product.quantity_available,
    }));
    toast.success(`${product.name} added to cart!`);
  };

  // Navigate to product detail
  const handleProductClick = (product: IProduct) => {
    navigate(`/products/${product.sku}`);
  };

  // Clear all filters
  const handleClearFilters = () => {
    setSelectedCategory('');
    setSelectedBrand('');
    setPriceRange({ min: 0, max: 1000 });
    setSortBy('name_asc');
    dispatch(clearFilters());
    dispatch(fetchProducts({ storeId, page: 0, limit }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Cannabis Products</h1>

        {/* Filters Section */}
        <div className="flex gap-8 mb-8">
          {/* Sidebar Filters */}
          <div className="w-64 bg-white p-6 rounded-lg shadow-sm h-fit">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold">Filters</h2>
              <button
                onClick={handleClearFilters}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Clear all
              </button>
            </div>

            {/* Category Filter */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">Category</h3>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full p-2 border rounded-lg"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.slug}>
                    {cat.name} ({cat.product_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Brand Filter */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">Brand</h3>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="w-full p-2 border rounded-lg"
              >
                <option value="">All Brands</option>
                {brands.map((brand) => (
                  <option key={brand.id} value={brand.slug}>
                    {brand.name} ({brand.product_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Price Range */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">Price Range</h3>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={priceRange.min}
                  onChange={(e) => setPriceRange({ ...priceRange, min: Number(e.target.value) })}
                  className="w-1/2 p-2 border rounded-lg"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={priceRange.max}
                  onChange={(e) => setPriceRange({ ...priceRange, max: Number(e.target.value) })}
                  className="w-1/2 p-2 border rounded-lg"
                />
              </div>
            </div>

            <button
              onClick={handleFilterChange}
              className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700"
            >
              Apply Filters
            </button>
          </div>

          {/* Products Grid */}
          <div className="flex-1">
            {/* Toolbar */}
            <div className="bg-white p-4 rounded-lg shadow-sm mb-6 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  Showing {products.length} of {total} products
                </span>
              </div>

              <div className="flex items-center gap-4">
                {/* Sort */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="p-2 border rounded-lg"
                >
                  <option value="name_asc">Name (A-Z)</option>
                  <option value="name_desc">Name (Z-A)</option>
                  <option value="price_asc">Price (Low to High)</option>
                  <option value="price_desc">Price (High to Low)</option>
                  <option value="rating">Top Rated</option>
                  <option value="newest">Newest</option>
                </select>

                {/* View Mode */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-200' : 'bg-white'}`}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM13 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-200' : 'bg-white'}`}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {isLoading && products.length === 0 && (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            {/* Products Grid/List */}
            <div className={viewMode === 'grid'
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              : "space-y-4"
            }>
              {products.map((product) => (
                <div
                  key={product.id}
                  className={`bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-shadow cursor-pointer
                    ${viewMode === 'list' ? 'flex' : ''}`}
                  onClick={() => handleProductClick(product)}
                >
                  {/* Product Image */}
                  <div className={viewMode === 'grid' ? 'h-48 overflow-hidden' : 'w-48 h-48 flex-shrink-0'}>
                    <img
                      src={product.image_url || '/placeholder.jpg'}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Product Info */}
                  <div className="p-4 flex-1">
                    <div className="mb-2">
                      <span className="text-xs text-gray-500">{product.brand}</span>
                      <h3 className="font-semibold text-lg">{product.name}</h3>
                    </div>

                    {/* THC/CBD Content */}
                    <div className="flex gap-4 mb-2 text-sm">
                      <span className="text-gray-600">
                        THC: <span className="font-medium">{product.thc_content}</span>
                      </span>
                      <span className="text-gray-600">
                        CBD: <span className="font-medium">{product.cbd_content}</span>
                      </span>
                    </div>

                    {/* Price */}
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        {product.sale_price ? (
                          <div className="flex items-center gap-2">
                            <span className="text-xl font-bold text-primary-600">
                              ${product.sale_price.toFixed(2)}
                            </span>
                            <span className="text-sm text-gray-400 line-through">
                              ${product.price.toFixed(2)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xl font-bold">
                            ${product.price.toFixed(2)}
                          </span>
                        )}
                        <span className="text-sm text-gray-500">/{product.unit_size}</span>
                      </div>

                      {/* Stock Status */}
                      <span className={`text-sm px-2 py-1 rounded-full ${
                        product.in_stock
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {product.in_stock ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </div>

                    {/* Add to Cart Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddToCart(product);
                      }}
                      disabled={!product.in_stock}
                      className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                        product.in_stock
                          ? 'bg-primary-600 text-white hover:bg-primary-700'
                          : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {product.in_stock ? 'Add to Cart' : 'Out of Stock'}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="mt-8 text-center">
                <button
                  onClick={handleLoadMore}
                  disabled={isLoading}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {isLoading ? 'Loading...' : 'Load More Products'}
                </button>
              </div>
            )}

            {/* No Products */}
            {!isLoading && products.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No products found matching your criteria.</p>
                <button
                  onClick={handleClearFilters}
                  className="mt-4 text-primary-600 hover:text-primary-700 underline"
                >
                  Clear filters and try again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductsPage;