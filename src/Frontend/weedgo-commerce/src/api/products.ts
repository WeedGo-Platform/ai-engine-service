import apiClient from './client';

// Types based on actual API response
export interface Product {
  id: string;
  sku: string;
  name: string;
  brand: string;
  category: string;
  sub_category: string;
  plant_type: string | null;
  strain_type: string | null;
  size: number;
  image_url: string;
  gtin: number;
  ocs_item_number: number;
  price: number;
  unit_price: number;
  available_quantity: number;
  in_stock: boolean;
  stock_status: string;
  thc_content: number;
  cbd_content: number;
  batch_count: number;
  batches: string; // JSON string of batch info
  description?: string;
  effects?: string[];
  terpenes?: string[];
}

export interface ProductFilters {
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  min_thc?: number;
  max_thc?: number;
  min_cbd?: number;
  max_cbd?: number;
  effects?: string[];
  in_stock?: boolean;
  sort_by?: 'price_asc' | 'price_desc' | 'name_asc' | 'name_desc' | 'rating' | 'newest';
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  limit: number;
  offset: number;
  page: number;
  total_pages: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image_url?: string;
  product_count: number;
  subcategories?: Category[];
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  description?: string;
  website?: string;
  product_count: number;
}

export interface ProductReview {
  id: string;
  user_id: string;
  user_name: string;
  rating: number;
  comment: string;
  created_at: string;
  helpful_count: number;
  verified_purchase: boolean;
}

export interface ProductSearchRequest {
  query: string;
  filters?: ProductFilters;
  limit?: number;
  offset?: number;
}

// API Functions
export const productsApi = {
  // Browse products with filters - using the actual working endpoint
  browse: async (
    storeId?: string,
    filters?: ProductFilters,
    limit = 20,
    offset = 0
  ): Promise<ProductsResponse> => {
    try {
      const params = new URLSearchParams({
        q: filters?.category || '',  // Can use query for category/search
        limit: String(limit),
        offset: String(offset),
      });

      if (storeId) {
        params.append('store_id', storeId);
      }

      if (filters) {
        if (filters.category) params.append('category', filters.category);
        if (filters.brand) params.append('brand', filters.brand);
        if (filters.min_price) params.append('min_price', String(filters.min_price));
        if (filters.max_price) params.append('max_price', String(filters.max_price));
        if (filters.min_thc) params.append('min_thc', String(filters.min_thc));
        if (filters.max_thc) params.append('max_thc', String(filters.max_thc));
        if (filters.in_stock !== undefined) params.append('in_stock', String(filters.in_stock));
      }

      const response = await apiClient.get<ProductsResponse>(`/api/search/products?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch products:', error);
      return {
        products: [],
        total: 0,
        limit,
        offset,
        page: 1,
        total_pages: 0
      };
    }
  },

  // Get single product by SKU
  getProduct: async (sku: string): Promise<Product | null> => {
    try {
      // First search for the product by SKU
      const response = await apiClient.get<ProductsResponse>(`/api/search/products?q=${sku}&limit=1`);
      if (response.data.products && response.data.products.length > 0) {
        // Find exact match
        const product = response.data.products.find(p => p.sku === sku || p.id === sku);
        return product || response.data.products[0];
      }
      return null;
    } catch (error) {
      console.error('Failed to fetch product:', error);
      return null;
    }
  },

  // Search products
  search: async (request: ProductSearchRequest): Promise<ProductsResponse> => {
    try {
      const params = new URLSearchParams({
        q: request.query,
        limit: String(request.limit || 20),
        offset: String(request.offset || 0),
      });

      const response = await apiClient.get<ProductsResponse>(`/api/search/products?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Search failed:', error);
      return {
        products: [],
        total: 0,
        limit: request.limit || 20,
        offset: request.offset || 0,
        page: 1,
        total_pages: 0
      };
    }
  },

  // Get categories
  getCategories: async (): Promise<Category[]> => {
    try {
      const response = await apiClient.get<Category[]>('/api/kiosk/categories');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return [];
    }
  },

  // Get brands
  getBrands: async (): Promise<Brand[]> => {
    try {
      const response = await apiClient.get<Brand[]>('/api/kiosk/brands');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch brands:', error);
      return [];
    }
  },

  // Get product reviews
  getProductReviews: async (
    productId: string,
    limit = 10,
    offset = 0
  ): Promise<{
    reviews: ProductReview[];
    total: number;
    average_rating: number;
  }> => {
    const response = await apiClient.get(
      `/api/products/${productId}/reviews?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },

  // Submit product review
  submitReview: async (
    productId: string,
    rating: number,
    comment: string
  ): Promise<ProductReview> => {
    const response = await apiClient.post<ProductReview>(
      `/api/products/${productId}/reviews`,
      { rating, comment }
    );
    return response.data;
  },

  // Get related products
  getRelatedProducts: async (productId: string, limit = 6): Promise<Product[]> => {
    const response = await apiClient.get<Product[]>(
      `/api/products/${productId}/related?limit=${limit}`
    );
    return response.data;
  },

  // Get featured products
  getFeaturedProducts: async (storeId: string, limit = 8): Promise<Product[]> => {
    const response = await apiClient.get<Product[]>(
      `/api/stores/${storeId}/featured-products?limit=${limit}`
    );
    return response.data;
  },

  // Get products on sale
  getSaleProducts: async (storeId: string, limit = 12): Promise<Product[]> => {
    const response = await apiClient.get<Product[]>(
      `/api/stores/${storeId}/sale-products?limit=${limit}`
    );
    return response.data;
  },

  // Check product availability
  checkAvailability: async (
    productId: string,
    storeId: string,
    quantity: number
  ): Promise<{
    available: boolean;
    quantity_available: number;
    message?: string;
  }> => {
    const response = await apiClient.post('/api/products/check-availability', {
      product_id: productId,
      store_id: storeId,
      quantity,
    });
    return response.data;
  },
};