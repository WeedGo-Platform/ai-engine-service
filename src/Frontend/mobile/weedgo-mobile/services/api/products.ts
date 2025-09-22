import { apiClient } from './client';
import {
  Product,
  ProductSearchParams,
  ProductSearchResponse,
  Category,
} from '@/types/api.types';

class ProductService {
  /**
   * Search products with filters
   */
  async searchProducts(params: ProductSearchParams = {}): Promise<ProductSearchResponse> {
    const response = await apiClient.get<ProductSearchResponse>(
      '/api/products/search',
      { params }
    );
    return response.data;
  }

  /**
   * Get all product categories
   */
  async getCategories(): Promise<Category[]> {
    const response = await apiClient.get<{ categories: Category[] }>(
      '/api/products/categories'
    );
    return response.data.categories;
  }

  /**
   * Get single product details
   */
  async getProductDetails(productId: string): Promise<Product> {
    const response = await apiClient.get<Product>(
      `/api/products/${productId}/details`
    );
    return response.data;
  }

  /**
   * Get store-specific inventory
   */
  async getStoreInventory(
    storeId: string,
    params: {
      category?: string;
      subcategory?: string;
      brand?: string;
      strain_type?: string;
      size?: string;
      quick_filter?: 'trending' | 'new' | 'staff-picks';
      search?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<{ products: Product[]; total: number }> {
    const response = await apiClient.get<{ products: Product[]; total: number }>(
      `/api/store-inventory/${storeId}/products`,
      { params }
    );
    return response.data;
  }

  /**
   * Get trending products
   */
  async getTrendingProducts(limit: number = 10): Promise<Product[]> {
    const response = await this.getStoreInventory(
      process.env.EXPO_PUBLIC_STORE_ID || '',
      { quick_filter: 'trending', limit }
    );
    return response.products;
  }

  /**
   * Get new products
   */
  async getNewProducts(limit: number = 10): Promise<Product[]> {
    const response = await this.getStoreInventory(
      process.env.EXPO_PUBLIC_STORE_ID || '',
      { quick_filter: 'new', limit }
    );
    return response.products;
  }

  /**
   * Get staff picks
   */
  async getStaffPicks(limit: number = 10): Promise<Product[]> {
    const response = await this.getStoreInventory(
      process.env.EXPO_PUBLIC_STORE_ID || '',
      { quick_filter: 'staff-picks', limit }
    );
    return response.products;
  }

  /**
   * Get products by category
   */
  async getProductsByCategory(
    category: string,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, category });
  }

  /**
   * Get products by brand
   */
  async getProductsByBrand(
    brand: string,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, brand });
  }

  /**
   * Get products by strain type
   */
  async getProductsByStrainType(
    strainType: 'indica' | 'sativa' | 'hybrid' | 'cbd',
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, strain_type: strainType });
  }

  /**
   * Get products by THC content range
   */
  async getProductsByTHCRange(
    thcMin: number,
    thcMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, thc_min: thcMin, thc_max: thcMax });
  }

  /**
   * Get products by CBD content range
   */
  async getProductsByCBDRange(
    cbdMin: number,
    cbdMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, cbd_min: cbdMin, cbd_max: cbdMax });
  }

  /**
   * Get products by price range
   */
  async getProductsByPriceRange(
    priceMin: number,
    priceMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, price_min: priceMin, price_max: priceMax });
  }

  /**
   * Search products by query string
   */
  async searchByQuery(query: string, params: ProductSearchParams = {}): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, q: query });
  }

  /**
   * Get product recommendations based on a product
   */
  async getRecommendations(productId: string, limit: number = 5): Promise<Product[]> {
    const response = await apiClient.get<{ products: Product[] }>(
      `/api/products/${productId}/recommendations`,
      { params: { limit } }
    );
    return response.data.products;
  }

  /**
   * Get product reviews
   */
  async getProductReviews(
    productId: string,
    params: { limit?: number; offset?: number } = {}
  ): Promise<{ reviews: any[]; total: number }> {
    const response = await apiClient.get<{ reviews: any[]; total: number }>(
      `/api/products/${productId}/reviews`,
      { params }
    );
    return response.data;
  }
}

// Export singleton instance
export const productService = new ProductService();