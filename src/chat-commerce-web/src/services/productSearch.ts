import api from './api';

export interface Product {
  id: string;
  name: string;
  brand?: string;
  supplier_name?: string;
  plant_type?: string;
  strain_type?: string;
  category?: string;
  sub_category?: string;
  sub_sub_category?: string;
  size?: string;
  street_name?: string;
  price: number;
  terpenes?: string[];
  size_pack?: string;
  image_url?: string;
  thumbnail_url?: string;
  description?: string;
  thc_content?: number;
  cbd_content?: number;
  in_stock?: boolean;
}

interface SearchCache {
  products: Product[];
  timestamp: number;
  expiryTime: number; // Cache for 5 minutes
}

class ProductSearchService {
  private cache: SearchCache | null = null;
  private loading: boolean = false;
  private loadPromise: Promise<Product[]> | null = null;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  /**
   * Load and cache products from API
   */
  async loadProducts(forceRefresh: boolean = false): Promise<Product[]> {
    // Check if cache is valid
    if (!forceRefresh && this.cache && Date.now() - this.cache.timestamp < this.cache.expiryTime) {
      console.log('Using cached products');
      return this.cache.products;
    }

    // If already loading, return the existing promise
    if (this.loading && this.loadPromise) {
      return this.loadPromise;
    }

    // Start loading
    this.loading = true;
    this.loadPromise = this.fetchProducts();
    
    try {
      const products = await this.loadPromise;
      
      // Cache the results
      this.cache = {
        products,
        timestamp: Date.now(),
        expiryTime: this.CACHE_DURATION
      };
      
      console.log(`Cached ${products.length} products`);
      return products;
    } finally {
      this.loading = false;
      this.loadPromise = null;
    }
  }

  /**
   * Fetch products from API
   */
  private async fetchProducts(): Promise<Product[]> {
    try {
      const response = await api.get('/api/search/products');
      
      // Handle different response structures
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data.products && Array.isArray(response.data.products)) {
        return response.data.products;
      } else if (response.data.data && Array.isArray(response.data.data)) {
        return response.data.data;
      } else {
        console.warn('Unexpected API response structure:', response.data);
        return [];
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      // Return cached data if available
      if (this.cache) {
        console.log('API error, using stale cache');
        return this.cache.products;
      }
      return [];
    }
  }

  /**
   * Get cached products without fetching
   */
  getCachedProducts(): Product[] {
    return this.cache?.products || [];
  }

  /**
   * Search products with multiple filters
   */
  searchProducts(query: string, products?: Product[]): Product[] {
    const productsToSearch = products || this.getCachedProducts();
    
    if (!query || query.trim() === '') {
      return [];
    }

    const searchTerm = query.toLowerCase().trim();
    
    // Filter products based on multiple fields
    const filtered = productsToSearch.filter(product => {
      const searchableFields = [
        product.name,
        product.brand,
        product.supplier_name,
        product.plant_type,
        product.strain_type,
        product.category,
        product.sub_category,
        product.sub_sub_category,
        product.size,
        product.street_name,
        product.size_pack,
        ...(product.terpenes || [])
      ].filter(Boolean).map(field => field!.toLowerCase());

      // Also check price range if query is a number
      const priceMatch = !isNaN(Number(searchTerm)) && 
        Math.abs(product.price - Number(searchTerm)) < product.price * 0.2; // Within 20% of price

      return searchableFields.some(field => field.includes(searchTerm)) || priceMatch;
    });

    // Sort by relevance (name matches first, then other fields)
    return filtered.sort((a, b) => {
      const aNameMatch = a.name.toLowerCase().includes(searchTerm);
      const bNameMatch = b.name.toLowerCase().includes(searchTerm);
      
      if (aNameMatch && !bNameMatch) return -1;
      if (!aNameMatch && bNameMatch) return 1;
      
      // Secondary sort by price
      return a.price - b.price;
    }).slice(0, 10); // Limit to 10 results for dropdown
  }

  /**
   * Advanced search with specific field filters
   */
  advancedSearch(filters: {
    query?: string;
    category?: string;
    plantType?: string;
    strainType?: string;
    minPrice?: number;
    maxPrice?: number;
    inStock?: boolean;
  }, products?: Product[]): Product[] {
    const productsToSearch = products || this.getCachedProducts();
    
    return productsToSearch.filter(product => {
      // Text search
      if (filters.query) {
        const searchTerm = filters.query.toLowerCase();
        const matchesText = [
          product.name,
          product.brand,
          product.supplier_name,
          product.street_name
        ].filter(Boolean).some(field => 
          field!.toLowerCase().includes(searchTerm)
        );
        if (!matchesText) return false;
      }

      // Category filter
      if (filters.category && product.category !== filters.category) {
        return false;
      }

      // Plant type filter
      if (filters.plantType && product.plant_type !== filters.plantType) {
        return false;
      }

      // Strain type filter
      if (filters.strainType && product.strain_type !== filters.strainType) {
        return false;
      }

      // Price range filter
      if (filters.minPrice !== undefined && product.price < filters.minPrice) {
        return false;
      }
      if (filters.maxPrice !== undefined && product.price > filters.maxPrice) {
        return false;
      }

      // Stock filter
      if (filters.inStock !== undefined && product.in_stock !== filters.inStock) {
        return false;
      }

      return true;
    });
  }

  /**
   * Get unique values for filters
   */
  getFilterOptions(): {
    categories: string[];
    plantTypes: string[];
    strainTypes: string[];
    brands: string[];
  } {
    const products = this.getCachedProducts();
    
    return {
      categories: [...new Set(products.map(p => p.category).filter(Boolean))].sort() as string[],
      plantTypes: [...new Set(products.map(p => p.plant_type).filter(Boolean))].sort() as string[],
      strainTypes: [...new Set(products.map(p => p.strain_type).filter(Boolean))].sort() as string[],
      brands: [...new Set(products.map(p => p.brand).filter(Boolean))].sort() as string[]
    };
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache = null;
  }
}

// Export singleton instance
export const productSearchService = new ProductSearchService();