import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ProductService } from '@/services/ProductService';
import { Product, ProductCategory } from '@/types';
import { Button } from '@/components/atoms/Button';
import { Input } from '@/components/atoms/Input';
import { Badge } from '@/components/atoms/Badge';
import { SkeletonCard } from '@/components/atoms/Skeleton';
import { SearchBar } from '@/components/molecules/SearchBar';
import { useDebounce } from '@/hooks/useDebounce';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

/**
 * Refactored Products page demonstrating:
 * - Clean architecture with service layer
 * - Custom hooks for state management
 * - Atomic design components
 * - Loading states with skeletons
 * - Error handling
 * - TypeScript best practices
 */
export const ProductsRefactored: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<ProductCategory | null>(null);
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'rating'>('name');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const productService = new ProductService();
  const searchQuery = searchParams.get('search') || '';
  const debouncedSearch = useDebounce(searchQuery, 500);

  // Load products
  useEffect(() => {
    loadProducts();
  }, [debouncedSearch, selectedCategory, sortBy, page]);

  const loadProducts = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await productService.getProducts({
        search: debouncedSearch,
        category: selectedCategory || undefined,
        minPrice: priceRange.min,
        maxPrice: priceRange.max,
        sortBy,
        sortOrder: 'asc',
        page,
        pageSize: 12
      });

      if (response.data) {
        setProducts(response.data.items);
        setTotalPages(Math.ceil(response.data.total / 12));
      } else if (response.error) {
        setError(response.error);
        toast.error('Failed to load products');
      }
    } catch (err) {
      setError('An unexpected error occurred');
      toast.error('An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (query: string) => {
    setSearchParams({ search: query });
    setPage(1);
  };

  const handleCategoryChange = (category: ProductCategory | null) => {
    setSelectedCategory(category);
    setPage(1);
  };

  const categories: ProductCategory[] = [
    ProductCategory.Flower,
    ProductCategory.Edibles,
    ProductCategory.Concentrates,
    ProductCategory.Vapes,
    ProductCategory.Accessories
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 dark:from-primary-700 dark:to-primary-900 py-16">
        <div className="container-max">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-4">
            Premium Cannabis Products
          </h1>
          <p className="text-lg text-primary-100 mb-8">
            Discover our curated selection of high-quality cannabis products
          </p>

          {/* Search Bar */}
          <SearchBar
            variant="expanded"
            onSearch={handleSearch}
            className="max-w-2xl"
            placeholder="Search for products, strains, or categories..."
          />
        </div>
      </section>

      {/* Filters and Products */}
      <section className="container-max py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Filters */}
          <aside className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 sticky top-4">
              <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Filters
              </h2>

              {/* Categories */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Categories
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => handleCategoryChange(null)}
                    className={clsx(
                      'w-full text-left px-3 py-2 rounded-lg transition-colors',
                      !selectedCategory
                        ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    )}
                  >
                    All Products
                  </button>
                  {categories.map(category => (
                    <button
                      key={category}
                      onClick={() => handleCategoryChange(category)}
                      className={clsx(
                        'w-full text-left px-3 py-2 rounded-lg transition-colors capitalize',
                        selectedCategory === category
                          ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      )}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Price Range
                </h3>
                <div className="space-y-3">
                  <Input
                    type="number"
                    placeholder="Min price"
                    value={priceRange.min}
                    onChange={(e) => setPriceRange({ ...priceRange, min: Number(e.target.value) })}
                    leftIcon={<span className="text-gray-500">$</span>}
                  />
                  <Input
                    type="number"
                    placeholder="Max price"
                    value={priceRange.max}
                    onChange={(e) => setPriceRange({ ...priceRange, max: Number(e.target.value) })}
                    leftIcon={<span className="text-gray-500">$</span>}
                  />
                </div>
              </div>

              {/* Sort By */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Sort By
                </h3>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="name">Name</option>
                  <option value="price">Price</option>
                  <option value="rating">Rating</option>
                </select>
              </div>
            </div>
          </aside>

          {/* Products Grid */}
          <div className="lg:col-span-3">
            {/* Results Header */}
            <div className="flex justify-between items-center mb-6">
              <p className="text-gray-600 dark:text-gray-400">
                {isLoading ? 'Loading...' : `${products.length} products found`}
              </p>

              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </Button>
                <Button variant="ghost" size="sm">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </Button>
              </div>
            </div>

            {/* Loading State */}
            {isLoading && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                <Button onClick={loadProducts} variant="primary">
                  Try Again
                </Button>
              </div>
            )}

            {/* Products Grid */}
            {!isLoading && !error && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {products.map(product => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center mt-8 space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>

                    {[...Array(Math.min(5, totalPages))].map((_, i) => {
                      const pageNum = i + 1;
                      return (
                        <Button
                          key={pageNum}
                          variant={page === pageNum ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setPage(pageNum)}
                        >
                          {pageNum}
                        </Button>
                      );
                    })}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

// Product Card Component
const ProductCard: React.FC<{ product: Product }> = ({ product }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group">
      <div className="relative h-48 overflow-hidden bg-gray-100 dark:bg-gray-700">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
        />
        {product.featured && (
          <Badge variant="warning" className="absolute top-2 right-2">
            Featured
          </Badge>
        )}
        {!product.inStock && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <Badge variant="danger" size="lg">
              Out of Stock
            </Badge>
          </div>
        )}
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2">
            {product.name}
          </h3>
          <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
            ${product.price}
          </span>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {product.description}
        </p>

        <div className="flex items-center justify-between mb-3">
          <div className="flex space-x-2">
            {product.thc && (
              <Badge variant="primary" size="xs">
                THC: {product.thc}%
              </Badge>
            )}
            {product.cbd && (
              <Badge variant="info" size="xs">
                CBD: {product.cbd}%
              </Badge>
            )}
          </div>

          {product.rating && (
            <div className="flex items-center">
              <span className="text-yellow-500">★</span>
              <span className="text-sm text-gray-600 dark:text-gray-400 ml-1">
                {product.rating}
              </span>
            </div>
          )}
        </div>

        <Button
          variant="primary"
          fullWidth
          disabled={!product.inStock}
          className="group-hover:shadow-glow"
        >
          {product.inStock ? 'Add to Cart' : 'Out of Stock'}
        </Button>
      </div>
    </div>
  );
};

export default ProductsRefactored;